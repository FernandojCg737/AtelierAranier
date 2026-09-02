"""tabla producto_imagen + funciones/PA de productos + seed catalogo base (CU05)

Revision ID: 5e06fd956807
Revises: fcca95be453b
Create Date: 2026-09-01

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "5e06fd956807"
down_revision = "fcca95be453b"
branch_labels = None
depends_on = None


# IF NOT EXISTS: en una base 100% nueva la migracion "esquema inicial" ya crea
# esta tabla a partir del estado actual de los modelos (Base.metadata.create_all).
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS producto_imagen (
    id SERIAL PRIMARY KEY,
    producto_id INTEGER NOT NULL REFERENCES producto(id),
    url VARCHAR(500) NOT NULL,
    orden INTEGER NOT NULL DEFAULT 0
);
"""

SEED_SQL = """
INSERT INTO categoria (nombre) VALUES
    ('Camisas'), ('Pantalones'), ('Chaquetas'), ('Trajes'), ('Accesorios'), ('Calzado')
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO talla (codigo) VALUES
    ('XS'), ('S'), ('M'), ('L'), ('XL'), ('XXL')
ON CONFLICT (codigo) DO NOTHING;

INSERT INTO color (nombre, codigo_hex)
SELECT * FROM (VALUES
    ('Negro', '#000000'),
    ('Blanco', '#FFFFFF'),
    ('Azul Marino', '#001F3F'),
    ('Gris', '#808080'),
    ('Beige', '#D2B48C'),
    ('Cafe', '#6F4E37')
) AS v(nombre, codigo_hex)
WHERE NOT EXISTS (SELECT 1 FROM color WHERE color.nombre = v.nombre);

INSERT INTO temporada (nombre, fecha_inicio, fecha_fin)
SELECT 'Otono-Invierno 2026', DATE '2026-04-01', DATE '2026-09-30'
WHERE NOT EXISTS (SELECT 1 FROM temporada WHERE nombre = 'Otono-Invierno 2026');

INSERT INTO temporada (nombre, fecha_inicio, fecha_fin)
SELECT 'Primavera-Verano 2026', DATE '2026-10-01', DATE '2027-03-31'
WHERE NOT EXISTS (SELECT 1 FROM temporada WHERE nombre = 'Primavera-Verano 2026');

INSERT INTO coleccion (temporada_id, nombre, descripcion)
SELECT t.id, 'Coleccion Basica', 'Prendas de uso diario para la temporada.'
FROM temporada t
WHERE t.nombre = 'Otono-Invierno 2026'
    AND NOT EXISTS (
        SELECT 1 FROM coleccion c WHERE c.temporada_id = t.id AND c.nombre = 'Coleccion Basica'
    );

INSERT INTO coleccion (temporada_id, nombre, descripcion)
SELECT t.id, 'Coleccion Basica', 'Prendas de uso diario para la temporada.'
FROM temporada t
WHERE t.nombre = 'Primavera-Verano 2026'
    AND NOT EXISTS (
        SELECT 1 FROM coleccion c WHERE c.temporada_id = t.id AND c.nombre = 'Coleccion Basica'
    );
"""

SP_CREAR_PRODUCTO = """
CREATE OR REPLACE FUNCTION sp_crear_producto(
    p_nombre VARCHAR,
    p_descripcion TEXT,
    p_precio NUMERIC,
    p_categoria_id INTEGER,
    p_proveedor_id INTEGER,
    p_temporada_id INTEGER,
    p_coleccion_id INTEGER
) RETURNS INTEGER AS $$
DECLARE
    v_producto_id INTEGER;
BEGIN
    INSERT INTO producto (categoria_id, proveedor_id, temporada_id, coleccion_id, nombre, descripcion, precio, estado)
    VALUES (p_categoria_id, p_proveedor_id, p_temporada_id, p_coleccion_id, p_nombre, p_descripcion, p_precio, 'activo')
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
    p_proveedor_id INTEGER,
    p_temporada_id INTEGER,
    p_coleccion_id INTEGER,
    p_estado VARCHAR
) RETURNS VOID AS $$
BEGIN
    UPDATE producto
    SET nombre = p_nombre, descripcion = p_descripcion, precio = p_precio,
        categoria_id = p_categoria_id, proveedor_id = p_proveedor_id,
        temporada_id = p_temporada_id, coleccion_id = p_coleccion_id, estado = p_estado
    WHERE id = p_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'producto_no_encontrado';
    END IF;
END;
$$ LANGUAGE plpgsql;
"""

SP_AGREGAR_IMAGEN_PRODUCTO = """
CREATE OR REPLACE FUNCTION sp_agregar_imagen_producto(
    p_producto_id INTEGER,
    p_url VARCHAR,
    p_orden INTEGER
) RETURNS INTEGER AS $$
DECLARE
    v_imagen_id INTEGER;
BEGIN
    INSERT INTO producto_imagen (producto_id, url, orden)
    VALUES (p_producto_id, p_url, p_orden)
    RETURNING id INTO v_imagen_id;

    RETURN v_imagen_id;
END;
$$ LANGUAGE plpgsql;
"""

SP_ELIMINAR_IMAGEN_PRODUCTO = """
CREATE OR REPLACE FUNCTION sp_eliminar_imagen_producto(p_imagen_id INTEGER)
RETURNS VOID AS $$
BEGIN
    DELETE FROM producto_imagen WHERE id = p_imagen_id;
END;
$$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    op.execute(CREATE_TABLE_SQL)
    op.execute(SEED_SQL)
    op.execute(SP_CREAR_PRODUCTO)
    op.execute(SP_ACTUALIZAR_PRODUCTO)
    op.execute(SP_AGREGAR_IMAGEN_PRODUCTO)
    op.execute(SP_ELIMINAR_IMAGEN_PRODUCTO)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS sp_eliminar_imagen_producto(INTEGER);")
    op.execute("DROP FUNCTION IF EXISTS sp_agregar_imagen_producto(INTEGER, VARCHAR, INTEGER);")
    op.execute(
        "DROP FUNCTION IF EXISTS sp_actualizar_producto(INTEGER, VARCHAR, TEXT, NUMERIC, INTEGER, INTEGER, INTEGER, INTEGER, VARCHAR);"
    )
    op.execute("DROP FUNCTION IF EXISTS sp_crear_producto(VARCHAR, TEXT, NUMERIC, INTEGER, INTEGER, INTEGER, INTEGER);")
    op.execute("DROP TABLE IF EXISTS producto_imagen;")
