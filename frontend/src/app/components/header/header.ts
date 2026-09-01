import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Component, DestroyRef, ElementRef, HostListener, OnInit, inject, signal, viewChild } from '@angular/core';
import { NavigationEnd, Router, RouterLink } from '@angular/router';
import { filter } from 'rxjs/operators';
import { Auth } from '../../services/auth';
import { Cart } from '../../services/cart';

interface NavLink {
  label: string;
  path: string;
  queryParams?: Record<string, string>;
}

@Component({
  selector: 'app-header',
  imports: [RouterLink],
  templateUrl: './header.html',
  styleUrl: './header.scss',
})
export class Header implements OnInit {
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);
  protected readonly cart = inject(Cart);
  protected readonly auth = inject(Auth);

  // Paginas sin ".hero" (fondo oscuro a pantalla completa) no tienen contra
  // que contrastar un header transparente: quedaria blanco sobre blanco. En
  // esas paginas el header se muestra siempre solido, sin importar el scroll.
  private hasHero = true;

  protected readonly scrolled = signal(false);
  protected readonly mobileMenuOpen = signal(false);
  protected readonly searchOpen = signal(false);
  protected readonly searchQuery = signal('');
  protected readonly accountMenuOpen = signal(false);

  private readonly searchInput = viewChild<ElementRef<HTMLInputElement>>('searchInput');

  protected readonly navLinks: NavLink[] = [
    { label: 'Tienda', path: '/tienda' },
    { label: 'Poleras', path: '/tienda', queryParams: { categoria: 'poleras' } },
    { label: 'Pantalones', path: '/tienda', queryParams: { categoria: 'pantalones' } },
    { label: 'Ofertas', path: '/tienda', queryParams: { filtro: 'ofertas' } },
    { label: 'Cotizaciones', path: '/cotizaciones' },
    { label: 'Contacto', path: '/contacto' },
  ];

  ngOnInit(): void {
    this.refreshForCurrentRoute();

    this.router.events
      .pipe(
        filter((event) => event instanceof NavigationEnd),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe(() => {
        // El componente de la nueva ruta recien se pinta despues de este
        // evento; se espera un tick para que ".hero" ya exista en el DOM.
        setTimeout(() => this.refreshForCurrentRoute());
        this.closeSearch();
        this.accountMenuOpen.set(false);
      });
  }

  @HostListener('document:click', ['$event'])
  protected onDocumentClick(event: MouseEvent): void {
    if (!this.accountMenuOpen()) return;

    const target = event.target as HTMLElement;
    if (!target.closest('.account-menu-wrap')) {
      this.accountMenuOpen.set(false);
    }
  }

  protected toggleAccountMenu(): void {
    this.accountMenuOpen.update((open) => !open);
  }

  protected async logout(): Promise<void> {
    await this.auth.logout();
    this.accountMenuOpen.set(false);
    this.router.navigateByUrl('/');
  }

  private refreshForCurrentRoute(): void {
    this.hasHero = !!document.querySelector('.hero');
    this.onWindowScroll();
  }

  @HostListener('window:scroll')
  protected onWindowScroll(): void {
    this.scrolled.set(!this.hasHero || window.scrollY > 40);
  }

  protected toggleMobileMenu(): void {
    this.mobileMenuOpen.update((open) => !open);
  }

  protected closeMobileMenu(): void {
    this.mobileMenuOpen.set(false);
  }

  protected toggleSearch(): void {
    this.searchOpen.update((open) => !open);
    if (this.searchOpen()) {
      // Esperar a que el input este en el DOM (fuera del @if) antes de enfocarlo.
      setTimeout(() => this.searchInput()?.nativeElement.focus());
    }
  }

  protected closeSearch(): void {
    this.searchOpen.set(false);
    this.searchQuery.set('');
  }

  // TODO: cuando exista el endpoint real de busqueda en el backend (tabla
  // Producto), este query param "buscar" ya queda listo para consumirse ahi
  // mismo. Por ahora ProductGrid filtra el catalogo de prueba por nombre.
  protected submitSearch(): void {
    const termino = this.searchQuery().trim();
    if (!termino) return;

    this.router.navigate(['/tienda'], { queryParams: { buscar: termino } });
    this.closeSearch();
  }
}
