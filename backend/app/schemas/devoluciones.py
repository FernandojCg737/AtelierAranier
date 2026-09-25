from datetime import datetime, timezone
from decimal import Decimal

from pydantic import BaseModel, Field, field_serializer


class ItemDevolucionIn(BaseModel):
    """Un item que se devuelve: referencia al detalle original de la venta
    (item_linea_id) y cuantas unidades de ese item se devuelven."""

    item_linea_id: int
    cantidad_devuelta: int = Field(ge=1)


class DevolucionCreate(BaseModel):
    """Payload para que el staff registre una devolucion desde el panel."""

    motivo: str = Field(pattern="^(defecto|talla_incorrecta|insatisfaccion|otro)$")
    tipo: str = Field(pattern="^(total|parcial)$")
    metodo_reembolso: str = Field(pattern="^(mismo_medio|credito_tienda|efectivo)$")
    observaciones: str | None = None
    items: list[ItemDevolucionIn] = Field(min_length=1)


class DetalleDevolucionOut(BaseModel):
    id: int
    item_linea_id: int
    producto_nombre: str
    talla_codigo: str
    color_nombre: str
    cantidad_devuelta: int
    precio_unitario: Decimal


class DevolucionOut(BaseModel):
    id: int
    venta_id: int
    empleado_nombre: str | None = None
    motivo: str
    tipo: str
    monto_reembolso: Decimal
    metodo_reembolso: str
    estado: str
    fecha_solicitud: datetime
    fecha_resolucion: datetime | None
    observaciones: str | None
    detalles: list[DetalleDevolucionOut]

    @field_serializer("fecha_solicitud", "fecha_resolucion")
    def _serialize_fecha(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()


class DevolucionAdminOut(DevolucionOut):
    """Vista extendida para el panel de admin: incluye datos del cliente."""

    cliente_nombre: str
    cliente_email: str
    venta_total: Decimal
    venta_fecha: datetime
    sucursal_nombre: str

    @field_serializer("venta_fecha")
    def _serialize_venta_fecha(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
