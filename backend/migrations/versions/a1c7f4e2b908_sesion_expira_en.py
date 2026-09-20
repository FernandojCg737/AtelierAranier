"""usuario: columna sesion_expira_en -- CU01, sesiones activas en tiempo real

Antes "sesion activa" solo significaba "session_id no es null", lo cual nunca
se limpiaba salvo logout explicito, nuevo login o cambio de password: un
usuario que cerraba la pestana sin desloguearse quedaba listado como activo
para siempre aunque su JWT (60 min) ya hubiera expirado. Esta columna guarda
el mismo instante de expiracion que ya lleva el JWT, para que /sesiones/activas
pueda filtrar por sesiones realmente vigentes.

Revision ID: a1c7f4e2b908
Revises: f8b3d6c2a915
Create Date: 2026-09-20

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1c7f4e2b908"
down_revision = "f8b3d6c2a915"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE usuario ADD COLUMN IF NOT EXISTS sesion_expira_en TIMESTAMP")


def downgrade() -> None:
    op.execute("ALTER TABLE usuario DROP COLUMN IF EXISTS sesion_expira_en")
