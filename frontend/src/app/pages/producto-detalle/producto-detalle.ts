import { HttpClient } from '@angular/common/http';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Component, DestroyRef, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Product } from '../../data/products';
import { isAgotado } from '../../services/catalogo-publico';
import { Cart } from '../../services/cart';

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

const WHATSAPP_NUMERO = '59173766956';
const PLACEHOLDER_IMAGE = '/img/productos/producto-1.jpg';

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

@Component({
  selector: 'app-producto-detalle',
  imports: [RouterLink],
  templateUrl: './producto-detalle.html',
  styleUrl: './producto-detalle.scss',
})
export class ProductoDetalle implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly route = inject(ActivatedRoute);
  private readonly destroyRef = inject(DestroyRef);
  private readonly cart = inject(Cart);

  protected readonly product = signal<Product | undefined>(undefined);
  protected readonly isAgotado = isAgotado;
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
    this.route.paramMap.pipe(takeUntilDestroyed(this.destroyRef)).subscribe(async (params) => {
      const id = params.get('id') ?? '';
      try {
        const res = await firstValueFrom(
          this.http.get<ProductoPublico>(`${environment.apiUrl}/productos/publico/${id}`),
        );
        const found = toProduct(res);
        this.product.set(found);
        this.selectedColor.set(found.colors[0]?.name ?? null);
        this.selectedSize.set(found.sizes[0] ?? null);
        this.activeImage.set(found.gallery[0] ?? found.image);
      } catch {
        this.product.set(undefined);
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
    if (!p || isAgotado(p)) return;

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
