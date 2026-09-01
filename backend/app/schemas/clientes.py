from datetime import date

from pydantic import BaseModel, EmailStr, Field


class ClienteAdminCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=150)
    email: EmailStr
    telefono: str | None = Field(default=None, max_length=30)
    direccion: str | None = Field(default=None, max_length=255)


class ClienteAdminUpdate(BaseModel):
    nombre: str = Field(min_length=2, max_length=150)
    telefono: str | None = Field(default=None, max_length=30)
    direccion: str | None = Field(default=None, max_length=255)
    estado: str = Field(pattern="^(activo|inactivo)$")


class ClienteAdminOut(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    telefono: str | None
    direccion: str | None
    estado: str
    fecha_registro: date
    metodo_registro: str

    model_config = {"from_attributes": True}
