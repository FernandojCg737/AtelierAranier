import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { PRODUCTS, Product } from '../../data/products';
import { Cart } from '../../services/cart';

@Component({
  selector: 'app-discounts',
  imports: [RouterLink],
  templateUrl: './discounts.html',
  styleUrl: './discounts.scss',
})
export class Discounts {
  private readonly cart = inject(Cart);

  protected readonly products: Product[] = PRODUCTS.filter((p) => p.discountLabel).slice(0, 3);

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
