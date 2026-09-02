from decimal import Decimal

from pydantic import BaseModel, Field


class ImagenOut(BaseModel):
    id: int
    url: str
    orden: int

    model_config = {"from_attributes": True}


class ProductoCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=150)
    descripcion: str | None = None
    precio: Decimal = Field(gt=0, decimal_places=2)
    precio_original: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    categoria_id: int
    marca_id: int
    proveedor_id: int
    temporada_id: int
    coleccion_id: int


class ProductoUpdate(ProductoCreate):
    estado: str = Field(pattern="^(activo|inactivo)$")


class DisponibilidadOut(BaseModel):
    sucursal_nombre: str
    cantidad: int


class ProductoOut(BaseModel):
    id: int
    nombre: str
    descripcion: str | None
    precio: Decimal
    precio_original: Decimal | None
    estado: str
    categoria_id: int
    categoria_nombre: str
    marca_id: int
    marca_nombre: str
    proveedor_id: int
    proveedor_nombre: str
    temporada_id: int
    temporada_nombre: str
    coleccion_id: int
    coleccion_nombre: str
    imagenes: list[ImagenOut]
    sucursales_disponibles: list[DisponibilidadOut]

    model_config = {"from_attributes": True}


class OpcionOut(BaseModel):
    id: int
    nombre: str

    model_config = {"from_attributes": True}


class CatalogoBaseOut(BaseModel):
    categorias: list[OpcionOut]
    marcas: list[OpcionOut]
    temporadas: list[OpcionOut]
    colecciones: list[OpcionOut]
    proveedores: list[OpcionOut]
    sucursales: list[OpcionOut]
    tallas: list[OpcionOut]
    colores: list[OpcionOut]


class MarcaCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)


class MarcaOut(BaseModel):
    id: int
    nombre: str

    model_config = {"from_attributes": True}


class InventarioOut(BaseModel):
    id: int
    sucursal_id: int
    sucursal_nombre: str
    talla_id: int
    talla_codigo: str
    color_id: int
    color_nombre: str
    cantidad: int

    model_config = {"from_attributes": True}


class InventarioUpsert(BaseModel):
    sucursal_id: int
    talla_id: int
    color_id: int
    cantidad: int = Field(ge=0)


class InventarioCantidadUpdate(BaseModel):
    cantidad: int = Field(ge=0)


class ProductoPublicoOut(BaseModel):
    id: int
    nombre: str
    descripcion: str | None
    precio: Decimal
    precio_original: Decimal | None
    marca_nombre: str
    categoria_nombre: str
    temporada_nombre: str
    imagenes: list[str]
    sucursales_disponibles: list[str]
