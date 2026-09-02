from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session, joinedload

from app.api.deps import require_permiso
from app.core.audit import log_bitacora
from app.db.session import get_db
from app.models import Coleccion, Usuario
from app.schemas.colecciones import ColeccionCreate, ColeccionOut, ColeccionUpdate

router = APIRouter()


def _to_out(coleccion: Coleccion) -> ColeccionOut:
    return ColeccionOut(
        id=coleccion.id,
        temporada_id=coleccion.temporada_id,
        temporada_nombre=coleccion.temporada.nombre,
        nombre=coleccion.nombre,
        descripcion=coleccion.descripcion,
    )


def _get_coleccion_or_404(db: Session, coleccion_id: int) -> Coleccion:
    coleccion = (
        db.query(Coleccion)
        .options(joinedload(Coleccion.temporada))
        .filter(Coleccion.id == coleccion_id)
        .first()
    )
    if coleccion is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Coleccion no encontrada.")
    return coleccion


@router.get("", response_model=list[ColeccionOut])
def list_colecciones(
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(require_permiso("CU07")),
) -> list[ColeccionOut]:
    colecciones = db.query(Coleccion).options(joinedload(Coleccion.temporada)).order_by(Coleccion.nombre).all()
    return [_to_out(c) for c in colecciones]


@router.post("", response_model=ColeccionOut, status_code=status.HTTP_201_CREATED)
def create_coleccion(
    payload: ColeccionCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_permiso("CU07")),
) -> ColeccionOut:
    result = db.execute(
        text("SELECT sp_crear_coleccion(:temporada_id, :nombre, :descripcion)"),
        {"temporada_id": payload.temporada_id, "nombre": payload.nombre, "descripcion": payload.descripcion},
    )
    coleccion_id = result.scalar_one()
    db.commit()

    coleccion = _get_coleccion_or_404(db, coleccion_id)
    log_bitacora(db, admin, "CREAR", "coleccion", coleccion.id, f"Alta de coleccion: {coleccion.nombre}", request)
    return _to_out(coleccion)


@router.put("/{coleccion_id}", response_model=ColeccionOut)
def update_coleccion(
    coleccion_id: int,
    payload: ColeccionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_permiso("CU07")),
) -> ColeccionOut:
    _get_coleccion_or_404(db, coleccion_id)

    db.execute(
        text("SELECT sp_actualizar_coleccion(:id, :temporada_id, :nombre, :descripcion)"),
        {
            "id": coleccion_id,
            "temporada_id": payload.temporada_id,
            "nombre": payload.nombre,
            "descripcion": payload.descripcion,
        },
    )
    db.commit()

    coleccion = _get_coleccion_or_404(db, coleccion_id)
    log_bitacora(db, admin, "ACTUALIZAR", "coleccion", coleccion.id, f"Edicion de coleccion: {coleccion.nombre}", request)
    return _to_out(coleccion)


@router.delete("/{coleccion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_coleccion(
    coleccion_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_permiso("CU07")),
) -> None:
    coleccion = _get_coleccion_or_404(db, coleccion_id)
    nombre = coleccion.nombre

    try:
        db.execute(text("SELECT sp_eliminar_coleccion(:id)"), {"id": coleccion_id})
        db.commit()
    except DBAPIError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "No se puede eliminar: la coleccion tiene productos asociados.",
        )

    log_bitacora(db, admin, "ELIMINAR", "coleccion", coleccion_id, f"Baja de coleccion: {nombre}", request)
