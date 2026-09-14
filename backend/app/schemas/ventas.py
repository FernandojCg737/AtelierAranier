from datetime import datetime, timezone
from decimal import Decimal

from pydantic import BaseModel, Field, field_serializer


class OrdenPaypalOut(BaseModel):
    order_id: str
    total: Decimal
    # Link "approve" que devuelve PayPal -- solo lo usa el movil (abre esto
    # en un WebView); el web lo ignora porque su JS SDK ya sabe como
    # aprobar la orden con el order_id solo.
    approve_url: str | None = None


class CapturarPaypalIn(BaseModel):
    sucursal_id: int


class DetalleVentaOut(BaseModel):
    id: int
    producto_id: int
    producto_nombre: str
    talla_id: int
    talla_codigo: str
    color_id: int
    color_nombre: str
    cantidad: int
    precio_unitario: Decimal


class VentaOut(BaseModel):
    id: int
    tipo: str
    sucursal_id: int
    sucursal_nombre: str
    fecha: datetime
    total: Decimal
    estado: str
    metodo_pago: str
    estado_pago: str
    atendido_por_nombre: str | None
    calificacion_estrellas: int | None
    calificacion_comentario: str | None
    detalles: list[DetalleVentaOut]

    @field_serializer("fecha")
    def _serialize_fecha(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()


class VentaAdminOut(VentaOut):
    cliente_nombre: str
    cliente_email: str
    comprobante_url: str | None


class VentaPage(BaseModel):
    items: list[VentaAdminOut]
    total: int
    page: int
    page_size: int


class ClienteBusquedaOut(BaseModel):
    id: int
    nombre: str
    email: str


class ItemVentaPresencialCreate(BaseModel):
    producto_id: int
    talla_id: int
    color_id: int
    cantidad: int = Field(ge=1)


class VentaPresencialCreate(BaseModel):
    cliente_id: int
    sucursal_id: int
    items: list[ItemVentaPresencialCreate] = Field(min_length=1)


class VentaEditIn(BaseModel):
    sucursal_id: int
    items: list[ItemVentaPresencialCreate] = Field(min_length=1)
    metodo_pago: str
    estado_pago: str = Field(pattern="^(pendiente|verificando|completado|rechazado)$")
