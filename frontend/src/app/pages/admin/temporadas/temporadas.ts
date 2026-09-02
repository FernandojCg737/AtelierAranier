import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../../environments/environment';

interface Temporada {
  id: number;
  nombre: string;
  fecha_inicio: string;
  fecha_fin: string;
}

interface Coleccion {
  id: number;
  temporada_id: number;
  temporada_nombre: string;
  nombre: string;
  descripcion: string | null;
}

type TopTab = 'temporadas' | 'colecciones';

@Component({
  selector: 'app-admin-temporadas',
  imports: [],
  templateUrl: './temporadas.html',
  styleUrl: './temporadas.scss',
})
export class AdminTemporadas implements OnInit {
  private readonly http = inject(HttpClient);

  protected readonly topTab = signal<TopTab>('temporadas');
  protected readonly loading = signal(false);
  protected readonly error = signal('');

  // ---------- temporadas ----------
  protected readonly temporadas = signal<Temporada[]>([]);
  protected readonly showTemporadaForm = signal(false);
  protected readonly editingTemporadaId = signal<number | null>(null);
  protected readonly tNombre = signal('');
  protected readonly tFechaInicio = signal('');
  protected readonly tFechaFin = signal('');
  protected readonly savingTemporada = signal(false);

  // ---------- colecciones ----------
  protected readonly colecciones = signal<Coleccion[]>([]);
  protected readonly showColeccionForm = signal(false);
  protected readonly editingColeccionId = signal<number | null>(null);
  protected readonly cTemporadaId = signal<number | null>(null);
  protected readonly cNombre = signal('');
  protected readonly cDescripcion = signal('');
  protected readonly savingColeccion = signal(false);

  ngOnInit(): void {
    this.loadTemporadas();
    this.loadColecciones();
  }

  protected setTopTab(tab: TopTab): void {
    this.topTab.set(tab);
  }

  // ---------- temporadas CRUD ----------

  protected openNewTemporada(): void {
    this.editingTemporadaId.set(null);
    this.tNombre.set('');
    this.tFechaInicio.set('');
    this.tFechaFin.set('');
    this.error.set('');
    this.showTemporadaForm.set(true);
  }

  protected editTemporada(t: Temporada): void {
    this.editingTemporadaId.set(t.id);
    this.tNombre.set(t.nombre);
    this.tFechaInicio.set(t.fecha_inicio);
    this.tFechaFin.set(t.fecha_fin);
    this.error.set('');
    this.showTemporadaForm.set(true);
  }

  protected closeTemporadaForm(): void {
    this.showTemporadaForm.set(false);
  }

  protected async submitTemporada(): Promise<void> {
    if (!this.tNombre() || !this.tFechaInicio() || !this.tFechaFin()) {
      this.error.set('Completa nombre, fecha de inicio y fecha de fin.');
      return;
    }

    const payload = {
      nombre: this.tNombre(),
      fecha_inicio: this.tFechaInicio(),
      fecha_fin: this.tFechaFin(),
    };

    this.error.set('');
    this.savingTemporada.set(true);
    try {
      const id = this.editingTemporadaId();
      if (id) {
        await firstValueFrom(this.http.put(`${environment.apiUrl}/temporadas/${id}`, payload));
      } else {
        await firstValueFrom(this.http.post(`${environment.apiUrl}/temporadas`, payload));
      }
      this.showTemporadaForm.set(false);
      await this.loadTemporadas();
    } catch (err) {
      this.error.set(this.extractError(err));
    } finally {
      this.savingTemporada.set(false);
    }
  }

  protected async removeTemporada(t: Temporada): Promise<void> {
    if (!confirm(`Eliminar la temporada "${t.nombre}"?`)) return;
    try {
      await firstValueFrom(this.http.delete(`${environment.apiUrl}/temporadas/${t.id}`));
      await this.loadTemporadas();
    } catch (err) {
      this.error.set(this.extractError(err));
    }
  }

  // ---------- colecciones CRUD ----------

  protected openNewColeccion(): void {
    this.editingColeccionId.set(null);
    this.cTemporadaId.set(this.temporadas()[0]?.id ?? null);
    this.cNombre.set('');
    this.cDescripcion.set('');
    this.error.set('');
    this.showColeccionForm.set(true);
  }

  protected editColeccion(c: Coleccion): void {
    this.editingColeccionId.set(c.id);
    this.cTemporadaId.set(c.temporada_id);
    this.cNombre.set(c.nombre);
    this.cDescripcion.set(c.descripcion ?? '');
    this.error.set('');
    this.showColeccionForm.set(true);
  }

  protected closeColeccionForm(): void {
    this.showColeccionForm.set(false);
  }

  protected async submitColeccion(): Promise<void> {
    if (!this.cTemporadaId() || !this.cNombre()) {
      this.error.set('Completa temporada y nombre.');
      return;
    }

    const payload = {
      temporada_id: this.cTemporadaId(),
      nombre: this.cNombre(),
      descripcion: this.cDescripcion() || null,
    };

    this.error.set('');
    this.savingColeccion.set(true);
    try {
      const id = this.editingColeccionId();
      if (id) {
        await firstValueFrom(this.http.put(`${environment.apiUrl}/colecciones/${id}`, payload));
      } else {
        await firstValueFrom(this.http.post(`${environment.apiUrl}/colecciones`, payload));
      }
      this.showColeccionForm.set(false);
      await this.loadColecciones();
    } catch (err) {
      this.error.set(this.extractError(err));
    } finally {
      this.savingColeccion.set(false);
    }
  }

  protected async removeColeccion(c: Coleccion): Promise<void> {
    if (!confirm(`Eliminar la coleccion "${c.nombre}"?`)) return;
    try {
      await firstValueFrom(this.http.delete(`${environment.apiUrl}/colecciones/${c.id}`));
      await this.loadColecciones();
    } catch (err) {
      this.error.set(this.extractError(err));
    }
  }

  // ---------- carga ----------

  private async loadTemporadas(): Promise<void> {
    this.loading.set(true);
    this.error.set('');
    try {
      const res = await firstValueFrom(this.http.get<Temporada[]>(`${environment.apiUrl}/temporadas`));
      this.temporadas.set(res);
    } catch {
      this.error.set('No se pudo cargar las temporadas.');
    } finally {
      this.loading.set(false);
    }
  }

  private async loadColecciones(): Promise<void> {
    this.loading.set(true);
    this.error.set('');
    try {
      const res = await firstValueFrom(this.http.get<Coleccion[]>(`${environment.apiUrl}/colecciones`));
      this.colecciones.set(res);
    } catch {
      this.error.set('No se pudo cargar las colecciones.');
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
