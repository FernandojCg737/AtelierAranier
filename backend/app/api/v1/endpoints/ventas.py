import json
from decimal import Decimal

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, UploadFile, status
from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_permiso
from app.core.audit import log_bitacora
from app.core.paypal import capturar_orden, crear_orden
from app.core.storage import upload_comprobante_pago
from app.db.session import get_db
from app.models import (
    Carrito,
    Cliente,
    Color,
    DetalleCarrito,
    DetalleVentaDigital,
    DetalleVentaPresencial,
    Empleado,
    Inventario,
    Pago,
    Producto,
    Sucursal,
    Talla,
    Usuario,
    Venta,
    VentaDigital,
    VentaPresencial,
)
from app.schemas.ventas import (
    CapturarPaypalIn,
    ClienteBusquedaOut,
    DetalleVentaOut,
    OrdenPaypalOut,
    VentaAdminOut,
    VentaEditIn,
    VentaOut,
    VentaPage,
    VentaPresencialCreate,
)

router = APIRouter()


def _get_cliente_o_403(db: Session, usuario: Usuario) -> Cliente:
    cliente = db.query(Cliente).filter(Cliente.id == usuario.id).first()
    if cliente is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo los clientes pueden comprar.")
    return cliente


def _get_empleado_o_403(db: Session, usuario: Usuario) -> Empleado:
    empleado = db.query(Empleado).filter(Empleado.id == usuario.id).first()
    if empleado is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo el personal de sucursal puede hacer esto.")
    return empleado


def _get_carrito_activo_no_vacio(db: Session, cliente_id: int) -> Carrito:
    carrito = (
        db.query(Carrito)
        .options(
            joinedload(Carrito.detalles).joinedload(DetalleCarrito.producto),
            joinedload(Carrito.detalles).joinedload(DetalleCarrito.talla),
            joinedload(Carrito.detalles).joinedload(DetalleCarrito.color),
        )
        .filter(Carrito.cliente_id == cliente_id, Carrito.estado == "activo")
        .first()
    )
    if carrito is None or not carrito.detalles:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Tu carrito esta vacio.")
    return carrito


def _calcular_total(carrito: Carrito) -> Decimal:
    return sum((d.precio_unitario * d.cantidad for d in carrito.detalles), Decimal("0"))


def _items_json(items) -> str:
    """Arma el JSONB que reciben las funciones sp_crear_venta_*/sp_editar_venta:
    [{"producto_id":..,"talla_id":..,"color_id":..,"cantidad":..}, ...]."""
    return json.dumps(
        [
            {
                "producto_id": i.producto_id,
                "talla_id": i.talla_id,
                "color_id": i.color_id,
                "cantidad": i.cantidad,
            }
            for i in items
        ]
    )


def _verificar_stock_carrito(db: Session, carrito: Carrito, sucursal_id: int) -> None:
    """Chequeo 'amigable' en Python (con el nombre real del producto en el
    mensaje) antes de llamar a la funcion -- la funcion vuelve a validar con
    lock por su cuenta como resguardo de bajo nivel ante condiciones de
    carrera, igual que ya hace sp_actualizar_inventario_cantidad."""
    for d in carrito.detalles:
        inventario = (
            db.query(Inventario)
            .filter(
                Inventario.producto_id == d.producto_id,
                Inventario.talla_id == d.talla_id,
                Inventario.color_id == d.color_id,
                Inventario.sucursal_id == sucursal_id,
            )
            .first()
        )
        if inventario is None or inventario.cantidad < d.cantidad:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f'No hay suficiente stock de "{d.producto.nombre}" ({d.talla.codigo}, {d.color.nombre}) en esa sucursal.',
            )


def _query_venta_con_detalles(db: Session):
    return db.query(Venta).options(
        joinedload(Venta.sucursal),
        joinedload(Venta.cliente),
        joinedload(Venta.pago),
        joinedload(Venta.calificacion),
        joinedload(VentaDigital.detalles).joinedload(DetalleVentaDigital.producto),
        joinedload(VentaDigital.detalles).joinedload(DetalleVentaDigital.talla),
        joinedload(VentaDigital.detalles).joinedload(DetalleVentaDigital.color),
        joinedload(VentaPresencial.atendido_por),
        joinedload(VentaPresencial.detalles).joinedload(DetalleVentaPresencial.producto),
        joinedload(VentaPresencial.detalles).joinedload(DetalleVentaPresencial.talla),
        joinedload(VentaPresencial.detalles).joinedload(DetalleVentaPresencial.color),
    )


def _to_out(venta: Venta) -> VentaOut:
    detalles = getattr(venta, "detalles", [])
    atendido_por = getattr(venta, "atendido_por", None)
    calificacion = getattr(venta, "calificacion", None)
    return VentaOut(
        id=venta.id,
        tipo=venta.tipo,
        sucursal_id=venta.sucursal_id,
        sucursal_nombre=venta.sucursal.nombre,
        fecha=venta.fecha,
        total=venta.total,
        estado=venta.estado,
        metodo_pago=venta.pago.metodo if venta.pago else "",
        estado_pago=venta.pago.estado if venta.pago else "",
        atendido_por_nombre=atendido_por.nombre if atendido_por else None,
        calificacion_estrellas=calificacion.estrellas if calificacion else None,
        calificacion_comentario=calificacion.comentario if calificacion else None,
        detalles=[
            DetalleVentaOut(
                id=d.id,
                producto_id=d.producto_id,
                producto_nombre=d.producto.nombre,
                talla_id=d.talla_id,
                talla_codigo=d.talla.codigo,
                color_id=d.color_id,
                color_nombre=d.color.nombre,
                cantidad=d.cantidad,
                precio_unitario=d.precio_unitario,
            )
            for d in detalles
        ],
    )


def _to_admin_out(venta: Venta) -> VentaAdminOut:
    return VentaAdminOut(
        **_to_out(venta).model_dump(),
        cliente_nombre=venta.cliente.nombre,
        cliente_email=venta.cliente.email,
        comprobante_url=venta.pago.comprobante_url if venta.pago else None,
    )


@router.post("/checkout/paypal/crear-orden", response_model=OrdenPaypalOut)
def crear_orden_paypal(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> OrdenPaypalOut:
    """Solo crea la orden en PayPal para que el frontend abra el checkout --
    no cobra nada ni toca el carrito todavia (eso recien pasa al capturar la
    orden). Asi, si el cliente cierra el popup de PayPal sin pagar, su
    carrito sigue intacto."""
    cliente = _get_cliente_o_403(db, usuario)
    carrito = _get_carrito_activo_no_vacio(db, cliente.id)
    total = _calcular_total(carrito)

    orden = crear_orden(total, referencia=f"carrito-{carrito.id}")
    return OrdenPaypalOut(order_id=orden["id"], total=total)


@router.post("/checkout/paypal/capturar/{order_id}", response_model=VentaOut)
def capturar_orden_paypal(
    order_id: str,
    payload: CapturarPaypalIn,
    request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> VentaOut:
    cliente = _get_cliente_o_403(db, usuario)
    carrito = _get_carrito_activo_no_vacio(db, cliente.id)

    sucursal = db.query(Sucursal).filter(Sucursal.id == payload.sucursal_id).first()
    if sucursal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sucursal no encontrada.")

    _verificar_stock_carrito(db, carrito, payload.sucursal_id)

    resultado = capturar_orden(order_id)
    if resultado.get("status") != "COMPLETED":
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "PayPal no confirmo el pago.")

    result = db.execute(
        text(
            "SELECT sp_crear_venta_digital_paypal(:cliente_id, :sucursal_id, :carrito_id, CAST(:items AS JSONB), :referencia)"
        ),
        {
            "cliente_id": cliente.id,
            "sucursal_id": payload.sucursal_id,
            "carrito_id": carrito.id,
            "items": _items_json(carrito.detalles),
            "referencia": order_id,
        },
    )
    venta_id = result.scalar_one()
    db.commit()

    log_bitacora(db, usuario, "CREAR", "venta", venta_id, f"Venta digital pagada con PayPal (orden {order_id})", request)

    venta = _query_venta_con_detalles(db).filter(Venta.id == venta_id).first()
    return _to_out(venta)


@router.post("/checkout/qr", response_model=VentaOut, status_code=status.HTTP_201_CREATED)
async def checkout_qr(
    request: Request,
    sucursal_id: int = Form(...),
    file: UploadFile = None,  # type: ignore[assignment]
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> VentaOut:
    """Pago por QR: no hay pasarela que lo verifique solo, asi que el
    cliente sube la foto del comprobante y la venta queda pendiente de que
    un cajero/encargado la revise (el stock recien se descuenta cuando se
    aprueba, no aca)."""
    cliente = _get_cliente_o_403(db, usuario)
    carrito = _get_carrito_activo_no_vacio(db, cliente.id)

    sucursal = db.query(Sucursal).filter(Sucursal.id == sucursal_id).first()
    if sucursal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sucursal no encontrada.")
    if file is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Debes subir una foto del comprobante.")

    content = await file.read()
    comprobante_url = upload_comprobante_pago(cliente.id, content, file.content_type or "")

    result = db.execute(
        text("SELECT sp_crear_venta_digital_qr(:cliente_id, :sucursal_id, :carrito_id, CAST(:items AS JSONB), :comprobante)"),
        {
            "cliente_id": cliente.id,
            "sucursal_id": sucursal_id,
            "carrito_id": carrito.id,
            "items": _items_json(carrito.detalles),
            "comprobante": comprobante_url,
        },
    )
    venta_id = result.scalar_one()
    db.commit()

    log_bitacora(db, usuario, "CREAR", "venta", venta_id, "Venta digital con comprobante QR pendiente de verificacion", request)

    venta = _query_venta_con_detalles(db).filter(Venta.id == venta_id).first()
    return _to_out(venta)


@router.get("/mias", response_model=list[VentaOut])
def mis_ventas(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> list[VentaOut]:
    cliente = _get_cliente_o_403(db, usuario)
    ventas = (
        _query_venta_con_detalles(db)
        .filter(Venta.cliente_id == cliente.id)
        .order_by(Venta.fecha.desc())
        .all()
    )
    return [_to_out(v) for v in ventas]


@router.get("/mias/{venta_id}", response_model=VentaOut)
def mi_venta_detalle(
    venta_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> VentaOut:
    """Detalle de una compra propia -- usado por la pantalla de comprobante
    descargable/imprimible en 'Mis compras'."""
    cliente = _get_cliente_o_403(db, usuario)
    venta = (
        _query_venta_con_detalles(db)
        .filter(Venta.id == venta_id, Venta.cliente_id == cliente.id)
        .first()
    )
    if venta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Compra no encontrada.")
    return _to_out(venta)


# ---------- Staff: Administrador, Encargado de Sucursal, Cajero (CU11) ----------
# CU11 "Gestion de Ventas": panel financiero de staff -- reune las ventas
# digitales (PayPal y QR) y las de mostrador en un solo lugar, deja aprobar
# o rechazar los comprobantes QR pendientes, y permite registrar una venta
# presencial en efectivo. Se usa el permiso CU14 (Registrar Venta
# Presencial) porque ya lo tienen exactamente Administrador/Encargado/Cajero,
# y CU11 (Atender Reservas en Sucursal) porque asi esta etiquetado el item
# del menu -- ver la migracion que le otorga CU11 tambien al Cajero.


@router.get("", response_model=VentaPage)
def listar_ventas(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tipo: str | None = Query(default=None),
    metodo: str | None = Query(default=None),
    estado_pago: str | None = Query(default=None),
    sucursal_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _empleado: Usuario = Depends(require_permiso("CU11", "CU14")),
) -> VentaPage:
    query = _query_venta_con_detalles(db)
    if tipo:
        query = query.filter(Venta.tipo == tipo)
    if sucursal_id:
        query = query.filter(Venta.sucursal_id == sucursal_id)
    if metodo or estado_pago:
        query = query.join(Pago, Pago.venta_id == Venta.id)
        if metodo:
            query = query.filter(Pago.metodo == metodo)
        if estado_pago:
            query = query.filter(Pago.estado == estado_pago)

    total = query.count()
    rows = query.order_by(Venta.fecha.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return VentaPage(items=[_to_admin_out(v) for v in rows], total=total, page=page, page_size=page_size)


@router.get("/{venta_id}", response_model=VentaAdminOut)
def obtener_venta(
    venta_id: int,
    db: Session = Depends(get_db),
    _empleado: Usuario = Depends(require_permiso("CU11", "CU14")),
) -> VentaAdminOut:
    """Detalle de cualquier venta (no solo las propias) -- usado por la
    pantalla de factura/comprobante que ve el staff desde el panel de
    Gestion de Ventas."""
    venta = _query_venta_con_detalles(db).filter(Venta.id == venta_id).first()
    if venta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Venta no encontrada.")
    return _to_admin_out(venta)


@router.post("/{venta_id}/aprobar-qr", response_model=VentaAdminOut)
def aprobar_pago_qr(
    venta_id: int,
    request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> VentaAdminOut:
    empleado = _get_empleado_o_403(db, usuario)
    venta = _query_venta_con_detalles(db).filter(Venta.id == venta_id).first()
    if venta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Venta no encontrada.")
    if venta.pago is None or venta.pago.metodo != "qr" or venta.pago.estado != "verificando":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Esta venta no tiene un pago QR pendiente de verificacion.")

    for d in venta.detalles:
        inventario = (
            db.query(Inventario)
            .filter(
                Inventario.producto_id == d.producto_id,
                Inventario.talla_id == d.talla_id,
                Inventario.color_id == d.color_id,
                Inventario.sucursal_id == venta.sucursal_id,
            )
            .first()
        )
        if inventario is None or inventario.cantidad < d.cantidad:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f'No hay suficiente stock de "{d.producto.nombre}" ({d.talla.codigo}, {d.color.nombre}) para aprobar esta venta.',
            )

    db.execute(text("SELECT sp_aprobar_pago_qr(:venta_id, :empleado_id)"), {"venta_id": venta_id, "empleado_id": empleado.id})
    db.commit()

    log_bitacora(db, usuario, "ACTUALIZAR", "venta", venta.id, "Pago QR aprobado", request)

    venta = _query_venta_con_detalles(db).filter(Venta.id == venta.id).first()
    return _to_admin_out(venta)


@router.post("/{venta_id}/rechazar-qr", response_model=VentaAdminOut)
def rechazar_pago_qr(
    venta_id: int,
    request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> VentaAdminOut:
    empleado = _get_empleado_o_403(db, usuario)
    venta = _query_venta_con_detalles(db).filter(Venta.id == venta_id).first()
    if venta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Venta no encontrada.")
    if venta.pago is None or venta.pago.metodo != "qr" or venta.pago.estado != "verificando":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Esta venta no tiene un pago QR pendiente de verificacion.")

    db.execute(text("SELECT sp_rechazar_pago_qr(:venta_id, :empleado_id)"), {"venta_id": venta_id, "empleado_id": empleado.id})
    db.commit()

    log_bitacora(db, usuario, "ACTUALIZAR", "venta", venta.id, "Pago QR rechazado", request)

    venta = _query_venta_con_detalles(db).filter(Venta.id == venta.id).first()
    return _to_admin_out(venta)


@router.get("/clientes/buscar", response_model=list[ClienteBusquedaOut])
def buscar_clientes_para_venta(
    buscar: str = Query(min_length=1),
    db: Session = Depends(get_db),
    _empleado: Usuario = Depends(require_permiso("CU11", "CU14")),
) -> list[ClienteBusquedaOut]:
    like = f"%{buscar}%"
    clientes = (
        db.query(Cliente)
        .filter(Cliente.nombre.ilike(like) | Cliente.email.ilike(like))
        .order_by(Cliente.nombre)
        .limit(10)
        .all()
    )
    return [ClienteBusquedaOut(id=c.id, nombre=c.nombre, email=c.email) for c in clientes]


@router.post("/presencial", response_model=VentaAdminOut, status_code=status.HTTP_201_CREATED)
def registrar_venta_presencial(
    payload: VentaPresencialCreate,
    request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permiso("CU11", "CU14")),
) -> VentaAdminOut:
    """Venta de mostrador cobrada en efectivo -- el staff arma la venta ahi
    mismo (sin pasar por un carrito) y se cobra al instante."""
    empleado = _get_empleado_o_403(db, usuario)

    cliente = db.query(Cliente).filter(Cliente.id == payload.cliente_id).first()
    if cliente is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado.")
    sucursal = db.query(Sucursal).filter(Sucursal.id == payload.sucursal_id).first()
    if sucursal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sucursal no encontrada.")

    for item in payload.items:
        producto = db.query(Producto).filter(Producto.id == item.producto_id).first()
        talla = db.query(Talla).filter(Talla.id == item.talla_id).first()
        color = db.query(Color).filter(Color.id == item.color_id).first()
        if producto is None or talla is None or color is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto, talla o color no encontrado.")
        inventario = (
            db.query(Inventario)
            .filter(
                Inventario.producto_id == item.producto_id,
                Inventario.talla_id == item.talla_id,
                Inventario.color_id == item.color_id,
                Inventario.sucursal_id == payload.sucursal_id,
            )
            .first()
        )
        if inventario is None or inventario.cantidad < item.cantidad:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f'No hay suficiente stock de "{producto.nombre}" ({talla.codigo}, {color.nombre}) en esa sucursal.',
            )

    result = db.execute(
        text("SELECT sp_crear_venta_presencial(:cliente_id, :sucursal_id, :empleado_id, CAST(:items AS JSONB))"),
        {
            "cliente_id": cliente.id,
            "sucursal_id": payload.sucursal_id,
            "empleado_id": empleado.id,
            "items": _items_json(payload.items),
        },
    )
    venta_id = result.scalar_one()
    db.commit()

    log_bitacora(db, usuario, "CREAR", "venta", venta_id, f"Venta presencial en efectivo a {cliente.nombre}", request)

    venta = _query_venta_con_detalles(db).filter(Venta.id == venta_id).first()
    return _to_admin_out(venta)


@router.put("/{venta_id}", response_model=VentaAdminOut)
def editar_venta(
    venta_id: int,
    payload: VentaEditIn,
    request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permiso("CU11", "CU14")),
) -> VentaAdminOut:
    """Edicion completa (CU11): productos, cantidades, sucursal y estado del
    pago -- por esta misma via se puede "completar" un pago QR o en
    efectivo (poniendo estado_pago='completado'), igual que con los botones
    rapidos de aprobar/rechazar QR. sp_editar_venta libera el stock viejo (si
    la venta ya estaba pagada) y retiene el nuevo dentro de la misma
    transaccion -- si no alcanza, no se confirma nada."""
    empleado = _get_empleado_o_403(db, usuario)
    venta = _query_venta_con_detalles(db).filter(Venta.id == venta_id).first()
    if venta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Venta no encontrada.")

    sucursal = db.query(Sucursal).filter(Sucursal.id == payload.sucursal_id).first()
    if sucursal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sucursal no encontrada.")

    for item in payload.items:
        producto = db.query(Producto).filter(Producto.id == item.producto_id).first()
        talla = db.query(Talla).filter(Talla.id == item.talla_id).first()
        color = db.query(Color).filter(Color.id == item.color_id).first()
        if producto is None or talla is None or color is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto, talla o color no encontrado.")

    db.execute(
        text(
            "SELECT sp_editar_venta(:venta_id, :sucursal_id, CAST(:items AS JSONB), :metodo_pago, :estado_pago, :empleado_id)"
        ),
        {
            "venta_id": venta_id,
            "sucursal_id": payload.sucursal_id,
            "items": _items_json(payload.items),
            "metodo_pago": payload.metodo_pago,
            "estado_pago": payload.estado_pago,
            "empleado_id": empleado.id,
        },
    )
    db.commit()

    log_bitacora(db, usuario, "ACTUALIZAR", "venta", venta_id, "Venta editada", request)

    venta = _query_venta_con_detalles(db).filter(Venta.id == venta_id).first()
    return _to_admin_out(venta)


@router.delete("/{venta_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_venta(
    venta_id: int,
    request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permiso("CU11", "CU14")),
) -> None:
    """Borra la venta por completo. sp_eliminar_venta devuelve el stock al
    inventario si estaba retenido (estado 'pagada') antes de borrar."""
    empleado = _get_empleado_o_403(db, usuario)
    venta = _query_venta_con_detalles(db).filter(Venta.id == venta_id).first()
    if venta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Venta no encontrada.")

    cliente_nombre = venta.cliente.nombre
    db.execute(text("SELECT sp_eliminar_venta(:venta_id, :empleado_id)"), {"venta_id": venta_id, "empleado_id": empleado.id})
    db.commit()

    log_bitacora(db, usuario, "ELIMINAR", "venta", venta_id, f"Venta de {cliente_nombre} eliminada", request)
