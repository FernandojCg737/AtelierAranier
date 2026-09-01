"""sucursal: columna fecha_creacion (CU04)

Revision ID: aa5caf333180
Revises: 19b5adfcb3e2
Create Date: 2026-08-31

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "aa5caf333180"
down_revision = "19b5adfcb3e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sucursal",
        sa.Column("fecha_creacion", sa.Date(), nullable=False, server_default=sa.text("CURRENT_DATE")),
    )


def downgrade() -> None:
    op.drop_column("sucursal", "fecha_creacion")
