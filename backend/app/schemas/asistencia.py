from datetime import date, datetime, time

from pydantic import BaseModel


class EstadoAsistenciaOut(BaseModel):
    liberado: bool
    ventana_cerrada: bool
    hora_liberacion: time
    codigo_fecha: date
    # El codigo solo viaja en la respuesta cuando ya esta liberado (o si
    # quien pregunta es Administrador, que lo ve siempre para poder
    # anunciarlo/supervisar) -- se arma asi en el endpoint, no aca.
    codigo: str | None = None


class ConfigurarHoraRequest(BaseModel):
    hora_liberacion: time


class MarcadoOut(BaseModel):
    id: int
    empleado_id: int
    empleado_nombre: str
    sucursal_nombre: str | None
    fecha: date
    hora_marcado: datetime
    latitud: float
    longitud: float
    foto_url: str | None

    model_config = {"from_attributes": True}


class MarcadoHoyOut(BaseModel):
    empleado_id: int
    empleado_nombre: str
    sucursal_nombre: str | None
    marco: bool
    hora_marcado: datetime | None
    # "marco" | "pendiente" (la ventana sigue abierta o aun no libera) |
    # "falta" (la ventana de 5 min ya cerro y no marco).
    estado: str
