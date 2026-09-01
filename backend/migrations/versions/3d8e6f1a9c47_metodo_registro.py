"""usuario: columna metodo_registro (email/google/admin) + trigger la incluye (CU03/CU19)

Revision ID: 3d8e6f1a9c47
Revises: 7f3ac9d4e1b2
Create Date: 2026-08-31

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3d8e6f1a9c47"
down_revision = "7f3ac9d4e1b2"
branch_labels = None
depends_on = None


FN_BITACORA_NUEVO_USUARIO = """
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
        'Alta automatica de usuario (' || NEW.tipo || ') via ' || NEW.metodo_registro || ': ' || NEW.email,
        NULLIF(current_setting('atelier.client_ip', true), '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

FN_BITACORA_NUEVO_USUARIO_DOWN = """
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

SP_CREAR_CLIENTE_DOWN = """
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


def upgrade() -> None:
    op.execute(
        "ALTER TABLE usuario ADD COLUMN IF NOT EXISTS metodo_registro VARCHAR(20) NOT NULL DEFAULT 'sistema'"
    )
    op.execute(FN_BITACORA_NUEVO_USUARIO)
    op.execute("DROP FUNCTION IF EXISTS sp_crear_cliente(VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR);")
    op.execute(SP_CREAR_CLIENTE)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS sp_crear_cliente(VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR);")
    op.execute(SP_CREAR_CLIENTE_DOWN)
    op.execute(FN_BITACORA_NUEVO_USUARIO_DOWN)
    op.drop_column("usuario", "metodo_registro")
