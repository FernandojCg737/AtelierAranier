from decimal import Decimal

from pydantic import BaseModel


class SucursalOpcion(BaseModel):
    id: int
    nombre: str

    model_config = {"from_attributes": True}


class CatalogoVarianteOut(BaseModel):
    id: int
    talla_codigo: str
    color_nombre: str
    cantidad: int


class CatalogoProductoOut(BaseModel):
    id: int
    nombre: str
    marca_nombre: str
    categoria_nombre: str
    precio: Decimal
    imagen_url: str | None
    cantidad_total: int
    disponible: bool
    variantes: list[CatalogoVarianteOut]
