import { HttpClient } from '@angular/common/http';
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
  selector: 'app-admin-catalogo',
  imports: [],
  templateUrl: './catalogo.html',
  styleUrl: './catalogo.scss',
})
export class AdminCatalogo implements OnInit {
  private readonly http = inject(HttpClient);

  protected readonly sucursalesDisponibles = signal<Sucursal[]>([]);
  protected readonly catalogos = signal<CatalogoSucursal[]>([]);
  protected readonly showPicker = signal(false);
  protected readonly error = signal('');
  protected readonly busqueda = signal('');

  protected readonly sucursalesParaAgregar = computed(() => {
    const yaAgregadas = new Set(this.catalogos().map((c) => c.sucursal.id));
    return this.sucursalesDisponibles().filter((s) => !yaAgregadas.has(s.id));
  });

  protected filtrarProductos(productos: ProductoCatalogo[]): ProductoCatalogo[] {
    const termino = this.busqueda().trim().toLowerCase();
    if (!termino) return productos;

    return productos.filter(
      (p) =>
        p.nombre.toLowerCase().includes(termino) ||
        p.marca_nombre.toLowerCase().includes(termino) ||
        p.categoria_nombre.toLowerCase().includes(termino) ||
        p.variantes.some(
          (v) => v.talla_codigo.toLowerCase().includes(termino) || v.color_nombre.toLowerCase().includes(termino),
        ),
    );
  }

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
