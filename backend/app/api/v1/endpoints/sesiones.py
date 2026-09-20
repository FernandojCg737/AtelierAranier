from datetime import datetime

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
    # "Activa" = tiene session_id Y todavia no paso su expiracion (60 min
    # desde el login). Antes solo se filtraba por session_id no nulo, que
    # nunca se limpiaba si el usuario cerraba la pestana sin desloguearse.
    usuarios = (
        db.query(Usuario)
        .filter(
            Usuario.session_id.isnot(None),
            Usuario.sesion_expira_en.isnot(None),
            Usuario.sesion_expira_en > datetime.utcnow(),
        )
        .order_by(Usuario.nombre)
        .all()
    )
    return [to_usuario_out(u) for u in usuarios]
