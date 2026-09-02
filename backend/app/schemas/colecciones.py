from pydantic import BaseModel, Field


class ColeccionCreate(BaseModel):
    temporada_id: int
    nombre: str = Field(min_length=2, max_length=100)
    descripcion: str | None = None


class ColeccionUpdate(ColeccionCreate):
    pass


class ColeccionOut(BaseModel):
    id: int
    temporada_id: int
    temporada_nombre: str
    nombre: str
    descripcion: str | None

    model_config = {"from_attributes": True}
