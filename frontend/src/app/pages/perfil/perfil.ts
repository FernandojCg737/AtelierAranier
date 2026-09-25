import { DatePipe } from '@angular/common';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Auth } from '../../services/auth';
import { Notificaciones } from '../../services/notificaciones';
import { checkPassword, isPasswordValid } from '../../utils/password';

interface DetalleReservaItem {
  id: number;
  producto_nombre: string;
  talla_codigo: string;
  color_nombre: string;
  cantidad: number;
}

interface ReservaItem {
  id: number;
  sucursal_nombre: string;
  horario_atencion: string;
  estado: string;
  detalles: DetalleReservaItem[];
}

interface DetalleVentaItem {
  id: number;
  producto_nombre: string;
  talla_codigo: string;
  color_nombre: string;
  cantidad: number;
  precio_unitario: string;
}

interface VentaItem {
  id: number;
  tipo: string;
  sucursal_nombre: string;
  fecha: string;
  total: string;
  estado: string;
  metodo_pago: string;
  estado_pago: string;
  calificacion_estrellas: number | null;
  calificacion_comentario: string | null;
  detalles: DetalleVentaItem[];
  tiene_devolucion?: boolean;
  estado_devolucion?: string | null;
  monto_devolucion?: string | null;
  puede_devolver?: boolean;
  horas_restantes_devolucion?: number | null;
}

interface ItemDevolucionSeleccion {
  item_linea_id: number;
  producto_nombre: string;
  talla_codigo: string;
  color_nombre: string;
  cantidad_comprada: number;
  cantidad_devuelta: number;
  precio_unitario: number;
  seleccionado: boolean;
}

type Tab = 'resumen' | 'reservas' | 'compras' | 'pagos' | 'notificaciones' | 'datos' | 'seguridad';

const METODO_LABEL: Record<string, string> = {
  paypal: 'PayPal / Tarjeta',
  qr: 'QR (transferencia)',
  efectivo: 'Efectivo en sucursal',
};

@Component({
  selector: 'app-perfil',
  imports: [RouterLink, DatePipe],
  templateUrl: './perfil.html',
  styleUrl: './perfil.scss',
})
export class Perfil implements OnInit {
  protected readonly auth = inject(Auth);
  private readonly http = inject(HttpClient);
  private readonly route = inject(ActivatedRoute);
  protected readonly notificaciones = inject(Notificaciones);

  protected readonly isCliente = computed(() => this.auth.currentUser()?.tipo === 'cliente');
  protected readonly metodoLabel = METODO_LABEL;

  protected readonly tab = signal<Tab>('resumen');

  // ---------- Reservas y compras (solo clientes) ----------
  protected readonly reservas = signal<ReservaItem[]>([]);
  protected readonly compras = signal<VentaItem[]>([]);
  protected readonly cargandoReservas = signal(false);
  protected readonly cargandoCompras = signal(false);
  protected readonly procesandoReserva = signal<number | null>(null);

  protected readonly reservasActivas = computed(
    () => this.reservas().filter((r) => r.estado === 'pendiente' || r.estado === 'confirmada').length,
  );
  protected readonly totalGastado = computed(() =>
    this.compras()
      .filter((v) => v.estado_pago === 'completado')
      .reduce((sum, v) => sum + Number(v.total), 0)
      .toFixed(2),
  );
  protected readonly metodosUsados = computed(() => {
    const conteo = new Map<string, number>();
    for (const v of this.compras()) {
      if (v.estado_pago !== 'completado') continue;
      conteo.set(v.metodo_pago, (conteo.get(v.metodo_pago) ?? 0) + 1);
    }
    return Array.from(conteo.entries()).map(([metodo, veces]) => ({ metodo, veces }));
  });

  // ---------- Datos personales ----------
  protected readonly nombre = signal(this.auth.currentUser()?.nombre ?? '');
  protected readonly telefono = signal(this.auth.currentUser()?.telefono ?? '');
  protected readonly direccion = signal(this.auth.currentUser()?.direccion ?? '');
  protected readonly profileError = signal('');
  protected readonly profileSuccess = signal('');
  protected readonly profileSaving = signal(false);

  // ---------- Contrasena ----------
  protected readonly passwordActual = signal('');
  protected readonly passwordNueva = signal('');
  protected readonly passwordConfirmar = signal('');
  protected readonly showActual = signal(false);
  protected readonly showNueva = signal(false);
  protected readonly showConfirmar = signal(false);
  protected readonly passwordTouched = signal(false);
  protected readonly passwordChecks = computed(() => checkPassword(this.passwordNueva()));
  protected readonly passwordError = signal('');
  protected readonly passwordSuccess = signal('');
  protected readonly passwordSaving = signal(false);

  ngOnInit(): void {
    if (this.isCliente()) {
      void this.cargarReservas();
      void this.cargarCompras();
      void this.notificaciones.cargar();
    }

    const tabParam = this.route.snapshot.queryParamMap.get('tab') as Tab | null;
    if (tabParam) this.tab.set(tabParam);
  }

  protected setTab(t: Tab): void {
    this.tab.set(t);
  }

  private async cargarReservas(): Promise<void> {
    this.cargandoReservas.set(true);
    try {
      const res = await firstValueFrom(this.http.get<ReservaItem[]>(`${environment.apiUrl}/reservas/mias`));
      this.reservas.set(res);
    } catch {
      this.reservas.set([]);
    } finally {
      this.cargandoReservas.set(false);
    }
  }

  private async cargarCompras(): Promise<void> {
    this.cargandoCompras.set(true);
    try {
      const res = await firstValueFrom(this.http.get<VentaItem[]>(`${environment.apiUrl}/ventas/mias`));
      this.compras.set(res);
    } catch {
      this.compras.set([]);
    } finally {
      this.cargandoCompras.set(false);
    }
  }

  // ---------- Calificar una compra (CU20) ----------
  protected readonly calificandoVentaId = signal<number | null>(null);
  protected readonly estrellasSeleccionadas = signal(0);
  protected readonly comentarioCalificacion = signal('');
  protected readonly guardandoCalificacion = signal(false);
  protected readonly errorCalificacion = signal('');

  protected abrirCalificar(venta: VentaItem): void {
    this.calificandoVentaId.set(venta.id);
    this.estrellasSeleccionadas.set(0);
    this.comentarioCalificacion.set('');
    this.errorCalificacion.set('');
  }

  protected cerrarCalificar(): void {
    this.calificandoVentaId.set(null);
  }

  protected async enviarCalificacion(venta: VentaItem): Promise<void> {
    const estrellas = this.estrellasSeleccionadas();
    if (estrellas < 1) return;

    this.guardandoCalificacion.set(true);
    this.errorCalificacion.set('');
    try {
      await firstValueFrom(
        this.http.post(`${environment.apiUrl}/calificaciones/venta/${venta.id}`, {
          estrellas,
          comentario: this.comentarioCalificacion().trim() || null,
        }),
      );
      this.compras.update((items) =>
        items.map((v) =>
          v.id === venta.id
            ? { ...v, calificacion_estrellas: estrellas, calificacion_comentario: this.comentarioCalificacion().trim() || null }
            : v,
        ),
      );
      this.calificandoVentaId.set(null);
    } catch (err) {
      this.errorCalificacion.set(this.extractError(err));
    } finally {
      this.guardandoCalificacion.set(false);
    }
  }

  // ---------- Solicitar Devolucion (CU11 - Cliente, 24 horas) ----------
  protected readonly devolviendoVenta = signal<VentaItem | null>(null);
  protected readonly itemsDevolucion = signal<ItemDevolucionSeleccion[]>([]);
  protected readonly motivoDevolucion = signal<'defecto' | 'talla_incorrecta' | 'insatisfaccion' | 'otro'>('defecto');
  protected readonly metodoReembolso = signal<'mismo_medio' | 'credito_tienda' | 'efectivo'>('mismo_medio');
  protected readonly observacionesDevolucion = signal('');
  protected readonly guardandoDevolucion = signal(false);
  protected readonly errorDevolucion = signal('');
  protected readonly exitoDevolucion = signal('');

  protected readonly montoReembolsoTotal = computed(() => {
    return this.itemsDevolucion()
      .filter((i) => i.seleccionado)
      .reduce((sum, i) => sum + i.precio_unitario * i.cantidad_devuelta, 0)
      .toFixed(2);
  });

  protected readonly tieneItemsSeleccionados = computed(() => {
    return this.itemsDevolucion().some((i) => i.seleccionado && i.cantidad_devuelta > 0);
  });

  protected estaEnPlazo24h(v: VentaItem): boolean {
    if (v.puede_devolver !== undefined) {
      return v.puede_devolver;
    }
    const fecha = new Date(v.fecha).getTime();
    const diffHoras = (Date.now() - fecha) / (1000 * 60 * 60);
    return diffHoras <= 24 && v.estado_pago === 'completado' && !v.tiene_devolucion;
  }

  protected horasRestantes(v: VentaItem): string {
    if (v.horas_restantes_devolucion !== null && v.horas_restantes_devolucion !== undefined) {
      const horas = Math.floor(v.horas_restantes_devolucion);
      const minutos = Math.round((v.horas_restantes_devolucion - horas) * 60);
      return `${horas}h ${minutos}m`;
    }
    const fecha = new Date(v.fecha).getTime();
    const diffMs = fecha + 24 * 60 * 60 * 1000 - Date.now();
    if (diffMs <= 0) return '0h';
    const horas = Math.floor(diffMs / (1000 * 60 * 60));
    const minutos = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    return `${horas}h ${minutos}m`;
  }

  protected abrirModalDevolucion(v: VentaItem): void {
    this.devolviendoVenta.set(v);
    this.errorDevolucion.set('');
    this.exitoDevolucion.set('');
    this.observacionesDevolucion.set('');
    this.motivoDevolucion.set('defecto');
    this.metodoReembolso.set('mismo_medio');
    this.itemsDevolucion.set(
      (v.detalles || []).map((d) => ({
        item_linea_id: d.id,
        producto_nombre: d.producto_nombre,
        talla_codigo: d.talla_codigo,
        color_nombre: d.color_nombre,
        cantidad_comprada: d.cantidad,
        cantidad_devuelta: d.cantidad,
        precio_unitario: Number(d.precio_unitario) || 0,
        seleccionado: true,
      })),
    );
  }

  protected cerrarModalDevolucion(): void {
    this.devolviendoVenta.set(null);
  }

  protected toggleItemDevolucion(index: number): void {
    this.itemsDevolucion.update((items) =>
      items.map((item, idx) => (idx === index ? { ...item, seleccionado: !item.seleccionado } : item)),
    );
  }

  protected setCantidadDevolucion(index: number, cantidad: number): void {
    this.itemsDevolucion.update((items) =>
      items.map((item, idx) => {
        if (idx !== index) return item;
        const cant = Math.max(1, Math.min(item.cantidad_comprada, cantidad));
        return { ...item, cantidad_devuelta: cant };
      }),
    );
  }

  protected async enviarSolicitudDevolucion(): Promise<void> {
    const venta = this.devolviendoVenta();
    if (!venta) return;

    const itemsAEnviar = this.itemsDevolucion()
      .filter((i) => i.seleccionado && i.cantidad_devuelta > 0)
      .map((i) => ({
        item_linea_id: i.item_linea_id,
        cantidad_devuelta: i.cantidad_devuelta,
      }));

    if (itemsAEnviar.length === 0) {
      this.errorDevolucion.set('Debes seleccionar al menos un producto a devolver.');
      return;
    }

    const todosCompletos = this.itemsDevolucion().every(
      (i) => i.seleccionado && i.cantidad_devuelta === i.cantidad_comprada,
    );
    const tipo = todosCompletos ? 'total' : 'parcial';

    this.guardandoDevolucion.set(true);
    this.errorDevolucion.set('');

    try {
      await firstValueFrom(
        this.http.post(`${environment.apiUrl}/devoluciones/solicitar/${venta.id}`, {
          motivo: this.motivoDevolucion(),
          tipo,
          metodo_reembolso: this.metodoReembolso(),
          observaciones: this.observacionesDevolucion() || null,
          items: itemsAEnviar,
        }),
      );

      this.exitoDevolucion.set('Tu solicitud de devolución fue enviada con éxito. Nuestro personal la revisará.');

      // Actualizar estado reactivamente en compras()
      this.compras.update((items) =>
        items.map((it) =>
          it.id === venta.id
            ? {
                ...it,
                tiene_devolucion: true,
                estado_devolucion: 'solicitada',
                puede_devolver: false,
              }
            : it,
        ),
      );

      setTimeout(() => {
        this.cerrarModalDevolucion();
      }, 1800);
    } catch (err) {
      this.errorDevolucion.set(this.extractError(err));
    } finally {
      this.guardandoDevolucion.set(false);
    }
  }

  protected async cancelarReserva(r: ReservaItem): Promise<void> {
    if (!confirm(`Cancelar tu reserva #${r.id}?`)) return;
    this.procesandoReserva.set(r.id);
    try {
      await firstValueFrom(this.http.post(`${environment.apiUrl}/reservas/${r.id}/cancelar`, {}));
      await this.cargarReservas();
    } catch {
      // el error se ve reflejado simplemente en que la reserva no cambia de estado
    } finally {
      this.procesandoReserva.set(null);
    }
  }

  protected async submitProfile(): Promise<void> {
    if (!this.nombre()) {
      this.profileError.set('El nombre no puede estar vacio.');
      return;
    }

    this.profileError.set('');
    this.profileSuccess.set('');
    this.profileSaving.set(true);
    try {
      await this.auth.updateProfile({
        nombre: this.nombre(),
        telefono: this.telefono() || null,
        direccion: this.direccion() || null,
      });
      this.profileSuccess.set('Tus datos se actualizaron correctamente.');
    } catch (err) {
      this.profileError.set(this.extractError(err));
    } finally {
      this.profileSaving.set(false);
    }
  }

  protected async submitPassword(): Promise<void> {
    this.passwordTouched.set(true);
    this.passwordSuccess.set('');

    if (!this.passwordActual()) {
      this.passwordError.set('Ingresa tu contrasena actual.');
      return;
    }
    if (!isPasswordValid(this.passwordNueva())) {
      this.passwordError.set('La nueva contrasena no cumple los requisitos minimos.');
      return;
    }
    if (this.passwordNueva() !== this.passwordConfirmar()) {
      this.passwordError.set('Las contrasenas no coinciden.');
      return;
    }

    this.passwordError.set('');
    this.passwordSaving.set(true);
    try {
      await this.auth.changePassword(this.passwordActual(), this.passwordNueva());
      this.passwordSuccess.set('Tu contrasena se actualizo. Te avisamos por correo.');
      this.passwordActual.set('');
      this.passwordNueva.set('');
      this.passwordConfirmar.set('');
      this.passwordTouched.set(false);
    } catch (err) {
      this.passwordError.set(this.extractError(err));
    } finally {
      this.passwordSaving.set(false);
    }
  }

  private extractError(err: unknown): string {
    if (err instanceof HttpErrorResponse) {
      const detail = err.error?.detail;
      if (typeof detail === 'string') return detail;
      if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
      if (err.status === 0) return 'No pudimos conectar con el servidor.';
    }
    return 'Ocurrio un error inesperado.';
  }
}
