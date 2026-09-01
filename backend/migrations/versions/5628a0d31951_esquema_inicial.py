"""esquema inicial: 37 clases del diagrama (docs/uml) + tabla puente rol_permiso

Revision ID: 5628a0d31951
Revises:
Create Date: 2026-08-30

"""
from alembic import op

from app.db.session import Base
from app.models import *  # noqa: F401,F403  (registra las tablas en Base.metadata)

# revision identifiers, used by Alembic.
revision = "5628a0d31951"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Se crea a partir de Base.metadata (no de op.create_table por tabla) porque
    # esta revision se escribio sin una conexion viva a Postgres para correr
    # `alembic revision --autogenerate`. Queda garantizado 1:1 con los modelos
    # SQLAlchemy en app/models/, que ya fueron validados con configure_mappers().
    Base.metadata.create_all(bind=op.get_bind(), checkfirst=False)


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
