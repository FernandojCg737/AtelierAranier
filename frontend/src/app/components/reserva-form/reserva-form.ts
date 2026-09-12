import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Component, afterNextRender, computed, inject, input, output, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';

interface DisponibilidadItem {
  sucursal_id: number;
  sucursal_nombre: string;
  talla_id: number;
  talla_codigo: string;
  color_id: number;
  color_nombre: string;
  cantidad: number;
}

type Estado = 'cargando' | 'formulario' | 'enviando' | 'listo' | 'error' | 'sin-stock';

// CU10 (cliente): reservar una prenda para probarsela/recogerla en una
// sucursal en un horario. Antes de mostrar el formulario, trae las
// combinaciones talla/color/sucursal que de verdad tienen stock (no se
// puede reservar algo que no existe) via GET /reservas/disponibilidad.
@Component({
  selector: 'app-reserva-form',
  imports: [],
  templateUrl: './reserva-form.html',
  styleUrl: './reserva-form.scss',
})
export class ReservaForm {
  readonly productoId = input.required<string>();
  readonly productoNombre = input.required<string>();
  readonly closed = output<void>();

  private readonly http = inject(HttpClient);

  protected readonly estado = signal<Estado>('cargando');
  protected readonly opciones = signal<DisponibilidadItem[]>([]);
  protected readonly claveSeleccionada = signal('');
  protected readonly cantidad = signal(1);
  protected readonly horario = signal('');
  protected readonly errorMsg = signal('');

  protected readonly minDatetime = new Date(Date.now() + 60 * 60 * 1000).toISOString().slice(0, 16);

  protected readonly opcionActual = computed<DisponibilidadItem | undefined>(() =>
    this.opciones().find((o) => this.clave(o) === this.claveSeleccionada()),
  );

  constructor() {
    afterNextRender(() => void this.cargar());
  }

  protected clave(o: DisponibilidadItem): string {
    return `${o.sucursal_id}-${o.talla_id}-${o.color_id}`;
  }

  private async cargar(): Promise<void> {
    try {
      const res = await firstValueFrom(
        this.http.get<DisponibilidadItem[]>(`${environment.apiUrl}/reservas/disponibilidad/${this.productoId()}`),
      );
      if (res.length === 0) {
        this.estado.set('sin-stock');
        return;
      }
      this.opciones.set(res);
      this.claveSeleccionada.set(this.clave(res[0]));
      this.estado.set('formulario');
    } catch {
      this.estado.set('error');
    }
  }

  protected onOpcionChange(clave: string): void {
    this.claveSeleccionada.set(clave);
    this.cantidad.set(1);
  }

  protected async enviar(): Promise<void> {
    const o = this.opcionActual();
    if (!o || !this.horario()) return;

    this.estado.set('enviando');
    this.errorMsg.set('');
    try {
      await firstValueFrom(
        this.http.post(`${environment.apiUrl}/reservas`, {
          sucursal_id: o.sucursal_id,
          horario_atencion: new Date(this.horario()).toISOString(),
          items: [
            {
              producto_id: Number(this.productoId()),
              talla_id: o.talla_id,
              color_id: o.color_id,
              cantidad: this.cantidad(),
            },
          ],
        }),
      );
      this.estado.set('listo');
    } catch (err) {
      this.errorMsg.set(this.extraerError(err));
      this.estado.set('formulario');
    }
  }

  private extraerError(err: unknown): string {
    if (err instanceof HttpErrorResponse) {
      const detail = err.error?.detail;
      if (typeof detail === 'string') return detail;
      if (err.status === 0) return 'No pudimos conectar con el servidor.';
    }
    return 'No se pudo crear la reserva.';
  }

  protected cerrar(): void {
    this.closed.emit();
  }
}
