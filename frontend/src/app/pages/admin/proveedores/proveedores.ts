import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../../environments/environment';

interface Proveedor {
  id: number;
  nombre: string;
  email: string;
  nit: string;
  contacto_nombre: string | null;
  telefono: string | null;
  direccion: string | null;
  estado: string;
  fecha_registro: string;
  metodo_registro: string;
}

@Component({
  selector: 'app-admin-proveedores',
  imports: [],
  templateUrl: './proveedores.html',
  styleUrl: './proveedores.scss',
})
export class AdminProveedores implements OnInit {
  private readonly http = inject(HttpClient);

  protected readonly proveedores = signal<Proveedor[]>([]);
  protected readonly buscar = signal('');
  protected readonly loading = signal(false);
  protected readonly error = signal('');

  protected readonly showCreateForm = signal(false);
  protected readonly cNombre = signal('');
  protected readonly cEmail = signal('');
  protected readonly cNit = signal('');
  protected readonly cContactoNombre = signal('');
  protected readonly cTelefono = signal('');
  protected readonly cDireccion = signal('');
  protected readonly createSaving = signal(false);

  protected readonly editingId = signal<number | null>(null);
  protected readonly eNombre = signal('');
  protected readonly eNit = signal('');
  protected readonly eContactoNombre = signal('');
  protected readonly eTelefono = signal('');
  protected readonly eDireccion = signal('');
  protected readonly eEstado = signal('activo');
  protected readonly editSaving = signal(false);

  ngOnInit(): void {
    this.load();
  }

  protected search(): void {
    this.load();
  }

  protected openCreate(): void {
    this.cNombre.set('');
    this.cEmail.set('');
    this.cNit.set('');
    this.cContactoNombre.set('');
    this.cTelefono.set('');
    this.cDireccion.set('');
    this.error.set('');
    this.showCreateForm.set(true);
  }

  protected closeCreate(): void {
    this.showCreateForm.set(false);
  }

  protected async submitCreate(): Promise<void> {
    if (!this.cNombre() || !this.cEmail() || !this.cNit()) {
      this.error.set('Completa nombre, correo y NIT.');
      return;
    }

    this.error.set('');
    this.createSaving.set(true);
    try {
      await firstValueFrom(
        this.http.post(`${environment.apiUrl}/proveedores`, {
          nombre: this.cNombre(),
          email: this.cEmail(),
          nit: this.cNit(),
          contacto_nombre: this.cContactoNombre() || null,
          telefono: this.cTelefono() || null,
          direccion: this.cDireccion() || null,
        }),
      );
      this.showCreateForm.set(false);
      await this.load();
    } catch (err) {
      this.error.set(this.extractError(err));
    } finally {
      this.createSaving.set(false);
    }
  }

  protected editProveedor(p: Proveedor): void {
    this.editingId.set(p.id);
    this.eNombre.set(p.nombre);
    this.eNit.set(p.nit);
    this.eContactoNombre.set(p.contacto_nombre ?? '');
    this.eTelefono.set(p.telefono ?? '');
    this.eDireccion.set(p.direccion ?? '');
    this.eEstado.set(p.estado);
    this.error.set('');
  }

  protected closeEdit(): void {
    this.editingId.set(null);
  }

  protected async submitEdit(): Promise<void> {
    const id = this.editingId();
    if (!id || !this.eNombre() || !this.eNit()) {
      this.error.set('Completa nombre y NIT.');
      return;
    }

    this.error.set('');
    this.editSaving.set(true);
    try {
      await firstValueFrom(
        this.http.put(`${environment.apiUrl}/proveedores/${id}`, {
          nombre: this.eNombre(),
          nit: this.eNit(),
          contacto_nombre: this.eContactoNombre() || null,
          telefono: this.eTelefono() || null,
          direccion: this.eDireccion() || null,
          estado: this.eEstado(),
        }),
      );
      this.editingId.set(null);
      await this.load();
    } catch (err) {
      this.error.set(this.extractError(err));
    } finally {
      this.editSaving.set(false);
    }
  }

  protected async toggleEstado(p: Proveedor): Promise<void> {
    const nuevoEstado = p.estado === 'activo' ? 'inactivo' : 'activo';
    const accion = nuevoEstado === 'inactivo' ? 'desactivar' : 'activar';
    if (!confirm(`Seguro que queres ${accion} a "${p.nombre}"?`)) return;

    try {
      await firstValueFrom(
        this.http.put(`${environment.apiUrl}/proveedores/${p.id}`, {
          nombre: p.nombre,
          nit: p.nit,
          contacto_nombre: p.contacto_nombre,
          telefono: p.telefono,
          direccion: p.direccion,
          estado: nuevoEstado,
        }),
      );
      await this.load();
    } catch (err) {
      this.error.set(this.extractError(err));
    }
  }

  private async load(): Promise<void> {
    this.loading.set(true);
    this.error.set('');
    try {
      const params: Record<string, string> = {};
      if (this.buscar().trim()) params['buscar'] = this.buscar().trim();

      const res = await firstValueFrom(this.http.get<Proveedor[]>(`${environment.apiUrl}/proveedores`, { params }));
      this.proveedores.set(res);
    } catch {
      this.error.set('No se pudo cargar los proveedores.');
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
