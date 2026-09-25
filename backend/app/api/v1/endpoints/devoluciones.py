"""CU11: Devoluciones -- flujo de devolucion total o parcial de una venta
ya pagada. El empleado registra la devolucion, y al completarla se reingresa
el stock al inventario y se actualiza el estado de la venta."""

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_permiso, require_permiso_cliente
from app.core.audit import log_bitacora
from app.db.session import get_db
from app.models import (
    Cliente,
    DetalleVentaDigital,
    DetalleVentaPresencial,
    Empleado,
    Inventario,
    ItemLinea,
    Notificacion,
    Usuario,
    Venta,
    VentaDigital,
    VentaPresencial,
)
from app.models.p4_ventas import DetalleDevolucion, Devolucion
from app.schemas.devoluciones import DevolucionAdminOut, DevolucionCreate, DevolucionOut, DetalleDevolucionOut

router = APIRouter()


# ---------------------------------------------------------------- helpers --

def _get_empleado_o_403(db: Session, usuario: Usuario) -> Empleado:
    empleado = db.query(Empleado).filter(Empleado.id == usuario.id).first()
    if empleado is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo el personal de sucursal puede hacer esto.")
    return empleado


def _get_cliente_o_403(db: Session, usuario: Usuario) -> Cliente:
    cliente = db.query(Cliente).filter(Cliente.id == usuario.id).first()
    if cliente is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo los clientes pueden realizar esta accion.")
    return cliente


def _query_devolucion(db: Session):
    return db.query(Devolucion).options(
        joinedload(Devolucion.venta).joinedload(Venta.sucursal),
        joinedload(Devolucion.venta).joinedload(Venta.cliente),
        joinedload(Devolucion.venta).joinedload(Venta.pago),
        joinedload(Devolucion.empleado),
        joinedload(Devolucion.detalles).joinedload(DetalleDevolucion.item_linea).joinedload(ItemLinea.producto),
        joinedload(Devolucion.detalles).joinedload(DetalleDevolucion.item_linea).joinedload(ItemLinea.talla),
        joinedload(Devolucion.detalles).joinedload(DetalleDevolucion.item_linea).joinedload(ItemLinea.color),
    )


def _get_precio_unitario(item: ItemLinea) -> Decimal:
    """Obtiene el precio unitario del detalle de venta original."""
    if hasattr(item, "detalle_venta_presencial") and item.detalle_venta_presencial:
        return item.detalle_venta_presencial[0].precio_unitario
    if hasattr(item, "detalle_venta_digital") and item.detalle_venta_digital:
        return item.detalle_venta_digital[0].precio_unitario
    # Fallback: buscar en la subclase via query
    dvp = getattr(item, "precio_unitario", None)
    return dvp if dvp else Decimal("0")


def _precio_unitario_desde_item(db: Session, item_linea_id: int) -> Decimal:
    """Busca el precio unitario del item en detalle_venta_presencial o
    detalle_venta_digital."""
    row = db.execute(
        text(
            "SELECT COALESCE("
            "  (SELECT precio_unitario FROM detalle_venta_presencial WHERE id = :id),"
            "  (SELECT precio_unitario FROM detalle_venta_digital WHERE id = :id),"
            "  0"
            ")"
        ),
        {"id": item_linea_id},
    ).scalar()
    return Decimal(str(row))


def _to_detalle_out(d: DetalleDevolucion, db: Session) -> DetalleDevolucionOut:
    item = d.item_linea
    return DetalleDevolucionOut(
        id=d.id,
        item_linea_id=d.item_linea_id,
        producto_nombre=item.producto.nombre,
        talla_codigo=item.talla.codigo,
        color_nombre=item.color.nombre,
        cantidad_devuelta=d.cantidad_devuelta,
        precio_unitario=_precio_unitario_desde_item(db, d.item_linea_id),
    )


def _to_out(dev: Devolucion, db: Session) -> DevolucionOut:
    return DevolucionOut(
        id=dev.id,
        venta_id=dev.venta_id,
        empleado_nombre=dev.empleado.nombre if dev.empleado else None,
        motivo=dev.motivo,
        tipo=dev.tipo,
        monto_reembolso=dev.monto_reembolso,
        metodo_reembolso=dev.metodo_reembolso,
        estado=dev.estado,
        fecha_solicitud=dev.fecha_solicitud,
        fecha_resolucion=dev.fecha_resolucion,
        observaciones=dev.observaciones,
        detalles=[_to_detalle_out(d, db) for d in dev.detalles],
    )


def _to_admin_out(dev: Devolucion, db: Session) -> DevolucionAdminOut:
    return DevolucionAdminOut(
        **_to_out(dev, db).model_dump(),
        cliente_nombre=dev.venta.cliente.nombre,
        cliente_email=dev.venta.cliente.email,
        venta_total=dev.venta.total,
        venta_fecha=dev.venta.fecha,
        sucursal_nombre=dev.venta.sucursal.nombre,
    )


# --------------------------------------------------------------- endpoints --


@router.get("", response_model=list[DevolucionAdminOut])
def listar_devoluciones(
    estado: str | None = Query(default=None),
    venta_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _empleado: Usuario = Depends(require_permiso("CU11")),
) -> list[DevolucionAdminOut]:
    query = _query_devolucion(db)
    if estado:
        query = query.filter(Devolucion.estado == estado)
    if venta_id:
        query = query.filter(Devolucion.venta_id == venta_id)
    devoluciones = query.order_by(Devolucion.fecha_solicitud.desc()).all()
    return [_to_admin_out(d, db) for d in devoluciones]


@router.get("/{devolucion_id}", response_model=DevolucionAdminOut)
def obtener_devolucion(
    devolucion_id: int,
    db: Session = Depends(get_db),
    _empleado: Usuario = Depends(require_permiso("CU11")),
) -> DevolucionAdminOut:
    dev = _query_devolucion(db).filter(Devolucion.id == devolucion_id).first()
    if dev is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Devolucion no encontrada.")
    return _to_admin_out(dev, db)


@router.post("/solicitar/{venta_id}", response_model=DevolucionOut, status_code=status.HTTP_201_CREATED)
def solicitar_devolucion_cliente(
    venta_id: int,
    payload: DevolucionCreate,
    request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permiso_cliente("CU11")),
) -> DevolucionOut:
    """CU11: Un cliente solicita la devolucion de una compra suya pagada.
    Restriccion obligatoria: solo es valida dentro de las 24 horas a partir
    de realizada la compra."""
    cliente = _get_cliente_o_403(db, usuario)

    venta = (
        db.query(Venta)
        .options(
            joinedload(Venta.sucursal),
            joinedload(Venta.cliente),
            joinedload(Venta.pago),
            joinedload(Venta.devoluciones),
            joinedload(VentaDigital.detalles).joinedload(DetalleVentaDigital.producto),
            joinedload(VentaDigital.detalles).joinedload(DetalleVentaDigital.talla),
            joinedload(VentaDigital.detalles).joinedload(DetalleVentaDigital.color),
            joinedload(VentaPresencial.detalles).joinedload(DetalleVentaPresencial.producto),
            joinedload(VentaPresencial.detalles).joinedload(DetalleVentaPresencial.talla),
            joinedload(VentaPresencial.detalles).joinedload(DetalleVentaPresencial.color),
        )
        .filter(Venta.id == venta_id, Venta.cliente_id == cliente.id)
        .first()
    )
    if venta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Compra no encontrada.")

    if venta.estado != "pagada":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Solo se pueden solicitar devoluciones de compras pagadas.")

    # Validar plazo maximo de 24 horas
    ahora = datetime.utcnow()
    horas_transcurridas = (ahora - venta.fecha).total_seconds() / 3600.0 if venta.fecha else 999.0
    if horas_transcurridas > 24.0:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "El plazo maximo de 24 horas para solicitar una devolucion ha vencido.",
        )

    # Validar que no tenga devolucion activa o completada
    devs_activas = [d for d in venta.devoluciones if d.estado in ("solicitada", "aprobada", "completada")]
    if devs_activas:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Esta compra ya cuenta con una devolucion en estado '{devs_activas[-1].estado}'.",
        )

    detalles_venta = getattr(venta, "detalles", [])
    ids_detalles = {d.id for d in detalles_venta}

    monto_total = Decimal("0")
    detalles_devolucion = []
    for item_in in payload.items:
        if item_in.item_linea_id not in ids_detalles:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"El item {item_in.item_linea_id} no pertenece a esta compra.",
            )
        detalle_original = next(d for d in detalles_venta if d.id == item_in.item_linea_id)
        if item_in.cantidad_devuelta > detalle_original.cantidad:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f'No puedes devolver {item_in.cantidad_devuelta} unidades de "{detalle_original.producto.nombre}" '
                f"({detalle_original.talla.codigo}, {detalle_original.color.nombre}) — "
                f"solo compraste {detalle_original.cantidad}.",
            )
        precio = _precio_unitario_desde_item(db, item_in.item_linea_id)
        monto_total += precio * item_in.cantidad_devuelta
        detalles_devolucion.append(
            DetalleDevolucion(
                item_linea_id=item_in.item_linea_id,
                cantidad_devuelta=item_in.cantidad_devuelta,
            )
        )

    if payload.tipo == "total":
        for det in detalles_venta:
            match = next((d for d in payload.items if d.item_linea_id == det.id), None)
            if match is None or match.cantidad_devuelta != det.cantidad:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    "Una devolucion total debe incluir todos los items con sus cantidades completas.",
                )

    devolucion = Devolucion(
        venta_id=venta_id,
        empleado_id=None,
        motivo=payload.motivo,
        tipo=payload.tipo,
        monto_reembolso=monto_total,
        metodo_reembolso=payload.metodo_reembolso,
        estado="solicitada",
        observaciones=payload.observaciones,
        detalles=detalles_devolucion,
    )
    db.add(devolucion)
    db.commit()
    db.refresh(devolucion)

    log_bitacora(
        db, usuario, "CREAR", "devolucion", devolucion.id,
        f"Cliente #{cliente.id} solicito devolucion {payload.tipo} para compra #{venta_id} por {monto_total} Bs (plazo 24h)",
        request,
    )

    db.add(Notificacion(
        cliente_id=cliente.id,
        canal="sistema",
        tipo_evento="devolucion_solicitada",
        mensaje=f"Has solicitado una devolucion {payload.tipo} para tu compra #{venta_id} "
                f"por {monto_total} Bs. Nuestro personal la revisara a la brevedad.",
        estado="enviada",
        leida=False,
        entidad_tipo="devolucion",
        entidad_id=devolucion.id,
    ))
    db.commit()

    dev = _query_devolucion(db).filter(Devolucion.id == devolucion.id).first()
    return _to_out(dev, db)


@router.post("/{venta_id}", response_model=DevolucionAdminOut, status_code=status.HTTP_201_CREATED)
def registrar_devolucion(
    venta_id: int,
    payload: DevolucionCreate,
    request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permiso("CU11")),
) -> DevolucionAdminOut:
    """Registra una devolucion para una venta pagada. El empleado selecciona
    los items y cantidades a devolver. La devolucion queda en estado
    'solicitada' hasta que se complete (se aprueba y reingresa el stock en
    un solo paso, ver completar_devolucion)."""
    empleado = _get_empleado_o_403(db, usuario)

    venta = (
        db.query(Venta)
        .options(
            joinedload(Venta.sucursal),
            joinedload(Venta.cliente),
            joinedload(VentaDigital.detalles).joinedload(DetalleVentaDigital.producto),
            joinedload(VentaDigital.detalles).joinedload(DetalleVentaDigital.talla),
            joinedload(VentaDigital.detalles).joinedload(DetalleVentaDigital.color),
            joinedload(VentaPresencial.detalles).joinedload(DetalleVentaPresencial.producto),
            joinedload(VentaPresencial.detalles).joinedload(DetalleVentaPresencial.talla),
            joinedload(VentaPresencial.detalles).joinedload(DetalleVentaPresencial.color),
        )
        .filter(Venta.id == venta_id)
        .first()
    )
    if venta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Venta no encontrada.")
    if venta.estado not in ("pagada",):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Solo se pueden devolver ventas pagadas.")

    # Validar que todos los items existen y pertenecen a esta venta
    detalles_venta = getattr(venta, "detalles", [])
    ids_detalles = {d.id for d in detalles_venta}

    monto_total = Decimal("0")
    detalles_devolucion = []
    for item_in in payload.items:
        if item_in.item_linea_id not in ids_detalles:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"El item {item_in.item_linea_id} no pertenece a esta venta.",
            )
        # Verificar que no se devuelva mas de lo comprado
        detalle_original = next(d for d in detalles_venta if d.id == item_in.item_linea_id)
        if item_in.cantidad_devuelta > detalle_original.cantidad:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f'No puedes devolver {item_in.cantidad_devuelta} unidades de "{detalle_original.producto.nombre}" '
                f"({detalle_original.talla.codigo}, {detalle_original.color.nombre}) — "
                f"solo se compraron {detalle_original.cantidad}.",
            )
        precio = _precio_unitario_desde_item(db, item_in.item_linea_id)
        monto_total += precio * item_in.cantidad_devuelta
        detalles_devolucion.append(
            DetalleDevolucion(
                item_linea_id=item_in.item_linea_id,
                cantidad_devuelta=item_in.cantidad_devuelta,
            )
        )

    # Si es devolucion total, verificar que se devuelven TODOS los items completos
    if payload.tipo == "total":
        for det in detalles_venta:
            match = next((d for d in payload.items if d.item_linea_id == det.id), None)
            if match is None or match.cantidad_devuelta != det.cantidad:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    "Una devolucion total debe incluir todos los items con sus cantidades completas.",
                )

    devolucion = Devolucion(
        venta_id=venta_id,
        empleado_id=empleado.id,
        motivo=payload.motivo,
        tipo=payload.tipo,
        monto_reembolso=monto_total,
        metodo_reembolso=payload.metodo_reembolso,
        estado="solicitada",
        observaciones=payload.observaciones,
        detalles=detalles_devolucion,
    )
    db.add(devolucion)
    db.commit()
    db.refresh(devolucion)

    log_bitacora(
        db, usuario, "CREAR", "devolucion", devolucion.id,
        f"Devolucion {payload.tipo} registrada para venta #{venta_id} por {monto_total} Bs",
        request,
    )

    # Notificar al cliente
    db.add(Notificacion(
        cliente_id=venta.cliente_id,
        canal="sistema",
        tipo_evento="devolucion_registrada",
        mensaje=f"Se ha registrado una devolucion {payload.tipo} para tu compra #{venta_id} "
                f"por {monto_total} Bs. Te avisaremos cuando se procese.",
        estado="enviada",
        leida=False,
        entidad_tipo="devolucion",
        entidad_id=devolucion.id,
    ))
    db.commit()

    dev = _query_devolucion(db).filter(Devolucion.id == devolucion.id).first()
    return _to_admin_out(dev, db)


@router.post("/{devolucion_id}/completar", response_model=DevolucionAdminOut)
def completar_devolucion(
    devolucion_id: int,
    request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permiso("CU11")),
) -> DevolucionAdminOut:
    """Completa la devolucion: reingresa el stock al inventario y actualiza
    el estado de la venta. Si la venta estaba pagada y se devuelve todo,
    queda como 'devuelto'; si se devuelve parcialmente, 'devuelto_parcial'."""
    empleado = _get_empleado_o_403(db, usuario)

    dev = _query_devolucion(db).filter(Devolucion.id == devolucion_id).first()
    if dev is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Devolucion no encontrada.")
    if dev.estado != "solicitada":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Esta devolucion ya fue procesada.")

    venta = dev.venta
    sucursal_id = venta.sucursal_id

    # Reingresar stock al inventario
    for detalle in dev.detalles:
        item = detalle.item_linea
        inventario = (
            db.query(Inventario)
            .filter(
                Inventario.producto_id == item.producto_id,
                Inventario.talla_id == item.talla_id,
                Inventario.color_id == item.color_id,
                Inventario.sucursal_id == sucursal_id,
            )
            .first()
        )
        if inventario is not None:
            inventario.cantidad += detalle.cantidad_devuelta
            db.flush()
            db.execute(
                text(
                    "INSERT INTO movimiento_inventario "
                    "(inventario_id, empleado_id, tipo, cantidad, fecha, documento_referencia) "
                    "VALUES (:inv_id, :emp_id, 'entrada', :cant, now(), :doc)"
                ),
                {
                    "inv_id": inventario.id,
                    "emp_id": empleado.id,
                    "cant": detalle.cantidad_devuelta,
                    "doc": f"Devolucion #{dev.id} de venta #{venta.id}",
                },
            )

    # Actualizar estado de la devolucion
    dev.empleado_id = empleado.id
    dev.estado = "completada"
    dev.fecha_resolucion = datetime.utcnow()

    # Actualizar estado de la venta
    nuevo_estado = "devuelto" if dev.tipo == "total" else "devuelto_parcial"
    venta.estado = nuevo_estado

    db.commit()

    log_bitacora(
        db, usuario, "ACTUALIZAR", "devolucion", dev.id,
        f"Devolucion #{dev.id} completada — stock reingresado, venta #{venta.id} marcada como {nuevo_estado}",
        request,
    )

    # Notificar al cliente
    db.add(Notificacion(
        cliente_id=venta.cliente_id,
        canal="sistema",
        tipo_evento="devolucion_completada",
        mensaje=f"Tu devolucion para la compra #{venta.id} fue aprobada. "
                f"Se te reembolsaran {dev.monto_reembolso} Bs via {dev.metodo_reembolso.replace('_', ' ')}.",
        estado="enviada",
        leida=False,
        entidad_tipo="devolucion",
        entidad_id=dev.id,
    ))
    db.commit()

    dev = _query_devolucion(db).filter(Devolucion.id == dev.id).first()
    return _to_admin_out(dev, db)


@router.post("/{devolucion_id}/rechazar", response_model=DevolucionAdminOut)
def rechazar_devolucion(
    devolucion_id: int,
    request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permiso("CU11")),
) -> DevolucionAdminOut:
    """Rechaza la devolucion. No se reingresa stock ni se cambia el estado
    de la venta."""
    empleado = _get_empleado_o_403(db, usuario)

    dev = _query_devolucion(db).filter(Devolucion.id == devolucion_id).first()
    if dev is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Devolucion no encontrada.")
    if dev.estado != "solicitada":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Esta devolucion ya fue procesada.")

    dev.empleado_id = empleado.id
    dev.estado = "rechazada"
    dev.fecha_resolucion = datetime.utcnow()
    db.commit()

    log_bitacora(
        db, usuario, "ACTUALIZAR", "devolucion", dev.id,
        f"Devolucion #{dev.id} rechazada para venta #{dev.venta_id}",
        request,
    )

    # Notificar al cliente
    db.add(Notificacion(
        cliente_id=dev.venta.cliente_id,
        canal="sistema",
        tipo_evento="devolucion_rechazada",
        mensaje=f"Tu solicitud de devolucion para la compra #{dev.venta_id} fue rechazada.",
        estado="enviada",
        leida=False,
        entidad_tipo="devolucion",
        entidad_id=dev.id,
    ))
    db.commit()

    dev = _query_devolucion(db).filter(Devolucion.id == dev.id).first()
    return _to_admin_out(dev, db)


@router.delete("/{devolucion_id}")
def eliminar_devolucion(
    devolucion_id: int,
    request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permiso("CU11")),
):
    """Elimina una devolucion. Si la devolucion estaba completada, se revierte
    el reingreso de stock en el inventario y se restaura el estado de la venta
    a 'pagada'. Registra la accion en la bitacora."""
    empleado = _get_empleado_o_403(db, usuario)

    dev = _query_devolucion(db).filter(Devolucion.id == devolucion_id).first()
    if dev is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Devolucion no encontrada.")

    venta = dev.venta
    estado_previo = dev.estado

    # Si estaba completada, revertir el reingreso de stock en la sucursal de la venta
    if estado_previo == "completada":
        sucursal_id = venta.sucursal_id
        for detalle in dev.detalles:
            item = detalle.item_linea
            inventario = (
                db.query(Inventario)
                .filter(
                    Inventario.producto_id == item.producto_id,
                    Inventario.talla_id == item.talla_id,
                    Inventario.color_id == item.color_id,
                    Inventario.sucursal_id == sucursal_id,
                )
                .first()
            )
            if inventario is not None:
                inventario.cantidad = max(0, inventario.cantidad - detalle.cantidad_devuelta)
                db.flush()
                db.execute(
                    text(
                        "INSERT INTO movimiento_inventario "
                        "(inventario_id, empleado_id, tipo, cantidad, fecha, documento_referencia) "
                        "VALUES (:inv_id, :emp_id, 'salida', :cant, now(), :doc)"
                    ),
                    {
                        "inv_id": inventario.id,
                        "emp_id": empleado.id,
                        "cant": detalle.cantidad_devuelta,
                        "doc": f"Reversion Devolucion #{dev.id} de venta #{venta.id}",
                    },
                )

        # Restaurar venta a 'pagada' si no existen otras devoluciones completadas
        otras_completadas = (
            db.query(Devolucion)
            .filter(
                Devolucion.venta_id == venta.id,
                Devolucion.id != dev.id,
                Devolucion.estado == "completada",
            )
            .first()
        )
        if not otras_completadas:
            venta.estado = "pagada"

    db.delete(dev)
    db.commit()

    log_bitacora(
        db,
        usuario,
        "ELIMINAR",
        "devolucion",
        devolucion_id,
        f"Devolucion #{devolucion_id} (estado previo: {estado_previo}) eliminada para venta #{venta.id}",
        request,
    )

    return {"message": f"Devolucion #{devolucion_id} eliminada exitosamente."}

