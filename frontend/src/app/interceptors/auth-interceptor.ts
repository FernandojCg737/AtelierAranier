import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { Auth } from '../services/auth';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(Auth);
  const router = inject(Router);
  const token = auth.token();

  // CU17: le dice al backend de que app vino la accion (ver bitacora,
  // columna "plataforma") -- se manda siempre, no solo autenticado, para
  // que quede en acciones anonimas como registro/login tambien.
  const headers: Record<string, string> = { 'X-Client-Platform': 'web' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const authReq = req.clone({ setHeaders: headers });

  return next(authReq).pipe(
    catchError((error: unknown) => {
      // Solo forzamos el logout si el request iba autenticado: un 401 en
      // /auth/login (contrasena incorrecta) es un error normal de formulario,
      // no una sesion invalidada.
      if (token && error instanceof HttpErrorResponse && error.status === 401) {
        const detail = (error.error as { detail?: unknown } | null)?.detail;
        const message = typeof detail === 'string' ? detail : 'Tu sesion expiro. Inicia sesion de nuevo.';
        auth.forceLogout(message);
        router.navigateByUrl('/login');
      }
      return throwError(() => error);
    }),
  );
};
