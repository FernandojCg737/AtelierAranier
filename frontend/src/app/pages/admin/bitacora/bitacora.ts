import { DatePipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../../environments/environment';

interface BitacoraItem {
  id: number;
  usuario_id: number;
  usuario_nombre: string;
  usuario_email: string;
  accion: string;
  entidad_afectada: string;
  entidad_id: number | null;
  fecha: string;
  detalle: string | null;
  ip_address: string | null;
}

interface BitacoraPage {
  items: BitacoraItem[];
  total: number;
  page: number;
  page_size: number;
}

@Component({
  selector: 'app-admin-bitacora',
  imports: [DatePipe],
  templateUrl: './bitacora.html',
  styleUrl: './bitacora.scss',
})
export class AdminBitacora implements OnInit {
  private readonly http = inject(HttpClient);

  protected readonly items = signal<BitacoraItem[]>([]);
  protected readonly total = signal(0);
  protected readonly page = signal(1);
  protected readonly pageSize = 20;
  protected readonly buscar = signal('');
  protected readonly loading = signal(false);
  protected readonly error = signal('');

  protected get totalPages(): number {
    return Math.max(1, Math.ceil(this.total() / this.pageSize));
  }

  ngOnInit(): void {
    this.load();
  }

  protected search(): void {
    this.page.set(1);
    this.load();
  }

  protected goToPage(page: number): void {
    if (page < 1 || page > this.totalPages) return;
    this.page.set(page);
    this.load();
  }

  private async load(): Promise<void> {
    this.loading.set(true);
    this.error.set('');
    try {
      const params: Record<string, string> = {
        page: String(this.page()),
        page_size: String(this.pageSize),
      };
      if (this.buscar().trim()) params['buscar'] = this.buscar().trim();

      const res = await firstValueFrom(this.http.get<BitacoraPage>(`${environment.apiUrl}/bitacora`, { params }));
      this.items.set(res.items);
      this.total.set(res.total);
    } catch {
      this.error.set('No se pudo cargar la bitacora.');
    } finally {
      this.loading.set(false);
    }
  }
}
