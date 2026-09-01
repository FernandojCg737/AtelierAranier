"""seed: rol Administrador y cuenta de administrador inicial

Revision ID: f24ecfd3368d
Revises: 21d95c34bed6
Create Date: 2026-08-31

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "f24ecfd3368d"
down_revision = "21d95c34bed6"
branch_labels = None
depends_on = None

ADMIN_EMAIL = "admin@atelieraranier.com"
# Hash bcrypt de la contrasena temporal inicial -- cambiar desde el primer login (CU17).
ADMIN_PASSWORD_HASH = "$2b$12$UXs3oDrk1VXhncOjH6EOpepIVF7xXsD7C.0bRay/HvwwufggwOK/C"

SEED_SQL = f"""
DO $$
DECLARE
    v_rol_id INT;
    v_usuario_id INT;
BEGIN
    INSERT INTO rol (nombre, descripcion)
    VALUES ('Administrador', 'Acceso total al sistema: gestion de productos, ventas, usuarios y reportes.')
    ON CONFLICT (nombre) DO NOTHING;

    SELECT id INTO v_rol_id FROM rol WHERE nombre = 'Administrador';

    INSERT INTO usuario (nombre, email, password_hash, estado, fecha_registro, tipo, rol_id)
    VALUES (
        'Administrador General',
        '{ADMIN_EMAIL}',
        '{ADMIN_PASSWORD_HASH}',
        'activo',
        CURRENT_DATE,
        'administrador',
        v_rol_id
    )
    RETURNING id INTO v_usuario_id;

    INSERT INTO empleado (id, sucursal_id) VALUES (v_usuario_id, NULL);
    INSERT INTO administrador (id) VALUES (v_usuario_id);
END $$;
"""

DOWNGRADE_SQL = f"""
DELETE FROM administrador WHERE id = (SELECT id FROM usuario WHERE email = '{ADMIN_EMAIL}');
DELETE FROM empleado WHERE id = (SELECT id FROM usuario WHERE email = '{ADMIN_EMAIL}');
DELETE FROM usuario WHERE email = '{ADMIN_EMAIL}';
DELETE FROM rol WHERE nombre = 'Administrador' AND NOT EXISTS (
    SELECT 1 FROM usuario WHERE rol_id = rol.id
);
"""


def upgrade() -> None:
    op.execute(SEED_SQL)


def downgrade() -> None:
    op.execute(DOWNGRADE_SQL)
