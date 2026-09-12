def render_ar_embed_html(producto_id: int) -> str:
    """Genera la pagina HTML standalone del probador CU09 para el `producto_id`
    dado. Logica identica (mismos estados, mismo cronometro de seguridad de
    180s, misma resolucion/codec) a `frontend/src/app/components/ar-tryon`,
    portada a JS plano porque esta pagina no pasa por el build de Angular:
    la sirve el backend directo para que el WebView de la app movil tenga
    un origen https real (ver comentario en `main.py::ar_embed`)."""
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
<title>Probador AR</title>
<style>
  html, body {{ margin: 0; padding: 0; background: #000; height: 100%; overflow: hidden; }}
  #stage {{ position: fixed; inset: 0; display: flex; align-items: center; justify-content: center; }}
  #video {{ max-width: 100%; max-height: 100%; background: #111; transform: scaleX(-1); }}
  #video-local {{ position: absolute; width: 1px; height: 1px; opacity: 0; pointer-events: none; }}
  .mensaje {{
    position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center;
    justify-content: center; gap: 8px; padding: 24px; text-align: center; color: #fff;
    background: rgba(32, 60, 64, 0.85); font-family: system-ui, sans-serif;
  }}
  .mensaje p {{ margin: 0; font-size: 16px; font-weight: 700; }}
  .detalle {{ font-size: 13px !important; font-weight: 400 !important; color: #ccc; }}
  .flotante {{
    inset: auto; bottom: 32px; left: 50%; transform: translateX(-50%); width: auto; max-width: 90%;
    padding: 12px 20px; background: rgba(0, 0, 0, 0.7); border-radius: 4px;
  }}
  .en-vivo {{
    position: absolute; top: 16px; left: 16px; z-index: 5; display: flex; align-items: center; gap: 6px;
    padding: 6px 12px; border-radius: 999px; background: rgba(34, 197, 94, 0.9); color: #fff;
    font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;
    font-family: system-ui, sans-serif;
  }}
  .en-vivo__punto {{ width: 8px; height: 8px; border-radius: 50%; background: #fff; animation: pulso 1.4s ease-in-out infinite; }}
  @keyframes pulso {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} }}
  .aviso-tiempo {{
    position: absolute; bottom: 24px; left: 50%; transform: translateX(-50%); z-index: 5;
    padding: 8px 16px; border-radius: 4px; background: rgba(0,0,0,0.75); color: #fff;
    font-size: 12px; font-weight: 600; font-family: system-ui, sans-serif;
  }}
  .seguir {{
    margin-top: 8px; padding: 10px 24px; border: none; background: #fff; color: #203c40;
    font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; cursor: pointer;
  }}
  [hidden] {{ display: none !important; }}
</style>
</head>
<body>
<div id="stage">
  <video id="video" autoplay playsinline muted></video>
  <video id="video-local" autoplay playsinline muted></video>
  <div id="en-vivo" class="en-vivo" hidden><span class="en-vivo__punto"></span>En vivo</div>
  <div id="aviso-tiempo" class="aviso-tiempo" hidden></div>
  <div id="msg-cargando" class="mensaje"><p>Iniciando camara...</p></div>
  <div id="msg-sin-permiso" class="mensaje" hidden>
    <p>No se pudo acceder a la camara.</p>
    <p class="detalle">Da permiso de camara y vuelve a intentar.</p>
  </div>
  <div id="msg-conectando" class="mensaje" hidden><p>Conectando con el probador en vivo...</p></div>
  <div id="msg-reconectando" class="mensaje flotante" hidden><p>Reconectando...</p></div>
  <div id="msg-error" class="mensaje" hidden>
    <p>No se pudo iniciar el probador de realidad aumentada.</p>
    <p class="detalle">Intenta de nuevo en unos segundos.</p>
  </div>
  <div id="msg-finalizado" class="mensaje" hidden>
    <p>Sesion finalizada para cuidar los creditos de la API.</p>
    <button type="button" class="seguir" id="btn-seguir">Seguir probando</button>
  </div>
</div>
<script type="module">
import {{ createDecartClient, models }} from "https://cdn.jsdelivr.net/npm/@decartai/sdk@0.1.22/+esm";

const PRODUCTO_ID = {producto_id};
const SESION_MAX_SEG = 180;
const AVISO_SEG = 20;
// CU09 requiere sesion iniciada (para registrar quien probo cada prenda);
// esta pagina la carga el WebView de la app movil con una navegacion
// normal (no podemos ponerle el header Authorization ahi), asi que el
// token viaja como query param y se lee aca para mandarlo en el fetch.
const TOKEN = new URLSearchParams(location.search).get("token");

const video = document.getElementById("video");
const videoLocal = document.getElementById("video-local");
const pantallas = {{
  cargando: document.getElementById("msg-cargando"),
  "sin-permiso": document.getElementById("msg-sin-permiso"),
  conectando: document.getElementById("msg-conectando"),
  reconectando: document.getElementById("msg-reconectando"),
  error: document.getElementById("msg-error"),
  finalizado: document.getElementById("msg-finalizado"),
}};
const enVivoEl = document.getElementById("en-vivo");
const avisoEl = document.getElementById("aviso-tiempo");

let stream = null;
let rtClient = null;
let cronometroId = null;
let segundosRestantes = SESION_MAX_SEG;
let detenido = false;

function setEstado(estado) {{
  for (const [nombre, el] of Object.entries(pantallas)) el.hidden = nombre !== estado;
  enVivoEl.hidden = estado !== "listo";
  if (estado !== "listo") avisoEl.hidden = true;
}}

function detenerCronometro() {{
  if (cronometroId !== null) {{
    clearInterval(cronometroId);
    cronometroId = null;
  }}
}}

function iniciarCronometro() {{
  segundosRestantes = SESION_MAX_SEG;
  cronometroId = setInterval(() => {{
    segundosRestantes -= 1;
    if (segundosRestantes <= AVISO_SEG && segundosRestantes > 0) {{
      avisoEl.hidden = false;
      avisoEl.textContent = `Se cierra en ${{segundosRestantes}}s para cuidar los creditos de la API`;
    }}
    if (segundosRestantes <= 0) finalizarPorTiempo();
  }}, 1000);
}}

function finalizarPorTiempo() {{
  detenerCronometro();
  rtClient?.disconnect();
  rtClient = null;
  setEstado("finalizado");
}}

async function conectarDecart() {{
  let sesion;
  try {{
    const res = await fetch(`/api/v1/productos/${{PRODUCTO_ID}}/ar-sesion`, {{
      method: "POST",
      headers: TOKEN ? {{ Authorization: `Bearer ${{TOKEN}}` }} : {{}},
    }});
    if (!res.ok) throw new Error("sesion");
    sesion = await res.json();
  }} catch {{
    setEstado("error");
    return;
  }}
  if (detenido || !stream) return;

  setEstado("conectando");

  try {{
    const client = createDecartClient({{ apiKey: sesion.token }});
    const model = models.realtime("lucy-vton-3.5");

    // Sin initialState: el ejemplo oficial conecta "en blanco" y manda
    // prompt+imagen juntos con setImage() una sola vez. Mandar solo texto
    // sin imagen al conectar dejaba al modelo VTON en un estado invalido
    // (bucle de reconexion sin llegar nunca a "generating").
    const cliente = await client.realtime.connect(stream, {{
      model,
      onRemoteStream: (remoteStream) => {{ video.srcObject = remoteStream; }},
    }});

    if (detenido) {{
      cliente.disconnect();
      return;
    }}

    cliente.on("connectionChange", (state) => {{
      if (detenido) return;
      if (state === "generating") setEstado("listo");
      else if (state === "reconnecting") setEstado("reconectando");
      else if (state === "connecting" || state === "connected") setEstado("conectando");
    }});
    cliente.on("error", () => setEstado("error"));
    rtClient = cliente;
    iniciarCronometro();

    await cliente.setImage(sesion.imagen_url, {{ prompt: sesion.prompt, enhance: false }});
  }} catch {{
    setEstado("error");
  }}
}}

async function iniciar() {{
  try {{
    stream = await navigator.mediaDevices.getUserMedia({{
      video: {{ facingMode: "user", width: {{ ideal: 1280 }}, height: {{ ideal: 720 }} }},
      audio: false,
    }});
  }} catch {{
    setEstado("sin-permiso");
    return;
  }}
  if (detenido) {{
    stream.getTracks().forEach((t) => t.stop());
    return;
  }}
  // Sin reproducir el track localmente en algun lado, varios navegadores no
  // lo mantienen produciendo frames de forma confiable (la sesion se
  // quedaba colgada sin nunca poder generar).
  videoLocal.srcObject = stream;
  try {{ await videoLocal.play(); }} catch {{}}
  await conectarDecart();
}}

document.getElementById("btn-seguir").addEventListener("click", () => {{ void conectarDecart(); }});

// La app movil (Flutter) llama esto antes de cerrar el WebView para
// desconectar y apagar la camara de forma prolija.
window.pararTodo = () => {{
  detenido = true;
  detenerCronometro();
  rtClient?.disconnect();
  stream?.getTracks().forEach((t) => t.stop());
}};

void iniciar();
</script>
</body>
</html>
"""
