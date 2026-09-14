"""bitacora: columna plataforma (web/movil) -- CU17, pedido del usuario

Revision ID: 23d136ba4401
Revises: a9d5e1f0c837
Create Date: 2026-09-14

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "23d136ba4401"
down_revision = "a9d5e1f0c837"
branch_labels = None
depends_on = None


FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION fn_bitacora_nuevo_usuario()
RETURNS trigger AS $$
BEGIN
    INSERT INTO bitacora (usuario_id, accion, entidad_afectada, entidad_id, fecha, detalle, ip_address, plataforma)
    VALUES (
        NEW.id,
        'CREAR',
        'usuario',
        NEW.id,
        now(),
        'Alta automatica de usuario (' || NEW.tipo || '): ' || NEW.email,
        NULLIF(current_setting('atelier.client_ip', true), ''),
        NULLIF(current_setting('atelier.client_platform', true), '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

FUNCTION_SQL_DOWN = """
CREATE OR REPLACE FUNCTION fn_bitacora_nuevo_usuario()
RETURNS trigger AS $$
BEGIN
    INSERT INTO bitacora (usuario_id, accion, entidad_afectada, entidad_id, fecha, detalle, ip_address)
    VALUES (
        NEW.id,
        'CREAR',
        'usuario',
        NEW.id,
        now(),
        'Alta automatica de usuario (' || NEW.tipo || '): ' || NEW.email,
        NULLIF(current_setting('atelier.client_ip', true), '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    op.execute("ALTER TABLE bitacora ADD COLUMN IF NOT EXISTS plataforma VARCHAR(20)")
    op.execute(FUNCTION_SQL)


def downgrade() -> None:
    op.execute(FUNCTION_SQL_DOWN)
    op.execute("ALTER TABLE bitacora DROP COLUMN IF EXISTS plataforma")
