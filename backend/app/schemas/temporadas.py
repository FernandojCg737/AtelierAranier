from datetime import date

from pydantic import BaseModel, Field, model_validator


class TemporadaCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    fecha_inicio: date
    fecha_fin: date

    @model_validator(mode="after")
    def _validar_rango(self) -> "TemporadaCreate":
        if self.fecha_fin <= self.fecha_inicio:
            raise ValueError("La fecha de fin debe ser posterior a la fecha de inicio.")
        return self


class TemporadaUpdate(TemporadaCreate):
    pass


class TemporadaOut(BaseModel):
    id: int
    nombre: str
    fecha_inicio: date
    fecha_fin: date

    model_config = {"from_attributes": True}
