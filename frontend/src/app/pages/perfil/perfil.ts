import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';
import { Auth } from '../../services/auth';
import { checkPassword, isPasswordValid } from '../../utils/password';

@Component({
  selector: 'app-perfil',
  imports: [],
  templateUrl: './perfil.html',
  styleUrl: './perfil.scss',
})
export class Perfil {
  protected readonly auth = inject(Auth);

  protected readonly isCliente = computed(() => this.auth.currentUser()?.tipo === 'cliente');

  protected readonly nombre = signal(this.auth.currentUser()?.nombre ?? '');
  protected readonly telefono = signal(this.auth.currentUser()?.telefono ?? '');
  protected readonly direccion = signal(this.auth.currentUser()?.direccion ?? '');
  protected readonly profileError = signal('');
  protected readonly profileSuccess = signal('');
  protected readonly profileSaving = signal(false);

  protected readonly passwordActual = signal('');
  protected readonly passwordNueva = signal('');
  protected readonly passwordConfirmar = signal('');
  protected readonly showActual = signal(false);
  protected readonly showNueva = signal(false);
  protected readonly showConfirmar = signal(false);
  protected readonly passwordTouched = signal(false);
  protected readonly passwordChecks = computed(() => checkPassword(this.passwordNueva()));
  protected readonly passwordError = signal('');
  protected readonly passwordSuccess = signal('');
  protected readonly passwordSaving = signal(false);

  protected async submitProfile(): Promise<void> {
    if (!this.nombre()) {
      this.profileError.set('El nombre no puede estar vacio.');
      return;
    }

    this.profileError.set('');
    this.profileSuccess.set('');
    this.profileSaving.set(true);
    try {
      await this.auth.updateProfile({
        nombre: this.nombre(),
        telefono: this.telefono() || null,
        direccion: this.direccion() || null,
      });
      this.profileSuccess.set('Tus datos se actualizaron correctamente.');
    } catch (err) {
      this.profileError.set(this.extractError(err));
    } finally {
      this.profileSaving.set(false);
    }
  }

  protected async submitPassword(): Promise<void> {
    this.passwordTouched.set(true);
    this.passwordSuccess.set('');

    if (!this.passwordActual()) {
      this.passwordError.set('Ingresa tu contrasena actual.');
      return;
    }
    if (!isPasswordValid(this.passwordNueva())) {
      this.passwordError.set('La nueva contrasena no cumple los requisitos minimos.');
      return;
    }
    if (this.passwordNueva() !== this.passwordConfirmar()) {
      this.passwordError.set('Las contrasenas no coinciden.');
      return;
    }

    this.passwordError.set('');
    this.passwordSaving.set(true);
    try {
      await this.auth.changePassword(this.passwordActual(), this.passwordNueva());
      this.passwordSuccess.set('Tu contrasena se actualizo. Te avisamos por correo.');
      this.passwordActual.set('');
      this.passwordNueva.set('');
      this.passwordConfirmar.set('');
      this.passwordTouched.set(false);
    } catch (err) {
      this.passwordError.set(this.extractError(err));
    } finally {
      this.passwordSaving.set(false);
    }
  }

  private extractError(err: unknown): string {
    if (err instanceof HttpErrorResponse) {
      const detail = err.error?.detail;
      if (typeof detail === 'string') return detail;
      if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
      if (err.status === 0) return 'No pudimos conectar con el servidor.';
    }
    return 'Ocurrio un error inesperado.';
  }
}
