"""seed rol Cliente + sp_crear_cliente lo asigna automaticamente (CU02, preparado a futuro)

Revision ID: 5a1d9f6c3e28
Revises: 9c4b7e2f0a11
Create Date: 2026-09-01

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "5a1d9f6c3e28"
down_revision = "9c4b7e2f0a11"
branch_labels = None
depends_on = None


SEED_SQL = """
INSERT INTO rol (nombre, descripcion) VALUES
    ('Cliente', 'Cuenta de cliente de la tienda. Hoy no restringe nada: la tienda es igual para todos los clientes.')
ON CONFLICT (nombre) DO NOTHING;

UPDATE usuario SET rol_id = (SELECT id FROM rol WHERE nombre = 'Cliente')
WHERE tipo = 'cliente' AND rol_id IS NULL;
"""

SP_CREAR_CLIENTE = """
CREATE OR REPLACE FUNCTION sp_crear_cliente(
    p_nombre VARCHAR,
    p_email VARCHAR,
    p_password_hash VARCHAR,
    p_telefono VARCHAR,
    p_direccion VARCHAR,
    p_metodo_registro VARCHAR
) RETURNS INTEGER AS $$
DECLARE
    v_usuario_id INTEGER;
    v_rol_id INTEGER;
BEGIN
    SELECT id INTO v_rol_id FROM rol WHERE nombre = 'Cliente';

    INSERT INTO usuario (nombre, email, password_hash, estado, fecha_registro, tipo, metodo_registro, rol_id)
    VALUES (p_nombre, p_email, p_password_hash, 'activo', CURRENT_DATE, 'cliente', p_metodo_registro, v_rol_id)
    RETURNING id INTO v_usuario_id;

    INSERT INTO cliente (id, telefono, direccion)
    VALUES (v_usuario_id, p_telefono, p_direccion);

    RETURN v_usuario_id;
END;
$$ LANGUAGE plpgsql;
"""

SP_CREAR_CLIENTE_DOWN = """
CREATE OR REPLACE FUNCTION sp_crear_cliente(
    p_nombre VARCHAR,
    p_email VARCHAR,
    p_password_hash VARCHAR,
    p_telefono VARCHAR,
    p_direccion VARCHAR,
    p_metodo_registro VARCHAR
) RETURNS INTEGER AS $$
DECLARE
    v_usuario_id INTEGER;
BEGIN
    INSERT INTO usuario (nombre, email, password_hash, estado, fecha_registro, tipo, metodo_registro)
    VALUES (p_nombre, p_email, p_password_hash, 'activo', CURRENT_DATE, 'cliente', p_metodo_registro)
    RETURNING id INTO v_usuario_id;

    INSERT INTO cliente (id, telefono, direccion)
    VALUES (v_usuario_id, p_telefono, p_direccion);

    RETURN v_usuario_id;
END;
$$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    op.execute(SEED_SQL)
    op.execute(SP_CREAR_CLIENTE)


def downgrade() -> None:
    op.execute(SP_CREAR_CLIENTE_DOWN)
    op.execute("""
        UPDATE usuario SET rol_id = NULL
        WHERE tipo = 'cliente' AND rol_id = (SELECT id FROM rol WHERE nombre = 'Cliente');
    """)
    op.execute("DELETE FROM rol WHERE nombre = 'Cliente';")
