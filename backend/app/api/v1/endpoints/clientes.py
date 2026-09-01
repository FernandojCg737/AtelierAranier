import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import require_permiso
from app.core.audit import log_bitacora, set_client_ip_for_trigger
from app.core.email import send_email
from app.core.security import generate_temp_password, hash_password
from app.db.session import get_db
from app.models import Cliente, Usuario
from app.schemas.clientes import ClienteAdminCreate, ClienteAdminOut, ClienteAdminUpdate

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_cliente_or_404(db: Session, cliente_id: int) -> Cliente:
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if cliente is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado.")
    return cliente


@router.get("", response_model=list[ClienteAdminOut])
def list_clientes(
    buscar: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(require_permiso("CU03")),
) -> list[ClienteAdminOut]:
    query = db.query(Cliente)
    if buscar:
        like = f"%{buscar}%"
        query = query.filter(Cliente.nombre.ilike(like) | Cliente.email.ilike(like))
    return query.order_by(Cliente.nombre).all()


@router.post("", response_model=ClienteAdminOut, status_code=status.HTTP_201_CREATED)
def create_cliente(
    payload: ClienteAdminCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_permiso("CU03")),
) -> ClienteAdminOut:
    existing = db.query(Usuario).filter(Usuario.email == payload.email).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una cuenta con ese correo.")

    password_temporal = generate_temp_password()

    set_client_ip_for_trigger(db, request)
    result = db.execute(
        text(
            "SELECT sp_crear_cliente(:nombre, :email, :password_hash, :telefono, :direccion, :metodo_registro)"
        ),
        {
            "nombre": payload.nombre,
            "email": payload.email,
            "password_hash": hash_password(password_temporal),
            "telefono": payload.telefono,
            "direccion": payload.direccion,
            "metodo_registro": "admin",
        },
    )
    cliente_id = result.scalar_one()
    db.commit()

    cliente = _get_cliente_or_404(db, cliente_id)

    try:
        send_email(
            to=cliente.email,
            subject="Bienvenido a Atelier Aranier",
            html_body=(
                f"<p>Hola {cliente.nombre},</p>"
                "<p>Un administrador creo una cuenta para vos en <strong>Atelier Aranier</strong>. "
                "Ya sos parte de nuestra tienda como cliente.</p>"
                "<p>Estos son tus datos de acceso:</p>"
                f"<p>Correo: {cliente.email}<br>Contrasena temporal: {password_temporal}</p>"
                "<p>Te recomendamos cambiar la contrasena desde tu perfil apenas inicies sesion.</p>"
            ),
        )
    except Exception:
        logger.exception("No se pudo enviar el correo de bienvenida a %s", cliente.email)

    log_bitacora(db, admin, "CREAR", "usuario", cliente.id, f"Alta de cliente (admin): {cliente.email}", request)
    return cliente


@router.put("/{cliente_id}", response_model=ClienteAdminOut)
def update_cliente(
    cliente_id: int,
    payload: ClienteAdminUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_permiso("CU03")),
) -> ClienteAdminOut:
    _get_cliente_or_404(db, cliente_id)

    db.execute(
        text("SELECT sp_actualizar_cliente_admin(:id, :nombre, :telefono, :direccion, :estado)"),
        {
            "id": cliente_id,
            "nombre": payload.nombre,
            "telefono": payload.telefono,
            "direccion": payload.direccion,
            "estado": payload.estado,
        },
    )
    db.commit()

    cliente = _get_cliente_or_404(db, cliente_id)
    log_bitacora(db, admin, "ACTUALIZAR", "usuario", cliente.id, f"Edicion de cliente (admin): {cliente.email}", request)
    return cliente
