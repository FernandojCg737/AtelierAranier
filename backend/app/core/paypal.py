from decimal import Decimal

import requests
from fastapi import HTTPException, status

from app.core.config import settings

PAYPAL_BASE_URLS = {
    "sandbox": "https://api-m.sandbox.paypal.com",
    "live": "https://api-m.paypal.com",
}

# PayPal no soporta Bolivianos (BOB) como moneda -- para no meter conversion
# de tipo de cambio real en un proyecto academico, se cobra el mismo monto
# numerico del carrito pero en USD. Es una simplificacion conocida, no una
# conversion de moneda real.
PAYPAL_CURRENCY = "USD"


def _paypal_base_url() -> str:
    return PAYPAL_BASE_URLS.get(settings.PAYPAL_MODE, PAYPAL_BASE_URLS["sandbox"])


def _obtener_token_acceso() -> str:
    """Token OAuth2 de PayPal (client_credentials). Se pide uno nuevo en cada
    llamada por simplicidad -- el volumen de este proyecto no justifica
    cachearlo hasta que expire (~9 horas)."""
    if not settings.PAYPAL_CLIENT_ID or not settings.PAYPAL_CLIENT_SECRET:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "El pago con PayPal no esta configurado.")

    resp = requests.post(
        f"{_paypal_base_url()}/v1/oauth2/token",
        auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
        data={"grant_type": "client_credentials"},
        timeout=15,
    )
    if not resp.ok:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "No se pudo conectar con PayPal.")
    return resp.json()["access_token"]


def crear_orden(total: Decimal, referencia: str) -> dict:
    """Crea una orden de pago en PayPal (intent=CAPTURE) por el total del
    carrito. Esto NO cobra nada todavia: el frontend (web o el WebView
    inline del movil, ver `paypal_embed.py`) usa el order_id devuelto para
    abrir el boton/checkout de PayPal, y el cargo real recien ocurre cuando
    el backend captura la orden (ver capturar_orden), despues de que el
    cliente la aprueba (con su cuenta PayPal o con tarjeta de credito via
    el checkout de invitado de PayPal)."""
    token = _obtener_token_acceso()
    resp = requests.post(
        f"{_paypal_base_url()}/v2/checkout/orders",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "reference_id": referencia,
                    "amount": {"currency_code": PAYPAL_CURRENCY, "value": f"{total:.2f}"},
                }
            ],
        },
        timeout=15,
    )
    if not resp.ok:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "No se pudo crear la orden de pago en PayPal.")
    return resp.json()


def capturar_orden(order_id: str) -> dict:
    """Confirma (cobra) una orden que el cliente ya aprobo en el checkout de
    PayPal. Si nunca la aprobo o la orden no existe, PayPal responde con
    error y no se cobra nada."""
    token = _obtener_token_acceso()
    resp = requests.post(
        f"{_paypal_base_url()}/v2/checkout/orders/{order_id}/capture",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=15,
    )
    if not resp.ok:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "No se pudo confirmar el pago con PayPal.")
    return resp.json()
