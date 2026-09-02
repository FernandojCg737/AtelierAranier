import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../../environments/environment';

interface Sucursal {
  id: number;
  nombre: string;
}

interface Variante {
  id: number;
  talla_codigo: string;
  color_nombre: string;
  cantidad: number;
}

interface ProductoCatalogo {
  id: number;
  nombre: string;
  marca_nombre: string;
  categoria_nombre: string;
  precio: string;
  imagen_url: string | null;
  cantidad_total: number;
  disponible: boolean;
  variantes: Variante[];
}

interface CatalogoSucursal {
  sucursal: Sucursal;
  productos: ProductoCatalogo[];
  loading: boolean;
  error: string;
}

@Component({
  selector: 'app-admin-inventario',
  imports: [],
  templateUrl: './inventario.html',
  styleUrl: './inventario.scss',
})
export class AdminInventario implements OnInit {
  private readonly http = inject(HttpClient);

  protected readonly sucursalesDisponibles = signal<Sucursal[]>([]);
  protected readonly catalogos = signal<CatalogoSucursal[]>([]);
  protected readonly showPicker = signal(false);
  protected readonly error = signal('');

  protected readonly sucursalesParaAgregar = computed(() => {
    const yaAgregadas = new Set(this.catalogos().map((c) => c.sucursal.id));
    return this.sucursalesDisponibles().filter((s) => !yaAgregadas.has(s.id));
  });

  ngOnInit(): void {
    this.loadSucursales();
  }

  protected togglePicker(): void {
    this.showPicker.update((v) => !v);
  }

  protected async agregarCatalogo(sucursal: Sucursal): Promise<void> {
    this.showPicker.set(false);
    const entrada: CatalogoSucursal = { sucursal, productos: [], loading: true, error: '' };
    this.catalogos.update((lista) => [...lista, entrada]);

    try {
      const productos = await firstValueFrom(
        this.http.get<ProductoCatalogo[]>(`${environment.apiUrl}/catalogo/sucursales/${sucursal.id}/productos`),
      );
      this.catalogos.update((lista) =>
        lista.map((c) => (c.sucursal.id === sucursal.id ? { ...c, productos, loading: false } : c)),
      );
    } catch {
      this.catalogos.update((lista) =>
        lista.map((c) =>
          c.sucursal.id === sucursal.id ? { ...c, loading: false, error: 'No se pudo cargar el catalogo.' } : c,
        ),
      );
    }
  }

  protected quitarCatalogo(sucursalId: number): void {
    this.catalogos.update((lista) => lista.filter((c) => c.sucursal.id !== sucursalId));
  }

  protected async actualizarCantidad(
    sucursalId: number,
    producto: ProductoCatalogo,
    variante: Variante,
    valor: string,
  ): Promise<void> {
    const cantidad = Number(valor);
    if (Number.isNaN(cantidad) || cantidad < 0) return;

    try {
      const actualizada = await firstValueFrom(
        this.http.put<Variante>(`${environment.apiUrl}/productos/${producto.id}/inventario/${variante.id}`, {
          cantidad,
        }),
      );

      this.catalogos.update((lista) =>
        lista.map((cat) => {
          if (cat.sucursal.id !== sucursalId) return cat;
          const productos = cat.productos.map((p) => {
            if (p.id !== producto.id) return p;
            const variantes = p.variantes.map((v) => (v.id === variante.id ? { ...v, cantidad: actualizada.cantidad } : v));
            const cantidad_total = variantes.reduce((sum, v) => sum + v.cantidad, 0);
            return { ...p, variantes, cantidad_total, disponible: cantidad_total > 0 };
          });
          return { ...cat, productos };
        }),
      );
    } catch (err) {
      this.error.set(this.extractError(err));
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

  private async loadSucursales(): Promise<void> {
    this.error.set('');
    try {
      const res = await firstValueFrom(this.http.get<Sucursal[]>(`${environment.apiUrl}/catalogo/sucursales`));
      this.sucursalesDisponibles.set(res);
      // Precarga el catalogo de todas las sucursales para que siempre esten
      // visibles al entrar a la pagina, sin depender de que el usuario los
      // haya agregado a mano en una visita anterior (el estado no persiste
      // entre navegaciones).
      await Promise.all(res.map((s) => this.agregarCatalogo(s)));
    } catch {
      this.error.set('No se pudo cargar las sucursales.');
    }
  }
}
