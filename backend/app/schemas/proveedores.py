from datetime import date

from pydantic import BaseModel, EmailStr, Field


class ProveedorCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=150)
    email: EmailStr
    nit: str = Field(min_length=1, max_length=30)
    contacto_nombre: str | None = Field(default=None, max_length=150)
    telefono: str | None = Field(default=None, max_length=30)
    direccion: str | None = Field(default=None, max_length=255)


class ProveedorUpdate(BaseModel):
    nombre: str = Field(min_length=2, max_length=150)
    nit: str = Field(min_length=1, max_length=30)
    contacto_nombre: str | None = Field(default=None, max_length=150)
    telefono: str | None = Field(default=None, max_length=30)
    direccion: str | None = Field(default=None, max_length=255)
    estado: str = Field(pattern="^(activo|inactivo)$")


class ProveedorOut(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    nit: str
    contacto_nombre: str | None
    telefono: str | None
    direccion: str | None
    estado: str
    fecha_registro: date
    metodo_registro: str

    model_config = {"from_attributes": True}
