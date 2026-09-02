"""seed categoria Chompa (CU05)

Revision ID: 71c1889baa78
Revises: 41befe2fca95
Create Date: 2026-09-02

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "71c1889baa78"
down_revision = "41befe2fca95"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("INSERT INTO categoria (nombre) VALUES ('Chompa') ON CONFLICT (nombre) DO NOTHING;")


def downgrade() -> None:
    op.execute("DELETE FROM categoria WHERE nombre = 'Chompa';")
