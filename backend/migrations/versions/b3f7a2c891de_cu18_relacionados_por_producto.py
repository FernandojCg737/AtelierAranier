"""CU18: Productos relacionados por producto (vista + cache) -- seccion
"Tambien te puede interesar" en el detalle de producto, basada en que otros
productos vieron juntos los clientes (no en el historial de compra de UNO
solo, eso ya lo cubre "recomendacion").

Revision ID: b3f7a2c891de
Revises: 23d136ba4401
Create Date: 2026-09-17

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b3f7a2c891de"
down_revision = "23d136ba4401"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vista_producto",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cliente_id", sa.Integer(), sa.ForeignKey("cliente.id"), nullable=False),
        sa.Column("producto_id", sa.Integer(), sa.ForeignKey("producto.id"), nullable=False),
        sa.Column("fecha", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_vista_producto_producto_id", "vista_producto", ["producto_id"])
    op.create_index("ix_vista_producto_cliente_id", "vista_producto", ["cliente_id"])

    op.create_table(
        "producto_relacionado",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("producto_id", sa.Integer(), sa.ForeignKey("producto.id"), nullable=False),
        sa.Column("relacionado_id", sa.Integer(), sa.ForeignKey("producto.id"), nullable=False),
        sa.Column("score", sa.Numeric(5, 4), nullable=False),
        sa.Column("origen", sa.String(50), nullable=False),
        sa.Column("razon", sa.Text(), nullable=True),
        sa.Column("fecha", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("producto_id", "relacionado_id", name="uq_producto_relacionado_par"),
    )
    op.create_index("ix_producto_relacionado_producto_id", "producto_relacionado", ["producto_id"])


def downgrade() -> None:
    op.drop_index("ix_producto_relacionado_producto_id", table_name="producto_relacionado")
    op.drop_table("producto_relacionado")
    op.drop_index("ix_vista_producto_cliente_id", table_name="vista_producto")
    op.drop_index("ix_vista_producto_producto_id", table_name="vista_producto")
    op.drop_table("vista_producto")
