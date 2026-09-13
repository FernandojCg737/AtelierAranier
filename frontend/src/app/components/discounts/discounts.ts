import { Component, OnInit, computed, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { Product } from '../../data/products';
import { CatalogoPublico, isAgotado } from '../../services/catalogo-publico';

@Component({
  selector: 'app-discounts',
  imports: [RouterLink],
  templateUrl: './discounts.html',
  styleUrl: './discounts.scss',
})
export class Discounts implements OnInit {
  private readonly router = inject(Router);
  private readonly catalogo = inject(CatalogoPublico);

  protected readonly isAgotado = isAgotado;

  protected readonly products = computed<Product[]>(() =>
    this.catalogo
      .products()
      .filter((p) => p.discountLabel)
      .slice(0, 3),
  );

  ngOnInit(): void {
    this.catalogo.load();
  }

  protected addToCart(product: Product): void {
    if (isAgotado(product)) return;
    void this.router.navigate(['/producto', product.id]);
  }
}
