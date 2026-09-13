import { DatePipe, KeyValuePipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../../environments/environment';

interface NotificacionItem {
  id: number;
  tipo_evento: string;
  mensaje: string;
  fecha_envio: string;
  leida: boolean;
  canal: string;
  estado: string;
  cliente_nombre: string;
  cliente_email: string;
}

interface NotificacionPage {
  items: NotificacionItem[];
  total: number;
  page: number;
  page_size: number;
}

const TIPOS_EVENTO: Record<string, string> = {
  reserva_creada: 'Reserva creada',
  reserva_cancelada: 'Reserva cancelada',
  reserva_vencida: 'Reserva vencida',
  reserva_por_vencer: 'Reserva por vencer',
  compra_confirmada: 'Compra confirmada',
  pago_rechazado: 'Pago rechazado',
};

// CU16 "Enviar Notificaciones": panel informativo de solo lectura -- las
// notificaciones las genera el propio backend (triggers al crear/cambiar
// una reserva o un pago, mas un barrido perezoso para las que estan por
// vencer); esta pantalla solo deja auditar a quien se le mando cada una,
// de que tipo, cuando y con que mensaje.
@Component({
  selector: 'app-admin-notificaciones',
  imports: [DatePipe, KeyValuePipe],
  templateUrl: './notificaciones.html',
  styleUrl: './notificaciones.scss',
})
export class AdminNotificaciones implements OnInit {
  private readonly http = inject(HttpClient);

  protected readonly items = signal<NotificacionItem[]>([]);
  protected readonly total = signal(0);
  protected readonly page = signal(1);
  protected readonly pageSize = 20;
  protected readonly filtroTipo = signal('');
  protected readonly loading = signal(false);
  protected readonly error = signal('');
  protected readonly tiposEvento = TIPOS_EVENTO;

  protected get totalPages(): number {
    return Math.max(1, Math.ceil(this.total() / this.pageSize));
  }

  ngOnInit(): void {
    void this.load();
  }

  protected filtrar(): void {
    this.page.set(1);
    void this.load();
  }

  protected goToPage(page: number): void {
    if (page < 1 || page > this.totalPages) return;
    this.page.set(page);
    void this.load();
  }

  private async load(): Promise<void> {
    this.loading.set(true);
    this.error.set('');
    try {
      const params: Record<string, string> = {
        page: String(this.page()),
        page_size: String(this.pageSize),
      };
      if (this.filtroTipo()) params['tipo_evento'] = this.filtroTipo();

      const res = await firstValueFrom(
        this.http.get<NotificacionPage>(`${environment.apiUrl}/notificaciones`, { params }),
      );
      this.items.set(res.items);
      this.total.set(res.total);
    } catch {
      this.error.set('No se pudo cargar las notificaciones.');
    } finally {
      this.loading.set(false);
    }
  }
}
