"""CU18: Recomendar Prendas por IA -- razon/convertido + trigger de conversion

Revision ID: d6b2e8a4c913
Revises: c4a7e91b3f05
Create Date: 2026-09-13

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "d6b2e8a4c913"
down_revision = "c4a7e91b3f05"
branch_labels = None
depends_on = None


FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION fn_marcar_recomendacion_convertida()
RETURNS trigger AS $$
DECLARE
    v_cliente_id INTEGER;
    v_producto_id INTEGER;
BEGIN
    SELECT il.producto_id INTO v_producto_id FROM item_linea il WHERE il.id = NEW.id;

    IF TG_TABLE_NAME = 'detalle_venta_presencial' THEN
        SELECT v.cliente_id INTO v_cliente_id
        FROM venta_presencial vp JOIN venta v ON v.id = vp.id
        WHERE vp.id = NEW.venta_presencial_id;
    ELSE
        SELECT v.cliente_id INTO v_cliente_id
        FROM venta_digital vd JOIN venta v ON v.id = vd.id
        WHERE vd.id = NEW.venta_digital_id;
    END IF;

    IF v_cliente_id IS NOT NULL AND v_producto_id IS NOT NULL THEN
        UPDATE recomendacion SET convertido = true
        WHERE cliente_id = v_cliente_id AND producto_id = v_producto_id AND convertido = false;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

TRIGGER_PRESENCIAL_SQL = """
CREATE TRIGGER trg_detalle_venta_presencial_convertida
AFTER INSERT ON detalle_venta_presencial
FOR EACH ROW
EXECUTE FUNCTION fn_marcar_recomendacion_convertida();
"""

TRIGGER_DIGITAL_SQL = """
CREATE TRIGGER trg_detalle_venta_digital_convertida
AFTER INSERT ON detalle_venta_digital
FOR EACH ROW
EXECUTE FUNCTION fn_marcar_recomendacion_convertida();
"""


def upgrade() -> None:
    op.add_column("recomendacion", sa.Column("razon", sa.Text(), nullable=True))
    op.add_column(
        "recomendacion", sa.Column("convertido", sa.Boolean(), server_default=sa.false(), nullable=False)
    )
    op.create_unique_constraint("uq_recomendacion_cliente_producto", "recomendacion", ["cliente_id", "producto_id"])

    op.execute(FUNCTION_SQL)
    op.execute(TRIGGER_PRESENCIAL_SQL)
    op.execute(TRIGGER_DIGITAL_SQL)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_detalle_venta_digital_convertida ON detalle_venta_digital;")
    op.execute("DROP TRIGGER IF EXISTS trg_detalle_venta_presencial_convertida ON detalle_venta_presencial;")
    op.execute("DROP FUNCTION IF EXISTS fn_marcar_recomendacion_convertida();")
    op.drop_constraint("uq_recomendacion_cliente_producto", "recomendacion", type_="unique")
    op.drop_column("recomendacion", "convertido")
    op.drop_column("recomendacion", "razon")
