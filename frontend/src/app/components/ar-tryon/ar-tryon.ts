import { HttpClient } from '@angular/common/http';
import {
  Component,
  ElementRef,
  OnDestroy,
  afterNextRender,
  inject,
  input,
  output,
  signal,
  viewChild,
} from '@angular/core';
import { ConnectionState, RealTimeClient, createDecartClient, models } from '@decartai/sdk';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';

interface ArSesion {
  token: string;
  imagen_url: string;
  prompt: string;
}

type Estado = 'cargando' | 'sin-permiso' | 'conectando' | 'listo' | 'reconectando' | 'error' | 'finalizado';

// Cada segundo conectado a Decart tiene costo real ($0.02/s). Para no
// quemar creditos por descuido (alguien deja la pestaña abierta y se
// olvida), la sesion se corta sola a los 3 minutos; el cliente puede
// seguir probando de inmediato con "Seguir probando" (pide una sesion
// nueva, sin volver a pedir permiso de camara).
const SESION_MAX_SEG = 180;
const AVISO_SEG = 20;

// Probador virtual con realidad aumentada (CU09): motor Decart lucy-vton en
// tiempo real (el mismo motor detras de la extension Anywear). El backend
// genera un token de cliente de corta duracion a partir de la API key
// permanente (que nunca sale del servidor) y arma el prompt de la prenda;
// este componente abre la camara, conecta por WebRTC contra Decart y
// muestra el video ya transformado en vivo (no dibujamos nada nosotros:
// el modelo genera el frame completo con la prenda puesta).
@Component({
  selector: 'app-ar-tryon',
  imports: [],
  templateUrl: './ar-tryon.html',
  styleUrl: './ar-tryon.scss',
})
export class ArTryon implements OnDestroy {
  readonly productoId = input.required<string>();
  readonly closed = output<void>();

  private readonly http = inject(HttpClient);
  private readonly videoRef = viewChild<ElementRef<HTMLVideoElement>>('video');
  private readonly localVideoRef = viewChild<ElementRef<HTMLVideoElement>>('localVideo');

  protected readonly estado = signal<Estado>('cargando');
  protected readonly segundosRestantes = signal(SESION_MAX_SEG);
  protected readonly avisoSeg = AVISO_SEG;

  private stream: MediaStream | null = null;
  private rtClient: RealTimeClient | null = null;
  private cronometroId: ReturnType<typeof setInterval> | null = null;
  private detenido = false;

  constructor() {
    afterNextRender(() => void this.iniciar());
  }

  private async iniciar(): Promise<void> {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        // 1280x720: resolucion nativa del modelo (lucy-vton-latest). Se
        // probo pedir 1920x1080 a la camara para "mejorar calidad" pero
        // dejaba la sesion colgada en "connected" sin nunca generar.
        video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });
    } catch {
      this.estado.set('sin-permiso');
      return;
    }
    if (this.detenido) {
      this.pararCamara();
      return;
    }

    // Sin esto, el track de la camara nunca se "reproduce" en ningun lado
    // localmente (solo mostramos el video YA transformado que vuelve del
    // servidor) -- en varios navegadores un track que nadie esta
    // consumiendo/renderizando no llega a producir frames de forma
    // confiable, lo que dejaba la sesion colgada sin nunca poder generar
    // ("could not determine track dimensions" en la consola era la pista).
    const localVideo = this.localVideoRef()?.nativeElement;
    if (localVideo) {
      localVideo.srcObject = this.stream;
      try {
        await localVideo.play();
      } catch {
        // Autoplay bloqueado no deberia pasar (esta muted), pero si pasa
        // seguimos igual: el intento de conectar es lo importante.
      }
    }

    await this.conectarDecart();
  }

  private async conectarDecart(): Promise<void> {
    let sesion: ArSesion;
    try {
      sesion = await firstValueFrom(
        this.http.post<ArSesion>(`${environment.apiUrl}/productos/${this.productoId()}/ar-sesion`, {}),
      );
    } catch {
      this.estado.set('error');
      return;
    }
    if (this.detenido || !this.stream) return;

    this.estado.set('conectando');

    try {
      const client = createDecartClient({ apiKey: sesion.token });
      // Version fija en vez del alias "latest": si "latest" esta apuntando
      // a un rollout inestable en este momento, esto lo evita.
      const model = models.realtime('lucy-vton-3.5');

      // NOTA: el ejemplo oficial de Decart conecta SIN initialState y recien
      // manda prompt+imagen juntos con setImage() una sola vez -- nosotros
      // mandabamos initialState.prompt SIN imagen al conectar (la imagen
      // recien llegaba despues con setImage). Es probable que pedirle al
      // modelo VTON que arranque con solo texto y sin imagen de referencia
      // lo deje en un estado invalido que termina cerrando la conexion en
      // bucle. Se saca initialState: setImage() ya manda prompt+imagen
      // juntos, replicando el patron que funciona en el ejemplo oficial.
      const rtClient = await client.realtime.connect(this.stream, {
        model,
        onRemoteStream: (remoteStream) => {
          const video = this.videoRef()?.nativeElement;
          if (video) video.srcObject = remoteStream;
        },
      });

      if (this.detenido) {
        rtClient.disconnect();
        return;
      }

      rtClient.on('connectionChange', (state) => {
        console.log('[AR] connectionChange:', state);
        this.onEstadoConexion(state);
      });
      rtClient.on('error', (err) => {
        console.error('[AR] rtClient error:', err);
        this.estado.set('error');
      });
      this.rtClient = rtClient;
      this.iniciarCronometro();

      // Referencia visual de la prenda (la foto del producto, con fondo
      // transparente): el modelo la usa para saber exactamente que
      // sustituir sobre el cuerpo detectado, ademas del prompt de texto.
      // (Diagnostico confirmado: el bucle de reconexion pasa IGUAL sin esto,
      // asi que no es la causa -- reactivado.)
      console.log('[AR] llamando setImage con', sesion.imagen_url);
      try {
        await rtClient.setImage(sesion.imagen_url, { prompt: sesion.prompt, enhance: false });
        console.log('[AR] setImage OK');
      } catch (err) {
        console.error('[AR] setImage fallo (no fatal, sigue con el prompt inicial):', err);
      }
    } catch (err) {
      console.error('[AR] connect() fallo:', err);
      this.estado.set('error');
    }
  }

  private onEstadoConexion(state: ConnectionState): void {
    if (this.detenido) return;
    if (state === 'generating') this.estado.set('listo');
    else if (state === 'reconnecting') this.estado.set('reconectando');
    else if (state === 'connecting' || state === 'connected') this.estado.set('conectando');
  }

  private iniciarCronometro(): void {
    this.segundosRestantes.set(SESION_MAX_SEG);
    this.cronometroId = setInterval(() => {
      const restante = this.segundosRestantes() - 1;
      this.segundosRestantes.set(restante);
      if (restante <= 0) this.finalizarPorTiempo();
    }, 1000);
  }

  private detenerCronometro(): void {
    if (this.cronometroId !== null) {
      clearInterval(this.cronometroId);
      this.cronometroId = null;
    }
  }

  private finalizarPorTiempo(): void {
    this.detenerCronometro();
    this.rtClient?.disconnect();
    this.rtClient = null;
    this.estado.set('finalizado');
  }

  protected seguirProbando(): void {
    void this.conectarDecart();
  }

  protected cerrar(): void {
    this.closed.emit();
  }

  private pararCamara(): void {
    this.stream?.getTracks().forEach((t) => t.stop());
    this.stream = null;
  }

  ngOnDestroy(): void {
    this.detenido = true;
    this.detenerCronometro();
    this.rtClient?.disconnect();
    this.pararCamara();
  }
}
