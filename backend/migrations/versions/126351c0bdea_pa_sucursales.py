"""funciones/PA: CRUD de sucursal via Postgres (CU04)

Revision ID: 126351c0bdea
Revises: aa5caf333180
Create Date: 2026-08-31

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "126351c0bdea"
down_revision = "aa5caf333180"
branch_labels = None
depends_on = None


FN_GET_OR_CREATE_CIUDAD = """
CREATE OR REPLACE FUNCTION fn_get_or_create_ciudad(p_nombre VARCHAR, p_departamento VARCHAR)
RETURNS INTEGER AS $$
DECLARE
    v_ciudad_id INTEGER;
BEGIN
    SELECT id INTO v_ciudad_id FROM ciudad WHERE lower(nombre) = lower(trim(p_nombre));

    IF v_ciudad_id IS NULL THEN
        INSERT INTO ciudad (nombre, departamento)
        VALUES (trim(p_nombre), trim(p_departamento))
        RETURNING id INTO v_ciudad_id;
    ELSE
        UPDATE ciudad SET departamento = trim(p_departamento)
        WHERE id = v_ciudad_id AND departamento <> trim(p_departamento);
    END IF;

    RETURN v_ciudad_id;
END;
$$ LANGUAGE plpgsql;
"""

SP_CREAR_SUCURSAL = """
CREATE OR REPLACE FUNCTION sp_crear_sucursal(
    p_nombre VARCHAR,
    p_ciudad_nombre VARCHAR,
    p_departamento VARCHAR,
    p_direccion VARCHAR,
    p_horario_atencion VARCHAR,
    p_telefono VARCHAR,
    p_estado VARCHAR
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
"""

SP_ACTUALIZAR_SUCURSAL = """
CREATE OR REPLACE FUNCTION sp_actualizar_sucursal(
    p_id INTEGER,
    p_nombre VARCHAR,
    p_ciudad_nombre VARCHAR,
    p_departamento VARCHAR,
    p_direccion VARCHAR,
    p_horario_atencion VARCHAR,
    p_telefono VARCHAR,
    p_estado VARCHAR
) RETURNS VOID AS $$
DECLARE
    v_ciudad_id INTEGER;
BEGIN
    v_ciudad_id := fn_get_or_create_ciudad(p_ciudad_nombre, p_departamento);

    UPDATE sucursal
    SET nombre = p_nombre,
        ciudad_id = v_ciudad_id,
        direccion = p_direccion,
        horario_atencion = p_horario_atencion,
        telefono = p_telefono,
        estado = p_estado
    WHERE id = p_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'sucursal_no_encontrada';
    END IF;
END;
$$ LANGUAGE plpgsql;
"""

SP_ELIMINAR_SUCURSAL = """
CREATE OR REPLACE FUNCTION sp_eliminar_sucursal(p_id INTEGER)
RETURNS VOID AS $$
BEGIN
    DELETE FROM sucursal WHERE id = p_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'sucursal_no_encontrada';
    END IF;
END;
$$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    op.execute(FN_GET_OR_CREATE_CIUDAD)
    op.execute(SP_CREAR_SUCURSAL)
    op.execute(SP_ACTUALIZAR_SUCURSAL)
    op.execute(SP_ELIMINAR_SUCURSAL)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS sp_eliminar_sucursal(INTEGER);")
    op.execute("DROP FUNCTION IF EXISTS sp_actualizar_sucursal(INTEGER, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR);")
    op.execute("DROP FUNCTION IF EXISTS sp_crear_sucursal(VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR);")
    op.execute("DROP FUNCTION IF EXISTS fn_get_or_create_ciudad(VARCHAR, VARCHAR);")
