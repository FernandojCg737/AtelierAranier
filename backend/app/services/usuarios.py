from app.models import Usuario
from app.schemas.auth import UsuarioOut


def to_usuario_out(usuario: Usuario) -> UsuarioOut:
    return UsuarioOut(
        id=usuario.id,
        nombre=usuario.nombre,
        email=usuario.email,
        telefono=getattr(usuario, "telefono", None),
        direccion=getattr(usuario, "direccion", None),
        tipo=usuario.tipo,
        rol=usuario.rol.nombre if usuario.rol else None,
        permisos=[p.nombre for p in usuario.rol.permisos] if usuario.rol else [],
    )
