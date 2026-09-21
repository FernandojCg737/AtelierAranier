"""CU01 asistencia: ventana de 5 min + falta automatica, hora Bolivia, foto,
validacion de ubicacion contra la sucursal (pedido del usuario)

- Reemplaza "liberado_manual_en" por "ventana_inicio": la clave ya no queda
  liberada indefinidamente, solo por 5 minutos desde que se libera (manual
  o automatico). Pasada la ventana sin marcar, se considera falta (se
  calcula al vuelo comparando contra marcado_asistencia, no se persiste).
- Todos los calculos de "ahora" pasan a usar la hora de Bolivia
  (America/La_Paz, UTC-4 fijo, sin horario de verano) en vez de la hora del
  servidor (que corre en UTC en Docker) -- antes la hora de liberacion
  configurada se comparaba contra UTC, liberando 4 horas antes de lo que el
  administrador esperaba.
- marcado_asistencia.foto_url: foto de verificacion que el empleado se
  toma al marcar.
- sucursal.latitud/longitud (agregadas en el modelo, aca solo se valida
  contra ellas): si la sucursal del empleado tiene coordenadas cargadas,
  sp_marcar_asistencia rechaza el marcado si esta a mas de 200 metros
  (formula de Haversine). Si la sucursal no tiene coordenadas, no se valida.

Revision ID: c3d7f1a8e042
Revises: b8f4a2e916c7
Create Date: 2026-09-21

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "c3d7f1a8e042"
down_revision = "b8f4a2e916c7"
branch_labels = None
depends_on = None

RADIO_MAXIMO_METROS = 200

COLUMNAS_SQL = """
ALTER TABLE sucursal ADD COLUMN IF NOT EXISTS latitud DOUBLE PRECISION;
ALTER TABLE sucursal ADD COLUMN IF NOT EXISTS longitud DOUBLE PRECISION;
ALTER TABLE marcado_asistencia ADD COLUMN IF NOT EXISTS foto_url VARCHAR(500);
ALTER TABLE configuracion_asistencia ADD COLUMN IF NOT EXISTS ventana_inicio TIMESTAMP;
"""

COLUMNAS_SQL_DOWN = """
ALTER TABLE configuracion_asistencia DROP COLUMN IF EXISTS ventana_inicio;
ALTER TABLE marcado_asistencia DROP COLUMN IF EXISTS foto_url;
ALTER TABLE sucursal DROP COLUMN IF EXISTS longitud;
ALTER TABLE sucursal DROP COLUMN IF EXISTS latitud;
"""

FUNCIONES_SQL = f"""
DROP FUNCTION IF EXISTS fn_estado_asistencia_hoy();
DROP FUNCTION IF EXISTS sp_marcar_asistencia(INTEGER, VARCHAR, DOUBLE PRECISION, DOUBLE PRECISION);

CREATE OR REPLACE FUNCTION fn_bolivia_now()
RETURNS TIMESTAMP AS $$
    SELECT now() AT TIME ZONE 'America/La_Paz';
$$ LANGUAGE sql STABLE;

CREATE OR REPLACE FUNCTION fn_estado_asistencia_hoy()
RETURNS TABLE (
    codigo VARCHAR, hora_liberacion TIME, liberado BOOLEAN, ventana_cerrada BOOLEAN,
    ventana_inicio TIMESTAMP, codigo_fecha DATE
) AS $$
DECLARE
    v_codigo VARCHAR(10);
    v_hora TIME;
    v_ventana_inicio TIMESTAMP;
    v_hoy_bolivia DATE;
    v_ahora_bolivia TIMESTAMP;
BEGIN
    v_ahora_bolivia := fn_bolivia_now();
    v_hoy_bolivia := v_ahora_bolivia::DATE;

    -- barrido perezoso: si la clave guardada es de otro dia (hora Bolivia),
    -- se genera una nueva y se resetea la ventana.
    UPDATE configuracion_asistencia c
    SET codigo = LPAD(FLOOR(RANDOM() * 900000 + 100000)::TEXT, 6, '0'),
        codigo_fecha = v_hoy_bolivia,
        ventana_inicio = NULL
    WHERE c.id = 1 AND (c.codigo_fecha IS NULL OR c.codigo_fecha != v_hoy_bolivia);

    SELECT c.codigo, c.hora_liberacion, c.ventana_inicio
    INTO v_codigo, v_hora, v_ventana_inicio
    FROM configuracion_asistencia c WHERE c.id = 1;

    -- disparo automatico: si todavia no arranco la ventana hoy y ya se
    -- paso la hora configurada (hora Bolivia), arranca ahora mismo. Con
    -- barrido perezoso esto puede arrancar unos minutos tarde si nadie
    -- consulta justo a esa hora -- aceptado, no hay proceso en segundo
    -- plano en este proyecto.
    IF v_ventana_inicio IS NULL AND v_ahora_bolivia::TIME >= v_hora THEN
        UPDATE configuracion_asistencia SET ventana_inicio = v_ahora_bolivia WHERE id = 1;
        v_ventana_inicio := v_ahora_bolivia;
    END IF;

    RETURN QUERY SELECT
        v_codigo,
        v_hora,
        (v_ventana_inicio IS NOT NULL AND v_ahora_bolivia < v_ventana_inicio + INTERVAL '5 minutes'),
        (v_ventana_inicio IS NOT NULL AND v_ahora_bolivia >= v_ventana_inicio + INTERVAL '5 minutes'),
        v_ventana_inicio,
        v_hoy_bolivia;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_liberar_asistencia_manual()
RETURNS VOID AS $$
BEGIN
    PERFORM * FROM fn_estado_asistencia_hoy();
    UPDATE configuracion_asistencia SET ventana_inicio = fn_bolivia_now() WHERE id = 1;
END;
$$ LANGUAGE plpgsql;

-- Haversine en metros entre dos puntos lat/lng.
CREATE OR REPLACE FUNCTION fn_distancia_metros(lat1 DOUBLE PRECISION, lng1 DOUBLE PRECISION, lat2 DOUBLE PRECISION, lng2 DOUBLE PRECISION)
RETURNS DOUBLE PRECISION AS $$
DECLARE
    r DOUBLE PRECISION := 6371000; -- radio de la Tierra en metros
    dlat DOUBLE PRECISION := RADIANS(lat2 - lat1);
    dlng DOUBLE PRECISION := RADIANS(lng2 - lng1);
    a DOUBLE PRECISION;
BEGIN
    a := SIN(dlat / 2) ^ 2 + COS(RADIANS(lat1)) * COS(RADIANS(lat2)) * SIN(dlng / 2) ^ 2;
    RETURN r * 2 * ASIN(SQRT(a));
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION sp_marcar_asistencia(
    p_empleado_id INTEGER, p_codigo VARCHAR, p_latitud DOUBLE PRECISION, p_longitud DOUBLE PRECISION, p_foto_url VARCHAR
)
RETURNS INTEGER AS $$
DECLARE
    v_estado RECORD;
    v_sucursal RECORD;
    v_distancia DOUBLE PRECISION;
    v_id INTEGER;
BEGIN
    SELECT * INTO v_estado FROM fn_estado_asistencia_hoy();

    IF v_estado.ventana_cerrada THEN
        RAISE EXCEPTION 'La ventana de 5 minutos para marcar ya se cerro.';
    END IF;

    IF NOT v_estado.liberado THEN
        RAISE EXCEPTION 'La clave de asistencia todavia no fue liberada.';
    END IF;

    IF p_codigo IS NULL OR p_codigo != v_estado.codigo THEN
        RAISE EXCEPTION 'La clave ingresada no es correcta.';
    END IF;

    IF EXISTS (SELECT 1 FROM marcado_asistencia WHERE empleado_id = p_empleado_id AND fecha = v_estado.codigo_fecha) THEN
        RAISE EXCEPTION 'Ya marcaste tu asistencia hoy.';
    END IF;

    SELECT s.latitud, s.longitud INTO v_sucursal
    FROM empleado e JOIN sucursal s ON s.id = e.sucursal_id
    WHERE e.id = p_empleado_id;

    IF v_sucursal.latitud IS NOT NULL AND v_sucursal.longitud IS NOT NULL THEN
        v_distancia := fn_distancia_metros(p_latitud, p_longitud, v_sucursal.latitud, v_sucursal.longitud);
        IF v_distancia > {RADIO_MAXIMO_METROS} THEN
            RAISE EXCEPTION 'Estas a % metros de tu sucursal (maximo {RADIO_MAXIMO_METROS}m). No se pudo marcar.', ROUND(v_distancia::NUMERIC, 0);
        END IF;
    END IF;

    INSERT INTO marcado_asistencia (empleado_id, fecha, latitud, longitud, foto_url)
    VALUES (p_empleado_id, v_estado.codigo_fecha, p_latitud, p_longitud, p_foto_url)
    RETURNING id INTO v_id;

    RETURN v_id;
END;
$$ LANGUAGE plpgsql;
"""

FUNCIONES_SQL_DOWN = """
DROP FUNCTION IF EXISTS sp_marcar_asistencia(INTEGER, VARCHAR, DOUBLE PRECISION, DOUBLE PRECISION, VARCHAR);
DROP FUNCTION IF EXISTS fn_distancia_metros(DOUBLE PRECISION, DOUBLE PRECISION, DOUBLE PRECISION, DOUBLE PRECISION);
DROP FUNCTION IF EXISTS sp_liberar_asistencia_manual();
DROP FUNCTION IF EXISTS fn_estado_asistencia_hoy();
DROP FUNCTION IF EXISTS fn_bolivia_now();
"""

# firma vieja de sp_marcar_asistencia (4 args, sin foto) que reemplaza esta migracion
FUNCIONES_SQL_DOWN_RESTORE_OLD = """
CREATE OR REPLACE FUNCTION sp_marcar_asistencia(p_empleado_id INTEGER, p_codigo VARCHAR, p_latitud DOUBLE PRECISION, p_longitud DOUBLE PRECISION)
RETURNS INTEGER AS $$
DECLARE
    v_estado RECORD;
    v_id INTEGER;
BEGIN
    SELECT * INTO v_estado FROM fn_estado_asistencia_hoy();
    IF NOT v_estado.liberado THEN
        RAISE EXCEPTION 'La clave de asistencia todavia no fue liberada.';
    END IF;
    IF p_codigo IS NULL OR p_codigo != v_estado.codigo THEN
        RAISE EXCEPTION 'La clave ingresada no es correcta.';
    END IF;
    IF EXISTS (SELECT 1 FROM marcado_asistencia WHERE empleado_id = p_empleado_id AND fecha = CURRENT_DATE) THEN
        RAISE EXCEPTION 'Ya marcaste tu asistencia hoy.';
    END IF;
    INSERT INTO marcado_asistencia (empleado_id, fecha, latitud, longitud)
    VALUES (p_empleado_id, CURRENT_DATE, p_latitud, p_longitud)
    RETURNING id INTO v_id;
    RETURN v_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_liberar_asistencia_manual()
RETURNS VOID AS $$
BEGIN
    PERFORM * FROM fn_estado_asistencia_hoy();
    UPDATE configuracion_asistencia SET liberado_manual_en = now() WHERE id = 1;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_estado_asistencia_hoy()
RETURNS TABLE (codigo VARCHAR, hora_liberacion TIME, liberado BOOLEAN, codigo_fecha DATE) AS $$
DECLARE
    v_codigo VARCHAR(10);
    v_hora TIME;
    v_liberado_manual TIMESTAMP;
BEGIN
    UPDATE configuracion_asistencia c
    SET codigo = LPAD(FLOOR(RANDOM() * 900000 + 100000)::TEXT, 6, '0'),
        codigo_fecha = CURRENT_DATE,
        liberado_manual_en = NULL
    WHERE c.id = 1 AND (c.codigo_fecha IS NULL OR c.codigo_fecha != CURRENT_DATE);
    SELECT c.codigo, c.hora_liberacion, c.liberado_manual_en
    INTO v_codigo, v_hora, v_liberado_manual
    FROM configuracion_asistencia c WHERE c.id = 1;
    RETURN QUERY SELECT v_codigo, v_hora, (v_liberado_manual IS NOT NULL OR CURRENT_TIME >= v_hora), CURRENT_DATE;
END;
$$ LANGUAGE plpgsql;
"""


SP_SUCURSAL_CON_COORDENADAS = """
DROP FUNCTION IF EXISTS sp_crear_sucursal(VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR);
CREATE OR REPLACE FUNCTION sp_crear_sucursal(
    p_nombre VARCHAR, p_ciudad_nombre VARCHAR, p_departamento VARCHAR, p_direccion VARCHAR,
    p_horario_atencion VARCHAR, p_telefono VARCHAR, p_estado VARCHAR,
    p_latitud DOUBLE PRECISION, p_longitud DOUBLE PRECISION
) RETURNS INTEGER AS $$
DECLARE
    v_ciudad_id INTEGER;
    v_sucursal_id INTEGER;
BEGIN
    v_ciudad_id := fn_get_or_create_ciudad(p_ciudad_nombre, p_departamento);

    INSERT INTO sucursal (nombre, ciudad_id, direccion, horario_atencion, telefono, estado, fecha_creacion, latitud, longitud)
    VALUES (p_nombre, v_ciudad_id, p_direccion, p_horario_atencion, p_telefono, p_estado, CURRENT_DATE, p_latitud, p_longitud)
    RETURNING id INTO v_sucursal_id;

    RETURN v_sucursal_id;
END;
$$ LANGUAGE plpgsql;

DROP FUNCTION IF EXISTS sp_actualizar_sucursal(INTEGER, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR);
CREATE OR REPLACE FUNCTION sp_actualizar_sucursal(
    p_id INTEGER, p_nombre VARCHAR, p_ciudad_nombre VARCHAR, p_departamento VARCHAR, p_direccion VARCHAR,
    p_horario_atencion VARCHAR, p_telefono VARCHAR, p_estado VARCHAR,
    p_latitud DOUBLE PRECISION, p_longitud DOUBLE PRECISION
) RETURNS VOID AS $$
DECLARE
    v_ciudad_id INTEGER;
BEGIN
    v_ciudad_id := fn_get_or_create_ciudad(p_ciudad_nombre, p_departamento);

    UPDATE sucursal
    SET nombre = p_nombre, ciudad_id = v_ciudad_id, direccion = p_direccion,
        horario_atencion = p_horario_atencion, telefono = p_telefono, estado = p_estado,
        latitud = p_latitud, longitud = p_longitud
    WHERE id = p_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'sucursal_no_encontrada';
    END IF;
END;
$$ LANGUAGE plpgsql;
"""

SP_SUCURSAL_CON_COORDENADAS_DOWN = """
DROP FUNCTION IF EXISTS sp_actualizar_sucursal(INTEGER, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, DOUBLE PRECISION, DOUBLE PRECISION);
DROP FUNCTION IF EXISTS sp_crear_sucursal(VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, DOUBLE PRECISION, DOUBLE PRECISION);
"""

SP_SUCURSAL_RESTAURAR_VIEJA = """
CREATE OR REPLACE FUNCTION sp_crear_sucursal(
    p_nombre VARCHAR, p_ciudad_nombre VARCHAR, p_departamento VARCHAR, p_direccion VARCHAR,
    p_horario_atencion VARCHAR, p_telefono VARCHAR, p_estado VARCHAR
) RETURNS INTEGER AS $$
DECLARE
    v_ciudad_id INTEGER;
    v_sucursal_id INTEGER;
BEGIN
    v_ciudad_id := fn_get_or_create_ciudad(p_ciudad_nombre, p_departamento);
    INSERT INTO sucursal (nombre, ciudad_id, direccion, horario_atencion, telefono, estado, fecha_creacion)
    VALUES (p_nombre, v_ciudad_id, p_direccion, p_horario_atencion, p_telefono, p_estado, CURRENT_DATE)
    RETURNING id INTO v_sucursal_id;
    RETURN v_sucursal_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_actualizar_sucursal(
    p_id INTEGER, p_nombre VARCHAR, p_ciudad_nombre VARCHAR, p_departamento VARCHAR, p_direccion VARCHAR,
    p_horario_atencion VARCHAR, p_telefono VARCHAR, p_estado VARCHAR
) RETURNS VOID AS $$
DECLARE
    v_ciudad_id INTEGER;
BEGIN
    v_ciudad_id := fn_get_or_create_ciudad(p_ciudad_nombre, p_departamento);
    UPDATE sucursal
    SET nombre = p_nombre, ciudad_id = v_ciudad_id, direccion = p_direccion,
        horario_atencion = p_horario_atencion, telefono = p_telefono, estado = p_estado
    WHERE id = p_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'sucursal_no_encontrada';
    END IF;
END;
$$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    op.execute(COLUMNAS_SQL)
    op.execute(FUNCIONES_SQL)
    op.execute(SP_SUCURSAL_CON_COORDENADAS)


def downgrade() -> None:
    op.execute(SP_SUCURSAL_CON_COORDENADAS_DOWN)
    op.execute(SP_SUCURSAL_RESTAURAR_VIEJA)
    op.execute(FUNCIONES_SQL_DOWN)
    op.execute(FUNCIONES_SQL_DOWN_RESTORE_OLD)
    op.execute(COLUMNAS_SQL_DOWN)
