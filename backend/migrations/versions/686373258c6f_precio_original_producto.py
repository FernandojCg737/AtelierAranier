"""producto.precio_original + actualiza PA de productos (descuentos, CU05)

Revision ID: 686373258c6f
Revises: d57173559b3c
Create Date: 2026-09-02

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "686373258c6f"
down_revision = "d57173559b3c"
branch_labels = None
depends_on = None


ADD_COLUMN_SQL = "ALTER TABLE producto ADD COLUMN IF NOT EXISTS precio_original NUMERIC(10, 2);"

SP_CREAR_PRODUCTO = """
CREATE OR REPLACE FUNCTION sp_crear_producto(
    p_nombre VARCHAR,
    p_descripcion TEXT,
    p_precio NUMERIC,
    p_precio_original NUMERIC,
    p_categoria_id INTEGER,
    p_marca_id INTEGER,
    p_proveedor_id INTEGER,
    p_temporada_id INTEGER,
    p_coleccion_id INTEGER
) RETURNS INTEGER AS $$
DECLARE
    v_producto_id INTEGER;
BEGIN
    INSERT INTO producto (
        categoria_id, marca_id, proveedor_id, temporada_id, coleccion_id, nombre, descripcion, precio,
        precio_original, estado
    )
    VALUES (
        p_categoria_id, p_marca_id, p_proveedor_id, p_temporada_id, p_coleccion_id, p_nombre, p_descripcion,
        p_precio, p_precio_original, 'activo'
    )
    RETURNING id INTO v_producto_id;

    RETURN v_producto_id;
END;
$$ LANGUAGE plpgsql;
"""

SP_ACTUALIZAR_PRODUCTO = """
CREATE OR REPLACE FUNCTION sp_actualizar_producto(
    p_id INTEGER,
    p_nombre VARCHAR,
    p_descripcion TEXT,
    p_precio NUMERIC,
    p_precio_original NUMERIC,
    p_categoria_id INTEGER,
    p_marca_id INTEGER,
    p_proveedor_id INTEGER,
    p_temporada_id INTEGER,
    p_coleccion_id INTEGER,
    p_estado VARCHAR
) RETURNS VOID AS $$
BEGIN
    UPDATE producto
    SET nombre = p_nombre, descripcion = p_descripcion, precio = p_precio, precio_original = p_precio_original,
        categoria_id = p_categoria_id, marca_id = p_marca_id, proveedor_id = p_proveedor_id,
        temporada_id = p_temporada_id, coleccion_id = p_coleccion_id, estado = p_estado
    WHERE id = p_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'producto_no_encontrado';
    END IF;
END;
$$ LANGUAGE plpgsql;
"""

DROP_OLD_SPS = """
DROP FUNCTION IF EXISTS sp_crear_producto(VARCHAR, TEXT, NUMERIC, INTEGER, INTEGER, INTEGER, INTEGER, INTEGER);
DROP FUNCTION IF EXISTS sp_actualizar_producto(INTEGER, VARCHAR, TEXT, NUMERIC, INTEGER, INTEGER, INTEGER, INTEGER, INTEGER, VARCHAR);
"""


def upgrade() -> None:
    op.execute(ADD_COLUMN_SQL)
    op.execute(DROP_OLD_SPS)
    op.execute(SP_CREAR_PRODUCTO)
    op.execute(SP_ACTUALIZAR_PRODUCTO)


def downgrade() -> None:
    op.execute(
        "DROP FUNCTION IF EXISTS sp_actualizar_producto(INTEGER, VARCHAR, TEXT, NUMERIC, NUMERIC, INTEGER, INTEGER, INTEGER, INTEGER, INTEGER, VARCHAR);"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS sp_crear_producto(VARCHAR, TEXT, NUMERIC, NUMERIC, INTEGER, INTEGER, INTEGER, INTEGER, INTEGER);"
    )
    op.execute("ALTER TABLE producto DROP COLUMN IF EXISTS precio_original;")
