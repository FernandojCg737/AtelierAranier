"""CU13: columna fecha_actualizacion en carrito + trigger que la mantiene al dia

Revision ID: a1f9d3c6e820
Revises: b73cb98a93c4
Create Date: 2026-09-12

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a1f9d3c6e820"
down_revision = "b73cb98a93c4"
branch_labels = None
depends_on = None


FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION fn_carrito_tocar_actualizacion()
RETURNS trigger AS $$
BEGIN
    UPDATE carrito SET fecha_actualizacion = now()
    WHERE id = COALESCE(NEW.carrito_id, OLD.carrito_id);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
"""

TRIGGER_SQL = """
CREATE TRIGGER trg_detalle_carrito_tocar_actualizacion
AFTER INSERT OR UPDATE OR DELETE ON detalle_carrito
FOR EACH ROW
EXECUTE FUNCTION fn_carrito_tocar_actualizacion();
"""


def upgrade() -> None:
    op.add_column(
        "carrito",
        sa.Column("fecha_actualizacion", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )
    op.execute(FUNCTION_SQL)
    op.execute(TRIGGER_SQL)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_detalle_carrito_tocar_actualizacion ON detalle_carrito;")
    op.execute("DROP FUNCTION IF EXISTS fn_carrito_tocar_actualizacion();")
    op.drop_column("carrito", "fecha_actualizacion")
