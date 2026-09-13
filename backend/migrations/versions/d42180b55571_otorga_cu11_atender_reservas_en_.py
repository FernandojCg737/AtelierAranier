"""otorga CU11 (Atender Reservas en Sucursal) al rol Cajero tambien (CU11)

Revision ID: d42180b55571
Revises: 7d8b214335d1
Create Date: 2026-09-13

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "d42180b55571"
down_revision = "7d8b214335d1"
branch_labels = None
depends_on = None


# El menu de administracion (frontend) ya tenia un item "CU11 - Gestion de
# Ventas" listado bajo P4, pero solo Encargado de Sucursal tenia ese permiso
# -- el Cajero se hubiera quedado sin acceso al panel de ventas aunque el
# usuario pidio explicitamente que Administrador, Encargado y Cajero puedan
# usarlo. Se le otorga CU11 al Cajero tambien para que quede consistente.
def upgrade() -> None:
    op.execute(
        """
        INSERT INTO rol_permiso (rol_id, permiso_id)
        SELECT r.id, p.id FROM rol r CROSS JOIN permiso p
        WHERE r.nombre = 'Cajero' AND p.nombre = 'CU11'
        ON CONFLICT (rol_id, permiso_id) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM rol_permiso
        WHERE rol_id = (SELECT id FROM rol WHERE nombre = 'Cajero')
          AND permiso_id = (SELECT id FROM permiso WHERE nombre = 'CU11');
        """
    )
