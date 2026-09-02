import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class TiendaFiltros {
  readonly temporadaSeleccionada = signal<string | null>(null);
  readonly categoriaSeleccionada = signal<string | null>(null);
  readonly marcasSeleccionadas = signal<Set<string>>(new Set());
  readonly sucursalSeleccionada = signal<string | null>(null);
  readonly precioMin = signal<number | null>(null);
  readonly precioMax = signal<number | null>(null);

  seleccionarTemporada(nombre: string | null): void {
    this.temporadaSeleccionada.set(nombre);
  }

  seleccionarCategoria(id: string | null): void {
    this.categoriaSeleccionada.set(id);
  }

  toggleMarca(nombre: string): void {
    this.marcasSeleccionadas.update((set) => {
      const next = new Set(set);
      next.has(nombre) ? next.delete(nombre) : next.add(nombre);
      return next;
    });
  }

  limpiarMarcas(): void {
    this.marcasSeleccionadas.set(new Set());
  }

  seleccionarSucursal(nombre: string | null): void {
    this.sucursalSeleccionada.set(nombre);
  }

  setPrecio(min: number | null, max: number | null): void {
    this.precioMin.set(min);
    this.precioMax.set(max);
  }

  limpiarTodo(): void {
    this.temporadaSeleccionada.set(null);
    this.categoriaSeleccionada.set(null);
    this.marcasSeleccionadas.set(new Set());
    this.sucursalSeleccionada.set(null);
    this.precioMin.set(null);
    this.precioMax.set(null);
  }
}
