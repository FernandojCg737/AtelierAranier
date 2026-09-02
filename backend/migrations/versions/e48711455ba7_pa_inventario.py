"""funciones/PA: ver y editar stock de producto por sucursal (CU05/CU12 minimo)

Revision ID: e48711455ba7
Revises: 71c1889baa78
Create Date: 2026-09-02

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "e48711455ba7"
down_revision = "71c1889baa78"
branch_labels = None
depends_on = None


# DO-block: en una base 100% nueva la migracion "esquema inicial" ya crea la
# tabla inventario desde el estado actual de los modelos, esta constraint no
# existe ahi todavia porque no forma parte de la definicion del modelo
# SQLAlchemy (se agrega solo a nivel de base de datos), asi que el guard
# evita fallar si ya se agrego antes.
ADD_CONSTRAINT_SQL = """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'inventario_producto_talla_color_sucursal_key'
    ) THEN
        ALTER TABLE inventario
            ADD CONSTRAINT inventario_producto_talla_color_sucursal_key
            UNIQUE (producto_id, talla_id, color_id, sucursal_id);
    END IF;
END $$;
"""

SP_ESTABLECER_INVENTARIO = """
CREATE OR REPLACE FUNCTION sp_establecer_inventario(
    p_producto_id INTEGER,
    p_talla_id INTEGER,
    p_color_id INTEGER,
    p_sucursal_id INTEGER,
    p_cantidad INTEGER
) RETURNS INTEGER AS $$
DECLARE
    v_id INTEGER;
BEGIN
    IF p_cantidad < 0 THEN
        RAISE EXCEPTION 'cantidad_invalida';
    END IF;

    INSERT INTO inventario (producto_id, talla_id, color_id, sucursal_id, cantidad, estado)
    VALUES (p_producto_id, p_talla_id, p_color_id, p_sucursal_id, p_cantidad, 'disponible')
    ON CONFLICT (producto_id, talla_id, color_id, sucursal_id)
    DO UPDATE SET cantidad = EXCLUDED.cantidad
    RETURNING id INTO v_id;

    RETURN v_id;
END;
$$ LANGUAGE plpgsql;
"""

SP_ACTUALIZAR_INVENTARIO_CANTIDAD = """
CREATE OR REPLACE FUNCTION sp_actualizar_inventario_cantidad(p_id INTEGER, p_cantidad INTEGER)
RETURNS VOID AS $$
BEGIN
    IF p_cantidad < 0 THEN
        RAISE EXCEPTION 'cantidad_invalida';
    END IF;

    UPDATE inventario SET cantidad = p_cantidad WHERE id = p_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'inventario_no_encontrado';
    END IF;
END;
$$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    op.execute(ADD_CONSTRAINT_SQL)
    op.execute(SP_ESTABLECER_INVENTARIO)
    op.execute(SP_ACTUALIZAR_INVENTARIO_CANTIDAD)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS sp_actualizar_inventario_cantidad(INTEGER, INTEGER);")
    op.execute("DROP FUNCTION IF EXISTS sp_establecer_inventario(INTEGER, INTEGER, INTEGER, INTEGER, INTEGER);")
    op.execute(
        "ALTER TABLE inventario DROP CONSTRAINT IF EXISTS inventario_producto_talla_color_sucursal_key;"
    )
