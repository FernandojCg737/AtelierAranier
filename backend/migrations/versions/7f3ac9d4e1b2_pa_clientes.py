"""funciones/PA: alta y edicion de cliente, cambio de password (CU03/CU17)

Revision ID: 7f3ac9d4e1b2
Revises: 126351c0bdea
Create Date: 2026-08-31

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "7f3ac9d4e1b2"
down_revision = "126351c0bdea"
branch_labels = None
depends_on = None


SP_CREAR_CLIENTE = """
CREATE OR REPLACE FUNCTION sp_crear_cliente(
    p_nombre VARCHAR,
    p_email VARCHAR,
    p_password_hash VARCHAR,
    p_telefono VARCHAR,
    p_direccion VARCHAR
) RETURNS INTEGER AS $$
DECLARE
    v_usuario_id INTEGER;
BEGIN
    INSERT INTO usuario (nombre, email, password_hash, estado, fecha_registro, tipo)
    VALUES (p_nombre, p_email, p_password_hash, 'activo', CURRENT_DATE, 'cliente')
    RETURNING id INTO v_usuario_id;

    INSERT INTO cliente (id, telefono, direccion)
    VALUES (v_usuario_id, p_telefono, p_direccion);

    RETURN v_usuario_id;
END;
$$ LANGUAGE plpgsql;
"""

SP_ACTUALIZAR_CLIENTE_PERFIL = """
CREATE OR REPLACE FUNCTION sp_actualizar_cliente_perfil(
    p_id INTEGER,
    p_nombre VARCHAR,
    p_telefono VARCHAR,
    p_direccion VARCHAR
) RETURNS VOID AS $$
BEGIN
    UPDATE usuario SET nombre = p_nombre WHERE id = p_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'usuario_no_encontrado';
    END IF;

    UPDATE cliente SET telefono = p_telefono, direccion = p_direccion WHERE id = p_id;
END;
$$ LANGUAGE plpgsql;
"""

SP_ACTUALIZAR_USUARIO_NOMBRE = """
CREATE OR REPLACE FUNCTION sp_actualizar_usuario_nombre(
    p_id INTEGER,
    p_nombre VARCHAR
) RETURNS VOID AS $$
BEGIN
    UPDATE usuario SET nombre = p_nombre WHERE id = p_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'usuario_no_encontrado';
    END IF;
END;
$$ LANGUAGE plpgsql;
"""

SP_ACTUALIZAR_CLIENTE_ADMIN = """
CREATE OR REPLACE FUNCTION sp_actualizar_cliente_admin(
    p_id INTEGER,
    p_nombre VARCHAR,
    p_telefono VARCHAR,
    p_direccion VARCHAR,
    p_estado VARCHAR
) RETURNS VOID AS $$
BEGIN
    UPDATE usuario SET nombre = p_nombre, estado = p_estado WHERE id = p_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'usuario_no_encontrado';
    END IF;

    UPDATE cliente SET telefono = p_telefono, direccion = p_direccion WHERE id = p_id;
END;
$$ LANGUAGE plpgsql;
"""

SP_CAMBIAR_PASSWORD = """
CREATE OR REPLACE FUNCTION sp_cambiar_password(
    p_id INTEGER,
    p_password_hash VARCHAR,
    p_session_id VARCHAR
) RETURNS VOID AS $$
BEGIN
    UPDATE usuario
    SET password_hash = p_password_hash, session_id = p_session_id
    WHERE id = p_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'usuario_no_encontrado';
    END IF;
END;
$$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    op.execute(SP_CREAR_CLIENTE)
    op.execute(SP_ACTUALIZAR_CLIENTE_PERFIL)
    op.execute(SP_ACTUALIZAR_USUARIO_NOMBRE)
    op.execute(SP_ACTUALIZAR_CLIENTE_ADMIN)
    op.execute(SP_CAMBIAR_PASSWORD)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS sp_cambiar_password(INTEGER, VARCHAR, VARCHAR);")
    op.execute("DROP FUNCTION IF EXISTS sp_actualizar_cliente_admin(INTEGER, VARCHAR, VARCHAR, VARCHAR, VARCHAR);")
    op.execute("DROP FUNCTION IF EXISTS sp_actualizar_usuario_nombre(INTEGER, VARCHAR);")
    op.execute("DROP FUNCTION IF EXISTS sp_actualizar_cliente_perfil(INTEGER, VARCHAR, VARCHAR, VARCHAR);")
    op.execute("DROP FUNCTION IF EXISTS sp_crear_cliente(VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR);")
