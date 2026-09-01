import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Cart } from '../../services/cart';

@Component({
  selector: 'app-carrito',
  imports: [RouterLink],
  templateUrl: './carrito.html',
  styleUrl: './carrito.scss',
})
export class Carrito {
  protected readonly cart = inject(Cart);

  protected decrease(id: string, currentQuantity: number): void {
    this.cart.setQuantity(id, currentQuantity - 1);
  }

  protected increase(id: string, currentQuantity: number): void {
    this.cart.setQuantity(id, currentQuantity + 1);
  }
}
