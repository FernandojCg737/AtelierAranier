"""funciones/PA: alta y edicion de proveedor (CU06)

Revision ID: fcca95be453b
Revises: 5a1d9f6c3e28
Create Date: 2026-09-01

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "fcca95be453b"
down_revision = "5a1d9f6c3e28"
branch_labels = None
depends_on = None


SP_CREAR_PROVEEDOR = """
CREATE OR REPLACE FUNCTION sp_crear_proveedor(
    p_nombre VARCHAR,
    p_email VARCHAR,
    p_password_hash VARCHAR,
    p_nit VARCHAR,
    p_contacto_nombre VARCHAR,
    p_telefono VARCHAR,
    p_direccion VARCHAR,
    p_metodo_registro VARCHAR
) RETURNS INTEGER AS $$
DECLARE
    v_usuario_id INTEGER;
BEGIN
    INSERT INTO usuario (nombre, email, password_hash, estado, fecha_registro, tipo, metodo_registro)
    VALUES (p_nombre, p_email, p_password_hash, 'activo', CURRENT_DATE, 'proveedor', p_metodo_registro)
    RETURNING id INTO v_usuario_id;

    INSERT INTO proveedor (id, nit, contacto_nombre, telefono, direccion)
    VALUES (v_usuario_id, p_nit, p_contacto_nombre, p_telefono, p_direccion);

    RETURN v_usuario_id;
END;
$$ LANGUAGE plpgsql;
"""

SP_ACTUALIZAR_PROVEEDOR = """
CREATE OR REPLACE FUNCTION sp_actualizar_proveedor(
    p_id INTEGER,
    p_nombre VARCHAR,
    p_nit VARCHAR,
    p_contacto_nombre VARCHAR,
    p_telefono VARCHAR,
    p_direccion VARCHAR,
    p_estado VARCHAR
) RETURNS VOID AS $$
BEGIN
    UPDATE usuario SET nombre = p_nombre, estado = p_estado WHERE id = p_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'usuario_no_encontrado';
    END IF;

    UPDATE proveedor
    SET nit = p_nit, contacto_nombre = p_contacto_nombre, telefono = p_telefono, direccion = p_direccion
    WHERE id = p_id;
END;
$$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    op.execute(SP_CREAR_PROVEEDOR)
    op.execute(SP_ACTUALIZAR_PROVEEDOR)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS sp_actualizar_proveedor(INTEGER, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR);")
    op.execute(
        "DROP FUNCTION IF EXISTS sp_crear_proveedor(VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR);"
    )
