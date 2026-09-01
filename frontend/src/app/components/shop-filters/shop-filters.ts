import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Component, DestroyRef, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

interface Sucursal {
  id: string;
  nombre: string;
  direccion: string;
}

interface FiltroOpcion {
  id: string;
  label: string;
}

const PRECIO_MIN = 0;
const PRECIO_MAX = 3500;

// TODO: placeholder de que marcas vende cada categoria. Reemplazar cuando el
// catalogo real (Producto -> Categoria / Proveedor) este conectado al backend.
const MARCAS_POR_CATEGORIA: Record<string, string[]> = {
  camisas: ['tommy', 'calvin-klein', 'levis'],
  chalecos: ['champion', 'calvin-klein', 'tommy'],
  hoodie: ['nike', 'adidas', 'puma', 'champion', 'new-balance'],
  pantalones: ['levis', 'nike', 'adidas', 'calvin-klein'],
  poleras: ['nike', 'adidas', 'puma', 'jordan', 'champion', 'converse'],
};

@Component({
  selector: 'app-shop-filters',
  imports: [],
  templateUrl: './shop-filters.html',
  styleUrl: './shop-filters.scss',
})
export class ShopFilters implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly destroyRef = inject(DestroyRef);

  protected readonly sucursales: Sucursal[] = [
    { id: 'todas', nombre: 'Todas las Sucursales', direccion: '' },
    {
      id: 'equipetrol',
      nombre: 'Sucursal Equipetrol',
      direccion: 'Av. San Martin, 3er Anillo Interno, Equipetrol',
    },
    { id: 'las-palmas', nombre: 'Sucursal Las Palmas', direccion: 'Av. Beni, 2do Anillo, B. Las Palmas' },
    {
      id: 'norte',
      nombre: 'Sucursal Norte',
      direccion: 'Av. Cristo Redentor, entre 4to y 5to Anillo, Zona Norte',
    },
  ];

  protected readonly filtrosRapidos: FiltroOpcion[] = [
    { id: 'todos', label: 'Todos los productos' },
    { id: 'ofertas', label: 'Ofertas y Descuentos' },
    { id: 'nuevo', label: 'Lo mas nuevo' },
  ];

  protected readonly categorias: FiltroOpcion[] = [
    { id: 'todas', label: 'Todas' },
    { id: 'camisas', label: 'Camisas' },
    { id: 'chalecos', label: 'Chalecos' },
    { id: 'hoodie', label: 'Hoodie' },
    { id: 'pantalones', label: 'Pantalones' },
    { id: 'poleras', label: 'Poleras' },
  ];

  // TODO: placeholder de marcas que la tienda vende en todas sus sucursales.
  // Ajustar cuando tengamos el catalogo real de proveedores conectado al backend.
  protected readonly marcas: FiltroOpcion[] = [
    { id: 'nike', label: 'Nike' },
    { id: 'adidas', label: 'Adidas' },
    { id: 'puma', label: 'Puma' },
    { id: 'new-balance', label: 'New Balance' },
    { id: 'converse', label: 'Converse' },
    { id: 'jordan', label: 'Jordan' },
    { id: 'champion', label: 'Champion' },
    { id: 'levis', label: "Levi's" },
    { id: 'tommy', label: 'Tommy Hilfiger' },
    { id: 'calvin-klein', label: 'Calvin Klein' },
  ];

  protected readonly precioMin = PRECIO_MIN;
  protected readonly precioMax = PRECIO_MAX;

  protected readonly selectedSucursal = signal('todas');
  protected readonly selectedFiltrosRapidos = signal(new Set<string>(['todos']));
  protected readonly selectedCategoria = signal('todas');
  protected readonly selectedMarcas = signal(new Set<string>());
  protected readonly selectedPrecioMin = signal(PRECIO_MIN);
  protected readonly selectedPrecioMax = signal(PRECIO_MAX);

  protected readonly categoriasOpen = signal(true);
  protected readonly precioOpen = signal(true);

  protected readonly marcasVisibles = computed<FiltroOpcion[]>(() => {
    const categoria = this.selectedCategoria();
    if (categoria === 'todas') return this.marcas;

    const idsPermitidos = MARCAS_POR_CATEGORIA[categoria] ?? [];
    return this.marcas.filter((m) => idsPermitidos.includes(m.id));
  });

  protected readonly todasMarcasChecked = computed(() => this.selectedMarcas().size === 0);

  protected readonly minPercent = computed(
    () => ((this.selectedPrecioMin() - PRECIO_MIN) / (PRECIO_MAX - PRECIO_MIN)) * 100,
  );
  protected readonly maxPercent = computed(
    () => ((this.selectedPrecioMax() - PRECIO_MIN) / (PRECIO_MAX - PRECIO_MIN)) * 100,
  );

  ngOnInit(): void {
    // Permite llegar desde el header con un filtro ya aplicado, ej.
    // /tienda?categoria=poleras o /tienda?filtro=ofertas.
    this.route.queryParamMap.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((params) => {
      const categoria = params.get('categoria');
      if (categoria && this.categorias.some((c) => c.id === categoria)) {
        this.selectCategoria(categoria);
      }

      const filtro = params.get('filtro');
      if (filtro && this.filtrosRapidos.some((f) => f.id === filtro)) {
        this.selectedFiltrosRapidos.set(new Set([filtro]));
      }
    });
  }

  protected selectSucursal(id: string): void {
    this.selectedSucursal.set(id);
  }

  protected toggleFiltroRapido(id: string): void {
    this.selectedFiltrosRapidos.update((set) => {
      const next = new Set(set);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  protected selectCategoria(id: string): void {
    this.selectedCategoria.set(id);

    const idsPermitidos = id === 'todas' ? null : MARCAS_POR_CATEGORIA[id] ?? [];
    if (idsPermitidos) {
      this.selectedMarcas.update((set) => {
        const next = new Set([...set].filter((m) => idsPermitidos.includes(m)));
        return next;
      });
    }
  }

  protected toggleMarca(id: string): void {
    this.selectedMarcas.update((set) => {
      const next = new Set(set);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  protected selectTodasMarcas(): void {
    this.selectedMarcas.set(new Set());
  }

  protected onMinRangeInput(value: string): void {
    const parsed = Math.min(Number(value), this.selectedPrecioMax());
    this.selectedPrecioMin.set(parsed);
  }

  protected onMaxRangeInput(value: string): void {
    const parsed = Math.max(Number(value), this.selectedPrecioMin());
    this.selectedPrecioMax.set(parsed);
  }

  protected onMinInputChange(value: string): void {
    const parsed = Math.max(PRECIO_MIN, Math.min(Number(value) || 0, this.selectedPrecioMax()));
    this.selectedPrecioMin.set(parsed);
  }

  protected onMaxInputChange(value: string): void {
    const parsed = Math.min(PRECIO_MAX, Math.max(Number(value) || 0, this.selectedPrecioMin()));
    this.selectedPrecioMax.set(parsed);
  }

  protected limpiarFiltros(): void {
    this.selectedSucursal.set('todas');
    this.selectedFiltrosRapidos.set(new Set(['todos']));
    this.selectedCategoria.set('todas');
    this.selectedMarcas.set(new Set());
    this.selectedPrecioMin.set(PRECIO_MIN);
    this.selectedPrecioMax.set(PRECIO_MAX);
  }
}
