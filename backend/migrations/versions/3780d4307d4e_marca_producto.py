"""tabla marca + producto.marca_id + actualiza PA de productos (CU05)

Revision ID: 3780d4307d4e
Revises: 5e06fd956807
Create Date: 2026-09-02

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "3780d4307d4e"
down_revision = "5e06fd956807"
branch_labels = None
depends_on = None


# IF NOT EXISTS / DO-block: en una base 100% nueva la migracion "esquema
# inicial" ya crea marca y producto.marca_id a partir del estado actual de
# los modelos (Base.metadata.create_all), asi que estos guards evitan que
# esta migracion falle al re-crearlos en una base que arranca de cero.
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS marca (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'producto' AND column_name = 'marca_id'
    ) THEN
        ALTER TABLE producto ADD COLUMN marca_id INTEGER REFERENCES marca(id);
    END IF;
END $$;
"""

SEED_SQL = """
INSERT INTO marca (nombre) VALUES ('Atelier Aranier')
ON CONFLICT (nombre) DO NOTHING;
"""

BACKFILL_SQL = """
UPDATE producto SET marca_id = (SELECT id FROM marca ORDER BY id LIMIT 1) WHERE marca_id IS NULL;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM producto WHERE marca_id IS NULL) THEN
        ALTER TABLE producto ALTER COLUMN marca_id SET NOT NULL;
    END IF;
END $$;
"""

SP_CREAR_MARCA = """
CREATE OR REPLACE FUNCTION sp_crear_marca(p_nombre VARCHAR)
RETURNS INTEGER AS $$
DECLARE
    v_id INTEGER;
BEGIN
    INSERT INTO marca (nombre) VALUES (p_nombre)
    ON CONFLICT (nombre) DO UPDATE SET nombre = EXCLUDED.nombre
    RETURNING id INTO v_id;

    RETURN v_id;
END;
$$ LANGUAGE plpgsql;
"""

SP_CREAR_PRODUCTO = """
CREATE OR REPLACE FUNCTION sp_crear_producto(
    p_nombre VARCHAR,
    p_descripcion TEXT,
    p_precio NUMERIC,
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
        categoria_id, marca_id, proveedor_id, temporada_id, coleccion_id, nombre, descripcion, precio, estado
    )
    VALUES (
        p_categoria_id, p_marca_id, p_proveedor_id, p_temporada_id, p_coleccion_id, p_nombre, p_descripcion,
        p_precio, 'activo'
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
    p_categoria_id INTEGER,
    p_marca_id INTEGER,
    p_proveedor_id INTEGER,
    p_temporada_id INTEGER,
    p_coleccion_id INTEGER,
    p_estado VARCHAR
) RETURNS VOID AS $$
BEGIN
    UPDATE producto
    SET nombre = p_nombre, descripcion = p_descripcion, precio = p_precio,
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
DROP FUNCTION IF EXISTS sp_crear_producto(VARCHAR, TEXT, NUMERIC, INTEGER, INTEGER, INTEGER, INTEGER);
DROP FUNCTION IF EXISTS sp_actualizar_producto(INTEGER, VARCHAR, TEXT, NUMERIC, INTEGER, INTEGER, INTEGER, INTEGER, VARCHAR);
"""


def upgrade() -> None:
    op.execute(SCHEMA_SQL)
    op.execute(SEED_SQL)
    op.execute(BACKFILL_SQL)
    op.execute(DROP_OLD_SPS)
    op.execute(SP_CREAR_MARCA)
    op.execute(SP_CREAR_PRODUCTO)
    op.execute(SP_ACTUALIZAR_PRODUCTO)


def downgrade() -> None:
    op.execute(
        "DROP FUNCTION IF EXISTS sp_actualizar_producto(INTEGER, VARCHAR, TEXT, NUMERIC, INTEGER, INTEGER, INTEGER, INTEGER, INTEGER, VARCHAR);"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS sp_crear_producto(VARCHAR, TEXT, NUMERIC, INTEGER, INTEGER, INTEGER, INTEGER, INTEGER);"
    )
    op.execute("DROP FUNCTION IF EXISTS sp_crear_marca(VARCHAR);")
    op.execute("ALTER TABLE producto ALTER COLUMN marca_id DROP NOT NULL;")
    op.execute("ALTER TABLE producto DROP COLUMN IF EXISTS marca_id;")
    op.execute("DROP TABLE IF EXISTS marca;")
