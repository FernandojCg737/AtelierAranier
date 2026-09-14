from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.api.v1.router import api_router
from app.core.ar_embed import render_ar_embed_html
from app.core.config import settings
from app.core.paypal_embed import render_paypal_embed_html

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.ENVIRONMENT}


@app.get("/ar-embed/{producto_id}", response_class=HTMLResponse, include_in_schema=False)
def ar_embed(producto_id: int) -> str:
    """Pagina standalone del probador CU09 (motor Decart), pensada para
    cargarse dentro de un WebView de la app movil Flutter: @decartai/sdk es
    un paquete JS sin equivalente Dart, asi que en vez de reimplementar el
    protocolo WebRTC de Decart a mano en Dart, la app movil reutiliza esta
    misma logica (identica a la del componente Angular ar-tryon) sirviendola
    desde el backend.

    Se sirve HTML (no JSON) porque getUserMedia solo esta disponible en un
    "contexto seguro": https, o el literal "localhost". Una pagina cargada
    como asset local (file://) en el WebView NO califica y el navegador ni
    siquiera expone la API — por eso esta pagina vive en el backend (que en
    produccion es https) en vez de empaquetarse dentro de la app."""
    return render_ar_embed_html(producto_id)


@app.get("/paypal-embed", response_class=HTMLResponse, include_in_schema=False)
def paypal_embed() -> str:
    """Pagina standalone que renderiza los botones reales del JS SDK de
    PayPal, pensada para cargarse INLINE (no a pantalla completa) dentro
    del checkout movil -- misma experiencia que la web en vez del flujo de
    redireccion con link "approve". Ver `paypal_embed.py`."""
    return render_paypal_embed_html()
