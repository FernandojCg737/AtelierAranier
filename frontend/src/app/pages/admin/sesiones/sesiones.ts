import { HttpClient } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../../environments/environment';

interface UsuarioActivo {
  id: number;
  nombre: string;
  email: string;
  telefono: string | null;
  tipo: string;
  rol: string | null;
}

@Component({
  selector: 'app-admin-sesiones',
  imports: [],
  templateUrl: './sesiones.html',
  styleUrl: './sesiones.scss',
})
export class AdminSesiones implements OnInit {
  private readonly http = inject(HttpClient);

  protected readonly items = signal<UsuarioActivo[]>([]);
  protected readonly loading = signal(false);
  protected readonly error = signal('');

  ngOnInit(): void {
    this.load();
  }

  protected refrescar(): void {
    this.load();
  }

  private async load(): Promise<void> {
    this.loading.set(true);
    this.error.set('');
    try {
      const res = await firstValueFrom(this.http.get<UsuarioActivo[]>(`${environment.apiUrl}/sesiones/activas`));
      this.items.set(res);
    } catch {
      this.error.set('No se pudo cargar las sesiones activas.');
    } finally {
      this.loading.set(false);
    }
  }
}
