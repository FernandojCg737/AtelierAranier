from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permiso
from app.db.session import get_db
from app.models import Usuario
from app.schemas.auth import UsuarioOut
from app.services.usuarios import to_usuario_out

router = APIRouter()


@router.get("/activas", response_model=list[UsuarioOut])
def sesiones_activas(
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(require_permiso("CU01")),
) -> list[UsuarioOut]:
    usuarios = db.query(Usuario).filter(Usuario.session_id.isnot(None)).order_by(Usuario.nombre).all()
    return [to_usuario_out(u) for u in usuarios]
