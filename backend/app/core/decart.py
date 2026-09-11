import requests
from fastapi import HTTPException, status

from app.core.config import settings
from app.models import Producto

DECART_API_BASE = "https://api.decart.ai"


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
    no hay ningun texto entre comillas que el modelo intente dibujar."""
    return (
        f'Replace the persons current top completely with the garment shown '
        f'in the reference image. The new garment must fully cover and '
        f"replace what they are wearing now -- none of their original "
        f"clothing should remain visible."
    )[:280]
