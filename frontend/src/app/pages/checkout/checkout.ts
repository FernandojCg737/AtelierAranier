import { DecimalPipe } from '@angular/common';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { AfterViewInit, Component, ElementRef, OnInit, computed, inject, signal, viewChild } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Cart } from '../../services/cart';
import { PaypalSdk } from '../../services/paypal-sdk';

interface Sucursal {
  id: number;
  nombre: string;
  direccion: string;
}

interface StockItem {
  detalle_id: number;
  producto_id: number;
  producto_nombre: string;
  talla_codigo: string;
  color_nombre: string;
  cantidad_pedida: number;
  cantidad_disponible: number;
  disponible: boolean;
}

type Metodo = 'paypal' | 'qr';
type Estado = 'cargando' | 'formulario' | 'procesando' | 'listo' | 'listo-qr' | 'error' | 'vacio';

// CU11: checkout del carrito. El pago con PayPal/tarjeta se cobra solo (el
// SDK de PayPal muestra su propio boton, que llama a nuestro backend para
// crear y despues capturar la orden); el pago por QR sube un comprobante y
// queda pendiente de que un cajero/encargado lo revise.
@Component({
  selector: 'app-checkout',
  imports: [RouterLink, DecimalPipe],
  templateUrl: './checkout.html',
  styleUrl: './checkout.scss',
})
export class Checkout implements OnInit, AfterViewInit {
  protected readonly cart = inject(Cart);
  private readonly http = inject(HttpClient);
  private readonly paypalSdk = inject(PaypalSdk);
  private readonly router = inject(Router);

  private readonly paypalContainer = viewChild<ElementRef<HTMLDivElement>>('paypalContainer');

  protected readonly estado = signal<Estado>('cargando');
  protected readonly sucursales = signal<Sucursal[]>([]);
  protected readonly sucursalId = signal<number | null>(null);
  protected readonly metodo = signal<Metodo>('paypal');
  protected readonly errorMsg = signal('');
  protected readonly archivoComprobante = signal<File | null>(null);
  protected readonly stockStatus = signal<StockItem[] | null>(null);
  protected readonly verificandoStock = signal(false);

  // CU11, pedido del usuario: antes esto solo se descubria recien al tratar
  // de pagar (aprobando en PayPal o subiendo el comprobante QR). Ahora se
  // chequea cada vez que se elige/cambia la sucursal, ANTES de mostrar los
  // metodos de pago, para avisar producto por producto.
  protected readonly itemsSinStock = computed(() => this.stockStatus()?.filter((i) => !i.disponible) ?? []);
  protected readonly stockOk = computed(() => this.stockStatus() !== null && this.itemsSinStock().length === 0);

  private botonesPaypalRenderizados = false;

  ngOnInit(): void {
    void this.cargar();
  }

  ngAfterViewInit(): void {
    // Se intenta renderizar el boton de PayPal cada vez que Angular
    // actualiza la vista (cambia sucursal/metodo); si ya esta renderizado o
    // todavia no corresponde mostrarlo, renderizarBotonPaypal() no hace nada.
    void this.renderizarBotonPaypal();
  }

  private async cargar(): Promise<void> {
    await this.cart.cargar();
    if (this.cart.items().length === 0) {
      this.estado.set('vacio');
      return;
    }
    try {
      const res = await firstValueFrom(this.http.get<Sucursal[]>(`${environment.apiUrl}/sucursales/publico`));
      this.sucursales.set(res);
      this.sucursalId.set(res[0]?.id ?? null);
      this.estado.set('formulario');
      void this.verificarStock();
    } catch {
      this.estado.set('error');
    }
  }

  protected onSucursalChange(id: string): void {
    this.sucursalId.set(Number(id));
    this.botonesPaypalRenderizados = false;
    this.stockStatus.set(null);
    void this.verificarStock();
    setTimeout(() => void this.renderizarBotonPaypal());
  }

  private async verificarStock(): Promise<void> {
    const sucursalId = this.sucursalId();
    if (!sucursalId) return;

    this.verificandoStock.set(true);
    try {
      const res = await firstValueFrom(
        this.http.get<StockItem[]>(`${environment.apiUrl}/ventas/checkout/verificar-stock/${sucursalId}`),
      );
      this.stockStatus.set(res);
    } catch {
      // Si falla el chequeo, no bloqueamos el pago con esto -- la validacion
      // real y definitiva sigue estando del lado del backend al capturar.
      this.stockStatus.set([]);
    } finally {
      this.verificandoStock.set(false);
      this.botonesPaypalRenderizados = false;
      void this.renderizarBotonPaypal();
    }
  }

  protected onMetodoChange(m: Metodo): void {
    this.metodo.set(m);
    if (m === 'paypal') {
      this.botonesPaypalRenderizados = false;
      setTimeout(() => void this.renderizarBotonPaypal());
    }
  }

  private async renderizarBotonPaypal(): Promise<void> {
    if (this.metodo() !== 'paypal' || this.estado() !== 'formulario' || !this.stockOk()) return;
    if (this.botonesPaypalRenderizados) return;
    const contenedor = this.paypalContainer()?.nativeElement;
    if (!contenedor) return;

    this.botonesPaypalRenderizados = true;
    contenedor.innerHTML = '';

    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const paypal = (await this.paypalSdk.cargar()) as any;
      paypal
        .Buttons({
          createOrder: async () => {
            const res = await firstValueFrom(
              this.http.post<{ order_id: string }>(`${environment.apiUrl}/ventas/checkout/paypal/crear-orden`, {}),
            );
            return res.order_id;
          },
          onApprove: async (data: { orderID: string }) => {
            this.estado.set('procesando');
            try {
              await firstValueFrom(
                this.http.post(`${environment.apiUrl}/ventas/checkout/paypal/capturar/${data.orderID}`, {
                  sucursal_id: this.sucursalId(),
                }),
              );
              this.estado.set('listo');
            } catch (err) {
              this.errorMsg.set(this.extraerError(err));
              this.estado.set('formulario');
              this.botonesPaypalRenderizados = false;
              setTimeout(() => void this.renderizarBotonPaypal());
            }
          },
          onError: () => {
            this.errorMsg.set('Ocurrio un error con PayPal. Intenta de nuevo.');
          },
        })
        .render(contenedor);
    } catch {
      this.errorMsg.set('No se pudo cargar PayPal. Intenta de nuevo en unos segundos.');
    }
  }

  protected onArchivoSeleccionado(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.archivoComprobante.set(input.files?.[0] ?? null);
  }

  protected async enviarQr(): Promise<void> {
    const archivo = this.archivoComprobante();
    const sucursalId = this.sucursalId();
    if (!archivo || !sucursalId || !this.stockOk()) return;

    this.estado.set('procesando');
    this.errorMsg.set('');
    try {
      const formData = new FormData();
      formData.append('sucursal_id', String(sucursalId));
      formData.append('file', archivo);
      await firstValueFrom(this.http.post(`${environment.apiUrl}/ventas/checkout/qr`, formData));
      this.estado.set('listo-qr');
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
    return 'No se pudo procesar el pago.';
  }

  protected irATienda(): void {
    void this.router.navigate(['/tienda']);
  }
}
