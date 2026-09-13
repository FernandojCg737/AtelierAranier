"""CU16: Enviar Notificaciones -- columnas leida/entidad + triggers automaticos

Revision ID: c4a7e91b3f05
Revises: a1f9d3c6e820
Create Date: 2026-09-13

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c4a7e91b3f05"
down_revision = "a1f9d3c6e820"
branch_labels = None
depends_on = None


# ---------------------------------------------------------------- reserva --
FN_RESERVA_CREADA = """
CREATE OR REPLACE FUNCTION fn_notificar_reserva_creada()
RETURNS trigger AS $$
BEGIN
    INSERT INTO notificacion (cliente_id, canal, tipo_evento, mensaje, fecha_envio, estado, leida, entidad_tipo, entidad_id)
    VALUES (
        NEW.cliente_id,
        'sistema',
        'reserva_creada',
        'Tu reserva #' || NEW.id || ' quedo registrada para el ' || to_char(NEW.horario_atencion, 'DD/MM/YYYY HH24:MI') || '.',
        now(),
        'enviada',
        false,
        'reserva',
        NEW.id
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

TRG_RESERVA_CREADA = """
CREATE TRIGGER trg_reserva_notificar_creada
AFTER INSERT ON reserva
FOR EACH ROW
EXECUTE FUNCTION fn_notificar_reserva_creada();
"""

FN_RESERVA_ESTADO = """
CREATE OR REPLACE FUNCTION fn_notificar_reserva_estado()
RETURNS trigger AS $$
DECLARE
    v_mensaje TEXT;
BEGIN
    IF NEW.estado = 'cancelada' THEN
        v_mensaje := 'Tu reserva #' || NEW.id || ' fue cancelada.';
    ELSIF NEW.estado = 'vencida' THEN
        v_mensaje := 'Tu reserva #' || NEW.id || ' vencio sin cobrarse y liberamos el stock reservado.';
    ELSE
        RETURN NEW;
    END IF;

    INSERT INTO notificacion (cliente_id, canal, tipo_evento, mensaje, fecha_envio, estado, leida, entidad_tipo, entidad_id)
    VALUES (NEW.cliente_id, 'sistema', 'reserva_' || NEW.estado, v_mensaje, now(), 'enviada', false, 'reserva', NEW.id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

TRG_RESERVA_ESTADO = """
CREATE TRIGGER trg_reserva_notificar_estado
AFTER UPDATE ON reserva
FOR EACH ROW
WHEN (OLD.estado IS DISTINCT FROM NEW.estado)
EXECUTE FUNCTION fn_notificar_reserva_estado();
"""

# ------------------------------------------------------------------ pago --
FN_PAGO_ESTADO = """
CREATE OR REPLACE FUNCTION fn_notificar_pago_estado()
RETURNS trigger AS $$
DECLARE
    v_cliente_id INTEGER;
    v_mensaje TEXT;
    v_tipo_evento VARCHAR(50);
BEGIN
    IF NEW.estado NOT IN ('completado', 'rechazado') THEN
        RETURN NEW;
    END IF;
    IF TG_OP = 'UPDATE' AND OLD.estado = NEW.estado THEN
        RETURN NEW;
    END IF;

    SELECT cliente_id INTO v_cliente_id FROM venta WHERE id = NEW.venta_id;
    IF v_cliente_id IS NULL THEN
        RETURN NEW;
    END IF;

    IF NEW.estado = 'completado' THEN
        v_tipo_evento := 'compra_confirmada';
        v_mensaje := 'Tu compra #' || NEW.venta_id || ' fue confirmada. Total: ' || NEW.monto || ' Bs.';
    ELSE
        v_tipo_evento := 'pago_rechazado';
        v_mensaje := 'Tu pago para la compra #' || NEW.venta_id || ' fue rechazado. Intenta de nuevo o contactanos.';
    END IF;

    INSERT INTO notificacion (cliente_id, canal, tipo_evento, mensaje, fecha_envio, estado, leida, entidad_tipo, entidad_id)
    VALUES (v_cliente_id, 'sistema', v_tipo_evento, v_mensaje, now(), 'enviada', false, 'venta', NEW.venta_id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

TRG_PAGO_ESTADO = """
CREATE TRIGGER trg_pago_notificar_estado
AFTER INSERT OR UPDATE ON pago
FOR EACH ROW
EXECUTE FUNCTION fn_notificar_pago_estado();
"""

# --------------------------------------------- alertas de vencimiento (lazy) --
SP_ALERTAS_VENCIMIENTO = """
CREATE OR REPLACE FUNCTION sp_generar_alertas_reservas_por_vencer()
RETURNS VOID AS $$
BEGIN
    INSERT INTO notificacion (cliente_id, canal, tipo_evento, mensaje, fecha_envio, estado, leida, entidad_tipo, entidad_id)
    SELECT
        r.cliente_id,
        'sistema',
        'reserva_por_vencer',
        'Tu reserva #' || r.id || ' vence pronto: pasa por la sucursal antes del ' ||
            to_char(r.horario_atencion, 'DD/MM/YYYY HH24:MI') || ' o perderas el stock retenido.',
        now(),
        'enviada',
        false,
        'reserva',
        r.id
    FROM reserva r
    WHERE r.estado IN ('pendiente', 'confirmada')
      AND r.horario_atencion > now()
      AND r.horario_atencion <= now() + interval '24 hours'
      AND NOT EXISTS (
          SELECT 1 FROM notificacion n
          WHERE n.entidad_tipo = 'reserva' AND n.entidad_id = r.id AND n.tipo_evento = 'reserva_por_vencer'
      );
END;
$$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    op.add_column("notificacion", sa.Column("leida", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column("notificacion", sa.Column("entidad_tipo", sa.String(length=30), nullable=True))
    op.add_column("notificacion", sa.Column("entidad_id", sa.Integer(), nullable=True))

    op.execute(FN_RESERVA_CREADA)
    op.execute(TRG_RESERVA_CREADA)
    op.execute(FN_RESERVA_ESTADO)
    op.execute(TRG_RESERVA_ESTADO)
    op.execute(FN_PAGO_ESTADO)
    op.execute(TRG_PAGO_ESTADO)
    op.execute(SP_ALERTAS_VENCIMIENTO)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS sp_generar_alertas_reservas_por_vencer();")
    op.execute("DROP TRIGGER IF EXISTS trg_pago_notificar_estado ON pago;")
    op.execute("DROP FUNCTION IF EXISTS fn_notificar_pago_estado();")
    op.execute("DROP TRIGGER IF EXISTS trg_reserva_notificar_estado ON reserva;")
    op.execute("DROP FUNCTION IF EXISTS fn_notificar_reserva_estado();")
    op.execute("DROP TRIGGER IF EXISTS trg_reserva_notificar_creada ON reserva;")
    op.execute("DROP FUNCTION IF EXISTS fn_notificar_reserva_creada();")
    op.drop_column("notificacion", "entidad_id")
    op.drop_column("notificacion", "entidad_tipo")
    op.drop_column("notificacion", "leida")
