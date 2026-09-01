"""usuario: columnas para sesion unica y recuperacion de contrasena

Revision ID: d8cd7d73e5d6
Revises: f24ecfd3368d
Create Date: 2026-08-31

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d8cd7d73e5d6"
down_revision = "f24ecfd3368d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("usuario", sa.Column("session_id", sa.String(length=64), nullable=True))
    op.add_column("usuario", sa.Column("reset_code_hash", sa.String(length=255), nullable=True))
    op.add_column("usuario", sa.Column("reset_code_expires_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("usuario", "reset_code_expires_at")
    op.drop_column("usuario", "reset_code_hash")
    op.drop_column("usuario", "session_id")
