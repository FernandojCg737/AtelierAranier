import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize(config: { client_id: string; callback: (resp: { credential: string }) => void }): void;
          renderButton(container: HTMLElement, options: Record<string, unknown>): void;
        };
      };
    };
  }
}

@Injectable({ providedIn: 'root' })
export class GoogleIdentity {
  renderButton(elementId: string, onCredential: (credential: string) => void, attempt = 0): void {
    const container = document.getElementById(elementId);
    if (!container) return;

    if (!window.google?.accounts?.id) {
      if (attempt > 25) return;
      setTimeout(() => this.renderButton(elementId, onCredential, attempt + 1), 200);
      return;
    }

    window.google.accounts.id.initialize({
      client_id: environment.googleClientId,
      callback: (resp) => onCredential(resp.credential),
    });
    window.google.accounts.id.renderButton(container, {
      type: 'standard',
      theme: 'outline',
      size: 'large',
      width: 380,
    });
  }
}
