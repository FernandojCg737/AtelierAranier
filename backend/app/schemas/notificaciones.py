from datetime import datetime, timezone

from pydantic import BaseModel, field_serializer


class NotificacionOut(BaseModel):
    id: int
    tipo_evento: str
    mensaje: str
    fecha_envio: datetime
    leida: bool
    entidad_tipo: str | None
    entidad_id: int | None

    model_config = {"from_attributes": True}

    @field_serializer("fecha_envio")
    def _serialize_fecha(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()


class NotificacionAdminOut(NotificacionOut):
    cliente_id: int
    cliente_nombre: str
    cliente_email: str
    canal: str
    estado: str


class NotificacionPage(BaseModel):
    items: list[NotificacionAdminOut]
    total: int
    page: int
    page_size: int
