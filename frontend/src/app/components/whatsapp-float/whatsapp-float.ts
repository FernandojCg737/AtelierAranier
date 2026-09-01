import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Component, DestroyRef, OnInit, OnDestroy, computed, inject, input, signal } from '@angular/core';
import { NavigationEnd, Router } from '@angular/router';
import { filter } from 'rxjs/operators';

@Component({
  selector: 'app-whatsapp-float',
  imports: [],
  templateUrl: './whatsapp-float.html',
  styleUrl: './whatsapp-float.scss',
})
export class WhatsappFloat implements OnInit, OnDestroy {
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  // TODO: reemplazar con el numero real de WhatsApp de la tienda si cambia.
  readonly phoneNumber = input('59173766956');
  readonly message = input('Hola, tengo una consulta sobre un producto.');

  protected readonly whatsappUrl = computed(
    () => `https://wa.me/${this.phoneNumber()}?text=${encodeURIComponent(this.message())}`,
  );

  // Oculto mientras el hero esta a la vista (para no chocar con sus botones);
  // aparece apenas el usuario baja y el hero sale del viewport. En paginas
  // sin hero queda visible siempre.
  protected readonly visible = signal(false);

  private observer?: IntersectionObserver;

  ngOnInit(): void {
    this.watchCurrentRouteHero();

    this.router.events
      .pipe(
        filter((event) => event instanceof NavigationEnd),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe(() => {
        // El componente de la nueva ruta recien se pinta despues de este
        // evento; se espera un tick para que ".hero" ya exista (o no) en el DOM.
        setTimeout(() => this.watchCurrentRouteHero());
      });
  }

  private watchCurrentRouteHero(): void {
    this.observer?.disconnect();

    const hero = document.querySelector('.hero');
    if (!hero) {
      this.visible.set(true);
      return;
    }

    this.observer = new IntersectionObserver(([entry]) => {
      this.visible.set(!entry.isIntersecting);
    });
    this.observer.observe(hero);
  }

  ngOnDestroy(): void {
    this.observer?.disconnect();
  }
}
