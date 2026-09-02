import uuid

import requests
from fastapi import HTTPException, status

from app.core.config import settings

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}
MAX_IMAGE_BYTES = 5 * 1024 * 1024


def upload_producto_imagen(producto_id: int, content: bytes, content_type: str) -> str:
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Formato de imagen no soportado (usa JPG, PNG o WEBP).")
    if len(content) > MAX_IMAGE_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La imagen supera el tamano maximo de 5MB.")
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Almacenamiento de imagenes no configurado.")

    ext = ALLOWED_CONTENT_TYPES[content_type]
    path = f"{producto_id}/{uuid.uuid4().hex}.{ext}"

    resp = requests.post(
        f"{settings.SUPABASE_URL}/storage/v1/object/{settings.SUPABASE_STORAGE_BUCKET}/{path}",
        headers={
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
            "apikey": settings.SUPABASE_SERVICE_KEY,
            "Content-Type": content_type,
        },
        data=content,
        timeout=15,
    )
    if not resp.ok:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "No se pudo subir la imagen al almacenamiento.")

    return f"{settings.SUPABASE_URL}/storage/v1/object/public/{settings.SUPABASE_STORAGE_BUCKET}/{path}"


def delete_producto_imagen(url: str) -> None:
    marker = f"/object/public/{settings.SUPABASE_STORAGE_BUCKET}/"
    idx = url.find(marker)
    if idx == -1:
        return
    path = url[idx + len(marker) :]

    requests.delete(
        f"{settings.SUPABASE_URL}/storage/v1/object/{settings.SUPABASE_STORAGE_BUCKET}/{path}",
        headers={
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
            "apikey": settings.SUPABASE_SERVICE_KEY,
        },
        timeout=15,
    )
