import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Component, DestroyRef, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { PRODUCTS, Product } from '../../data/products';
import { Cart } from '../../services/cart';

@Component({
  selector: 'app-product-grid',
  imports: [RouterLink],
  templateUrl: './product-grid.html',
  styleUrl: './product-grid.scss',
})
export class ProductGrid implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly destroyRef = inject(DestroyRef);
  private readonly cart = inject(Cart);

  protected readonly sortOpen = signal(false);
  protected readonly sortLabel = signal('Predeterminado');

  protected readonly sortOptions = [
    'Predeterminado',
    'Precio: menor a mayor',
    'Precio: mayor a menor',
    'Mas recientes',
  ];

  protected readonly products: Product[] = PRODUCTS;

  protected readonly loadingMore = signal(false);

  // TODO: placeholder: filtra el catalogo de prueba por nombre/marca en el
  // cliente. Cuando exista el endpoint real de busqueda (tabla Producto),
  // este mismo query param "buscar" se manda al backend en su lugar.
  protected readonly busqueda = signal('');

  protected readonly visibleProducts = computed<Product[]>(() => {
    const termino = this.busqueda().trim().toLowerCase();
    if (!termino) return this.products;

    return this.products.filter(
      (p) =>
        p.name.toLowerCase().includes(termino) || (p.brand ?? '').toLowerCase().includes(termino),
    );
  });

  ngOnInit(): void {
    this.route.queryParamMap.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((params) => {
      this.busqueda.set(params.get('buscar') ?? '');
    });
  }

  protected toggleSort(): void {
    this.sortOpen.update((open) => !open);
  }

  protected selectSort(option: string): void {
    this.sortLabel.set(option);
    this.sortOpen.set(false);
  }

  // TODO: reemplazar con la llamada real al backend (paginacion de Producto)
  // cuando el catalogo este conectado. Por ahora solo simula el estado de
  // carga, no hay mas productos de prueba que agregar.
  protected loadMore(): void {
    this.loadingMore.set(true);
    setTimeout(() => this.loadingMore.set(false), 600);
  }

  protected addToCart(product: Product): void {
    this.cart.addItem({
      id: product.id,
      name: product.name,
      brand: product.brand,
      price: product.price,
      image: product.image,
    });
  }
}
