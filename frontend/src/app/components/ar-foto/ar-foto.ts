import { HttpClient } from '@angular/common/http';
import {
  Component,
  ElementRef,
  OnDestroy,
  effect,
  inject,
  input,
  output,
  signal,
  viewChild,
} from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';

interface ArFotoTrabajo {
  job_id: string;
}

interface ArFotoEstado {
  estado: string;
  listo: boolean;
  error: boolean;
}

type Estado = 'eligiendo' | 'camara' | 'subiendo' | 'procesando' | 'listo' | 'error';

const TIPOS_PERMITIDOS = ['image/jpeg', 'image/png', 'image/webp'];
const POLL_MS = 2500;

// Probador CU09, modo VIRTUAL: a diferencia de app-ar-tryon (camara en vivo
// via WebRTC continuo), aca el cliente manda UNA sola foto -- ya sea
// tomandola con la camara del dispositivo (una captura, no video en vivo)
// o subiendo un archivo -- y el backend la manda a un trabajo en cola de
// Decart (imagen-a-imagen); este componente sube el archivo, consulta el
// estado cada POLL_MS y muestra el resultado cuando esta listo.
@Component({
  selector: 'app-ar-foto',
  imports: [],
  templateUrl: './ar-foto.html',
  styleUrl: './ar-foto.scss',
})
export class ArFoto implements OnDestroy {
  readonly productoId = input.required<string>();
  readonly closed = output<void>();

  private readonly http = inject(HttpClient);
  private readonly camaraVideoRef = viewChild<ElementRef<HTMLVideoElement>>('camaraVideo');

  protected readonly estado = signal<Estado>('eligiendo');
  protected readonly previewUrl = signal<string | null>(null);
  protected readonly resultadoUrl = signal<string | null>(null);
  private readonly stream = signal<MediaStream | null>(null);

  private pollId: ReturnType<typeof setInterval> | null = null;
  private detenido = false;

  constructor() {
    // El elemento <video> de la camara solo existe en el DOM mientras
    // estado() === 'camara' (esta detras de un @if); este effect conecta
    // el stream apenas ese elemento aparece, sin importar el orden en que
    // stream/estado terminen de actualizarse.
    effect(() => {
      const video = this.camaraVideoRef()?.nativeElement;
      const s = this.stream();
      if (video && s) video.srcObject = s;
    });
  }

  protected async iniciarCamara(): Promise<void> {
    try {
      const s = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false });
      if (this.detenido) {
        s.getTracks().forEach((t) => t.stop());
        return;
      }
      this.stream.set(s);
      this.estado.set('camara');
    } catch {
      this.estado.set('error');
    }
  }

  protected async capturarFoto(): Promise<void> {
    const video = this.camaraVideoRef()?.nativeElement;
    if (!video || !video.videoWidth) return;

    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.drawImage(video, 0, 0);

    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.92));
    this.detenerCamara();
    if (!blob) {
      this.estado.set('error');
      return;
    }

    this.previewUrl.set(URL.createObjectURL(blob));
    void this.subir(new File([blob], 'foto.jpg', { type: 'image/jpeg' }));
  }

  protected cancelarCamara(): void {
    this.detenerCamara();
    this.estado.set('eligiendo');
  }

  private detenerCamara(): void {
    this.stream()?.getTracks().forEach((t) => t.stop());
    this.stream.set(null);
  }

  protected onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const files = input.files;
    if (!files || files.length === 0) return;
    const file = files[0];
    if (!TIPOS_PERMITIDOS.includes(file.type)) {
      this.estado.set('error');
      input.value = '';
      return;
    }

    this.previewUrl.set(URL.createObjectURL(file));
    void this.subir(file);
    input.value = '';
  }

  private async subir(file: File): Promise<void> {
    this.estado.set('subiendo');
    try {
      const formData = new FormData();
      formData.append('file', file);
      const trabajo = await firstValueFrom(
        this.http.post<ArFotoTrabajo>(`${environment.apiUrl}/productos/${this.productoId()}/ar-foto`, formData),
      );
      if (this.detenido) return;
      this.estado.set('procesando');
      this.iniciarPolling(trabajo.job_id);
    } catch {
      if (!this.detenido) this.estado.set('error');
    }
  }

  private iniciarPolling(jobId: string): void {
    this.pollId = setInterval(() => void this.consultarEstado(jobId), POLL_MS);
  }

  private async consultarEstado(jobId: string): Promise<void> {
    try {
      const res = await firstValueFrom(
        this.http.get<ArFotoEstado>(`${environment.apiUrl}/productos/ar-foto/${jobId}`),
      );
      if (this.detenido) return;
      if (res.error) {
        this.detenerPolling();
        this.estado.set('error');
        return;
      }
      if (res.listo) {
        this.detenerPolling();
        this.resultadoUrl.set(`${environment.apiUrl}/productos/ar-foto/${jobId}/resultado`);
        this.estado.set('listo');
      }
    } catch {
      if (!this.detenido) {
        this.detenerPolling();
        this.estado.set('error');
      }
    }
  }

  private detenerPolling(): void {
    if (this.pollId !== null) {
      clearInterval(this.pollId);
      this.pollId = null;
    }
  }

  protected reintentar(): void {
    const url = this.previewUrl();
    if (url) URL.revokeObjectURL(url);
    this.previewUrl.set(null);
    this.resultadoUrl.set(null);
    this.estado.set('eligiendo');
  }

  protected cerrar(): void {
    this.closed.emit();
  }

  ngOnDestroy(): void {
    this.detenido = true;
    this.detenerPolling();
    this.detenerCamara();
    const url = this.previewUrl();
    if (url) URL.revokeObjectURL(url);
  }
}
