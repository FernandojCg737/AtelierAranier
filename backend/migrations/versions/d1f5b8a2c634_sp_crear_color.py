"""color.nombre unico + sp_crear_color (CU05: "Otro..." al agregar stock)

Revision ID: d1f5b8a2c634
Revises: b3f7a2c891de
Create Date: 2026-09-17

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "d1f5b8a2c634"
down_revision = "b3f7a2c891de"
branch_labels = None
depends_on = None

UNIQUE_SQL = """
ALTER TABLE color ADD CONSTRAINT color_nombre_key UNIQUE (nombre);
"""

SP_CREAR_COLOR = """
CREATE OR REPLACE FUNCTION sp_crear_color(p_nombre VARCHAR)
RETURNS INTEGER AS $$
DECLARE
    v_id INTEGER;
BEGIN
    INSERT INTO color (nombre) VALUES (p_nombre)
    ON CONFLICT (nombre) DO UPDATE SET nombre = EXCLUDED.nombre
    RETURNING id INTO v_id;

    RETURN v_id;
END;
$$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    op.execute(UNIQUE_SQL)
    op.execute(SP_CREAR_COLOR)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS sp_crear_color(VARCHAR);")
    op.execute("ALTER TABLE color DROP CONSTRAINT IF EXISTS color_nombre_key;")
