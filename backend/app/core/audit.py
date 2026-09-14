from fastapi import Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import Bitacora, Usuario


def client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def client_platform(request: Request) -> str | None:
    # "web" (Angular) o "movil" (Flutter) -- cada app manda este header en
    # cada request (ver `auth-interceptor.ts` y `api_client.dart`). Si no
    # viene (ej. alguien pega la API a mano) queda sin dato, no se asume nada.
    plataforma = request.headers.get("x-client-platform")
    return plataforma if plataforma in ("web", "movil") else None


def set_client_ip_for_trigger(db: Session, request: Request) -> None:
    # El trigger de alta de usuario (fn_bitacora_nuevo_usuario) corre dentro
    # de Postgres y no tiene acceso al request HTTP: le pasamos la IP y la
    # plataforma via variables de sesion validas solo para esta transaccion
    # (SET LOCAL).
    ip = client_ip(request)
    if ip:
        db.execute(text("SET LOCAL atelier.client_ip = :ip"), {"ip": ip})
    plataforma = client_platform(request)
    if plataforma:
        db.execute(text("SET LOCAL atelier.client_platform = :plataforma"), {"plataforma": plataforma})


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
            plataforma=client_platform(request),
        )
    )
    db.commit()
