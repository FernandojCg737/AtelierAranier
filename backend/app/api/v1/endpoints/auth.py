import logging
import secrets
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from jose import JWTError, jwt
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.audit import log_bitacora, set_client_ip_for_trigger
from app.core.config import settings
from app.core.email import send_email
from app.core.security import create_access_token, create_reset_token, hash_password, verify_password
from app.db.session import get_db
from app.models import Cliente, Usuario
from app.schemas.auth import (
    ClienteLogin,
    ClienteRegister,
    ForgotPasswordRequest,
    GoogleAuthPayload,
    LoginWithResetTokenRequest,
    MessageResponse,
    ResetPasswordRequest,
    ResetTokenResponse,
    TokenResponse,
    UsuarioOut,
    VerifyResetCodeRequest,
)
from app.services.usuarios import to_usuario_out

router = APIRouter()
logger = logging.getLogger(__name__)


def _log_sesion_bitacora(db: Session, usuario: Usuario, accion: str, request: Request) -> None:
    detalle_por_accion = {
        "LOGIN": f"Inicio de sesion ({usuario.tipo}): {usuario.email}",
        "LOGOUT": f"Cierre de sesion ({usuario.tipo}): {usuario.email}",
    }
    log_bitacora(db, usuario, accion, "usuario", usuario.id, detalle_por_accion.get(accion), request)


def _issue_token(usuario: Usuario, db: Session, request: Request) -> TokenResponse:
    # Cada login/registro reemplaza el session_id guardado en la BD: si el
    # usuario tenia una sesion abierta en otro dispositivo, su token anterior
    # deja de matchear "sid" y get_current_user lo rechaza en su proximo request.
    usuario.session_id = uuid.uuid4().hex
    db.commit()
    db.refresh(usuario)

    _log_sesion_bitacora(db, usuario, "LOGIN", request)

    token = create_access_token(subject=str(usuario.id), session_id=usuario.session_id)
    return TokenResponse(access_token=token, usuario=to_usuario_out(usuario))


def _usuario_from_reset_token(reset_token: str, db: Session) -> Usuario:
    try:
        payload = jwt.decode(reset_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Token de recuperacion invalido o expirado.")

    if payload.get("scope") != "password_reset":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Token de recuperacion invalido.")

    usuario = db.query(Usuario).filter(Usuario.id == int(payload.get("sub", 0))).first()
    if usuario is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Token de recuperacion invalido.")
    return usuario


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: ClienteRegister, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    existing = db.query(Usuario).filter(Usuario.email == payload.email).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una cuenta con ese correo.")

    set_client_ip_for_trigger(db, request)
    result = db.execute(
        text(
            "SELECT sp_crear_cliente(:nombre, :email, :password_hash, :telefono, :direccion, :metodo_registro)"
        ),
        {
            "nombre": payload.nombre,
            "email": payload.email,
            "password_hash": hash_password(payload.password),
            "telefono": payload.telefono,
            "direccion": None,
            "metodo_registro": "email",
        },
    )
    cliente_id = result.scalar_one()
    db.commit()

    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()

    try:
        send_email(
            to=cliente.email,
            subject="Bienvenido a Atelier Aranier",
            html_body=(
                f"<p>Hola {cliente.nombre},</p>"
                "<p>Gracias por registrarte en <strong>Atelier Aranier</strong>. "
                "Ya sos parte de nuestra tienda como cliente.</p>"
                "<p>Estos son tus datos de acceso:</p>"
                f"<p>Correo: {cliente.email}<br>Contrasena: {payload.password}</p>"
                "<p>Ya podes iniciar sesion cuando quieras en nuestra tienda.</p>"
            ),
        )
    except Exception:
        logger.exception("No se pudo enviar el correo de bienvenida a %s", cliente.email)

    return _issue_token(cliente, db, request)


@router.post("/google", response_model=TokenResponse)
def google_auth(payload: GoogleAuthPayload, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        idinfo = google_id_token.verify_oauth2_token(
            payload.credential, google_requests.Request(), settings.GOOGLE_CLIENT_ID
        )
    except ValueError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token de Google invalido.")

    email = idinfo.get("email")
    if not email or not idinfo.get("email_verified"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No se pudo verificar el correo de Google.")

    cliente = db.query(Cliente).filter(Cliente.email == email).first()
    if cliente is None:
        existing_usuario = db.query(Usuario).filter(Usuario.email == email).first()
        if existing_usuario is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una cuenta con ese correo.")

        set_client_ip_for_trigger(db, request)
        result = db.execute(
            text(
                "SELECT sp_crear_cliente(:nombre, :email, :password_hash, :telefono, :direccion, :metodo_registro)"
            ),
            {
                "nombre": idinfo.get("name") or email.split("@")[0],
                "email": email,
                "password_hash": hash_password(secrets.token_urlsafe(32)),
                "telefono": None,
                "direccion": None,
                "metodo_registro": "google",
            },
        )
        cliente_id = result.scalar_one()
        db.commit()

        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()

        try:
            send_email(
                to=cliente.email,
                subject="Bienvenido a Atelier Aranier",
                html_body=(
                    f"<p>Hola {cliente.nombre},</p>"
                    "<p>Gracias por registrarte en <strong>Atelier Aranier</strong> con tu cuenta de Google. "
                    "Ya sos parte de nuestra tienda como cliente.</p>"
                    f"<p>Iniciaste sesion con tu cuenta de Google ({cliente.email}), "
                    "asi que podes volver a entrar en cualquier momento con el boton "
                    "\"Continuar con Google\".</p>"
                ),
            )
        except Exception:
            logger.exception("No se pudo enviar el correo de bienvenida a %s", cliente.email)

    if cliente.estado != "activo":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Esta cuenta esta desactivada.")

    return _issue_token(cliente, db, request)


@router.post("/login", response_model=TokenResponse)
def login(payload: ClienteLogin, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    usuario = db.query(Usuario).filter(Usuario.email == payload.email).first()
    if not usuario or not verify_password(payload.password, usuario.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Correo o contrasena incorrectos.")

    if usuario.estado != "activo":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Esta cuenta esta desactivada.")

    return _issue_token(usuario, db, request)


@router.get("/me", response_model=UsuarioOut)
def me(usuario: Usuario = Depends(get_current_user)) -> UsuarioOut:
    return to_usuario_out(usuario)


@router.post("/logout", response_model=MessageResponse)
def logout(
    request: Request,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    usuario.session_id = None
    db.commit()
    _log_sesion_bitacora(db, usuario, "LOGOUT", request)
    return MessageResponse(message="Sesion cerrada.")


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> MessageResponse:
    usuario = db.query(Usuario).filter(Usuario.email == payload.email).first()
    if usuario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No existe una cuenta con ese correo.")

    code = f"{secrets.randbelow(1_000_000):06d}"
    usuario.reset_code_hash = hash_password(code)
    usuario.reset_code_expires_at = datetime.utcnow() + timedelta(minutes=10)
    db.commit()

    send_email(
        to=usuario.email,
        subject="Codigo de verificacion - Atelier Aranier",
        html_body=(
            f"<p>Hola {usuario.nombre},</p>"
            "<p>Tu codigo de verificacion para recuperar tu contrasena es:</p>"
            f"<h2>{code}</h2>"
            "<p>Vence en 10 minutos. Si no fuiste vos, ignora este correo.</p>"
        ),
    )
    return MessageResponse(message="Codigo enviado a tu correo.")


@router.post("/verify-reset-code", response_model=ResetTokenResponse)
def verify_reset_code(payload: VerifyResetCodeRequest, db: Session = Depends(get_db)) -> ResetTokenResponse:
    usuario = db.query(Usuario).filter(Usuario.email == payload.email).first()
    if (
        usuario is None
        or usuario.reset_code_hash is None
        or usuario.reset_code_expires_at is None
        or usuario.reset_code_expires_at < datetime.utcnow()
        or not verify_password(payload.code, usuario.reset_code_hash)
    ):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Codigo invalido o expirado.")

    # codigo de un solo uso
    usuario.reset_code_hash = None
    usuario.reset_code_expires_at = None
    db.commit()

    return ResetTokenResponse(reset_token=create_reset_token(subject=str(usuario.id)))


@router.post("/reset-password", response_model=TokenResponse)
def reset_password(payload: ResetPasswordRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    usuario = _usuario_from_reset_token(payload.reset_token, db)
    usuario.password_hash = hash_password(payload.new_password)
    db.commit()
    return _issue_token(usuario, db, request)


@router.post("/login-with-reset-code", response_model=TokenResponse)
def login_with_reset_code(
    payload: LoginWithResetTokenRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    usuario = _usuario_from_reset_token(payload.reset_token, db)
    if usuario.estado != "activo":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Esta cuenta esta desactivada.")
    return _issue_token(usuario, db, request)
