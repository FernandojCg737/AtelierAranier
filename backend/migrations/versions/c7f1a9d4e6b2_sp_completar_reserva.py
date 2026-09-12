"""sp_completar_reserva: descuenta stock y registra el movimiento al completar (CU10)

Revision ID: c7f1a9d4e6b2
Revises: 5b8e2c14f6a3
Create Date: 2026-09-12

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "c7f1a9d4e6b2"
down_revision = "5b8e2c14f6a3"
branch_labels = None
depends_on = None


SP_COMPLETAR_RESERVA = """
CREATE OR REPLACE FUNCTION sp_completar_reserva(p_reserva_id INTEGER, p_empleado_id INTEGER)
RETURNS VOID AS $$
DECLARE
    v_sucursal_id INTEGER;
    det RECORD;
    v_inventario_id INTEGER;
    v_actual INTEGER;
BEGIN
    SELECT sucursal_id INTO v_sucursal_id
    FROM reserva
    WHERE id = p_reserva_id AND estado <> 'completada' AND estado <> 'cancelada';

    IF v_sucursal_id IS NULL THEN
        RAISE EXCEPTION 'Reserva no encontrada, ya completada o cancelada';
    END IF;

    FOR det IN
        SELECT il.producto_id, il.talla_id, il.color_id, il.cantidad
        FROM detalle_reserva dr
        JOIN item_linea il ON il.id = dr.id
        WHERE dr.reserva_id = p_reserva_id
    LOOP
        SELECT id, cantidad INTO v_inventario_id, v_actual
        FROM inventario
        WHERE producto_id = det.producto_id AND talla_id = det.talla_id
          AND color_id = det.color_id AND sucursal_id = v_sucursal_id
        FOR UPDATE;

        IF v_inventario_id IS NULL OR v_actual < det.cantidad THEN
            RAISE EXCEPTION 'Stock insuficiente para completar la reserva';
        END IF;

        UPDATE inventario SET cantidad = cantidad - det.cantidad WHERE id = v_inventario_id;

        INSERT INTO movimiento_inventario (inventario_id, empleado_id, tipo, cantidad, fecha, documento_referencia)
        VALUES (v_inventario_id, p_empleado_id, 'salida', det.cantidad, NOW(), 'Reserva #' || p_reserva_id);
    END LOOP;

    UPDATE reserva SET estado = 'completada' WHERE id = p_reserva_id;
END;
$$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    op.execute(SP_COMPLETAR_RESERVA)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS sp_completar_reserva(INTEGER, INTEGER);")
