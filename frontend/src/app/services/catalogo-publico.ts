import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';
import { Product } from '../data/products';

interface ProductoPublico {
  id: number;
  nombre: string;
  descripcion: string | null;
  precio: string;
  precio_original: string | null;
  marca_nombre: string;
  categoria_nombre: string;
  temporada_nombre: string;
  imagenes: string[];
  sucursales_disponibles: string[];
}

const PLACEHOLDER_IMAGE = '/img/productos/producto-1.jpg';

// Un producto sin stock en ninguna sucursal no tiene sentido mostrarlo como
// comprable: se sigue listando (para que el cliente lo encuentre) pero
// marcado como agotado en vez de ocultarlo.
export function isAgotado(product: Product): boolean {
  return product.branchesInStock.length === 0;
}

function toProduct(p: ProductoPublico): Product {
  const price = Number(p.precio);
  const originalPrice = p.precio_original ? Number(p.precio_original) : undefined;
  const discountLabel =
    originalPrice && originalPrice > price ? `-${Math.round((1 - price / originalPrice) * 100)}%` : undefined;

  return {
    id: String(p.id),
    name: p.nombre,
    brand: p.marca_nombre,
    price,
    originalPrice: discountLabel ? originalPrice : undefined,
    discountLabel,
    image: p.imagenes[0] ?? PLACEHOLDER_IMAGE,
    gallery: p.imagenes.length ? p.imagenes : [PLACEHOLDER_IMAGE],
    category: p.categoria_nombre.toLowerCase(),
    categoryLabel: p.categoria_nombre,
    temporada: p.temporada_nombre,
    isNew: false,
    colors: [],
    sizes: [],
    branchesInStock: p.sucursales_disponibles,
    description: p.descripcion ?? undefined,
  };
}

// Carga el catalogo publico una sola vez y lo comparte entre ShopFilters
// (para derivar categorias/marcas reales) y ProductGrid (para listar y
// filtrar), en vez de que cada componente pida su propia copia.
@Injectable({ providedIn: 'root' })
export class CatalogoPublico {
  private readonly http = inject(HttpClient);
  private cargado = false;

  readonly products = signal<Product[]>([]);
  readonly loading = signal(false);

  readonly categorias = computed(() => {
    const vistas = new Map<string, string>();
    for (const p of this.products()) vistas.set(p.category, p.categoryLabel);
    return Array.from(vistas.entries())
      .map(([id, label]) => ({ id, label }))
      .sort((a, b) => a.label.localeCompare(b.label));
  });

  readonly marcas = computed(() => {
    const vistas = new Set<string>();
    for (const p of this.products()) if (p.brand) vistas.add(p.brand);
    return Array.from(vistas).sort((a, b) => a.localeCompare(b));
  });

  async load(): Promise<void> {
    if (this.cargado) return;
    this.cargado = true;
    this.loading.set(true);
    try {
      const res = await firstValueFrom(this.http.get<ProductoPublico[]>(`${environment.apiUrl}/productos/publico`));
      this.products.set(res.map(toProduct));
    } catch {
      this.products.set([]);
    } finally {
      this.loading.set(false);
    }
  }
}
