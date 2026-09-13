import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Component, afterNextRender, computed, inject, input, output, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Cart } from '../../services/cart';

interface DisponibilidadItem {
  sucursal_id: number;
  sucursal_nombre: string;
  talla_id: number;
  talla_codigo: string;
  color_id: number;
  color_nombre: string;
  cantidad: number;
}

interface Variante {
  talla_id: number;
  talla_codigo: string;
  color_id: number;
  color_nombre: string;
  cantidad: number;
}

type Estado = 'cargando' | 'formulario' | 'agregando' | 'listo' | 'error' | 'sin-stock';

// CU11: agregar al carrito requiere elegir una combinacion talla/color que
// de verdad tenga stock -- reutiliza el mismo endpoint de disponibilidad
// que ya usa ReservaForm (GET /reservas/disponibilidad), pero acumulando
// cantidad entre sucursales: el carrito no fija sucursal todavia (eso se
// elige recien en el checkout).
@Component({
  selector: 'app-agregar-carrito',
  imports: [],
  templateUrl: './agregar-carrito.html',
  styleUrl: './agregar-carrito.scss',
})
export class AgregarCarrito {
  readonly productoId = input.required<string>();
  readonly productoNombre = input.required<string>();
  readonly closed = output<void>();

  private readonly http = inject(HttpClient);
  private readonly cart = inject(Cart);

  protected readonly estado = signal<Estado>('cargando');
  protected readonly variantes = signal<Variante[]>([]);
  protected readonly claveSeleccionada = signal('');
  protected readonly cantidad = signal(1);
  protected readonly errorMsg = signal('');

  protected readonly varianteActual = computed<Variante | undefined>(() =>
    this.variantes().find((v) => this.clave(v) === this.claveSeleccionada()),
  );

  constructor() {
    afterNextRender(() => void this.cargar());
  }

  protected clave(v: Variante): string {
    return `${v.talla_id}-${v.color_id}`;
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

      const porClave = new Map<string, Variante>();
      for (const item of res) {
        const clave = `${item.talla_id}-${item.color_id}`;
        const existente = porClave.get(clave);
        if (existente) {
          existente.cantidad += item.cantidad;
        } else {
          porClave.set(clave, {
            talla_id: item.talla_id,
            talla_codigo: item.talla_codigo,
            color_id: item.color_id,
            color_nombre: item.color_nombre,
            cantidad: item.cantidad,
          });
        }
      }

      const lista = [...porClave.values()];
      this.variantes.set(lista);
      this.claveSeleccionada.set(this.clave(lista[0]));
      this.estado.set('formulario');
    } catch {
      this.estado.set('error');
    }
  }

  protected onVarianteChange(clave: string): void {
    this.claveSeleccionada.set(clave);
    this.cantidad.set(1);
  }

  protected async enviar(): Promise<void> {
    const v = this.varianteActual();
    if (!v) return;

    this.estado.set('agregando');
    this.errorMsg.set('');
    try {
      await this.cart.agregar(Number(this.productoId()), v.talla_id, v.color_id, this.cantidad());
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
    return 'No se pudo agregar al carrito.';
  }

  protected cerrar(): void {
    this.closed.emit();
  }
}
