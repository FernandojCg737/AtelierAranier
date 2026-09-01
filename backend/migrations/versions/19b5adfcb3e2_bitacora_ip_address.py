"""bitacora: columna ip_address + trigger la registra desde la sesion (CU19)

Revision ID: 19b5adfcb3e2
Revises: d8cd7d73e5d6
Create Date: 2026-08-31

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "19b5adfcb3e2"
down_revision = "d8cd7d73e5d6"
branch_labels = None
depends_on = None


FUNCTION_SQL = """
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

FUNCTION_SQL_DOWN = """
CREATE OR REPLACE FUNCTION fn_bitacora_nuevo_usuario()
RETURNS trigger AS $$
BEGIN
    INSERT INTO bitacora (usuario_id, accion, entidad_afectada, entidad_id, fecha, detalle)
    VALUES (
        NEW.id,
        'CREAR',
        'usuario',
        NEW.id,
        now(),
        'Alta automatica de usuario (' || NEW.tipo || '): ' || NEW.email
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    op.execute('ALTER TABLE bitacora ADD COLUMN IF NOT EXISTS ip_address VARCHAR(45)')
    op.execute(FUNCTION_SQL)


def downgrade() -> None:
    op.execute(FUNCTION_SQL_DOWN)
    op.execute('ALTER TABLE bitacora DROP COLUMN IF EXISTS ip_address')
