from pydantic import BaseModel


class PermisoOut(BaseModel):
    id: int
    nombre: str
    descripcion: str | None

    model_config = {"from_attributes": True}


class RolOut(BaseModel):
    id: int
    nombre: str
    descripcion: str | None
    permisos: list[str]

    model_config = {"from_attributes": True}


class ActualizarPermisosRequest(BaseModel):
    permiso_ids: list[int]
