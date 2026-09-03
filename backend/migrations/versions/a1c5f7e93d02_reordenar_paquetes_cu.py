"""reordenar paquetes y renumerar CUs (fusiona reservas y ventas, agrega CU20)

Revision ID: a1c5f7e93d02
Revises: 686373258c6f
Create Date: 2026-09-03

"""
from alembic import op

revision = "a1c5f7e93d02"
down_revision = "686373258c6f"
branch_labels = None
depends_on = None

UPGRADE_SQL = """
-- 1) CU11 "Atender Reservas en Sucursal" se fusiona con CU10, que pasa a
--    llamarse "Gestion de Reservas" (une solicitar+atender en un solo CU).
DO $$
DECLARE
    v_cu10 INT;
    v_cu11 INT;
    v_cu14 INT;
    v_cu15 INT;
BEGIN
    SELECT id INTO v_cu10 FROM permiso WHERE nombre = 'CU10';
    SELECT id INTO v_cu11 FROM permiso WHERE nombre = 'CU11';
    IF v_cu10 IS NOT NULL AND v_cu11 IS NOT NULL THEN
        INSERT INTO rol_permiso (rol_id, permiso_id)
        SELECT rol_id, v_cu10 FROM rol_permiso WHERE permiso_id = v_cu11
        ON CONFLICT (rol_id, permiso_id) DO NOTHING;
        DELETE FROM rol_permiso WHERE permiso_id = v_cu11;
        DELETE FROM permiso WHERE id = v_cu11;
    END IF;

    -- 2) CU15 "Procesar Compra Digital" se fusiona con CU14, que pasa a
    --    llamarse "Gestion de Ventas" (une venta presencial+digital).
    SELECT id INTO v_cu14 FROM permiso WHERE nombre = 'CU14';
    SELECT id INTO v_cu15 FROM permiso WHERE nombre = 'CU15';
    IF v_cu14 IS NOT NULL AND v_cu15 IS NOT NULL THEN
        INSERT INTO rol_permiso (rol_id, permiso_id)
        SELECT rol_id, v_cu14 FROM rol_permiso WHERE permiso_id = v_cu15
        ON CONFLICT (rol_id, permiso_id) DO NOTHING;
        DELETE FROM rol_permiso WHERE permiso_id = v_cu15;
        DELETE FROM permiso WHERE id = v_cu15;
    END IF;
END $$;

-- 3) Renumerar el resto de codigos. El orden importa: cada UPDATE libera el
--    codigo que usa el siguiente antes de que este lo reclame.
UPDATE permiso SET nombre = 'CU11', descripcion = 'Gestion de Ventas' WHERE nombre = 'CU14';
UPDATE permiso SET nombre = 'CU10', descripcion = 'Gestion de Reservas' WHERE nombre = 'CU10';
UPDATE permiso SET nombre = 'CU15', descripcion = 'Actualizar Perfil de Usuario' WHERE nombre = 'CU17';
UPDATE permiso SET nombre = 'CU14', descripcion = 'Enviar Notificaciones' WHERE nombre = 'CU16';
UPDATE permiso SET nombre = 'CU17', descripcion = 'Auditar Operaciones (Bitacora)' WHERE nombre = 'CU19';
UPDATE permiso SET nombre = 'CU16', descripcion = 'Gestion Reportes y Dashboards' WHERE nombre = 'CU18';
UPDATE permiso SET nombre = 'CU18', descripcion = 'Recomendar Prendas por IA' WHERE nombre = 'CU20';
UPDATE permiso SET nombre = 'CU19', descripcion = 'Atender Cliente con Chatbot' WHERE nombre = 'CU21';

-- 4) Nuevo caso de uso.
INSERT INTO permiso (nombre, descripcion) VALUES
    ('CU20', 'Reputacion y Calificaciones')
ON CONFLICT (nombre) DO NOTHING;
"""

DOWNGRADE_SQL = """
DELETE FROM permiso WHERE nombre = 'CU20' AND descripcion = 'Reputacion y Calificaciones';
UPDATE permiso SET nombre = 'CU21', descripcion = 'Atender Cliente con Chatbot' WHERE nombre = 'CU19';
UPDATE permiso SET nombre = 'CU20', descripcion = 'Recomendar Prendas por IA' WHERE nombre = 'CU18';
UPDATE permiso SET nombre = 'CU18', descripcion = 'Generar Reportes y Dashboards' WHERE nombre = 'CU16';
UPDATE permiso SET nombre = 'CU19', descripcion = 'Auditar Operaciones (Bitacora)' WHERE nombre = 'CU17';
UPDATE permiso SET nombre = 'CU16', descripcion = 'Enviar Notificaciones' WHERE nombre = 'CU14';
UPDATE permiso SET nombre = 'CU17', descripcion = 'Actualizar Perfil de Usuario' WHERE nombre = 'CU15';
UPDATE permiso SET nombre = 'CU14', descripcion = 'Registrar Venta Presencial' WHERE nombre = 'CU11';
INSERT INTO permiso (nombre, descripcion) VALUES
    ('CU11', 'Atender Reservas en Sucursal'),
    ('CU15', 'Procesar Compra Digital')
ON CONFLICT (nombre) DO NOTHING;
"""


def upgrade() -> None:
    op.execute(UPGRADE_SQL)


def downgrade() -> None:
    op.execute(DOWNGRADE_SQL)
