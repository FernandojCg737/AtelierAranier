from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_serializer


class MensajeIn(BaseModel):
    mensaje: str = Field(min_length=1, max_length=1000)


class MensajeOut(BaseModel):
    id: int
    remitente: str
    mensaje: str
    fecha: datetime

    @field_serializer("fecha")
    def _serialize_fecha(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()


class ChatbotUsuarioOut(BaseModel):
    cliente_id: int
    cliente_nombre: str
    cliente_email: str
    total_mensajes: int
    ultima_actividad: datetime

    @field_serializer("ultima_actividad")
    def _serialize_fecha(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
