import { DatePipe, DecimalPipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../../environments/environment';

interface DetalleCarritoItem {
  id: number;
  producto_nombre: string;
  talla_codigo: string;
  color_nombre: string;
  cantidad: number;
  precio_unitario: string;
  subtotal: string;
}

interface CarritoItem {
  id: number;
  estado: string;
  cliente_id: number;
  cliente_nombre: string;
  cliente_email: string;
  fecha_creacion: string;
  fecha_actualizacion: string;
  cantidad_items: number;
  total: string;
  detalles: DetalleCarritoItem[];
}

const INTERVALO_REFRESCO_MS = 15000;

// CU13: vista de solo lectura para que staff vea, "en tiempo real", quienes
// tienen items en su carrito de compras y que estan por comprar -- se
// refresca sola por polling (no hay infraestructura de WebSockets en el
// proyecto, y para esta pantalla no hace falta: alcanza con que se sienta
// viva sin que el usuario tenga que apretar F5).
@Component({
  selector: 'app-admin-carritos',
  imports: [DatePipe, DecimalPipe],
  templateUrl: './carritos.html',
  styleUrl: './carritos.scss',
})
export class AdminCarritos implements OnInit, OnDestroy {
  private readonly http = inject(HttpClient);
  private intervalo?: ReturnType<typeof setInterval>;

  protected readonly items = signal<CarritoItem[]>([]);
  protected readonly loading = signal(true);
  protected readonly error = signal('');
  protected readonly ultimaActualizacion = signal<Date | null>(null);

  protected readonly totalClientes = () => this.items().length;
  protected readonly totalArticulos = () => this.items().reduce((sum, c) => sum + c.cantidad_items, 0);
  protected readonly valorTotal = () => this.items().reduce((sum, c) => sum + Number(c.total), 0);

  ngOnInit(): void {
    void this.cargar();
    this.intervalo = setInterval(() => void this.cargar(), INTERVALO_REFRESCO_MS);
  }

  ngOnDestroy(): void {
    if (this.intervalo) clearInterval(this.intervalo);
  }

  private async cargar(): Promise<void> {
    try {
      const res = await firstValueFrom(this.http.get<CarritoItem[]>(`${environment.apiUrl}/carritos`));
      this.items.set(res);
      this.ultimaActualizacion.set(new Date());
      this.error.set('');
    } catch {
      this.error.set('No se pudo cargar los carritos activos.');
    } finally {
      this.loading.set(false);
    }
  }

  protected async refrescarAhora(): Promise<void> {
    this.loading.set(true);
    await this.cargar();
  }
}
