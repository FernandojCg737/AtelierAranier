from fastapi import Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import Bitacora, Usuario


def client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def set_client_ip_for_trigger(db: Session, request: Request) -> None:
    # El trigger de alta de usuario (fn_bitacora_nuevo_usuario) corre dentro
    # de Postgres y no tiene acceso al request HTTP: le pasamos la IP via una
    # variable de sesion valida solo para esta transaccion (SET LOCAL).
    ip = client_ip(request)
    if ip:
        db.execute(text("SET LOCAL atelier.client_ip = :ip"), {"ip": ip})


def log_bitacora(
    db: Session,
    usuario: Usuario,
    accion: str,
    entidad_afectada: str,
    entidad_id: int | None,
    detalle: str | None,
    request: Request,
) -> None:
    db.add(
        Bitacora(
            usuario_id=usuario.id,
            accion=accion,
            entidad_afectada=entidad_afectada,
            entidad_id=entidad_id,
            detalle=detalle,
            ip_address=client_ip(request),
        )
    )
    db.commit()
