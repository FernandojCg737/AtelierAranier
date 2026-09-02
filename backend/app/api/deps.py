from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import Usuario

bearer_scheme = HTTPBearer(auto_error=False)

STAFF_TIPOS = {"administrador", "encargado_sucursal", "cajero"}


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No autenticado.")

    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token invalido o expirado.")

    if payload.get("scope") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token invalido.")

    usuario = db.query(Usuario).filter(Usuario.id == int(payload.get("sub", 0))).first()
    if usuario is None or usuario.estado != "activo":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Cuenta no disponible.")

    if not usuario.session_id or usuario.session_id != payload.get("sid"):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Tu sesion se cerro porque iniciaste sesion en otro dispositivo.",
        )

    return usuario


def require_staff(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    if usuario.tipo not in STAFF_TIPOS:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Acceso restringido al personal de la tienda.")
    return usuario


def require_permiso(*codigos: str) -> Callable[[Usuario], Usuario]:
    # Administrador es superusuario por diseno: no depende de la tabla
    # rol_permiso, para que nunca pueda quedar sin acceso al panel por un
    # cambio accidental en la matriz de permisos (CU02).
    # Acepta varios codigos (ej. CU05 o CU12) para endpoints compartidos por
    # mas de un caso de uso; basta con tener uno de ellos.
    def _dependency(usuario: Usuario = Depends(require_staff)) -> Usuario:
        if usuario.tipo == "administrador":
            return usuario

        codigos_usuario = {p.nombre for p in usuario.rol.permisos} if usuario.rol else set()
        if not codigos_usuario & set(codigos):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, f"Tu rol no tiene permiso para acceder a {' o '.join(codigos)}."
            )
        return usuario

    return _dependency
