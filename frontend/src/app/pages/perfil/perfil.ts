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
