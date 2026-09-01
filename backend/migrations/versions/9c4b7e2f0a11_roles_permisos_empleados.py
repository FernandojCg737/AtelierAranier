"""seed roles/permisos + funciones/PA para empleados y matriz de permisos (CU02)

Revision ID: 9c4b7e2f0a11
Revises: 3d8e6f1a9c47
Create Date: 2026-08-31

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "9c4b7e2f0a11"
down_revision = "3d8e6f1a9c47"
branch_labels = None
depends_on = None


SEED_SQL = """
INSERT INTO permiso (nombre, descripcion) VALUES
    ('CU01', 'Gestionar Inicio y Cierre de Sesion'),
    ('CU02', 'Administrar Usuarios, Roles y Permisos'),
    ('CU03', 'Registrar y Administrar Clientes'),
    ('CU04', 'Administrar Ciudades y Sucursales'),
    ('CU05', 'Administrar Catalogo de Productos'),
    ('CU06', 'Administrar Proveedores'),
    ('CU07', 'Configurar Temporadas y Colecciones'),
    ('CU08', 'Consultar Catalogo y Disponibilidad'),
    ('CU09', 'Visualizar Prenda con Realidad Aumentada'),
    ('CU10', 'Solicitar y Administrar Reservas'),
    ('CU11', 'Atender Reservas en Sucursal'),
    ('CU12', 'Controlar Inventario por Sucursal'),
    ('CU13', 'Administrar Carrito de Compras'),
    ('CU14', 'Registrar Venta Presencial'),
    ('CU15', 'Procesar Compra Digital'),
    ('CU16', 'Enviar Notificaciones'),
    ('CU17', 'Actualizar Perfil de Usuario'),
    ('CU18', 'Generar Reportes y Dashboards'),
    ('CU19', 'Auditar Operaciones (Bitacora)'),
    ('CU20', 'Recomendar Prendas por IA'),
    ('CU21', 'Atender Cliente con Chatbot')
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO rol (nombre, descripcion) VALUES
    ('Encargado de Sucursal', 'Administra la operacion diaria de una sucursal: inventario, reservas y ventas.'),
    ('Cajero', 'Atiende ventas presenciales y consulta el catalogo en sucursal.')
ON CONFLICT (nombre) DO NOTHING;

-- Administrador: acceso total (superusuario tambien a nivel de codigo, ver require_permiso)
INSERT INTO rol_permiso (rol_id, permiso_id)
SELECT r.id, p.id FROM rol r CROSS JOIN permiso p WHERE r.nombre = 'Administrador'
ON CONFLICT (rol_id, permiso_id) DO NOTHING;

-- Encargado de Sucursal: operacion de su sucursal
INSERT INTO rol_permiso (rol_id, permiso_id)
SELECT r.id, p.id FROM rol r CROSS JOIN permiso p
WHERE r.nombre = 'Encargado de Sucursal' AND p.nombre IN ('CU01','CU04','CU08','CU10','CU11','CU12','CU14','CU17')
ON CONFLICT (rol_id, permiso_id) DO NOTHING;

-- Cajero: ventas y catalogo
INSERT INTO rol_permiso (rol_id, permiso_id)
SELECT r.id, p.id FROM rol r CROSS JOIN permiso p
WHERE r.nombre = 'Cajero' AND p.nombre IN ('CU01','CU08','CU13','CU14','CU17')
ON CONFLICT (rol_id, permiso_id) DO NOTHING;
"""

SP_CREAR_EMPLEADO = """
CREATE OR REPLACE FUNCTION sp_crear_empleado(
    p_nombre VARCHAR,
    p_email VARCHAR,
    p_password_hash VARCHAR,
    p_tipo VARCHAR,
    p_sucursal_id INTEGER,
    p_rol_id INTEGER,
    p_metodo_registro VARCHAR
) RETURNS INTEGER AS $$
DECLARE
    v_usuario_id INTEGER;
BEGIN
    IF p_tipo NOT IN ('administrador', 'encargado_sucursal', 'cajero') THEN
        RAISE EXCEPTION 'tipo_empleado_invalido';
    END IF;

    INSERT INTO usuario (nombre, email, password_hash, estado, fecha_registro, tipo, metodo_registro, rol_id)
    VALUES (p_nombre, p_email, p_password_hash, 'activo', CURRENT_DATE, p_tipo, p_metodo_registro, p_rol_id)
    RETURNING id INTO v_usuario_id;

    INSERT INTO empleado (id, sucursal_id) VALUES (v_usuario_id, p_sucursal_id);

    IF p_tipo = 'administrador' THEN
        INSERT INTO administrador (id) VALUES (v_usuario_id);
    ELSIF p_tipo = 'encargado_sucursal' THEN
        INSERT INTO encargado_sucursal (id) VALUES (v_usuario_id);
    ELSIF p_tipo = 'cajero' THEN
        INSERT INTO cajero (id) VALUES (v_usuario_id);
    END IF;

    RETURN v_usuario_id;
END;
$$ LANGUAGE plpgsql;
"""

SP_ACTUALIZAR_EMPLEADO = """
CREATE OR REPLACE FUNCTION sp_actualizar_empleado(
    p_id INTEGER,
    p_nombre VARCHAR,
    p_sucursal_id INTEGER,
    p_rol_id INTEGER,
    p_estado VARCHAR
) RETURNS VOID AS $$
BEGIN
    UPDATE usuario SET nombre = p_nombre, estado = p_estado, rol_id = p_rol_id WHERE id = p_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'usuario_no_encontrado';
    END IF;

    UPDATE empleado SET sucursal_id = p_sucursal_id WHERE id = p_id;
END;
$$ LANGUAGE plpgsql;
"""

SP_REEMPLAZAR_PERMISOS_ROL = """
CREATE OR REPLACE FUNCTION sp_reemplazar_permisos_rol(p_rol_id INTEGER, p_permiso_ids INTEGER[])
RETURNS VOID AS $$
BEGIN
    DELETE FROM rol_permiso WHERE rol_id = p_rol_id;

    IF p_permiso_ids IS NOT NULL THEN
        INSERT INTO rol_permiso (rol_id, permiso_id)
        SELECT p_rol_id, unnest(p_permiso_ids);
    END IF;
END;
$$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    op.execute(SEED_SQL)
    op.execute(SP_CREAR_EMPLEADO)
    op.execute(SP_ACTUALIZAR_EMPLEADO)
    op.execute(SP_REEMPLAZAR_PERMISOS_ROL)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS sp_reemplazar_permisos_rol(INTEGER, INTEGER[]);")
    op.execute("DROP FUNCTION IF EXISTS sp_actualizar_empleado(INTEGER, VARCHAR, INTEGER, INTEGER, VARCHAR);")
    op.execute("DROP FUNCTION IF EXISTS sp_crear_empleado(VARCHAR, VARCHAR, VARCHAR, VARCHAR, INTEGER, INTEGER, VARCHAR);")
    op.execute("""
        DELETE FROM rol_permiso WHERE rol_id IN (
            SELECT id FROM rol WHERE nombre IN ('Encargado de Sucursal', 'Cajero')
        );
    """)
    op.execute("""
        DELETE FROM rol WHERE nombre IN ('Encargado de Sucursal', 'Cajero')
        AND NOT EXISTS (SELECT 1 FROM usuario WHERE rol_id = rol.id);
    """)
