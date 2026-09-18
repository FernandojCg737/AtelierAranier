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

interface TallaSucursal {
  key: string;
  talla_id: number;
  talla_codigo: string;
  sucursal_id: number;
  sucursal_nombre: string;
  total: number;
}

type Estado = 'cargando' | 'formulario' | 'agregando' | 'listo' | 'error' | 'sin-stock';

function clave(tallaId: number, sucursalId: number): string {
  return `${tallaId}:${sucursalId}`;
}

// CU11, pedido explicito del usuario: la sucursal de retiro se elige ACA,
// por producto, al agregarlo al carrito -- no recien en el checkout. La
// talla ya viene "atada" a una sucursal (ej. "XL -- Sucursal Norte, Stock
// 10"): elegirla fija ambas cosas de una, y el color se filtra a los que
// esa sucursal tiene en esa talla. Si el carrito termina con productos de
// sucursales distintas, el checkout reparte el pago en varias ventas.
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
  protected readonly variantes = signal<DisponibilidadItem[]>([]);
  protected readonly tallaSucursalSeleccionada = signal<string | null>(null);
  protected readonly colorSeleccionado = signal<number | null>(null);
  protected readonly cantidad = signal(1);
  protected readonly errorMsg = signal('');

  protected readonly tallasSucursal = computed<TallaSucursal[]>(() => {
    const vistos = new Set<string>();
    const lista: TallaSucursal[] = [];
    for (const v of this.variantes()) {
      const key = clave(v.talla_id, v.sucursal_id);
      if (vistos.has(key)) continue;
      vistos.add(key);
      const total = this.variantes()
        .filter((x) => x.talla_id === v.talla_id && x.sucursal_id === v.sucursal_id)
        .reduce((sum, x) => sum + x.cantidad, 0);
      lista.push({
        key,
        talla_id: v.talla_id,
        talla_codigo: v.talla_codigo,
        sucursal_id: v.sucursal_id,
        sucursal_nombre: v.sucursal_nombre,
        total,
      });
    }
    return lista;
  });

  protected readonly coloresDisponibles = computed(() => {
    const key = this.tallaSucursalSeleccionada();
    if (!key) return [];
    const [tallaId, sucursalId] = key.split(':').map(Number);
    return this.variantes().filter((v) => v.talla_id === tallaId && v.sucursal_id === sucursalId);
  });

  protected readonly varianteActual = computed<DisponibilidadItem | undefined>(() =>
    this.coloresDisponibles().find((v) => v.color_id === this.colorSeleccionado()),
  );

  constructor() {
    afterNextRender(() => void this.cargar());
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

      this.variantes.set(res);
      const primero = res[0];
      this.tallaSucursalSeleccionada.set(clave(primero.talla_id, primero.sucursal_id));
      this.colorSeleccionado.set(primero.color_id);
      this.estado.set('formulario');
    } catch {
      this.estado.set('error');
    }
  }

  protected onTallaSucursalChange(key: string): void {
    this.tallaSucursalSeleccionada.set(key);
    const [tallaId, sucursalId] = key.split(':').map(Number);
    // La talla/sucursal nueva puede no tener el mismo color que estaba
    // elegido -- se cae al primero que si tenga stock en esa combinacion.
    const primerColor = this.variantes().find((v) => v.talla_id === tallaId && v.sucursal_id === sucursalId);
    this.colorSeleccionado.set(primerColor?.color_id ?? null);
    this.cantidad.set(1);
  }

  protected onColorChange(colorId: string): void {
    this.colorSeleccionado.set(Number(colorId));
    this.cantidad.set(1);
  }

  protected async enviar(): Promise<void> {
    const v = this.varianteActual();
    if (!v) return;

    this.estado.set('agregando');
    this.errorMsg.set('');
    try {
      await this.cart.agregar(Number(this.productoId()), v.talla_id, v.color_id, v.sucursal_id, this.cantidad());
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
