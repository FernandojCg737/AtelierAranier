import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { PRODUCTS, Product } from '../../data/products';
import { Cart } from '../../services/cart';

@Component({
  selector: 'app-new-arrivals',
  imports: [RouterLink],
  templateUrl: './new-arrivals.html',
  styleUrl: './new-arrivals.scss',
})
export class NewArrivals {
  private readonly cart = inject(Cart);

  protected readonly products: Product[] = PRODUCTS.filter((p) => p.isNew).slice(0, 4);

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
