"""tabla uso_ar_prenda: registro de uso del probador de realidad aumentada (CU09)

Revision ID: 5b8e2c14f6a3
Revises: 3df6cf7d31e4
Create Date: 2026-09-12

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "5b8e2c14f6a3"
down_revision = "3df6cf7d31e4"
branch_labels = None
depends_on = None


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS uso_ar_prenda (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuario(id),
    producto_id INTEGER NOT NULL REFERENCES producto(id),
    modo VARCHAR(20) NOT NULL,
    fecha TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_uso_ar_prenda_fecha ON uso_ar_prenda (fecha DESC);
"""


def upgrade() -> None:
    op.execute(SCHEMA_SQL)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS uso_ar_prenda;")
