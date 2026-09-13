import { DatePipe, DecimalPipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../../environments/environment';

interface RecomendacionItem {
  id: number;
  cliente_nombre: string;
  cliente_email: string;
  producto_nombre: string;
  score: string;
  origen: string;
  razon: string | null;
  convertido: boolean;
  fecha: string;
}

interface RecomendacionPage {
  resumen: { total_activas: number; convertidas: number; tasa_conversion: number };
  items: RecomendacionItem[];
  total: number;
  page: number;
  page_size: number;
}

const ORIGEN_LABEL: Record<string, string> = {
  compra_conjunta: 'Comprado junto a...',
  similar_categoria: 'Similar a tus compras',
  mas_vendido: 'Mas vendido',
};

// CU18 "Recomendar Prendas por IA": panel de solo lectura -- el ranking lo
// arma un motor de reglas en SQL (compra conjunta / similares / mas
// vendidos) y Gemini redacta la razon de cada una; aca solo se audita a
// quien se le recomendo que, y si esa recomendacion termino en una compra
// real (convertido, marcado solo por un trigger cuando el cliente compra).
@Component({
  selector: 'app-admin-recomendaciones',
  imports: [DatePipe, DecimalPipe],
  templateUrl: './recomendaciones.html',
  styleUrl: './recomendaciones.scss',
})
export class AdminRecomendaciones implements OnInit {
  private readonly http = inject(HttpClient);

  protected readonly resumen = signal<RecomendacionPage['resumen'] | null>(null);
  protected readonly items = signal<RecomendacionItem[]>([]);
  protected readonly total = signal(0);
  protected readonly page = signal(1);
  protected readonly pageSize = 20;
  protected readonly filtroOrigen = signal('');
  protected readonly loading = signal(false);
  protected readonly error = signal('');
  protected readonly origenLabel = ORIGEN_LABEL;

  protected get totalPages(): number {
    return Math.max(1, Math.ceil(this.total() / this.pageSize));
  }

  ngOnInit(): void {
    void this.load();
  }

  protected filtrar(): void {
    this.page.set(1);
    void this.load();
  }

  protected goToPage(page: number): void {
    if (page < 1 || page > this.totalPages) return;
    this.page.set(page);
    void this.load();
  }

  private async load(): Promise<void> {
    this.loading.set(true);
    this.error.set('');
    try {
      const params: Record<string, string> = { page: String(this.page()), page_size: String(this.pageSize) };
      if (this.filtroOrigen()) params['origen'] = this.filtroOrigen();

      const res = await firstValueFrom(
        this.http.get<RecomendacionPage>(`${environment.apiUrl}/recomendaciones`, { params }),
      );
      this.resumen.set(res.resumen);
      this.items.set(res.items);
      this.total.set(res.total);
    } catch {
      this.error.set('No se pudo cargar las recomendaciones.');
    } finally {
      this.loading.set(false);
    }
  }
}
