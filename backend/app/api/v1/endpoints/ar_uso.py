from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_permiso
from app.db.session import get_db
from app.models import Producto, Usuario, UsoArPrenda
from app.schemas.ar_uso import UsoArPrendaItem, UsoArPrendaPage

router = APIRouter()


@router.get("", response_model=UsoArPrendaPage)
def list_uso_ar_prenda(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    buscar: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(require_permiso("CU09")),
) -> UsoArPrendaPage:
    query = (
        db.query(UsoArPrenda)
        .join(Usuario, Usuario.id == UsoArPrenda.usuario_id)
        .join(Producto, Producto.id == UsoArPrenda.producto_id)
    )

    if buscar:
        like = f"%{buscar}%"
        query = query.filter(
            Usuario.email.ilike(like) | Usuario.nombre.ilike(like) | Producto.nombre.ilike(like)
        )

    total = query.count()
    rows = (
        query.order_by(UsoArPrenda.fecha.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [
        UsoArPrendaItem(
            id=u.id,
            usuario_id=u.usuario_id,
            usuario_nombre=u.usuario.nombre,
            usuario_email=u.usuario.email,
            producto_id=u.producto_id,
            producto_nombre=u.producto.nombre,
            modo=u.modo,
            fecha=u.fecha,
        )
        for u in rows
    ]
    return UsoArPrendaPage(items=items, total=total, page=page, page_size=page_size)
