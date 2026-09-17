import { HttpClient } from '@angular/common/http';
import { Component, effect, inject, input, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Product } from '../../data/products';
import { CatalogoPublico, isAgotado } from '../../services/catalogo-publico';

interface RelacionadoApi {
  producto_id: number;
  producto_nombre: string;
  razon: string;
}

interface ProductoRelacionado extends Product {
  razon: string;
}

// CU18 extendido: "Tambien te puede interesar", en el detalle de producto
// -- a diferencia de <app-recomendaciones> (que es personalizado segun el
// historial de compras de UN cliente y solo aparece con sesion iniciada),
// esto se arma por PRODUCTO (que otros productos vieron juntos los
// clientes que pasaron por este mismo, con IA solo para la razon) y se
// muestra a cualquier visitante, tenga sesion o no -- mismo criterio que
// "quienes vieron esto tambien vieron" en un e-commerce real.
@Component({
  selector: 'app-relacionados',
  imports: [RouterLink],
  templateUrl: './relacionados.html',
  styleUrl: './relacionados.scss',
})
export class Relacionados {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly catalogo = inject(CatalogoPublico);

  readonly productoId = input.required<string>();

  protected readonly isAgotado = isAgotado;
  private readonly relacionados = signal<RelacionadoApi[]>([]);

  protected readonly productos = signal<ProductoRelacionado[]>([]);

  constructor() {
    // Cada vez que cambia el producto que se esta viendo (navegar de un
    // detalle a otro sin salir de la pagina) se registra la vista nueva y
    // se piden sus relacionados de nuevo.
    effect(() => {
      const id = this.productoId();
      void this.registrarVistaYCargar(id);
    });

    effect(() => {
      const catalogo = this.catalogo.products();
      const lista = this.relacionados();
      this.productos.set(
        lista
          .map((r) => {
            const producto = catalogo.find((p) => Number(p.id) === r.producto_id);
            return producto ? { ...producto, razon: r.razon } : null;
          })
          .filter((p): p is ProductoRelacionado => p !== null),
      );
    });
  }

  private async registrarVistaYCargar(productoId: string): Promise<void> {
    this.relacionados.set([]);
    void this.catalogo.load();
    // La vista es informativa (alimenta la señal de "vistos juntos" a
    // futuro): si falla (sin sesion, red caida) no debe romper la pagina.
    void firstValueFrom(this.http.post(`${environment.apiUrl}/recomendaciones/vista/${productoId}`, {})).catch(
      () => undefined,
    );
    try {
      const res = await firstValueFrom(
        this.http.get<RelacionadoApi[]>(`${environment.apiUrl}/recomendaciones/relacionados/${productoId}`),
      );
      this.relacionados.set(res);
    } catch {
      this.relacionados.set([]);
    }
  }

  protected seleccionar(product: Product): void {
    if (isAgotado(product)) return;
    void this.router.navigate(['/producto', product.id]);
  }
}
