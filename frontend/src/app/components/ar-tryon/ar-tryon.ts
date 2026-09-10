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
        video: { facingMode: 'user', width: { ideal: 1920 }, height: { ideal: 1080 } },
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
      const model = models.realtime('lucy-vton-latest');

      const rtClient = await client.realtime.connect(this.stream, {
        model,
        onRemoteStream: (remoteStream) => {
          const video = this.videoRef()?.nativeElement;
          if (video) video.srcObject = remoteStream;
        },
        initialState: { prompt: { text: sesion.prompt, enhance: false } },
        // Pide la mayor resolucion de salida que el servidor de Decart
        // soporta para este modelo (el modelo genera nativo en 720p; esto
        // le pide que escale a 1080p en vez de quedarse en 720p).
        resolution: '1080p',
        // h264 tiene aceleracion por hardware en mas dispositivos que vp8/vp9,
        // asi que decodifica mas fluido (menos placas/lag) en el celular o
        // laptop del cliente.
        preferredVideoCodec: 'h264',
      });

      if (this.detenido) {
        rtClient.disconnect();
        return;
      }

      rtClient.on('connectionChange', (state) => this.onEstadoConexion(state));
      rtClient.on('error', () => this.estado.set('error'));
      this.rtClient = rtClient;
      this.iniciarCronometro();

      // Referencia visual de la prenda (la foto del producto, con fondo
      // transparente): el modelo la usa para saber exactamente que
      // sustituir sobre el cuerpo detectado, ademas del prompt de texto.
      await rtClient.setImage(sesion.imagen_url, { prompt: sesion.prompt, enhance: false });
    } catch {
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
