import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { ADMIN_MENU } from '../admin-menu';

interface Sucursal {
  id: number;
  nombre: string;
}

interface Rol {
  id: number;
  nombre: string;
  descripcion: string | null;
  permisos: string[];
}

interface Permiso {
  id: number;
  nombre: string;
  descripcion: string | null;
}

interface Empleado {
  id: number;
  nombre: string;
  email: string;
  tipo: string;
  estado: string;
  fecha_registro: string;
  metodo_registro: string;
  sucursal_id: number | null;
  sucursal_nombre: string | null;
  rol_id: number | null;
  rol_nombre: string | null;
}

type TipoEmpleado = 'administrador' | 'encargado_sucursal' | 'cajero';
type TopTab = 'usuarios' | 'permisos';

const TIPO_LABEL: Record<TipoEmpleado, string> = {
  administrador: 'Administradores',
  encargado_sucursal: 'Encargados de Sucursal',
  cajero: 'Cajeros',
};

const TIPO_A_ROL: Record<TipoEmpleado, string> = {
  administrador: 'Administrador',
  encargado_sucursal: 'Encargado de Sucursal',
  cajero: 'Cajero',
};

@Component({
  selector: 'app-admin-usuarios',
  imports: [RouterLink],
  templateUrl: './usuarios.html',
  styleUrl: './usuarios.scss',
})
export class AdminUsuarios implements OnInit {
  private readonly http = inject(HttpClient);

  protected readonly menu = ADMIN_MENU;
  protected readonly tipoLabel = TIPO_LABEL;

  protected readonly topTab = signal<TopTab>('usuarios');
  protected readonly tipoActivo = signal<TipoEmpleado>('administrador');

  protected readonly empleados = signal<Empleado[]>([]);
  protected readonly sucursales = signal<Sucursal[]>([]);
  protected readonly roles = signal<Rol[]>([]);
  protected readonly permisosDisponibles = signal<Permiso[]>([]);
  protected readonly buscar = signal('');
  protected readonly loading = signal(false);
  protected readonly error = signal('');

  protected readonly requiereSucursal = computed(() => this.tipoActivo() !== 'administrador');

  protected readonly rolesEmpleado = computed(() =>
    this.roles().filter((r) => r.nombre === TIPO_A_ROL[this.tipoActivo()]),
  );

  protected readonly permisoIdPorCodigo = computed(() => {
    const mapa = new Map<string, number>();
    for (const p of this.permisosDisponibles()) mapa.set(p.nombre, p.id);
    return mapa;
  });

  // formulario crear/editar empleado
  protected readonly showForm = signal(false);
  protected readonly editingId = signal<number | null>(null);
  protected readonly fNombre = signal('');
  protected readonly fEmail = signal('');
  protected readonly fSucursalId = signal<number | null>(null);
  protected readonly fRolId = signal<number | null>(null);
  protected readonly fEstado = signal('activo');
  protected readonly saving = signal(false);

  // matriz de permisos
  protected readonly rolSeleccionadoId = signal<number | null>(null);
  protected readonly permisosSeleccionados = signal<Set<number>>(new Set());
  protected readonly permisosSaving = signal(false);
  protected readonly permisosError = signal('');
  protected readonly permisosSuccess = signal('');

  protected readonly rolSeleccionado = computed(
    () => this.roles().find((r) => r.id === this.rolSeleccionadoId()) ?? null,
  );

  ngOnInit(): void {
    this.loadCommon();
  }

  protected setTopTab(tab: TopTab): void {
    this.topTab.set(tab);
    if (tab === 'permisos' && this.rolSeleccionadoId() === null && this.roles().length) {
      this.selectRol(this.roles()[0].id);
    }
  }

  protected setTipoActivo(tipo: TipoEmpleado): void {
    this.tipoActivo.set(tipo);
    this.buscar.set('');
    this.loadEmpleados();
  }

  protected search(): void {
    this.loadEmpleados();
  }

  protected tableColspan(): number {
    return this.requiereSucursal() ? 7 : 6;
  }

  // ---------- empleados CRUD ----------

  protected openCreate(): void {
    this.editingId.set(null);
    this.fNombre.set('');
    this.fEmail.set('');
    this.fSucursalId.set(this.sucursales()[0]?.id ?? null);
    this.fRolId.set(this.rolesEmpleado()[0]?.id ?? null);
    this.fEstado.set('activo');
    this.error.set('');
    this.showForm.set(true);
  }

  protected editEmpleado(e: Empleado): void {
    this.editingId.set(e.id);
    this.fNombre.set(e.nombre);
    this.fEmail.set(e.email);
    this.fSucursalId.set(e.sucursal_id);
    this.fRolId.set(e.rol_id);
    this.fEstado.set(e.estado);
    this.error.set('');
    this.showForm.set(true);
  }

  protected closeForm(): void {
    this.showForm.set(false);
  }

  protected async submitForm(): Promise<void> {
    if (!this.fNombre() || (!this.editingId() && !this.fEmail())) {
      this.error.set('Completa nombre y correo.');
      return;
    }
    if (this.requiereSucursal() && !this.fSucursalId()) {
      this.error.set('Selecciona una sucursal para este cargo.');
      return;
    }

    this.error.set('');
    this.saving.set(true);
    try {
      const id = this.editingId();
      if (id) {
        await firstValueFrom(
          this.http.put(`${environment.apiUrl}/empleados/${id}`, {
            nombre: this.fNombre(),
            sucursal_id: this.requiereSucursal() ? this.fSucursalId() : null,
            rol_id: this.fRolId(),
            estado: this.fEstado(),
          }),
        );
      } else {
        await firstValueFrom(
          this.http.post(`${environment.apiUrl}/empleados`, {
            nombre: this.fNombre(),
            email: this.fEmail(),
            tipo: this.tipoActivo(),
            sucursal_id: this.requiereSucursal() ? this.fSucursalId() : null,
            rol_id: this.fRolId(),
          }),
        );
      }
      this.showForm.set(false);
      await this.loadEmpleados();
    } catch (err) {
      this.error.set(this.extractError(err));
    } finally {
      this.saving.set(false);
    }
  }

  protected async toggleEstado(e: Empleado): Promise<void> {
    const nuevoEstado = e.estado === 'activo' ? 'inactivo' : 'activo';
    const accion = nuevoEstado === 'inactivo' ? 'desactivar' : 'activar';
    if (!confirm(`Seguro que queres ${accion} a "${e.nombre}"?`)) return;

    try {
      await firstValueFrom(
        this.http.put(`${environment.apiUrl}/empleados/${e.id}`, {
          nombre: e.nombre,
          sucursal_id: e.sucursal_id,
          rol_id: e.rol_id,
          estado: nuevoEstado,
        }),
      );
      await this.loadEmpleados();
    } catch (err) {
      this.error.set(this.extractError(err));
    }
  }

  // ---------- permisos ----------

  protected selectRol(rolId: number): void {
    this.rolSeleccionadoId.set(rolId);
    this.permisosError.set('');
    this.permisosSuccess.set('');
    const rol = this.roles().find((r) => r.id === rolId);
    const codigos = new Set(rol?.permisos ?? []);
    const ids = new Set(
      this.permisosDisponibles()
        .filter((p) => codigos.has(p.nombre))
        .map((p) => p.id),
    );
    this.permisosSeleccionados.set(ids);
  }

  protected permisoIdForCode(code: string): number {
    return this.permisoIdPorCodigo().get(code) ?? -1;
  }

  protected togglePermiso(permisoId: number): void {
    if (permisoId === -1 || this.rolSeleccionado()?.nombre === 'Administrador') return;
    const actuales = new Set(this.permisosSeleccionados());
    if (actuales.has(permisoId)) actuales.delete(permisoId);
    else actuales.add(permisoId);
    this.permisosSeleccionados.set(actuales);
  }

  protected async guardarPermisos(): Promise<void> {
    const rol = this.rolSeleccionado();
    if (!rol) return;

    this.permisosError.set('');
    this.permisosSuccess.set('');
    this.permisosSaving.set(true);
    try {
      const rolActualizado = await firstValueFrom(
        this.http.put<Rol>(`${environment.apiUrl}/roles/${rol.id}/permisos`, {
          permiso_ids: Array.from(this.permisosSeleccionados()),
        }),
      );
      this.roles.update((lista) => lista.map((r) => (r.id === rolActualizado.id ? rolActualizado : r)));
      this.permisosSuccess.set('Permisos actualizados.');
    } catch (err) {
      this.permisosError.set(this.extractError(err));
    } finally {
      this.permisosSaving.set(false);
    }
  }

  // ---------- carga ----------

  private async loadCommon(): Promise<void> {
    this.loading.set(true);
    this.error.set('');
    try {
      const [roles, permisos] = await Promise.all([
        firstValueFrom(this.http.get<Rol[]>(`${environment.apiUrl}/roles`)),
        firstValueFrom(this.http.get<Permiso[]>(`${environment.apiUrl}/roles/permisos`)),
      ]);
      this.roles.set(roles);
      this.permisosDisponibles.set(permisos);
    } catch {
      this.error.set('No se pudo cargar la informacion de roles y permisos.');
    }

    try {
      const sucursales = await firstValueFrom(this.http.get<Sucursal[]>(`${environment.apiUrl}/sucursales`));
      this.sucursales.set(sucursales);
    } catch {
      // si el usuario no tiene CU04, el desplegable de sucursal queda vacio
    }

    await this.loadEmpleados();
    this.loading.set(false);
  }

  private async loadEmpleados(): Promise<void> {
    this.loading.set(true);
    this.error.set('');
    try {
      const params: Record<string, string> = { tipo: this.tipoActivo() };
      if (this.buscar().trim()) params['buscar'] = this.buscar().trim();
      const res = await firstValueFrom(this.http.get<Empleado[]>(`${environment.apiUrl}/empleados`, { params }));
      this.empleados.set(res);
    } catch {
      this.error.set('No se pudo cargar los empleados.');
    } finally {
      this.loading.set(false);
    }
  }

  private extractError(err: unknown): string {
    if (err instanceof HttpErrorResponse) {
      const detail = err.error?.detail;
      if (typeof detail === 'string') return detail;
      if (err.status === 0) return 'No pudimos conectar con el servidor.';
    }
    return 'Ocurrio un error inesperado.';
  }
}
