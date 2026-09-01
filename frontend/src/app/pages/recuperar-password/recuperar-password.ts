import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { AuthShowcase } from '../../components/auth-showcase/auth-showcase';
import { Auth } from '../../services/auth';
import { checkPassword, isPasswordValid } from '../../utils/password';

type Step = 'email' | 'code' | 'choice' | 'reset';

@Component({
  selector: 'app-recuperar-password',
  imports: [RouterLink, AuthShowcase],
  templateUrl: './recuperar-password.html',
  styleUrl: './recuperar-password.scss',
})
export class RecuperarPassword {
  private readonly auth = inject(Auth);
  private readonly router = inject(Router);

  protected readonly step = signal<Step>('email');
  protected readonly email = signal('');
  protected readonly code = signal('');
  protected readonly newPassword = signal('');
  protected readonly confirmPassword = signal('');
  protected readonly showPassword = signal(false);
  protected readonly showConfirmPassword = signal(false);
  protected readonly passwordTouched = signal(false);
  protected readonly passwordChecks = computed(() => checkPassword(this.newPassword()));
  protected readonly loading = signal(false);
  protected readonly error = signal('');

  private resetToken = '';

  protected async submitEmail(): Promise<void> {
    if (!this.email()) {
      this.error.set('Ingresa tu correo.');
      return;
    }

    this.error.set('');
    this.loading.set(true);
    try {
      await this.auth.forgotPassword(this.email());
      this.step.set('code');
    } catch (err) {
      this.error.set(this.extractError(err));
    } finally {
      this.loading.set(false);
    }
  }

  protected async submitCode(): Promise<void> {
    if (this.code().length !== 6) {
      this.error.set('Ingresa el codigo de 6 digitos que te enviamos.');
      return;
    }

    this.error.set('');
    this.loading.set(true);
    try {
      this.resetToken = await this.auth.verifyResetCode(this.email(), this.code());
      this.step.set('choice');
    } catch (err) {
      this.error.set(this.extractError(err));
    } finally {
      this.loading.set(false);
    }
  }

  protected async chooseLoginOnly(): Promise<void> {
    this.error.set('');
    this.loading.set(true);
    try {
      await this.auth.loginWithResetCode(this.resetToken);
      this.router.navigateByUrl(this.auth.landingRoute());
    } catch (err) {
      this.error.set(this.extractError(err));
    } finally {
      this.loading.set(false);
    }
  }

  protected chooseChangePassword(): void {
    this.error.set('');
    this.step.set('reset');
  }

  protected async submitReset(): Promise<void> {
    this.passwordTouched.set(true);

    if (!isPasswordValid(this.newPassword())) {
      this.error.set('La contrasena no cumple los requisitos minimos.');
      return;
    }

    if (this.newPassword() !== this.confirmPassword()) {
      this.error.set('Las contrasenas no coinciden.');
      return;
    }

    this.error.set('');
    this.loading.set(true);
    try {
      await this.auth.resetPassword(this.resetToken, this.newPassword());
      this.router.navigateByUrl(this.auth.landingRoute());
    } catch (err) {
      this.error.set(this.extractError(err));
    } finally {
      this.loading.set(false);
    }
  }

  private extractError(err: unknown): string {
    if (err instanceof HttpErrorResponse) {
      const detail = err.error?.detail;
      if (typeof detail === 'string') return detail;
      if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
      if (err.status === 0) return 'No pudimos conectar con el servidor. Intenta de nuevo.';
    }
    return 'Ocurrio un error inesperado. Intenta de nuevo.';
  }
}
