"""venta_presencial: empleado_id en vez de cajero_id, cualquier staff puede atender (CU11)

Revision ID: 7d8b214335d1
Revises: 5c3cd2ae4802
Create Date: 2026-09-13

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "7d8b214335d1"
down_revision = "5c3cd2ae4802"
branch_labels = None
depends_on = None


# CU11: antes solo un Cajero podia quedar registrado como quien atendio una
# venta presencial (FK a cajero.id); ahora tambien pueden ser Administrador
# o Encargado de Sucursal, asi que la columna pasa a apuntar a empleado.id
# (la tabla base de todos los tipos de personal).
def upgrade() -> None:
    op.execute("ALTER TABLE venta_presencial RENAME COLUMN cajero_id TO empleado_id;")
    op.execute("ALTER TABLE venta_presencial DROP CONSTRAINT venta_presencial_cajero_id_fkey;")
    op.execute(
        "ALTER TABLE venta_presencial ADD CONSTRAINT venta_presencial_empleado_id_fkey "
        "FOREIGN KEY (empleado_id) REFERENCES empleado(id);"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE venta_presencial DROP CONSTRAINT venta_presencial_empleado_id_fkey;")
    op.execute(
        "ALTER TABLE venta_presencial ADD CONSTRAINT venta_presencial_cajero_id_fkey "
        "FOREIGN KEY (cajero_id) REFERENCES cajero(id);"
    )
    op.execute("ALTER TABLE venta_presencial RENAME COLUMN empleado_id TO cajero_id;")
