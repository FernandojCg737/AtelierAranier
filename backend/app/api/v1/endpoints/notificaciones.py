from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_permiso
from app.db.session import get_db
from app.models import Cliente, Notificacion, Usuario
from app.schemas.notificaciones import NotificacionAdminOut, NotificacionOut, NotificacionPage

router = APIRouter()


def _get_cliente_o_403(db: Session, usuario: Usuario) -> Cliente:
    cliente = db.query(Cliente).filter(Cliente.id == usuario.id).first()
    if cliente is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo los clientes tienen notificaciones.")
    return cliente


def _to_admin_out(n: Notificacion) -> NotificacionAdminOut:
    return NotificacionAdminOut(
        id=n.id,
        tipo_evento=n.tipo_evento,
        mensaje=n.mensaje,
        fecha_envio=n.fecha_envio,
        leida=n.leida,
        entidad_tipo=n.entidad_tipo,
        entidad_id=n.entidad_id,
        cliente_id=n.cliente_id,
        cliente_nombre=n.cliente.nombre,
        cliente_email=n.cliente.email,
        canal=n.canal,
        estado=n.estado,
    )


# ---------- Cliente ----------


@router.get("/mias", response_model=list[NotificacionOut])
def mis_notificaciones(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> list[NotificacionOut]:
    cliente = _get_cliente_o_403(db, usuario)

    # Barrido perezoso (mismo patron que _vencer_reservas_expiradas): antes
    # de listar, se generan las alertas de "reserva por vencer" que
    # correspondan -- no hace falta un scheduler aparte.
    db.execute(text("SELECT sp_generar_alertas_reservas_por_vencer()"))
    db.commit()

    notificaciones = (
        db.query(Notificacion)
        .filter(Notificacion.cliente_id == cliente.id)
        .order_by(Notificacion.fecha_envio.desc())
        .limit(50)
        .all()
    )
    return [NotificacionOut.model_validate(n) for n in notificaciones]


@router.put("/mias/{notificacion_id}/leida", response_model=NotificacionOut)
def marcar_leida(
    notificacion_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> NotificacionOut:
    cliente = _get_cliente_o_403(db, usuario)
    notificacion = (
        db.query(Notificacion)
        .filter(Notificacion.id == notificacion_id, Notificacion.cliente_id == cliente.id)
        .first()
    )
    if notificacion is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notificacion no encontrada.")

    notificacion.leida = True
    db.commit()
    db.refresh(notificacion)
    return NotificacionOut.model_validate(notificacion)


@router.post("/mias/marcar-todas-leidas", status_code=status.HTTP_204_NO_CONTENT)
def marcar_todas_leidas(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> None:
    cliente = _get_cliente_o_403(db, usuario)
    db.query(Notificacion).filter(Notificacion.cliente_id == cliente.id, Notificacion.leida.is_(False)).update(
        {"leida": True}
    )
    db.commit()


# ---------- Staff: Administrador (CU14) ----------
# CU14 "Enviar Notificaciones": panel informativo de solo lectura -- quien
# recibio cada notificacion (generada automaticamente por triggers al crear
# o cambiar el estado de una reserva/pago), su tipo, fecha y mensaje.


@router.get("", response_model=NotificacionPage)
def listar_notificaciones(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tipo_evento: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _empleado: Usuario = Depends(require_permiso("CU14")),
) -> NotificacionPage:
    query = db.query(Notificacion).options(joinedload(Notificacion.cliente))
    if tipo_evento:
        query = query.filter(Notificacion.tipo_evento == tipo_evento)

    total = query.count()
    rows = query.order_by(Notificacion.fecha_envio.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return NotificacionPage(items=[_to_admin_out(n) for n in rows], total=total, page=page, page_size=page_size)
