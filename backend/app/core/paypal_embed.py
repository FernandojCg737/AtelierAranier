from app.core.config import settings


def render_paypal_embed_html() -> str:
    """Pagina standalone que renderiza el boton "PayPal" para cargarse
    INLINE dentro de un WebView chico en el checkout movil.

    Solo movil: a pedido explicito del usuario, aca NO se ofrece pago con
    tarjeta de invitado (eso sigue existiendo en la web, ver `checkout.ts` +
    `paypal-sdk.ts`) -- en el checkout movil el unico metodo (aparte del QR
    por transferencia) es este boton, para no depender del JS SDK de PayPal
    en absoluto: ni su deteccion de funding sources, ni su render de
    botones, nada de eso corrio bien de forma confiable dentro de un
    WebView embebido (ver commits anteriores). Este boton es un <button>
    HTML comun: al tocarlo, crea la orden (fetch propio a este backend) y
    navega (location.href, un cambio de pagina normal, NO un popup) directo
    al link "approve" que devuelve PayPal -- el checkout real de PayPal
    (login + aprobar el pago) se abre dentro del mismo WebView, ocupando
    toda la pagina, y al terminar PayPal redirige de vuelta a
    /paypal-embed/retorno (o /cancelado), que le avisa a Flutter por el
    canal JS `PaypalResultChannel` -- ver `checkout_screen.dart`, que
    tambien agranda el WebView a pantalla completa en cuanto detecta que
    navego fuera de este dominio (esta pagina no tiene forma de reportar el
    alto real de una pagina de otro dominio).

    La app movil solo necesita mandarle el JWT del cliente (via query param
    `token`, igual que `ar-embed` -- no hay forma de poner un header
    Authorization en un `loadRequest` de WebView)."""
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>PayPal</title>
<style>
  html, body {{ margin: 0; padding: 0; background: transparent; font-family: system-ui, sans-serif; }}
  #boton-paypal-login {{
    display: block; width: 100%; margin: 4px 0; padding: 12px;
    background: #ffc439; color: #253b80; border: none; border-radius: 4px;
    font-size: 16px; font-weight: 700; font-family: inherit; cursor: pointer;
  }}
  #boton-paypal-login:active {{ background: #f2ba36; }}
  #msg-error {{
    padding: 16px; text-align: center; font-size: 13px; color: #b3261e;
  }}
  [hidden] {{ display: none !important; }}
</style>
</head>
<body>
<button type="button" id="boton-paypal-login">PayPal</button>
<div id="msg-error" hidden>No se pudo iniciar el pago con PayPal. Volve a intentar.</div>
<script>
const TOKEN = new URLSearchParams(location.search).get("token");
const botonPaypalLogin = document.getElementById("boton-paypal-login");
const msgError = document.getElementById("msg-error");

function reportarAltura() {{
  if (window.PaypalHeightChannel) {{
    window.PaypalHeightChannel.postMessage(String(document.body.scrollHeight));
  }}
}}
window.addEventListener("load", reportarAltura);

botonPaypalLogin.addEventListener("click", async () => {{
  botonPaypalLogin.disabled = true;
  botonPaypalLogin.textContent = "Cargando...";
  try {{
    const res = await fetch("/api/v1/ventas/checkout/paypal/crear-orden", {{
      method: "POST",
      headers: {{ Authorization: `Bearer ${{TOKEN}}`, "Content-Type": "application/json" }},
    }});
    if (!res.ok) throw new Error("crear-orden");
    const data = await res.json();
    if (!data.approve_url) throw new Error("sin approve_url");
    location.href = data.approve_url;
  }} catch (e) {{
    botonPaypalLogin.disabled = false;
    botonPaypalLogin.textContent = "PayPal";
    msgError.hidden = false;
    reportarAltura();
  }}
}});
</script>
</body>
</html>
"""


def render_paypal_retorno_html(aprobado: bool) -> str:
    """Pagina a la que PayPal redirige (return_url/cancel_url) despues del
    checkout real que abre el boton "PayPal" de `render_paypal_embed_html`
    -- ver el docstring de esa funcion. El order_id viene en el query param
    `token` (asi lo manda PayPal en ambos casos). Le avisa a Flutter por el
    mismo canal PaypalResultChannel que ya escucha, igual que si hubiera
    sido el boton del JS SDK."""
    estado = "approved" if aprobado else "cancelled"
    mensaje = "Pago aprobado. Podes volver a la app..." if aprobado else "Pago cancelado."
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>PayPal</title>
<style>
  html, body {{ margin: 0; padding: 0; background: transparent; font-family: system-ui, sans-serif; }}
  p {{ padding: 20px; text-align: center; font-size: 13px; color: #203c40; }}
</style>
</head>
<body>
<p>{mensaje}</p>
<script>
const TOKEN = new URLSearchParams(location.search).get("token");
if (window.PaypalResultChannel) {{
  window.PaypalResultChannel.postMessage(JSON.stringify({{ status: "{estado}", orderId: TOKEN }}));
}}
if (window.PaypalHeightChannel) {{
  window.PaypalHeightChannel.postMessage(String(document.body.scrollHeight));
}}
</script>
</body>
</html>
"""
