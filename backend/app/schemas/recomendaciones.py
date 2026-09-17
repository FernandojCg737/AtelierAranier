from datetime import datetime, timezone
from decimal import Decimal

from pydantic import BaseModel, field_serializer


class RecomendacionOut(BaseModel):
    producto_id: int
    producto_nombre: str
    score: Decimal
    origen: str
    razon: str


class RelacionadoOut(BaseModel):
    producto_id: int
    producto_nombre: str
    origen: str
    razon: str


class RecomendacionAdminOut(BaseModel):
    id: int
    cliente_id: int
    cliente_nombre: str
    cliente_email: str
    producto_id: int
    producto_nombre: str
    score: Decimal
    origen: str
    razon: str | None
    convertido: bool
    fecha: datetime

    @field_serializer("fecha")
    def _serialize_fecha(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()


class RecomendacionResumen(BaseModel):
    total_activas: int
    convertidas: int
    tasa_conversion: float


class RecomendacionPage(BaseModel):
    resumen: RecomendacionResumen
    items: list[RecomendacionAdminOut]
    total: int
    page: int
    page_size: int


class RelacionadoAdminOut(BaseModel):
    id: int
    producto_id: int
    producto_nombre: str
    relacionado_id: int
    relacionado_nombre: str
    score: Decimal
    origen: str
    razon: str | None
    fecha: datetime

    @field_serializer("fecha")
    def _serialize_fecha(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()


class RelacionadoResumen(BaseModel):
    productos_totales: int
    productos_cubiertos: int
    cobertura_pct: float


class RelacionadoPage(BaseModel):
    resumen: RelacionadoResumen
    items: list[RelacionadoAdminOut]
    total: int
    page: int
    page_size: int
