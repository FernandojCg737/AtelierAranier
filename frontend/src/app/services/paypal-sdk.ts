import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';

declare global {
  interface Window {
    paypal?: unknown;
  }
}

// Carga el script del SDK de PayPal una sola vez (cachea la promesa: si se
// pide de nuevo mientras ya esta cargando, o ya cargado, reusa lo mismo en
// vez de inyectar el <script> dos veces).
@Injectable({ providedIn: 'root' })
export class PaypalSdk {
  private promesa: Promise<unknown> | null = null;

  cargar(): Promise<unknown> {
    if (window.paypal) return Promise.resolve(window.paypal);
    if (this.promesa) return this.promesa;

    this.promesa = new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = `https://www.paypal.com/sdk/js?client-id=${environment.paypalClientId}&currency=USD&intent=capture`;
      script.onload = () => resolve(window.paypal);
      script.onerror = () => reject(new Error('No se pudo cargar el SDK de PayPal.'));
      document.head.appendChild(script);
    });
    return this.promesa;
  }
}
