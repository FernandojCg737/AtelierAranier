from app.core.config import settings


def render_paypal_embed_html() -> str:
    """Pagina standalone que renderiza los botones reales del JS SDK de
    PayPal (los mismos, pixel a pixel, que carga `checkout.ts` en la web via
    `paypal-sdk.ts`) para cargarse INLINE dentro de un WebView chico en el
    checkout movil -- a diferencia de un WebView de pantalla completa con un
    link "approve", esto reproduce la misma experiencia que la web: el
    boton de PayPal y el boton de "Pagar con tarjeta de debito/credito"
    (que el SDK agrega solo cuando corresponde) aparecen ahi mismo, sin un
    paso extra.

    La app movil (Flutter) solo necesita mandarle el JWT del cliente (via
    query param `token`, igual que `ar-embed` -- no hay forma de poner un
    header Authorization en un `loadRequest` de WebView) y escuchar el
    canal JS `PaypalResultChannel`: la pagina llama `createOrder` sola
    (fetch propio a este mismo backend), pero el capturar la orden despues
    de `onApprove` lo hace Flutter (no esta pagina), para poder usar la
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
<div id="paypal-button-container" hidden></div>
<script>
// Instrumentacion temporal: `setOnConsoleMessage` de Flutter no esta
// llegando al logcat en release, asi que en vez de eso se manda todo
// (console.log/error, errores no capturados, y si PayPal intenta abrir una
// ventana emergente para 3D Secure -- el WebView no las soporta por
// defecto y esa llamada se perderia en silencio) por un canal JS propio
// para poder verlo directo en la pantalla de la app.
function _debug(msg) {{
  if (window.PaypalDebugChannel) window.PaypalDebugChannel.postMessage(String(msg));
}}
const _origLog = console.log;
const _origError = console.error;
console.log = function (...args) {{ _debug(args.join(" ")); _origLog.apply(console, args); }};
console.error = function (...args) {{ _debug("ERROR: " + args.join(" ")); _origError.apply(console, args); }};
window.addEventListener("error", (e) => _debug("window.onerror: " + e.message));
window.addEventListener("unhandledrejection", (e) => _debug("promise rechazada: " + (e.reason && e.reason.message ? e.reason.message : e.reason)));

const _origOpen = window.open;
window.open = function (...args) {{
  _debug("window.open llamado con: " + args[0]);
  return _origOpen ? _origOpen.apply(window, args) : null;
}};

const TOKEN = new URLSearchParams(location.search).get("token");
const msgCargando = document.getElementById("msg-cargando");
const msgError = document.getElementById("msg-error");
const contenedor = document.getElementById("paypal-button-container");

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
  if (!res.ok) {{
    const texto = await res.text().catch(() => "");
    _debug("crear-orden fallo (" + res.status + "): " + texto);
    throw new Error("crear-orden");
  }}
  const data = await res.json();
  _debug("orden creada: " + data.order_id);
  return data.order_id;
}}

const script = document.createElement("script");
script.src = "https://www.paypal.com/sdk/js?client-id={settings.PAYPAL_CLIENT_ID}&currency=USD&intent=capture";
script.onload = () => {{
  try {{
    window.paypal
      .Buttons({{
        style: {{ layout: "vertical", height: 45 }},
        createOrder: () => crearOrden(),
        onApprove: (data) => {{
          _debug("onApprove: " + data.orderID);
          enviarResultado({{ status: "approved", orderId: data.orderID }});
        }},
        onCancel: () => {{
          _debug("onCancel");
          enviarResultado({{ status: "cancelled" }});
        }},
        onError: (err) => {{
          _debug("onError de PayPal: " + (err && err.message ? err.message : err));
          enviarResultado({{ status: "error", message: "Ocurrio un error con PayPal." }});
        }},
      }})
      .render("#paypal-button-container");
    msgCargando.hidden = true;
    contenedor.hidden = false;
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
