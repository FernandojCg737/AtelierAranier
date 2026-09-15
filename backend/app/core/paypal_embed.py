from app.core.config import settings


def render_paypal_embed_html() -> str:
    """Pagina standalone que renderiza el pago con PayPal para cargarse
    INLINE dentro de un WebView chico en el checkout movil -- a diferencia
    de un WebView de pantalla completa con un link "approve", esto reproduce
    la misma experiencia que la web: los botones aparecen ahi mismo, sin un
    paso extra.

    Tiene DOS botones con implementaciones distintas a proposito:

    - "Tarjeta de debito o credito": el boton real del JS SDK de PayPal
      (fundingSource card), igual que en la web. Es un boton de checkout de
      invitado -- el formulario de la tarjeta se expande inline en esta
      misma pagina, sin ventanas ni redirecciones, asi que funciona sin
      problemas dentro del WebView (ya confirmado con toque real).

    - "PayPal" (iniciar sesion con la cuenta): NO usa el boton del JS SDK.
      El boton del SDK para este funding source abre un popup via
      window.open() para el login -- y ese popup lo abre el propio iframe
      del boton (dominio paypal.com, con su window propio), no esta pagina,
      asi que no hay forma de interceptarlo desde aca, y el WebView de
      Flutter no soporta multiples ventanas (no hay onCreateWindow
      configurado). Quedaba una tarjeta sin nada interactivo (reportado por
      el usuario probando en su celular real). En vez de pelear con eso, se
      usa un boton propio: al tocarlo, se crea la orden (igual que el otro)
      pero pidiendole a PayPal un return_url/cancel_url de vuelta a este
      mismo backend, y se navega (location.href, NO un popup) directo al
      link "approve" que PayPal devuelve -- el checkout real de PayPal se
      abre dentro del mismo WebView, ocupando toda la pagina, y al terminar
      PayPal redirige de vuelta a /paypal-embed/retorno (o /cancelado),
      que le avisa a Flutter por el mismo canal de siempre.

    La app movil (Flutter) solo necesita mandarle el JWT del cliente (via
    query param `token`, igual que `ar-embed` -- no hay forma de poner un
    header Authorization en un `loadRequest` de WebView) y escuchar el
    canal JS `PaypalResultChannel`: la pagina llama `createOrder` sola
    (fetch propio a este mismo backend), pero el capturar la orden despues
    de aprobado lo hace Flutter (no esta pagina), para poder usar la
    sucursal que el cliente tiene elegida en ESE momento en el formulario
    nativo sin tener que recargar este WebView cada vez que la cambia."""
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>PayPal</title>
<style>
  html, body {{ margin: 0; padding: 0; background: transparent; font-family: system-ui, sans-serif; }}
  #paypal-button-container {{ padding: 4px; min-height: 45px; }}
  #boton-paypal-login {{
    display: block; width: 100%; margin: 4px 0; padding: 12px;
    background: #ffc439; color: #253b80; border: none; border-radius: 4px;
    font-size: 16px; font-weight: 700; font-family: inherit; cursor: pointer;
  }}
  #boton-paypal-login:active {{ background: #f2ba36; }}
  #msg-cargando, #msg-error {{
    padding: 16px; text-align: center; font-size: 13px; color: #203c40;
  }}
  #msg-error {{ color: #b3261e; }}
  [hidden] {{ display: none !important; }}
</style>
</head>
<body>
<div id="msg-cargando">Cargando PayPal...</div>
<div id="msg-error" hidden>No se pudo cargar PayPal. Volve a intentar.</div>
<div id="zona-botones" hidden>
  <button type="button" id="boton-paypal-login">PayPal</button>
  <div id="paypal-button-container"></div>
</div>
<script>
const TOKEN = new URLSearchParams(location.search).get("token");
const msgCargando = document.getElementById("msg-cargando");
const msgError = document.getElementById("msg-error");
const zonaBotones = document.getElementById("zona-botones");
const contenedor = document.getElementById("paypal-button-container");
const botonPaypalLogin = document.getElementById("boton-paypal-login");

function enviarResultado(payload) {{
  if (window.PaypalResultChannel) {{
    window.PaypalResultChannel.postMessage(JSON.stringify(payload));
  }}
}}

// El WebView de Flutter (chico, embebido en el formulario) no sabe cuanto
// mide esta pagina -- sin esto, el formulario de tarjeta (que crece cuando
// se completa: numero -> vencimiento/CSC -> direccion de facturacion)
// quedaba recortado y el boton de pagar final no se podia ni ver ni
// scrollear hasta el (reportado por el usuario probando en su celular).
// En vez de adivinar un alto fijo, se le avisa a Flutter el alto real cada
// vez que el contenido cambia, y el WebView se agranda para que sea la
// pagina entera (checkout) la que scrollea, sin scroll anidado.
function reportarAltura() {{
  if (window.PaypalHeightChannel) {{
    window.PaypalHeightChannel.postMessage(String(document.body.scrollHeight));
  }}
}}
new ResizeObserver(reportarAltura).observe(document.body);
window.addEventListener("load", reportarAltura);

async function crearOrden() {{
  const res = await fetch("/api/v1/ventas/checkout/paypal/crear-orden", {{
    method: "POST",
    headers: {{ Authorization: `Bearer ${{TOKEN}}`, "Content-Type": "application/json" }},
  }});
  if (!res.ok) throw new Error("crear-orden");
  return res.json();
}}

// Boton "PayPal" (login con cuenta) -- ver docstring de arriba: navega
// dentro de este mismo WebView al checkout real de PayPal en vez de usar
// el boton del SDK (que depende de un popup que el WebView no soporta).
botonPaypalLogin.addEventListener("click", async () => {{
  botonPaypalLogin.disabled = true;
  botonPaypalLogin.textContent = "Cargando...";
  try {{
    const data = await crearOrden();
    if (!data.approve_url) throw new Error("sin approve_url");
    location.href = data.approve_url;
  }} catch (e) {{
    botonPaypalLogin.disabled = false;
    botonPaypalLogin.textContent = "PayPal";
    enviarResultado({{ status: "error", message: "No se pudo iniciar el pago con PayPal." }});
  }}
}});

const script = document.createElement("script");
// enable-funding=card: sin esto, algunas cuentas de PayPal (depende de que
// funding este habilitado para esa cuenta) no muestran el boton de tarjeta
// de invitado -- forzarlo lo deja visible siempre que este disponible.
// locale=es_BO: sin esto el texto sale en ingles. A proposito NO se manda
// disable-funding=paypal aca: para esta cuenta sandbox, deshabilitar ese
// funding globalmente hacia que el SDK ni siquiera pudiera renderizar el
// boton de tarjeta (Buttons() tiraba error de entrada, "zero valid
// buttons"). En vez de eso, el funding "paypal" se deja habilitado a nivel
// SDK pero simplemente no se le pide un boton para el (fundingSource:
// CARD) -- asi el propio SDK sigue conforme y solo se renderiza el de
// tarjeta; el boton "PayPal" que ve el usuario es el propio de arriba.
script.src = "https://www.paypal.com/sdk/js?client-id={settings.PAYPAL_CLIENT_ID}&currency=USD&intent=capture&enable-funding=card&locale=es_BO";
script.onload = () => {{
  try {{
    window.paypal
      .Buttons({{
        fundingSource: window.paypal.FUNDING.CARD,
        style: {{ layout: "vertical", height: 45 }},
        createOrder: () => crearOrden().then((d) => d.order_id),
        onApprove: (data) => {{
          enviarResultado({{ status: "approved", orderId: data.orderID }});
        }},
        onCancel: () => {{
          enviarResultado({{ status: "cancelled" }});
        }},
        onError: () => {{
          enviarResultado({{ status: "error", message: "Ocurrio un error con PayPal." }});
        }},
      }})
      .render("#paypal-button-container");
    msgCargando.hidden = true;
    zonaBotones.hidden = false;
    reportarAltura();
  }} catch (e) {{
    msgCargando.hidden = true;
    msgError.hidden = false;
    reportarAltura();
  }}
}};
script.onerror = () => {{
  msgCargando.hidden = true;
  msgError.hidden = false;
  reportarAltura();
}};
document.head.appendChild(script);
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
