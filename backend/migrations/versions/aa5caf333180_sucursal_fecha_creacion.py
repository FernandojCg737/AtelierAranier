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
    op.execute(
        'ALTER TABLE sucursal ADD COLUMN IF NOT EXISTS fecha_creacion DATE NOT NULL DEFAULT CURRENT_DATE'
    )


def downgrade() -> None:
    op.execute('ALTER TABLE sucursal DROP COLUMN IF EXISTS fecha_creacion')
