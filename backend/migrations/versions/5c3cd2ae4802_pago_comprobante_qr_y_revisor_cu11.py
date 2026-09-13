"""pago: comprobante QR y revisor (CU11)

Revision ID: 5c3cd2ae4802
Revises: d3e8b5a1c9f7
Create Date: 2026-09-13

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "5c3cd2ae4802"
down_revision = "d3e8b5a1c9f7"
branch_labels = None
depends_on = None


# CU11: pago por QR sin pasarela real -- el cliente sube la foto del
# comprobante de transferencia y un cajero/encargado la revisa manualmente
# (a diferencia de PayPal, un QR no se puede verificar automaticamente).
def upgrade() -> None:
    op.execute("ALTER TABLE pago ADD COLUMN comprobante_url VARCHAR(500);")
    op.execute("ALTER TABLE pago ADD COLUMN revisado_por_id INTEGER REFERENCES empleado(id);")


def downgrade() -> None:
    op.execute("ALTER TABLE pago DROP COLUMN revisado_por_id;")
    op.execute("ALTER TABLE pago DROP COLUMN comprobante_url;")
