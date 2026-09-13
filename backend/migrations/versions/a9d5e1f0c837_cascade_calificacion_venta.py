"""FK calificacion.venta_id ON DELETE CASCADE (sp_eliminar_venta borra la venta)

Revision ID: a9d5e1f0c837
Revises: f2a4d8c6b731
Create Date: 2026-09-13

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "a9d5e1f0c837"
down_revision = "f2a4d8c6b731"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE calificacion DROP CONSTRAINT calificacion_venta_id_fkey;
        ALTER TABLE calificacion ADD CONSTRAINT calificacion_venta_id_fkey
            FOREIGN KEY (venta_id) REFERENCES venta(id) ON DELETE CASCADE;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE calificacion DROP CONSTRAINT calificacion_venta_id_fkey;
        ALTER TABLE calificacion ADD CONSTRAINT calificacion_venta_id_fkey
            FOREIGN KEY (venta_id) REFERENCES venta(id);
        """
    )
