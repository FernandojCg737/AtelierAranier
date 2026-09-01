import { HttpErrorResponse } from '@angular/common/http';
import { AfterViewInit, Component, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { AuthShowcase } from '../../components/auth-showcase/auth-showcase';
import { Auth } from '../../services/auth';
import { GoogleIdentity } from '../../services/google-identity';

@Component({
  selector: 'app-login',
  imports: [RouterLink, AuthShowcase],
  templateUrl: './login.html',
  styleUrl: './login.scss',
})
export class Login implements AfterViewInit {
  private readonly auth = inject(Auth);
  private readonly router = inject(Router);
  private readonly googleIdentity = inject(GoogleIdentity);

  protected readonly email = signal('');
  protected readonly password = signal('');
  protected readonly loading = signal(false);
  protected readonly error = signal('');
  protected readonly showPassword = signal(false);

  ngAfterViewInit(): void {
    this.googleIdentity.renderButton('googleBtnLogin', (credential) => this.handleGoogleCredential(credential));
  }

  protected async submit(): Promise<void> {
    if (!this.email() || !this.password()) {
      this.error.set('Completa tu correo y contrasena.');
      return;
    }

    this.error.set('');
    this.loading.set(true);
    try {
      await this.auth.login({ email: this.email(), password: this.password() });
      this.redirectAfterLogin();
    } catch (err) {
      this.error.set(this.extractError(err));
    } finally {
      this.loading.set(false);
    }
  }

  private async handleGoogleCredential(credential: string): Promise<void> {
    this.error.set('');
    this.loading.set(true);
    try {
      await this.auth.loginWithGoogle(credential);
      this.redirectAfterLogin();
    } catch (err) {
      this.error.set(this.extractError(err));
    } finally {
      this.loading.set(false);
    }
  }

  private redirectAfterLogin(): void {
    this.router.navigateByUrl(this.auth.landingRoute());
  }

  private extractError(err: unknown): string {
    if (err instanceof HttpErrorResponse) {
      const detail = err.error?.detail;
      if (typeof detail === 'string') return detail;
      if (err.status === 0) return 'No pudimos conectar con el servidor. Intenta de nuevo.';
    }
    return 'Ocurrio un error inesperado. Intenta de nuevo.';
  }
}
