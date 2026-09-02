from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, status
from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload

from app.api.deps import require_permiso
from app.core.audit import log_bitacora, set_client_ip_for_trigger
from app.core.storage import delete_producto_imagen, upload_producto_imagen
from app.db.session import get_db
from app.models import (
    Categoria,
    Coleccion,
    Color,
    Inventario,
    Marca,
    Producto,
    ProductoImagen,
    Proveedor,
    Sucursal,
    Talla,
    Temporada,
    Usuario,
)
from app.schemas.productos import (
    CatalogoBaseOut,
    DisponibilidadOut,
    ImagenOut,
    InventarioCantidadUpdate,
    InventarioOut,
    InventarioUpsert,
    MarcaCreate,
    MarcaOut,
    OpcionOut,
    ProductoCreate,
    ProductoOut,
    ProductoPublicoOut,
    ProductoUpdate,
)

router = APIRouter()


def _sucursales_disponibles(producto: Producto) -> list[str]:
    nombres = {i.sucursal.nombre for i in producto.inventarios if i.cantidad > 0}
    return sorted(nombres)


def _disponibilidad_admin(producto: Producto) -> list[DisponibilidadOut]:
    totales: dict[str, int] = {}
    for i in producto.inventarios:
        totales[i.sucursal.nombre] = totales.get(i.sucursal.nombre, 0) + i.cantidad
    return [
        DisponibilidadOut(sucursal_nombre=nombre, cantidad=cantidad)
        for nombre, cantidad in sorted(totales.items())
        if cantidad > 0
    ]


def _to_out(producto: Producto) -> ProductoOut:
    return ProductoOut(
        id=producto.id,
        nombre=producto.nombre,
        descripcion=producto.descripcion,
        precio=producto.precio,
        precio_original=producto.precio_original,
        estado=producto.estado,
        categoria_id=producto.categoria_id,
        categoria_nombre=producto.categoria.nombre,
        marca_id=producto.marca_id,
        marca_nombre=producto.marca.nombre,
        proveedor_id=producto.proveedor_id,
        proveedor_nombre=producto.proveedor.nombre,
        temporada_id=producto.temporada_id,
        temporada_nombre=producto.temporada.nombre,
        coleccion_id=producto.coleccion_id,
        coleccion_nombre=producto.coleccion.nombre,
        imagenes=[ImagenOut.model_validate(i) for i in producto.imagenes],
        sucursales_disponibles=_disponibilidad_admin(producto),
    )


def _get_producto_or_404(db: Session, producto_id: int) -> Producto:
    producto = (
        db.query(Producto)
        .options(
            joinedload(Producto.categoria),
            joinedload(Producto.marca),
            joinedload(Producto.proveedor),
            joinedload(Producto.temporada),
            joinedload(Producto.coleccion),
            joinedload(Producto.imagenes),
            joinedload(Producto.inventarios).joinedload(Inventario.sucursal),
        )
        .filter(Producto.id == producto_id)
        .first()
    )
    if producto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado.")
    return producto


@router.get("/catalogo-base", response_model=CatalogoBaseOut)
def get_catalogo_base(
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(require_permiso("CU05")),
) -> CatalogoBaseOut:
    colecciones = (
        db.query(Coleccion).options(joinedload(Coleccion.temporada)).order_by(Coleccion.nombre).all()
    )
    return CatalogoBaseOut(
        categorias=[OpcionOut.model_validate(c) for c in db.query(Categoria).order_by(Categoria.nombre).all()],
        marcas=[OpcionOut.model_validate(m) for m in db.query(Marca).order_by(Marca.nombre).all()],
        temporadas=[OpcionOut.model_validate(t) for t in db.query(Temporada).order_by(Temporada.nombre).all()],
        colecciones=[
            OpcionOut(id=c.id, nombre=f"{c.nombre} ({c.temporada.nombre})") for c in colecciones
        ],
        proveedores=[
            OpcionOut.model_validate(p)
            for p in db.query(Proveedor).filter(Proveedor.estado == "activo").order_by(Proveedor.nombre).all()
        ],
        sucursales=[OpcionOut.model_validate(s) for s in db.query(Sucursal).order_by(Sucursal.nombre).all()],
        tallas=[
            OpcionOut(id=t.id, nombre=t.codigo) for t in db.query(Talla).order_by(Talla.id).all()
        ],
        colores=[OpcionOut.model_validate(c) for c in db.query(Color).order_by(Color.nombre).all()],
    )


@router.post("/marcas", response_model=MarcaOut, status_code=status.HTTP_201_CREATED)
def create_marca(
    payload: MarcaCreate,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(require_permiso("CU05")),
) -> MarcaOut:
    result = db.execute(text("SELECT sp_crear_marca(:nombre)"), {"nombre": payload.nombre})
    marca_id = result.scalar_one()
    db.commit()

    marca = db.query(Marca).filter(Marca.id == marca_id).first()
    return MarcaOut.model_validate(marca)


def _to_publico(producto: Producto) -> ProductoPublicoOut:
    return ProductoPublicoOut(
        id=producto.id,
        nombre=producto.nombre,
        descripcion=producto.descripcion,
        precio=producto.precio,
        precio_original=producto.precio_original,
        marca_nombre=producto.marca.nombre,
        categoria_nombre=producto.categoria.nombre,
        temporada_nombre=producto.temporada.nombre,
        imagenes=[i.url for i in producto.imagenes],
        sucursales_disponibles=_sucursales_disponibles(producto),
    )


@router.get("/publico", response_model=list[ProductoPublicoOut])
def list_productos_publico(db: Session = Depends(get_db)) -> list[ProductoPublicoOut]:
    query = (
        db.query(Producto)
        .options(
            joinedload(Producto.marca),
            joinedload(Producto.categoria),
            joinedload(Producto.temporada),
            joinedload(Producto.imagenes),
            joinedload(Producto.inventarios).joinedload(Inventario.sucursal),
        )
        .filter(Producto.estado == "activo")
    )
    return [_to_publico(p) for p in query.order_by(Producto.nombre).all()]


@router.get("/publico/{producto_id}", response_model=ProductoPublicoOut)
def get_producto_publico(producto_id: int, db: Session = Depends(get_db)) -> ProductoPublicoOut:
    producto = (
        db.query(Producto)
        .options(
            joinedload(Producto.marca),
            joinedload(Producto.categoria),
            joinedload(Producto.temporada),
            joinedload(Producto.imagenes),
            joinedload(Producto.inventarios).joinedload(Inventario.sucursal),
        )
        .filter(Producto.id == producto_id, Producto.estado == "activo")
        .first()
    )
    if producto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado.")
    return _to_publico(producto)


@router.get("", response_model=list[ProductoOut])
def list_productos(
    buscar: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(require_permiso("CU05")),
) -> list[ProductoOut]:
    query = db.query(Producto).options(
        joinedload(Producto.categoria),
        joinedload(Producto.marca),
        joinedload(Producto.proveedor),
        joinedload(Producto.temporada),
        joinedload(Producto.coleccion),
        joinedload(Producto.imagenes),
        joinedload(Producto.inventarios).joinedload(Inventario.sucursal),
    )
    if buscar:
        query = query.filter(Producto.nombre.ilike(f"%{buscar}%"))
    return [_to_out(p) for p in query.order_by(Producto.nombre).all()]


@router.post("", response_model=ProductoOut, status_code=status.HTTP_201_CREATED)
def create_producto(
    payload: ProductoCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_permiso("CU05")),
) -> ProductoOut:
    set_client_ip_for_trigger(db, request)
    result = db.execute(
        text(
            "SELECT sp_crear_producto(:nombre, :descripcion, :precio, :precio_original, :categoria_id, "
            ":marca_id, :proveedor_id, :temporada_id, :coleccion_id)"
        ),
        {
            "nombre": payload.nombre,
            "descripcion": payload.descripcion,
            "precio": payload.precio,
            "precio_original": payload.precio_original,
            "categoria_id": payload.categoria_id,
            "marca_id": payload.marca_id,
            "proveedor_id": payload.proveedor_id,
            "temporada_id": payload.temporada_id,
            "coleccion_id": payload.coleccion_id,
        },
    )
    producto_id = result.scalar_one()
    db.commit()

    producto = _get_producto_or_404(db, producto_id)
    log_bitacora(db, admin, "CREAR", "producto", producto.id, f"Alta de producto: {producto.nombre}", request)
    return _to_out(producto)


@router.put("/{producto_id}", response_model=ProductoOut)
def update_producto(
    producto_id: int,
    payload: ProductoUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_permiso("CU05")),
) -> ProductoOut:
    _get_producto_or_404(db, producto_id)

    db.execute(
        text(
            "SELECT sp_actualizar_producto(:id, :nombre, :descripcion, :precio, :precio_original, "
            ":categoria_id, :marca_id, :proveedor_id, :temporada_id, :coleccion_id, :estado)"
        ),
        {
            "id": producto_id,
            "nombre": payload.nombre,
            "descripcion": payload.descripcion,
            "precio": payload.precio,
            "precio_original": payload.precio_original,
            "categoria_id": payload.categoria_id,
            "marca_id": payload.marca_id,
            "proveedor_id": payload.proveedor_id,
            "temporada_id": payload.temporada_id,
            "coleccion_id": payload.coleccion_id,
            "estado": payload.estado,
        },
    )
    db.commit()

    producto = _get_producto_or_404(db, producto_id)
    log_bitacora(db, admin, "ACTUALIZAR", "producto", producto.id, f"Edicion de producto: {producto.nombre}", request)
    return _to_out(producto)


def _to_inventario_out(inv: Inventario) -> InventarioOut:
    return InventarioOut(
        id=inv.id,
        sucursal_id=inv.sucursal_id,
        sucursal_nombre=inv.sucursal.nombre,
        talla_id=inv.talla_id,
        talla_codigo=inv.talla.codigo,
        color_id=inv.color_id,
        color_nombre=inv.color.nombre,
        cantidad=inv.cantidad,
    )


@router.get("/{producto_id}/inventario", response_model=list[InventarioOut])
def list_inventario(
    producto_id: int,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(require_permiso("CU05")),
) -> list[InventarioOut]:
    _get_producto_or_404(db, producto_id)
    inventarios = (
        db.query(Inventario)
        .options(joinedload(Inventario.sucursal), joinedload(Inventario.talla), joinedload(Inventario.color))
        .filter(Inventario.producto_id == producto_id)
        .join(Sucursal)
        .order_by(Sucursal.nombre)
        .all()
    )
    return [_to_inventario_out(i) for i in inventarios]


@router.post("/{producto_id}/inventario", response_model=InventarioOut, status_code=status.HTTP_201_CREATED)
def upsert_inventario(
    producto_id: int,
    payload: InventarioUpsert,
    request: Request,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_permiso("CU05")),
) -> InventarioOut:
    producto = _get_producto_or_404(db, producto_id)

    result = db.execute(
        text(
            "SELECT sp_establecer_inventario(:producto_id, :talla_id, :color_id, :sucursal_id, :cantidad)"
        ),
        {
            "producto_id": producto_id,
            "talla_id": payload.talla_id,
            "color_id": payload.color_id,
            "sucursal_id": payload.sucursal_id,
            "cantidad": payload.cantidad,
        },
    )
    inventario_id = result.scalar_one()
    db.commit()

    inventario = (
        db.query(Inventario)
        .options(joinedload(Inventario.sucursal), joinedload(Inventario.talla), joinedload(Inventario.color))
        .filter(Inventario.id == inventario_id)
        .first()
    )
    log_bitacora(
        db, admin, "ACTUALIZAR", "producto", producto_id, f"Stock actualizado para: {producto.nombre}", request
    )
    return _to_inventario_out(inventario)


@router.put("/{producto_id}/inventario/{inventario_id}", response_model=InventarioOut)
def update_inventario_cantidad(
    producto_id: int,
    inventario_id: int,
    payload: InventarioCantidadUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_permiso("CU05", "CU12")),
) -> InventarioOut:
    producto = _get_producto_or_404(db, producto_id)

    inventario = (
        db.query(Inventario)
        .filter(Inventario.id == inventario_id, Inventario.producto_id == producto_id)
        .first()
    )
    if inventario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Registro de inventario no encontrado.")

    db.execute(
        text("SELECT sp_actualizar_inventario_cantidad(:id, :cantidad)"),
        {"id": inventario_id, "cantidad": payload.cantidad},
    )
    db.commit()

    db.refresh(inventario)
    log_bitacora(
        db, admin, "ACTUALIZAR", "producto", producto_id, f"Stock actualizado para: {producto.nombre}", request
    )
    return _to_inventario_out(inventario)


@router.post("/{producto_id}/imagenes", response_model=ImagenOut, status_code=status.HTTP_201_CREATED)
async def add_imagen(
    producto_id: int,
    request: Request,
    file: UploadFile,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_permiso("CU05")),
) -> ImagenOut:
    producto = _get_producto_or_404(db, producto_id)
    content = await file.read()
    url = upload_producto_imagen(producto_id, content, file.content_type or "")

    siguiente_orden = len(producto.imagenes)
    result = db.execute(
        text("SELECT sp_agregar_imagen_producto(:producto_id, :url, :orden)"),
        {"producto_id": producto_id, "url": url, "orden": siguiente_orden},
    )
    imagen_id = result.scalar_one()
    db.commit()

    log_bitacora(db, admin, "ACTUALIZAR", "producto", producto_id, f"Se agrego una imagen a: {producto.nombre}", request)
    return ImagenOut(id=imagen_id, url=url, orden=siguiente_orden)


@router.delete("/{producto_id}/imagenes/{imagen_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_imagen(
    producto_id: int,
    imagen_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_permiso("CU05")),
) -> None:
    imagen = (
        db.query(ProductoImagen)
        .filter(ProductoImagen.id == imagen_id, ProductoImagen.producto_id == producto_id)
        .first()
    )
    if imagen is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Imagen no encontrada.")

    url = imagen.url
    db.execute(text("SELECT sp_eliminar_imagen_producto(:id)"), {"id": imagen_id})
    db.commit()
    delete_producto_imagen(url)

    log_bitacora(db, admin, "ACTUALIZAR", "producto", producto_id, "Se elimino una imagen del producto", request)
