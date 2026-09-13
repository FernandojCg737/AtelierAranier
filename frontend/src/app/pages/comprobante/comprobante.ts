import { DatePipe, DecimalPipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';

interface DetalleVenta {
  id: number;
  producto_nombre: string;
  talla_codigo: string;
  color_nombre: string;
  cantidad: number;
  precio_unitario: string;
}

interface Venta {
  id: number;
  tipo: string;
  sucursal_nombre: string;
  fecha: string;
  total: string;
  estado: string;
  metodo_pago: string;
  estado_pago: string;
  atendido_por_nombre: string | null;
  detalles: DetalleVenta[];
}

const METODO_LABEL: Record<string, string> = {
  paypal: 'PayPal / Tarjeta de credito',
  qr: 'QR (transferencia)',
  efectivo: 'Efectivo en sucursal',
};

// Comprobante de compra descargable/imprimible (no es una factura fiscal
// con NIT/timbrado -- eso requeriria integrarse con la autoridad
// tributaria, fuera de alcance). "Descargar" es imprimir a PDF desde el
// navegador: no hace falta ninguna libreria de PDF para esto. Mismo diseno
// que la factura que ve el staff en /admin/factura/:id.
@Component({
  selector: 'app-comprobante',
  imports: [DatePipe, DecimalPipe, RouterLink],
  templateUrl: './comprobante.html',
  styleUrl: './comprobante.scss',
})
export class Comprobante implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly http = inject(HttpClient);

  protected readonly venta = signal<Venta | undefined>(undefined);
  protected readonly cargando = signal(true);
  protected readonly error = signal('');
  protected readonly metodoLabel = METODO_LABEL;

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (!id) {
      this.error.set('Compra no encontrada.');
      this.cargando.set(false);
      return;
    }
    void this.cargar(id);
  }

  private async cargar(id: string): Promise<void> {
    try {
      const res = await firstValueFrom(this.http.get<Venta>(`${environment.apiUrl}/ventas/mias/${id}`));
      this.venta.set(res);
    } catch {
      this.error.set('No pudimos encontrar esa compra.');
    } finally {
      this.cargando.set(false);
    }
  }

  protected folio(id: number): string {
    return String(id).padStart(6, '0');
  }

  protected subtotal(d: DetalleVenta): number {
    return Number(d.precio_unitario) * d.cantidad;
  }

  protected imprimir(): void {
    window.print();
  }
}
