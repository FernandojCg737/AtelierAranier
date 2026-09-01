import { Injectable, computed, signal } from '@angular/core';

export interface CartItem {
  id: string;
  name: string;
  brand?: string;
  price: number;
  image: string;
  quantity: number;
}

const STORAGE_KEY = 'atelieraranier_cart';

// TODO: cuando exista el backend (tabla Venta/Carrito/DetalleCarrito), esto
// pasa de localStorage a persistir contra la API y asociarse al Cliente
// autenticado. Por ahora es 100% cliente, no requiere backend.
@Injectable({ providedIn: 'root' })
export class Cart {
  private readonly _items = signal<CartItem[]>(this.readFromStorage());

  readonly items = this._items.asReadonly();

  readonly totalItems = computed(() => this._items().reduce((sum, i) => sum + i.quantity, 0));
  readonly totalPrice = computed(() => this._items().reduce((sum, i) => sum + i.price * i.quantity, 0));

  addItem(item: Omit<CartItem, 'quantity'>, quantity = 1): void {
    this._items.update((items) => {
      const existing = items.find((i) => i.id === item.id);
      const next = existing
        ? items.map((i) => (i.id === item.id ? { ...i, quantity: i.quantity + quantity } : i))
        : [...items, { ...item, quantity }];

      this.writeToStorage(next);
      return next;
    });
  }

  removeItem(id: string): void {
    this._items.update((items) => {
      const next = items.filter((i) => i.id !== id);
      this.writeToStorage(next);
      return next;
    });
  }

  setQuantity(id: string, quantity: number): void {
    if (quantity < 1) {
      this.removeItem(id);
      return;
    }

    this._items.update((items) => {
      const next = items.map((i) => (i.id === id ? { ...i, quantity } : i));
      this.writeToStorage(next);
      return next;
    });
  }

  clear(): void {
    this._items.set([]);
    this.writeToStorage([]);
  }

  private readFromStorage(): CartItem[] {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? (JSON.parse(raw) as CartItem[]) : [];
    } catch {
      return [];
    }
  }

  private writeToStorage(items: CartItem[]): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
    } catch {
      // localStorage no disponible (modo privado, etc.); el carrito sigue
      // funcionando en memoria durante la sesion.
    }
  }
}
