import { HttpClient } from '@angular/common/http';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Product } from '../../data/products';
import { Auth } from '../../services/auth';
import { CatalogoPublico, isAgotado } from '../../services/catalogo-publico';

interface RecomendacionApi {
  producto_id: number;
  producto_nombre: string;
  origen: string;
  razon: string;
}

interface ProductoRecomendado extends Product {
  razon: string;
}

// CU18: "Recomendado para ti" -- solo para clientes con sesion iniciada
// (las recomendaciones son por cliente). El ranking lo arma el backend
// (motor de reglas + IA para la razon); aca solo se cruza con el catalogo
// publico ya cargado para tener imagen/precio/marca listos para la tarjeta.
@Component({
  selector: 'app-recomendaciones',
  imports: [RouterLink],
  templateUrl: './recomendaciones.html',
  styleUrl: './recomendaciones.scss',
})
export class Recomendaciones implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly catalogo = inject(CatalogoPublico);
  protected readonly auth = inject(Auth);

  protected readonly isAgotado = isAgotado;
  private readonly recomendaciones = signal<RecomendacionApi[]>([]);

  protected readonly esClienteConSesion = computed(
    () => !!this.auth.currentUser() && this.auth.currentUser()?.tipo === 'cliente',
  );

  protected readonly productos = computed<ProductoRecomendado[]>(() => {
    const catalogo = this.catalogo.products();
    return this.recomendaciones()
      .map((r) => {
        const producto = catalogo.find((p) => Number(p.id) === r.producto_id);
        return producto ? { ...producto, razon: r.razon } : null;
      })
      .filter((p): p is ProductoRecomendado => p !== null);
  });

  ngOnInit(): void {
    this.catalogo.load();
    if (this.esClienteConSesion()) void this.cargar();
  }

  private async cargar(): Promise<void> {
    try {
      const res = await firstValueFrom(
        this.http.get<RecomendacionApi[]>(`${environment.apiUrl}/recomendaciones/mias`),
      );
      this.recomendaciones.set(res);
    } catch {
      this.recomendaciones.set([]);
    }
  }

  protected seleccionar(product: Product): void {
    if (isAgotado(product)) return;
    void this.router.navigate(['/producto', product.id]);
  }
}
