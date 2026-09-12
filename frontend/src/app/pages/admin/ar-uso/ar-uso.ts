import { DatePipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../../environments/environment';

interface UsoArPrendaItem {
  id: number;
  usuario_id: number;
  usuario_nombre: string;
  usuario_email: string;
  producto_id: number;
  producto_nombre: string;
  modo: string;
  fecha: string;
}

interface UsoArPrendaPage {
  items: UsoArPrendaItem[];
  total: number;
  page: number;
  page_size: number;
}

@Component({
  selector: 'app-admin-ar-uso',
  imports: [DatePipe],
  templateUrl: './ar-uso.html',
  styleUrl: './ar-uso.scss',
})
export class AdminArUso implements OnInit {
  private readonly http = inject(HttpClient);

  protected readonly items = signal<UsoArPrendaItem[]>([]);
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

      const res = await firstValueFrom(this.http.get<UsoArPrendaPage>(`${environment.apiUrl}/ar-uso`, { params }));
      this.items.set(res.items);
      this.total.set(res.total);
    } catch {
      this.error.set('No se pudo cargar el registro de uso del probador.');
    } finally {
      this.loading.set(false);
    }
  }
}
