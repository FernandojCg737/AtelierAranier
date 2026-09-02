"""funciones/PA: CRUD de temporadas y colecciones (CU07)

Revision ID: d57173559b3c
Revises: e48711455ba7
Create Date: 2026-09-02

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "d57173559b3c"
down_revision = "e48711455ba7"
branch_labels = None
depends_on = None


SP_CREAR_TEMPORADA = """
CREATE OR REPLACE FUNCTION sp_crear_temporada(p_nombre VARCHAR, p_fecha_inicio DATE, p_fecha_fin DATE)
RETURNS INTEGER AS $$
DECLARE
    v_id INTEGER;
BEGIN
    IF p_fecha_fin <= p_fecha_inicio THEN
        RAISE EXCEPTION 'rango_fechas_invalido';
    END IF;

    INSERT INTO temporada (nombre, fecha_inicio, fecha_fin)
    VALUES (p_nombre, p_fecha_inicio, p_fecha_fin)
    RETURNING id INTO v_id;

    RETURN v_id;
END;
$$ LANGUAGE plpgsql;
"""

SP_ACTUALIZAR_TEMPORADA = """
CREATE OR REPLACE FUNCTION sp_actualizar_temporada(p_id INTEGER, p_nombre VARCHAR, p_fecha_inicio DATE, p_fecha_fin DATE)
RETURNS VOID AS $$
BEGIN
    IF p_fecha_fin <= p_fecha_inicio THEN
        RAISE EXCEPTION 'rango_fechas_invalido';
    END IF;

    UPDATE temporada SET nombre = p_nombre, fecha_inicio = p_fecha_inicio, fecha_fin = p_fecha_fin
    WHERE id = p_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'temporada_no_encontrada';
    END IF;
END;
$$ LANGUAGE plpgsql;
"""

SP_ELIMINAR_TEMPORADA = """
CREATE OR REPLACE FUNCTION sp_eliminar_temporada(p_id INTEGER)
RETURNS VOID AS $$
BEGIN
    DELETE FROM temporada WHERE id = p_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'temporada_no_encontrada';
    END IF;
END;
$$ LANGUAGE plpgsql;
"""

SP_CREAR_COLECCION = """
CREATE OR REPLACE FUNCTION sp_crear_coleccion(p_temporada_id INTEGER, p_nombre VARCHAR, p_descripcion TEXT)
RETURNS INTEGER AS $$
DECLARE
    v_id INTEGER;
BEGIN
    INSERT INTO coleccion (temporada_id, nombre, descripcion)
    VALUES (p_temporada_id, p_nombre, p_descripcion)
    RETURNING id INTO v_id;

    RETURN v_id;
END;
$$ LANGUAGE plpgsql;
"""

SP_ACTUALIZAR_COLECCION = """
CREATE OR REPLACE FUNCTION sp_actualizar_coleccion(p_id INTEGER, p_temporada_id INTEGER, p_nombre VARCHAR, p_descripcion TEXT)
RETURNS VOID AS $$
BEGIN
    UPDATE coleccion SET temporada_id = p_temporada_id, nombre = p_nombre, descripcion = p_descripcion
    WHERE id = p_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'coleccion_no_encontrada';
    END IF;
END;
$$ LANGUAGE plpgsql;
"""

SP_ELIMINAR_COLECCION = """
CREATE OR REPLACE FUNCTION sp_eliminar_coleccion(p_id INTEGER)
RETURNS VOID AS $$
BEGIN
    DELETE FROM coleccion WHERE id = p_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'coleccion_no_encontrada';
    END IF;
END;
$$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    op.execute(SP_CREAR_TEMPORADA)
    op.execute(SP_ACTUALIZAR_TEMPORADA)
    op.execute(SP_ELIMINAR_TEMPORADA)
    op.execute(SP_CREAR_COLECCION)
    op.execute(SP_ACTUALIZAR_COLECCION)
    op.execute(SP_ELIMINAR_COLECCION)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS sp_eliminar_coleccion(INTEGER);")
    op.execute("DROP FUNCTION IF EXISTS sp_actualizar_coleccion(INTEGER, INTEGER, VARCHAR, TEXT);")
    op.execute("DROP FUNCTION IF EXISTS sp_crear_coleccion(INTEGER, VARCHAR, TEXT);")
    op.execute("DROP FUNCTION IF EXISTS sp_eliminar_temporada(INTEGER);")
    op.execute("DROP FUNCTION IF EXISTS sp_actualizar_temporada(INTEGER, VARCHAR, DATE, DATE);")
    op.execute("DROP FUNCTION IF EXISTS sp_crear_temporada(VARCHAR, DATE, DATE);")
