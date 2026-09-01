import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Component, DestroyRef, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { findProductById, Product } from '../../data/products';
import { Cart } from '../../services/cart';

const WHATSAPP_NUMERO = '59173766956';

@Component({
  selector: 'app-producto-detalle',
  imports: [RouterLink],
  templateUrl: './producto-detalle.html',
  styleUrl: './producto-detalle.scss',
})
export class ProductoDetalle implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly destroyRef = inject(DestroyRef);
  private readonly cart = inject(Cart);

  protected readonly product = signal<Product | undefined>(undefined);
  protected readonly selectedColor = signal<string | null>(null);
  protected readonly selectedSize = signal<string | null>(null);
  protected readonly activeImage = signal<string>('');
  protected readonly detallesOpen = signal(true);
  protected readonly addedFeedback = signal(false);

  protected readonly whatsappUrl = computed(() => {
    const p = this.product();
    const mensaje = p
      ? `Hola, quiero consultar sobre: ${p.name}${this.selectedColor() ? ' - color ' + this.selectedColor() : ''}${this.selectedSize() ? ' - talla ' + this.selectedSize() : ''}`
      : 'Hola, quiero hacer una consulta.';
    return `https://wa.me/${WHATSAPP_NUMERO}?text=${encodeURIComponent(mensaje)}`;
  });

  ngOnInit(): void {
    this.route.paramMap.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((params) => {
      const id = params.get('id') ?? '';
      const found = findProductById(id);
      this.product.set(found);

      if (found) {
        this.selectedColor.set(found.colors[0]?.name ?? null);
        this.selectedSize.set(found.sizes[0] ?? null);
        this.activeImage.set(found.gallery[0] ?? found.image);
      }
    });
  }

  protected selectColor(name: string): void {
    this.selectedColor.set(name);
  }

  protected selectSize(size: string): void {
    this.selectedSize.set(size);
  }

  protected selectImage(src: string): void {
    this.activeImage.set(src);
  }

  protected addToCart(): void {
    const p = this.product();
    if (!p) return;

    this.cart.addItem({
      id: p.id,
      name: p.name,
      brand: p.brand,
      price: p.price,
      image: p.image,
    });

    this.addedFeedback.set(true);
    setTimeout(() => this.addedFeedback.set(false), 1600);
  }
}
