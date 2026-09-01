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
    # IF NOT EXISTS: la migracion "esquema inicial" crea las tablas a partir del
    # estado *actual* de los modelos (Base.metadata.create_all), asi que en una
    # base 100% nueva estas columnas ya existen para cuando esta revision corre.
    op.execute('ALTER TABLE usuario ADD COLUMN IF NOT EXISTS session_id VARCHAR(64)')
    op.execute('ALTER TABLE usuario ADD COLUMN IF NOT EXISTS reset_code_hash VARCHAR(255)')
    op.execute('ALTER TABLE usuario ADD COLUMN IF NOT EXISTS reset_code_expires_at TIMESTAMP')


def downgrade() -> None:
    op.execute('ALTER TABLE usuario DROP COLUMN IF EXISTS reset_code_expires_at')
    op.execute('ALTER TABLE usuario DROP COLUMN IF EXISTS reset_code_hash')
    op.execute('ALTER TABLE usuario DROP COLUMN IF EXISTS session_id')
