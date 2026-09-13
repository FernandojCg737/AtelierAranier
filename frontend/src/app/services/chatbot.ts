import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';

export interface MensajeChat {
  id: number;
  remitente: 'cliente' | 'bot';
  mensaje: string;
  fecha: string;
}

// CU19: historial de la conversacion del cliente con el chatbot -- el
// backend arma la respuesta (motor de contexto + Gemini), aca solo se
// manda el mensaje y se muestra lo que vuelve.
@Injectable({ providedIn: 'root' })
export class ChatbotService {
  private readonly http = inject(HttpClient);

  private readonly _mensajes = signal<MensajeChat[]>([]);
  readonly mensajes = this._mensajes.asReadonly();
  readonly enviando = signal(false);

  async cargar(): Promise<void> {
    try {
      const res = await firstValueFrom(this.http.get<MensajeChat[]>(`${environment.apiUrl}/chatbot/mias`));
      this._mensajes.set(res);
    } catch {
      this._mensajes.set([]);
    }
  }

  async enviar(mensaje: string): Promise<MensajeChat | null> {
    const texto = mensaje.trim();
    if (!texto) return null;

    const optimista: MensajeChat = {
      id: -Date.now(),
      remitente: 'cliente',
      mensaje: texto,
      fecha: new Date().toISOString(),
    };
    this._mensajes.update((m) => [...m, optimista]);

    this.enviando.set(true);
    try {
      const res = await firstValueFrom(
        this.http.post<MensajeChat>(`${environment.apiUrl}/chatbot/mensajes`, { mensaje: texto }),
      );
      this._mensajes.update((m) => [...m, res]);
      return res;
    } catch {
      this._mensajes.update((m) => [
        ...m,
        {
          id: -Date.now(),
          remitente: 'bot',
          mensaje: 'No pudimos conectar con el asistente. Intenta de nuevo en un momento.',
          fecha: new Date().toISOString(),
        },
      ]);
      return null;
    } finally {
      this.enviando.set(false);
    }
  }

  limpiarLocal(): void {
    this._mensajes.set([]);
  }
}
