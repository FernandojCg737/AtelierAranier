"""CU11: tablas devolucion y detalle_devolucion para devoluciones de ventas

Revision ID: a2f7b3c8d4e1
Revises: c3d7f1a8e042
Create Date: 2026-09-25

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a2f7b3c8d4e1"
down_revision = "c3d7f1a8e042"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "devolucion",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("venta_id", sa.Integer(), sa.ForeignKey("venta.id"), nullable=False),
        sa.Column("empleado_id", sa.Integer(), sa.ForeignKey("empleado.id"), nullable=True),
        sa.Column("motivo", sa.String(30), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("monto_reembolso", sa.Numeric(10, 2), nullable=False),
        sa.Column("metodo_reembolso", sa.String(30), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="solicitada"),
        sa.Column("fecha_solicitud", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("fecha_resolucion", sa.DateTime(), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
    )

    op.create_table(
        "detalle_devolucion",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("devolucion_id", sa.Integer(), sa.ForeignKey("devolucion.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_linea_id", sa.Integer(), sa.ForeignKey("item_linea.id"), nullable=False),
        sa.Column("cantidad_devuelta", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("detalle_devolucion")
    op.drop_table("devolucion")
