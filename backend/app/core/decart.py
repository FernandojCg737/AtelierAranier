import requests
from fastapi import HTTPException, status

from app.core.config import settings
from app.models import Producto

DECART_API_BASE = "https://api.decart.ai"


def crear_token_cliente_decart() -> dict:
    """Crea un token de cliente de corta duracion (10 min) a partir de la
    API key permanente del backend. Replica la llamada que hace el SDK
    oficial (@decartai/sdk) en tokens.create(): POST /v1/client/tokens con
    la key permanente en el header X-API-KEY. El token resultante (campo
    "apiKey", ya efimero) es el unico que llega al frontend."""
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
        json={},
        timeout=15,
    )
    if not resp.ok:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "No se pudo iniciar la sesion del probador de realidad aumentada.",
        )
    return resp.json()


def construir_prompt_ar(producto: Producto) -> str:
    """Arma el prompt descriptivo que Decart usa para saber que prenda
    sustituir. El modelo espera ingles: meter ahi la categoria/descripcion
    de la BD tal cual (en espanol, ej. "poleras", "Polera oversize de
    algodon") no dice nada al modelo y en la practica hace que ignore esa
    parte del prompt y alucine detalles como el largo de manga en vez de
    confiar en la imagen de referencia. En lugar de traducir (fragil e
    incompleto para cualquier categoria futura), la instruccion principal
    es que respete exactamente lo que se ve en la imagen: manga, cuello,
    calce y color tal cual la referencia."""
    return (
        f'Substitute the current garment with the exact garment shown in '
        f'the reference image, "{producto.nombre}". Match the reference '
        f"image precisely: same sleeve length, neckline, fit, silhouette "
        f"and color. Do not invent or change any detail of the garment."
    )[:300]
