from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_permiso
from app.db.session import get_db
from app.models import Bitacora, Usuario
from app.schemas.bitacora import BitacoraItem, BitacoraPage

router = APIRouter()


@router.get("", response_model=BitacoraPage)
def list_bitacora(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    buscar: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(require_permiso("CU19")),
) -> BitacoraPage:
    query = db.query(Bitacora).join(Usuario, Usuario.id == Bitacora.usuario_id)

    if buscar:
        like = f"%{buscar}%"
        query = query.filter(
            Usuario.email.ilike(like) | Usuario.nombre.ilike(like) | Bitacora.entidad_afectada.ilike(like)
        )

    total = query.count()
    rows = (
        query.order_by(Bitacora.fecha.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [
        BitacoraItem(
            id=b.id,
            usuario_id=b.usuario_id,
            usuario_nombre=b.usuario.nombre,
            usuario_email=b.usuario.email,
            accion=b.accion,
            entidad_afectada=b.entidad_afectada,
            entidad_id=b.entidad_id,
            fecha=b.fecha,
            detalle=b.detalle,
            ip_address=b.ip_address,
        )
        for b in rows
    ]
    return BitacoraPage(items=items, total=total, page=page, page_size=page_size)
