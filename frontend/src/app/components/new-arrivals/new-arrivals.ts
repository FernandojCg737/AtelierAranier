import { Component, OnInit, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Product } from '../../data/products';
import { CatalogoPublico, isAgotado } from '../../services/catalogo-publico';
import { Cart } from '../../services/cart';

@Component({
  selector: 'app-new-arrivals',
  imports: [RouterLink],
  templateUrl: './new-arrivals.html',
  styleUrl: './new-arrivals.scss',
})
export class NewArrivals implements OnInit {
  private readonly cart = inject(Cart);
  private readonly catalogo = inject(CatalogoPublico);

  protected readonly isAgotado = isAgotado;

  // "Novedades": los productos con el id mas alto (los que se cargaron
  // ultimo), ya que el catalogo real no tiene una fecha de alta propia.
  protected readonly products = computed<Product[]>(() =>
    [...this.catalogo.products()].sort((a, b) => Number(b.id) - Number(a.id)).slice(0, 4),
  );

  ngOnInit(): void {
    this.catalogo.load();
  }

  protected addToCart(product: Product): void {
    if (isAgotado(product)) return;
    this.cart.addItem({
      id: product.id,
      name: product.name,
      brand: product.brand,
      price: product.price,
      image: product.image,
    });
  }
}
