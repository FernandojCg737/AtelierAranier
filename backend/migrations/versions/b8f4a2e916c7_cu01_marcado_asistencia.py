"""CU01: marcado de asistencia con clave diaria + ubicacion (pedido del usuario)

Nuevo mecanismo, independiente del reporte de "asistencia" que ya existia en
CU16 (ese es solo un calculo derivado de horas de login/logout en la
bitacora, no tiene clave ni ubicacion). Este agrega:

- configuracion_asistencia: una sola fila con la hora en que se libera la
  clave del dia, la clave vigente, y si el administrador la libero manual
  antes de esa hora.
- marcado_asistencia: un registro por empleado por dia, con la hora exacta
  y la ubicacion (lat/lng) que adjunto al marcar.

La clave se regenera sola cada vez que cambia el dia (primer acceso del
dia), sin necesitar un proceso en segundo plano -- mismo patron de barrido
perezoso que ya usa el sistema para vencer reservas
(sp_vencer_reservas_expiradas).

Revision ID: b8f4a2e916c7
Revises: a1c7f4e2b908
Create Date: 2026-09-21

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "b8f4a2e916c7"
down_revision = "a1c7f4e2b908"
branch_labels = None
depends_on = None


TABLAS_SQL = """
CREATE TABLE IF NOT EXISTS configuracion_asistencia (
    id INTEGER PRIMARY KEY DEFAULT 1,
    hora_liberacion TIME NOT NULL DEFAULT '08:00:00',
    codigo VARCHAR(10),
    codigo_fecha DATE,
    liberado_manual_en TIMESTAMP,
    CONSTRAINT configuracion_asistencia_singleton CHECK (id = 1)
);
INSERT INTO configuracion_asistencia (id) VALUES (1) ON CONFLICT (id) DO NOTHING;

CREATE TABLE IF NOT EXISTS marcado_asistencia (
    id SERIAL PRIMARY KEY,
    empleado_id INTEGER NOT NULL REFERENCES empleado(id),
    fecha DATE NOT NULL,
    hora_marcado TIMESTAMP NOT NULL DEFAULT now(),
    latitud DOUBLE PRECISION NOT NULL,
    longitud DOUBLE PRECISION NOT NULL,
    UNIQUE (empleado_id, fecha)
);
CREATE INDEX IF NOT EXISTS ix_marcado_asistencia_fecha ON marcado_asistencia (fecha);
"""

TABLAS_SQL_DOWN = """
DROP TABLE IF EXISTS marcado_asistencia;
DROP TABLE IF EXISTS configuracion_asistencia;
"""

FUNCIONES_SQL = """
CREATE OR REPLACE FUNCTION fn_estado_asistencia_hoy()
RETURNS TABLE (codigo VARCHAR, hora_liberacion TIME, liberado BOOLEAN, codigo_fecha DATE) AS $$
DECLARE
    v_codigo VARCHAR(10);
    v_hora TIME;
    v_liberado_manual TIMESTAMP;
BEGIN
    -- barrido perezoso: si la clave guardada es de otro dia (o no existe),
    -- se genera una nueva de 6 digitos y se resetea la liberacion manual.
    UPDATE configuracion_asistencia c
    SET codigo = LPAD(FLOOR(RANDOM() * 900000 + 100000)::TEXT, 6, '0'),
        codigo_fecha = CURRENT_DATE,
        liberado_manual_en = NULL
    WHERE c.id = 1 AND (c.codigo_fecha IS NULL OR c.codigo_fecha != CURRENT_DATE);

    SELECT c.codigo, c.hora_liberacion, c.liberado_manual_en
    INTO v_codigo, v_hora, v_liberado_manual
    FROM configuracion_asistencia c WHERE c.id = 1;

    RETURN QUERY SELECT
        v_codigo,
        v_hora,
        (v_liberado_manual IS NOT NULL OR CURRENT_TIME >= v_hora),
        CURRENT_DATE;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_configurar_hora_asistencia(p_hora TIME)
RETURNS VOID AS $$
BEGIN
    UPDATE configuracion_asistencia SET hora_liberacion = p_hora WHERE id = 1;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_liberar_asistencia_manual()
RETURNS VOID AS $$
BEGIN
    -- fuerza el barrido perezoso (por si nadie la consulto todavia hoy) y
    -- despues marca la liberacion manual.
    PERFORM * FROM fn_estado_asistencia_hoy();
    UPDATE configuracion_asistencia SET liberado_manual_en = now() WHERE id = 1;
END;
$$ LANGUAGE plpgsql;

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
"""

FUNCIONES_SQL_DOWN = """
DROP FUNCTION IF EXISTS sp_marcar_asistencia(INTEGER, VARCHAR, DOUBLE PRECISION, DOUBLE PRECISION);
DROP FUNCTION IF EXISTS sp_liberar_asistencia_manual();
DROP FUNCTION IF EXISTS sp_configurar_hora_asistencia(TIME);
DROP FUNCTION IF EXISTS fn_estado_asistencia_hoy();
"""


def upgrade() -> None:
    op.execute(TABLAS_SQL)
    op.execute(FUNCIONES_SQL)


def downgrade() -> None:
    op.execute(FUNCIONES_SQL_DOWN)
    op.execute(TABLAS_SQL_DOWN)
