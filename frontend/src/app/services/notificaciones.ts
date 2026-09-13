import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';

export interface Notificacion {
  id: number;
  tipo_evento: string;
  mensaje: string;
  fecha_envio: string;
  leida: boolean;
  entidad_tipo: string | null;
  entidad_id: number | null;
}

// CU16 (cliente): notificaciones generadas automaticamente por triggers en
// el backend (reserva creada/cancelada/vencida, reserva por vencer, compra
// confirmada/pago rechazado) -- el cliente solo las consulta y las marca
// como leidas, no las crea. El Header hace polling para que la campana se
// sienta "en vivo" sin necesitar websockets.
@Injectable({ providedIn: 'root' })
export class Notificaciones {
  private readonly http = inject(HttpClient);

  private readonly _items = signal<Notificacion[]>([]);

  readonly items = this._items.asReadonly();
  readonly noLeidas = computed(() => this._items().filter((n) => !n.leida).length);

  async cargar(): Promise<void> {
    try {
      const res = await firstValueFrom(this.http.get<Notificacion[]>(`${environment.apiUrl}/notificaciones/mias`));
      this._items.set(res);
    } catch {
      this._items.set([]);
    }
  }

  limpiarLocal(): void {
    this._items.set([]);
  }

  async marcarLeida(id: number): Promise<void> {
    const notif = this._items().find((n) => n.id === id);
    if (!notif || notif.leida) return;
    this._items.update((items) => items.map((n) => (n.id === id ? { ...n, leida: true } : n)));
    try {
      await firstValueFrom(this.http.put(`${environment.apiUrl}/notificaciones/mias/${id}/leida`, {}));
    } catch {
      await this.cargar();
    }
  }

  async marcarTodasLeidas(): Promise<void> {
    if (this.noLeidas() === 0) return;
    this._items.update((items) => items.map((n) => ({ ...n, leida: true })));
    try {
      await firstValueFrom(this.http.post(`${environment.apiUrl}/notificaciones/mias/marcar-todas-leidas`, {}));
    } catch {
      await this.cargar();
    }
  }
}
