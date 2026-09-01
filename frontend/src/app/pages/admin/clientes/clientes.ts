import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../../environments/environment';

interface Cliente {
  id: number;
  nombre: string;
  email: string;
  telefono: string | null;
  direccion: string | null;
  estado: string;
  fecha_registro: string;
  metodo_registro: string;
}

@Component({
  selector: 'app-admin-clientes',
  imports: [],
  templateUrl: './clientes.html',
  styleUrl: './clientes.scss',
})
export class AdminClientes implements OnInit {
  private readonly http = inject(HttpClient);

  protected readonly clientes = signal<Cliente[]>([]);
  protected readonly buscar = signal('');
  protected readonly loading = signal(false);
  protected readonly error = signal('');

  protected readonly showCreateForm = signal(false);
  protected readonly cNombre = signal('');
  protected readonly cEmail = signal('');
  protected readonly cTelefono = signal('');
  protected readonly cDireccion = signal('');
  protected readonly createSaving = signal(false);

  protected readonly editingId = signal<number | null>(null);
  protected readonly eNombre = signal('');
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
    this.cTelefono.set('');
    this.cDireccion.set('');
    this.error.set('');
    this.showCreateForm.set(true);
  }

  protected closeCreate(): void {
    this.showCreateForm.set(false);
  }

  protected async submitCreate(): Promise<void> {
    if (!this.cNombre() || !this.cEmail()) {
      this.error.set('Completa nombre y correo.');
      return;
    }

    this.error.set('');
    this.createSaving.set(true);
    try {
      await firstValueFrom(
        this.http.post(`${environment.apiUrl}/clientes`, {
          nombre: this.cNombre(),
          email: this.cEmail(),
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

  protected editCliente(c: Cliente): void {
    this.editingId.set(c.id);
    this.eNombre.set(c.nombre);
    this.eTelefono.set(c.telefono ?? '');
    this.eDireccion.set(c.direccion ?? '');
    this.eEstado.set(c.estado);
    this.error.set('');
  }

  protected closeEdit(): void {
    this.editingId.set(null);
  }

  protected async submitEdit(): Promise<void> {
    const id = this.editingId();
    if (!id || !this.eNombre()) {
      this.error.set('El nombre no puede estar vacio.');
      return;
    }

    this.error.set('');
    this.editSaving.set(true);
    try {
      await firstValueFrom(
        this.http.put(`${environment.apiUrl}/clientes/${id}`, {
          nombre: this.eNombre(),
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

  protected async toggleEstado(c: Cliente): Promise<void> {
    const nuevoEstado = c.estado === 'activo' ? 'inactivo' : 'activo';
    const accion = nuevoEstado === 'inactivo' ? 'desactivar' : 'activar';
    if (!confirm(`Seguro que queres ${accion} a "${c.nombre}"?`)) return;

    try {
      await firstValueFrom(
        this.http.put(`${environment.apiUrl}/clientes/${c.id}`, {
          nombre: c.nombre,
          telefono: c.telefono,
          direccion: c.direccion,
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

      const res = await firstValueFrom(this.http.get<Cliente[]>(`${environment.apiUrl}/clientes`, { params }));
      this.clientes.set(res);
    } catch {
      this.error.set('No se pudo cargar los clientes.');
    } finally {
      this.loading.set(false);
    }
  }

  protected metodoLabel(metodo: string): string {
    const etiquetas: Record<string, string> = {
      email: 'Email',
      google: 'Google',
      admin: 'Admin',
      sistema: 'Sistema',
    };
    return etiquetas[metodo] ?? metodo;
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
