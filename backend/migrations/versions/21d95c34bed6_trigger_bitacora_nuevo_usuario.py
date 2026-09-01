"""trigger: registrar en bitacora cada usuario nuevo (CU19)

Revision ID: 21d95c34bed6
Revises: 5628a0d31951
Create Date: 2026-08-31

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "21d95c34bed6"
down_revision = "5628a0d31951"
branch_labels = None
depends_on = None


FUNCTION_SQL = """
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

TRIGGER_SQL = """
CREATE TRIGGER trg_usuario_bitacora
AFTER INSERT ON usuario
FOR EACH ROW
EXECUTE FUNCTION fn_bitacora_nuevo_usuario();
"""


def upgrade() -> None:
    op.execute(FUNCTION_SQL)
    op.execute(TRIGGER_SQL)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_usuario_bitacora ON usuario;")
    op.execute("DROP FUNCTION IF EXISTS fn_bitacora_nuevo_usuario();")
