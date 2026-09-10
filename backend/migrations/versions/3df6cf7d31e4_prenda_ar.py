"""tabla prenda_ar + SPs: probador virtual con realidad aumentada (CU09)

Revision ID: 3df6cf7d31e4
Revises: a1c5f7e93d02
Create Date: 2026-09-09

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "3df6cf7d31e4"
down_revision = "a1c5f7e93d02"
branch_labels = None
depends_on = None


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS prenda_ar (
    id SERIAL PRIMARY KEY,
    producto_id INTEGER NOT NULL UNIQUE REFERENCES producto(id),
    url VARCHAR(500) NOT NULL,
    ancla_hombro_izq_x NUMERIC(4,3) NOT NULL DEFAULT 0.20,
    ancla_hombro_izq_y NUMERIC(4,3) NOT NULL DEFAULT 0.15,
    ancla_hombro_der_x NUMERIC(4,3) NOT NULL DEFAULT 0.80,
    ancla_hombro_der_y NUMERIC(4,3) NOT NULL DEFAULT 0.15,
    ancla_torso_y NUMERIC(4,3) NOT NULL DEFAULT 0.65
);
"""

SP_UPSERT_PRENDA_AR = """
CREATE OR REPLACE FUNCTION sp_upsert_prenda_ar(
    p_producto_id INTEGER,
    p_url VARCHAR,
    p_ancla_hombro_izq_x NUMERIC,
    p_ancla_hombro_izq_y NUMERIC,
    p_ancla_hombro_der_x NUMERIC,
    p_ancla_hombro_der_y NUMERIC,
    p_ancla_torso_y NUMERIC
) RETURNS INTEGER AS $$
DECLARE
    v_id INTEGER;
BEGIN
    INSERT INTO prenda_ar (
        producto_id, url, ancla_hombro_izq_x, ancla_hombro_izq_y,
        ancla_hombro_der_x, ancla_hombro_der_y, ancla_torso_y
    )
    VALUES (
        p_producto_id, p_url, p_ancla_hombro_izq_x, p_ancla_hombro_izq_y,
        p_ancla_hombro_der_x, p_ancla_hombro_der_y, p_ancla_torso_y
    )
    ON CONFLICT (producto_id) DO UPDATE SET
        url = EXCLUDED.url,
        ancla_hombro_izq_x = EXCLUDED.ancla_hombro_izq_x,
        ancla_hombro_izq_y = EXCLUDED.ancla_hombro_izq_y,
        ancla_hombro_der_x = EXCLUDED.ancla_hombro_der_x,
        ancla_hombro_der_y = EXCLUDED.ancla_hombro_der_y,
        ancla_torso_y = EXCLUDED.ancla_torso_y
    RETURNING id INTO v_id;

    RETURN v_id;
END;
$$ LANGUAGE plpgsql;
"""

SP_ELIMINAR_PRENDA_AR = """
CREATE OR REPLACE FUNCTION sp_eliminar_prenda_ar(p_producto_id INTEGER)
RETURNS VOID AS $$
BEGIN
    DELETE FROM prenda_ar WHERE producto_id = p_producto_id;
END;
$$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    op.execute(SCHEMA_SQL)
    op.execute(SP_UPSERT_PRENDA_AR)
    op.execute(SP_ELIMINAR_PRENDA_AR)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS sp_eliminar_prenda_ar(INTEGER);")
    op.execute(
        "DROP FUNCTION IF EXISTS sp_upsert_prenda_ar(INTEGER, VARCHAR, NUMERIC, NUMERIC, NUMERIC, NUMERIC, NUMERIC);"
    )
    op.execute("DROP TABLE IF EXISTS prenda_ar;")
