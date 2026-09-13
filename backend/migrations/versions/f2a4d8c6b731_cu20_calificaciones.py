"""CU20: Reputacion y Calificaciones -- una calificacion por venta completada

Revision ID: f2a4d8c6b731
Revises: e7c3f9a1d248
Create Date: 2026-09-13

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "f2a4d8c6b731"
down_revision = "e7c3f9a1d248"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "calificacion",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("venta_id", sa.Integer(), sa.ForeignKey("venta.id"), nullable=False, unique=True),
        sa.Column("cliente_id", sa.Integer(), sa.ForeignKey("cliente.id"), nullable=False),
        sa.Column("estrellas", sa.Integer(), nullable=False),
        sa.Column("comentario", sa.Text(), nullable=True),
        sa.Column("fecha", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("estrellas BETWEEN 1 AND 5", name="ck_calificacion_estrellas_rango"),
    )
    op.create_index("ix_calificacion_cliente_id", "calificacion", ["cliente_id"])


def downgrade() -> None:
    op.drop_index("ix_calificacion_cliente_id", table_name="calificacion")
    op.drop_table("calificacion")
