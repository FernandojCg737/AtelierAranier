"""CU10: retiene stock al reservar y lo libera si vence sin pagar

Revision ID: d3e8b5a1c9f7
Revises: c7f1a9d4e6b2
Create Date: 2026-09-12

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "d3e8b5a1c9f7"
down_revision = "c7f1a9d4e6b2"
branch_labels = None
depends_on = None


# Rediseno del flujo de stock de CU10: antes el stock se descontaba recien
# al "completar" (entregar) la reserva; ahora se descuenta al RESERVAR (se
# retiene), y sp_vencer_reservas_expiradas() lo devuelve automaticamente si
# el horario_atencion ya paso y la reserva sigue sin pagar (pendiente o
# confirmada, nunca llego a completada). sp_completar_reserva ya no hace
# falta -- "completar" ahora es solo un cambio de estado, el stock ya se
# movio al reservar.
SP_VENCER_RESERVAS = """
CREATE OR REPLACE FUNCTION sp_vencer_reservas_expiradas()
RETURNS INTEGER AS $$
DECLARE
    res RECORD;
    det RECORD;
    v_inventario_id INTEGER;
    v_contador INTEGER := 0;
BEGIN
    FOR res IN
        SELECT id, sucursal_id FROM reserva
        WHERE estado IN ('pendiente', 'confirmada') AND horario_atencion < NOW()
        FOR UPDATE
    LOOP
        FOR det IN
            SELECT il.producto_id, il.talla_id, il.color_id, il.cantidad
            FROM detalle_reserva dr
            JOIN item_linea il ON il.id = dr.id
            WHERE dr.reserva_id = res.id
        LOOP
            SELECT id INTO v_inventario_id
            FROM inventario
            WHERE producto_id = det.producto_id AND talla_id = det.talla_id
              AND color_id = det.color_id AND sucursal_id = res.sucursal_id
            FOR UPDATE;

            IF v_inventario_id IS NOT NULL THEN
                UPDATE inventario SET cantidad = cantidad + det.cantidad WHERE id = v_inventario_id;

                INSERT INTO movimiento_inventario (inventario_id, empleado_id, tipo, cantidad, fecha, documento_referencia)
                VALUES (v_inventario_id, NULL, 'entrada', det.cantidad, NOW(), 'Reserva #' || res.id || ' vencida sin pagar');
            END IF;
        END LOOP;

        UPDATE reserva SET estado = 'vencida' WHERE id = res.id;
        v_contador := v_contador + 1;
    END LOOP;

    RETURN v_contador;
END;
$$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    op.execute("ALTER TABLE movimiento_inventario ALTER COLUMN empleado_id DROP NOT NULL;")
    op.execute(SP_VENCER_RESERVAS)
    op.execute("DROP FUNCTION IF EXISTS sp_completar_reserva(INTEGER, INTEGER);")


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS sp_vencer_reservas_expiradas();")
    op.execute("ALTER TABLE movimiento_inventario ALTER COLUMN empleado_id SET NOT NULL;")
