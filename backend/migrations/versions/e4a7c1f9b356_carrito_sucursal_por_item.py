"""detalle_carrito.sucursal_id + permite varias ventas por carrito

Pedido explicito del usuario: la sucursal de retiro ahora se elige POR
PRODUCTO al agregarlo al carrito (no una sola vez para todo el pedido en
el checkout) -- si el carrito termina con productos de sucursales
distintas, el pago se reparte en varias ventas (una por sucursal).

Revision ID: e4a7c1f9b356
Revises: b3f7a2c891de
Create Date: 2026-09-18

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "e4a7c1f9b356"
down_revision = "d1f5b8a2c634"
branch_labels = None
depends_on = None

ADD_COLUMN_SQL = """
ALTER TABLE detalle_carrito ADD COLUMN sucursal_id INTEGER REFERENCES sucursal(id);

UPDATE detalle_carrito SET sucursal_id = (SELECT id FROM sucursal ORDER BY id LIMIT 1)
WHERE sucursal_id IS NULL;

ALTER TABLE detalle_carrito ALTER COLUMN sucursal_id SET NOT NULL;
"""

# Un carrito ahora puede generar VARIAS ventas digitales (una por sucursal,
# si el carrito quedo con productos de mas de una) -- antes esto era 1:1.
DROP_UNIQUE_SQL = """
ALTER TABLE venta_digital DROP CONSTRAINT venta_digital_carrito_id_key;
"""

# sp_agregar_item_carrito ahora guarda tambien la sucursal elegida --
# agrupar por (producto,talla,color) YA NO ALCANZA para decidir si es "el
# mismo item" del carrito: agregar el mismo producto/talla/color pero de
# OTRA sucursal debe quedar como una fila aparte (se van a retirar en
# lugares distintos), asi que se agrega sucursal_id al match.
SP_AGREGAR_ITEM_CARRITO = """
CREATE OR REPLACE FUNCTION sp_agregar_item_carrito(
    p_carrito_id INTEGER, p_producto_id INTEGER, p_talla_id INTEGER, p_color_id INTEGER,
    p_sucursal_id INTEGER, p_cantidad INTEGER, p_precio_unitario NUMERIC(10,2)
) RETURNS INTEGER AS $$
DECLARE
    v_detalle_id INTEGER;
BEGIN
    IF p_cantidad < 1 THEN
        RAISE EXCEPTION 'cantidad_invalida';
    END IF;

    SELECT dc.id INTO v_detalle_id
    FROM detalle_carrito dc
    JOIN item_linea il ON il.id = dc.id
    WHERE dc.carrito_id = p_carrito_id AND il.producto_id = p_producto_id
      AND il.talla_id = p_talla_id AND il.color_id = p_color_id AND dc.sucursal_id = p_sucursal_id;

    IF v_detalle_id IS NOT NULL THEN
        UPDATE item_linea SET cantidad = cantidad + p_cantidad WHERE id = v_detalle_id;
        UPDATE detalle_carrito SET precio_unitario = p_precio_unitario WHERE id = v_detalle_id;
    ELSE
        INSERT INTO item_linea (producto_id, talla_id, color_id, cantidad, tipo)
        VALUES (p_producto_id, p_talla_id, p_color_id, p_cantidad, 'detalle_carrito')
        RETURNING id INTO v_detalle_id;

        INSERT INTO detalle_carrito (id, carrito_id, precio_unitario, sucursal_id)
        VALUES (v_detalle_id, p_carrito_id, p_precio_unitario, p_sucursal_id);
    END IF;

    RETURN v_detalle_id;
END;
$$ LANGUAGE plpgsql;
"""

DROP_OLD_SP = """
DROP FUNCTION IF EXISTS sp_agregar_item_carrito(INTEGER, INTEGER, INTEGER, INTEGER, INTEGER, NUMERIC);
"""


def upgrade() -> None:
    op.execute(ADD_COLUMN_SQL)
    op.execute(DROP_UNIQUE_SQL)
    op.execute(DROP_OLD_SP)
    op.execute(SP_AGREGAR_ITEM_CARRITO)


def downgrade() -> None:
    op.execute(
        "DROP FUNCTION IF EXISTS sp_agregar_item_carrito(INTEGER, INTEGER, INTEGER, INTEGER, INTEGER, INTEGER, NUMERIC);"
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION sp_agregar_item_carrito(
            p_carrito_id INTEGER, p_producto_id INTEGER, p_talla_id INTEGER, p_color_id INTEGER,
            p_cantidad INTEGER, p_precio_unitario NUMERIC(10,2)
        ) RETURNS INTEGER AS $$
        DECLARE
            v_detalle_id INTEGER;
        BEGIN
            IF p_cantidad < 1 THEN
                RAISE EXCEPTION 'cantidad_invalida';
            END IF;

            SELECT dc.id INTO v_detalle_id
            FROM detalle_carrito dc
            JOIN item_linea il ON il.id = dc.id
            WHERE dc.carrito_id = p_carrito_id AND il.producto_id = p_producto_id
              AND il.talla_id = p_talla_id AND il.color_id = p_color_id;

            IF v_detalle_id IS NOT NULL THEN
                UPDATE item_linea SET cantidad = cantidad + p_cantidad WHERE id = v_detalle_id;
                UPDATE detalle_carrito SET precio_unitario = p_precio_unitario WHERE id = v_detalle_id;
            ELSE
                INSERT INTO item_linea (producto_id, talla_id, color_id, cantidad, tipo)
                VALUES (p_producto_id, p_talla_id, p_color_id, p_cantidad, 'detalle_carrito')
                RETURNING id INTO v_detalle_id;

                INSERT INTO detalle_carrito (id, carrito_id, precio_unitario)
                VALUES (v_detalle_id, p_carrito_id, p_precio_unitario);
            END IF;

            RETURN v_detalle_id;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute("ALTER TABLE venta_digital ADD CONSTRAINT venta_digital_carrito_id_key UNIQUE (carrito_id);")
    op.execute("ALTER TABLE detalle_carrito DROP COLUMN sucursal_id;")
