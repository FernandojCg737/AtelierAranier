import { HttpClient } from '@angular/common/http';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Component, DestroyRef, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';
import { CatalogoPublico } from '../../services/catalogo-publico';
import { TiendaFiltros } from '../../services/tienda-filtros';

interface Sucursal {
  id: number;
  nombre: string;
  direccion: string;
}

interface Temporada {
  id: number;
  nombre: string;
}

const PRECIO_MIN = 0;
const PRECIO_MAX = 3500;

@Component({
  selector: 'app-shop-filters',
  imports: [],
  templateUrl: './shop-filters.html',
  styleUrl: './shop-filters.scss',
})
export class ShopFilters implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly route = inject(ActivatedRoute);
  private readonly destroyRef = inject(DestroyRef);
  private readonly filtros = inject(TiendaFiltros);
  private readonly catalogo = inject(CatalogoPublico);

  protected readonly temporadas = signal<Temporada[]>([]);
  protected readonly temporadaSeleccionada = this.filtros.temporadaSeleccionada;

  protected readonly sucursales = signal<Sucursal[]>([]);
  protected readonly sucursalSeleccionada = this.filtros.sucursalSeleccionada;

  protected readonly categorias = this.catalogo.categorias;
  protected readonly categoriaSeleccionada = this.filtros.categoriaSeleccionada;

  protected readonly marcasVisibles = computed(() => {
    const categoria = this.categoriaSeleccionada();
    if (!categoria) return this.catalogo.marcas();

    const marcasEnCategoria = new Set(
      this.catalogo
        .products()
        .filter((p) => p.category === categoria)
        .map((p) => p.brand)
        .filter((b): b is string => !!b),
    );
    return this.catalogo.marcas().filter((m) => marcasEnCategoria.has(m));
  });
  protected readonly marcasSeleccionadas = this.filtros.marcasSeleccionadas;
  protected readonly todasMarcasChecked = computed(() => this.marcasSeleccionadas().size === 0);

  protected readonly precioMin = PRECIO_MIN;
  protected readonly precioMax = PRECIO_MAX;
  protected readonly selectedPrecioMin = signal(PRECIO_MIN);
  protected readonly selectedPrecioMax = signal(PRECIO_MAX);

  protected readonly categoriasOpen = signal(true);
  protected readonly precioOpen = signal(true);

  protected readonly minPercent = computed(
    () => ((this.selectedPrecioMin() - PRECIO_MIN) / (PRECIO_MAX - PRECIO_MIN)) * 100,
  );
  protected readonly maxPercent = computed(
    () => ((this.selectedPrecioMax() - PRECIO_MIN) / (PRECIO_MAX - PRECIO_MIN)) * 100,
  );

  ngOnInit(): void {
    // Permite llegar desde el header con una categoria ya aplicada, ej.
    // /tienda?categoria=poleras.
    this.route.queryParamMap.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((params) => {
      const categoria = params.get('categoria');
      if (categoria) this.selectCategoria(categoria);
    });

    this.catalogo.load();

    firstValueFrom(this.http.get<Temporada[]>(`${environment.apiUrl}/temporadas/publico`))
      .then((res) => this.temporadas.set(res))
      .catch(() => this.temporadas.set([]));

    firstValueFrom(this.http.get<Sucursal[]>(`${environment.apiUrl}/sucursales/publico`))
      .then((res) => this.sucursales.set(res))
      .catch(() => this.sucursales.set([]));
  }

  protected seleccionarTemporada(nombre: string | null): void {
    this.filtros.seleccionarTemporada(nombre);
  }

  protected selectSucursal(nombre: string | null): void {
    this.filtros.seleccionarSucursal(nombre);
  }

  protected selectCategoria(id: string | null): void {
    this.filtros.seleccionarCategoria(id === 'todas' ? null : id);
  }

  protected toggleMarca(nombre: string): void {
    this.filtros.toggleMarca(nombre);
  }

  protected selectTodasMarcas(): void {
    this.filtros.limpiarMarcas();
  }

  private aplicarPrecio(): void {
    const min = this.selectedPrecioMin() === PRECIO_MIN ? null : this.selectedPrecioMin();
    const max = this.selectedPrecioMax() === PRECIO_MAX ? null : this.selectedPrecioMax();
    this.filtros.setPrecio(min, max);
  }

  protected onMinRangeInput(value: string): void {
    const parsed = Math.min(Number(value), this.selectedPrecioMax());
    this.selectedPrecioMin.set(parsed);
    this.aplicarPrecio();
  }

  protected onMaxRangeInput(value: string): void {
    const parsed = Math.max(Number(value), this.selectedPrecioMin());
    this.selectedPrecioMax.set(parsed);
    this.aplicarPrecio();
  }

  protected onMinInputChange(value: string): void {
    const parsed = Math.max(PRECIO_MIN, Math.min(Number(value) || 0, this.selectedPrecioMax()));
    this.selectedPrecioMin.set(parsed);
    this.aplicarPrecio();
  }

  protected onMaxInputChange(value: string): void {
    const parsed = Math.min(PRECIO_MAX, Math.max(Number(value) || 0, this.selectedPrecioMin()));
    this.selectedPrecioMax.set(parsed);
    this.aplicarPrecio();
  }

  protected limpiarFiltros(): void {
    this.selectedPrecioMin.set(PRECIO_MIN);
    this.selectedPrecioMax.set(PRECIO_MAX);
    this.filtros.limpiarTodo();
  }
}
