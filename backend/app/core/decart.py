import io
import os
import subprocess
import tempfile

import pillow_heif
import requests
from fastapi import HTTPException, status
from PIL import Image

from app.core.config import settings
from app.models import Producto

DECART_API_BASE = "https://api.decart.ai"

# Registra el "opener" de HEIC/HEIF en Pillow (formato por defecto de la
# camara del iPhone) -- sin esto Pillow no sabe leer esos archivos.
pillow_heif.register_heif_opener()


def normalizar_foto_a_jpeg(contenido: bytes) -> bytes:
    """El modo VIRTUAL fallaba para algunos usuarios porque confiabamos en
    el content-type que manda el navegador para decidir si la foto es
    valida -- pero ese valor no es confiable (varia entre dispositivos, y
    en muchos casos las fotos del iPhone son HEIC, un formato que ni el
    navegador reporta bien ni ffmpeg puede leer directo).

    En vez de aceptar/rechazar por content-type, se intenta abrir el
    archivo con Pillow (que detecta el formato real por el contenido, no
    por lo que diga el navegador) y se re-guarda siempre como JPEG. Esto
    acepta transparentemente cualquier formato que Pillow entienda (JPG,
    PNG, WEBP, HEIC/HEIF, BMP, etc.) y le entrega a ffmpeg algo que sabe
    leer con seguridad."""
    try:
        imagen = Image.open(io.BytesIO(contenido))
        imagen = imagen.convert("RGB")
    except Exception:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "No pudimos leer esa foto. Probá con otra (JPG, PNG, WEBP o HEIC de iPhone).",
        )

    salida = io.BytesIO()
    imagen.save(salida, format="JPEG", quality=92)
    return salida.getvalue()


def crear_token_cliente_decart() -> dict:
    """Crea un token de cliente a partir de la API key permanente del
    backend. Replica la llamada que hace el SDK oficial (@decartai/sdk) en
    tokens.create(): POST /v1/client/tokens con la key permanente en el
    header X-API-KEY. El token resultante (campo "apiKey", ya efimero) es
    el unico que llega al frontend.

    IMPORTANTE: sin "expiresIn" el default del SDK es 60 segundos (no 10
    minutos como dice la doc de ejemplos) -- entre el permiso de camara,
    esta misma llamada y la negociacion WebRTC del video se pasa facil de
    60s, y el token expira a mitad de la conexion (el sintoma era la sesion
    colgada en "connected" sin nunca llegar a "generating", y al final
    fallaba con "Invalid API key" al reintentar la conexion de video).
    "maxSessionDuration" es un limite duro que hace cumplir el propio
    servidor de Decart (a diferencia del cronometro en JS del frontend, que
    se evita con solo cerrar la consola/pestaña de forma rara)."""
    if not settings.DECART_API_KEY:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "El probador de realidad aumentada no esta configurado.",
        )

    resp = requests.post(
        f"{DECART_API_BASE}/v1/client/tokens",
        headers={
            "X-API-KEY": settings.DECART_API_KEY,
            "content-type": "application/json",
        },
        json={
            "expiresIn": 600,
            "constraints": {"realtime": {"maxSessionDuration": 200}},
        },
        timeout=15,
    )
    if not resp.ok:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "No se pudo iniciar la sesion del probador de realidad aumentada.",
        )
    return resp.json()


def _convertir_foto_a_video(foto_bytes: bytes) -> bytes:
    """El modo cola de lucy-vton (el mismo modelo especializado que da buen
    resultado en el probador en vivo) rechaza fotos fijas de plano
    ("Invalid video file provided") -- solo acepta video. Se arma un video
    minimo (1 segundo, el mismo frame repetido) a partir de la foto para
    poder usar ese modelo igual, en vez de lucy-image-2 (edicion de imagen
    generica, sin entrenamiento especifico de VTON, que daba resultados
    mucho peores en la prueba real)."""
    with tempfile.TemporaryDirectory() as tmp:
        entrada = os.path.join(tmp, "in.jpg")
        salida = os.path.join(tmp, "out.mp4")
        with open(entrada, "wb") as f:
            f.write(foto_bytes)
        resultado = subprocess.run(
            [
                "ffmpeg", "-y", "-loop", "1", "-i", entrada,
                "-c:v", "libx264", "-t", "1", "-r", "20",
                "-pix_fmt", "yuv420p",
                # Ancho/alto pares (requisito de yuv420p), sin forzar una
                # relacion de aspecto especifica -- la mayoria de fotos de
                # celular son verticales, no 16:9.
                "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                salida,
            ],
            capture_output=True,
            timeout=30,
        )
        if resultado.returncode != 0 or not os.path.exists(salida):
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, "No se pudo preparar la foto para el modelo.")
        with open(salida, "rb") as f:
            return f.read()


def enviar_trabajo_foto_ar(persona_bytes: bytes, referencia_url: str, prompt: str) -> str:
    """Modo VIRTUAL (CU09): a diferencia del probador en vivo (WebRTC en
    tiempo real), esto sube una foto de la persona (normalizada a JPEG y
    despues convertida a un video minimo, ver normalizar_foto_a_jpeg y
    _convertir_foto_a_video) + la imagen de referencia de la prenda al
    modo "cola" de lucy-vton-3.5 -- el mismo modelo especializado en VTON
    que usa el modo ONLINE. Devuelve el job_id para consultar despues."""
    if not settings.DECART_API_KEY:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "El probador de realidad aumentada no esta configurado.",
        )

    ref_resp = requests.get(referencia_url, timeout=15)
    if not ref_resp.ok:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "No se pudo obtener la imagen de referencia de la prenda.")

    persona_bytes = normalizar_foto_a_jpeg(persona_bytes)
    video_bytes = _convertir_foto_a_video(persona_bytes)

    resp = requests.post(
        f"{DECART_API_BASE}/v1/jobs/lucy-vton-3.5",
        headers={"X-API-KEY": settings.DECART_API_KEY},
        files={
            "data": ("foto.mp4", video_bytes, "video/mp4"),
            "reference_image": (
                "referencia.png",
                ref_resp.content,
                ref_resp.headers.get("content-type", "image/png"),
            ),
        },
        data={"prompt": prompt, "enhance_prompt": "false"},
        timeout=30,
    )
    if not resp.ok:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "No se pudo iniciar la generacion de la foto.")

    job_id = resp.json().get("job_id")
    if not job_id:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Respuesta invalida del servicio de IA.")
    return job_id


def consultar_estado_trabajo_foto(job_id: str) -> dict:
    resp = requests.get(
        f"{DECART_API_BASE}/v1/jobs/{job_id}",
        headers={"X-API-KEY": settings.DECART_API_KEY},
        timeout=15,
    )
    if not resp.ok:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "No se pudo consultar el estado de la generacion.")
    return resp.json()


def _extraer_frame_de_video(video_bytes: bytes) -> bytes:
    """El resultado de lucy-vton-3.5 en modo cola es un video (porque la
    entrada tambien lo es, ver _convertir_foto_a_video) -- se saca un frame
    de la mitad del clip (no el primero, que a veces sale con artefactos de
    arranque) para devolver una FOTO como pidio el cliente, no un video."""
    with tempfile.TemporaryDirectory() as tmp:
        entrada = os.path.join(tmp, "in.mp4")
        salida = os.path.join(tmp, "out.jpg")
        with open(entrada, "wb") as f:
            f.write(video_bytes)
        resultado = subprocess.run(
            ["ffmpeg", "-y", "-ss", "0.5", "-i", entrada, "-frames:v", "1", "-q:v", "2", salida],
            capture_output=True,
            timeout=30,
        )
        if resultado.returncode != 0 or not os.path.exists(salida):
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, "No se pudo extraer la foto del resultado.")
        with open(salida, "rb") as f:
            return f.read()


def obtener_resultado_trabajo_foto(job_id: str) -> tuple[bytes, str]:
    resp = requests.get(
        f"{DECART_API_BASE}/v1/jobs/{job_id}/content",
        headers={"X-API-KEY": settings.DECART_API_KEY},
        timeout=30,
    )
    if not resp.ok:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "No se pudo obtener el resultado de la generacion.")
    content_type = resp.headers.get("content-type", "")
    if content_type.startswith("video/"):
        return _extraer_frame_de_video(resp.content), "image/jpeg"
    return resp.content, content_type or "image/png"


# Que region del cuerpo sustituir, segun la categoria real del catalogo
# (nombres tal cual en la BD, en minuscula). El prompt necesita saber si es
# "top" o "pants" -- decirle "top" para un pantalon confunde al modelo (le
# pide cambiar la parte de arriba mientras la imagen de referencia muestra
# un pantalon) y no sustituye nada. Categorias sin mapear (ej. accesorios)
# caen al generico "outfit".
_CATEGORIA_A_REGION = {
    "poleras": "top",
    "chaquetas": "top",
    "chompa": "top",
    "hoodie": "top",
    "pantalones": "pants",
}


def construir_prompt_ar(producto: Producto) -> str:
    """Arma el prompt descriptivo que Decart usa para saber que prenda
    sustituir. El modelo espera ingles: meter ahi la categoria/descripcion
    de la BD tal cual (en espanol, ej. "poleras", "Polera oversize de
    algodon") no dice nada al modelo y en la practica hace que ignore esa
    parte del prompt y alucine detalles como el largo de manga en vez de
    confiar en la imagen de referencia.

    OJO con la redaccion: una version anterior decia "Do not invent or
    change any detail of the garment" pensando en "no le inventes detalles
    a LA PRENDA DE REFERENCIA", pero es ambiguo -- el modelo lo puede leer
    como "no cambies la prenda que la persona ya tiene puesta" (osea, lo
    contrario de lo que queremos) y por eso no sustituia nada, solo pasaba
    la camara sin tocar. Redactado para que "reemplazar por completo" sea
    imposible de malinterpretar.

    Segunda vuelta: se probo agregar una instruccion extra pidiendo usar
    SOLO la textura/color de la referencia (para que no arrastre arrugas o
    estampado de la ropa original de la persona) -- pero esa version mas
    larga hizo que el modelo dejara de sustituir la prenda por completo
    (volvio al bug anterior).

    Tercera vuelta: el nombre del producto iba entre comillas en el prompt
    ("Polera Blanca Oversize") -- el modelo lo tomaba como texto literal
    para "escribir" sobre la prenda (se veia un logo/texto deformado tipo
    "POLERC" en la remera generada). Se saca el nombre del prompt por
    completo: la imagen de referencia ya dice todo lo que hace falta, y asi
    no hay ningun texto entre comillas que el modelo intente dibujar.

    Cuarta vuelta: el prompt decia siempre "top" (parte de arriba) sin
    importar la categoria real -- para un pantalon eso le pedia al modelo
    cambiar la remera mientras la referencia mostraba un pantalon, y no
    sustituia nada. Ahora se elige "top" o "pants" segun la categoria real
    del producto."""
    region = "outfit"
    if producto.categoria is not None:
        region = _CATEGORIA_A_REGION.get(producto.categoria.nombre.strip().lower(), "outfit")
    return (
        f"Replace the persons current {region} completely with the exact "
        f"garment shown in the reference image, using its exact design, "
        f"color and print. The new garment must fully cover and replace "
        f"what they are wearing now."
    )[:280]
