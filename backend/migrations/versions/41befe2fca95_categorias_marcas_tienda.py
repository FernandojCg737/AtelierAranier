"""seed categorias y marcas usadas por los filtros de la tienda (CU05/CU08)

Revision ID: 41befe2fca95
Revises: 3780d4307d4e
Create Date: 2026-09-02

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "41befe2fca95"
down_revision = "3780d4307d4e"
branch_labels = None
depends_on = None


SEED_SQL = """
INSERT INTO categoria (nombre) VALUES
    ('Poleras'), ('Chalecos'), ('Hoodie')
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO marca (nombre) VALUES
    ('Nike'), ('Adidas'), ('Puma'), ('New Balance'), ('Converse'),
    ('Jordan'), ('Champion'), ('Levi''s'), ('Tommy Hilfiger'), ('Calvin Klein')
ON CONFLICT (nombre) DO NOTHING;
"""

DELETE_SQL = """
DELETE FROM marca WHERE nombre IN
    ('Nike', 'Adidas', 'Puma', 'New Balance', 'Converse',
     'Jordan', 'Champion', 'Levi''s', 'Tommy Hilfiger', 'Calvin Klein');

DELETE FROM categoria WHERE nombre IN ('Poleras', 'Chalecos', 'Hoodie');
"""


def upgrade() -> None:
    op.execute(SEED_SQL)


def downgrade() -> None:
    op.execute(DELETE_SQL)
