import { DatePipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../../environments/environment';

interface UsuarioChatbot {
  cliente_id: number;
  cliente_nombre: string;
  cliente_email: string;
  total_mensajes: number;
  ultima_actividad: string;
}

// CU19 "Atender Cliente con Chatbot": panel de solo lectura -- lista de
// clientes que usaron el chatbot; al hacer click se ve la conversacion
// completa (/admin/chatbot/:clienteId).
@Component({
  selector: 'app-admin-chatbot',
  imports: [DatePipe, RouterLink],
  templateUrl: './chatbot.html',
  styleUrl: './chatbot.scss',
})
export class AdminChatbot implements OnInit {
  private readonly http = inject(HttpClient);

  protected readonly items = signal<UsuarioChatbot[]>([]);
  protected readonly loading = signal(true);
  protected readonly error = signal('');

  ngOnInit(): void {
    void this.cargar();
  }

  private async cargar(): Promise<void> {
    try {
      const res = await firstValueFrom(this.http.get<UsuarioChatbot[]>(`${environment.apiUrl}/chatbot`));
      this.items.set(res);
    } catch {
      this.error.set('No se pudo cargar los usuarios del chatbot.');
    } finally {
      this.loading.set(false);
    }
  }
}
