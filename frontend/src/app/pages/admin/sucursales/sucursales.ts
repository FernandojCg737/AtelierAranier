import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../../environments/environment';

interface Sucursal {
  id: number;
  nombre: string;
  ciudad_id: number;
  ciudad_nombre: string;
  departamento: string;
  direccion: string;
  horario_atencion: string | null;
  telefono: string | null;
  estado: string;
  fecha_creacion: string;
}

@Component({
  selector: 'app-admin-sucursales',
  imports: [],
  templateUrl: './sucursales.html',
  styleUrl: './sucursales.scss',
})
export class AdminSucursales implements OnInit {
  private readonly http = inject(HttpClient);

  protected readonly sucursales = signal<Sucursal[]>([]);
  protected readonly loading = signal(false);
  protected readonly error = signal('');

  protected readonly showForm = signal(false);
  protected readonly editingId = signal<number | null>(null);
  protected readonly sNombre = signal('');
  protected readonly sCiudad = signal('');
  protected readonly sDepartamento = signal('');
  protected readonly sDireccion = signal('');
  protected readonly sHorario = signal('');
  protected readonly sTelefono = signal('');
  protected readonly sEstado = signal('activa');
  protected readonly saving = signal(false);

  ngOnInit(): void {
    this.load();
  }

  protected openNew(): void {
    this.editingId.set(null);
    this.sNombre.set('');
    this.sCiudad.set('');
    this.sDepartamento.set('');
    this.sDireccion.set('');
    this.sHorario.set('');
    this.sTelefono.set('');
    this.sEstado.set('activa');
    this.error.set('');
    this.showForm.set(true);
  }

  protected edit(s: Sucursal): void {
    this.editingId.set(s.id);
    this.sNombre.set(s.nombre);
    this.sCiudad.set(s.ciudad_nombre);
    this.sDepartamento.set(s.departamento);
    this.sDireccion.set(s.direccion);
    this.sHorario.set(s.horario_atencion ?? '');
    this.sTelefono.set(s.telefono ?? '');
    this.sEstado.set(s.estado);
    this.error.set('');
    this.showForm.set(true);
  }

  protected closeForm(): void {
    this.showForm.set(false);
  }

  protected async submit(): Promise<void> {
    if (!this.sNombre() || !this.sCiudad() || !this.sDepartamento() || !this.sDireccion()) {
      this.error.set('Completa nombre, ciudad, departamento y direccion.');
      return;
    }

    const payload = {
      nombre: this.sNombre(),
      ciudad_nombre: this.sCiudad(),
      departamento: this.sDepartamento(),
      direccion: this.sDireccion(),
      horario_atencion: this.sHorario() || null,
      telefono: this.sTelefono() || null,
      estado: this.sEstado(),
    };

    this.error.set('');
    this.saving.set(true);
    try {
      const id = this.editingId();
      if (id) {
        await firstValueFrom(this.http.put(`${environment.apiUrl}/sucursales/${id}`, payload));
      } else {
        await firstValueFrom(this.http.post(`${environment.apiUrl}/sucursales`, payload));
      }
      this.showForm.set(false);
      await this.load();
    } catch (err) {
      this.error.set(this.extractError(err));
    } finally {
      this.saving.set(false);
    }
  }

  protected async remove(s: Sucursal): Promise<void> {
    if (!confirm(`Eliminar la sucursal "${s.nombre}"?`)) return;
    try {
      await firstValueFrom(this.http.delete(`${environment.apiUrl}/sucursales/${s.id}`));
      await this.load();
    } catch (err) {
      this.error.set(this.extractError(err));
    }
  }

  private async load(): Promise<void> {
    this.loading.set(true);
    this.error.set('');
    try {
      const res = await firstValueFrom(this.http.get<Sucursal[]>(`${environment.apiUrl}/sucursales`));
      this.sucursales.set(res);
    } catch {
      this.error.set('No se pudo cargar las sucursales.');
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
