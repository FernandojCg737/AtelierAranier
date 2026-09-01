import { Routes } from '@angular/router';
import { AdminLayout } from './pages/admin/admin-layout/admin-layout';
import { AdminBitacora } from './pages/admin/bitacora/bitacora';
import { AdminClientes } from './pages/admin/clientes/clientes';
import { AdminHome } from './pages/admin/home/home';
import { AdminPerfil } from './pages/admin/perfil/perfil';
import { AdminSesiones } from './pages/admin/sesiones/sesiones';
import { AdminSucursales } from './pages/admin/sucursales/sucursales';
import { AdminUsuarios } from './pages/admin/usuarios/usuarios';
import { Carrito } from './pages/carrito/carrito';
import { Cotizaciones } from './pages/cotizaciones/cotizaciones';
import { Home } from './pages/home/home';
import { Login } from './pages/login/login';
import { Perfil } from './pages/perfil/perfil';
import { ProductoDetalle } from './pages/producto-detalle/producto-detalle';
import { RecuperarPassword } from './pages/recuperar-password/recuperar-password';
import { Registro } from './pages/registro/registro';
import { Tienda } from './pages/tienda/tienda';
import { adminGuard, authGuard, permisoGuard } from './guards/auth-guard';

export const routes: Routes = [
  { path: '', component: Home },
  { path: 'tienda', component: Tienda },
  { path: 'cotizaciones', component: Cotizaciones },
  { path: 'carrito', component: Carrito },
  { path: 'producto/:id', component: ProductoDetalle },
  { path: 'login', component: Login, data: { hideChrome: true } },
  { path: 'registro', component: Registro, data: { hideChrome: true } },
  { path: 'recuperar', component: RecuperarPassword, data: { hideChrome: true } },
  { path: 'perfil', component: Perfil, canActivate: [authGuard] },
  {
    path: 'admin',
    component: AdminLayout,
    canActivate: [adminGuard],
    data: { hideChrome: true },
    children: [
      { path: '', component: AdminHome },
      { path: 'usuarios', component: AdminUsuarios, canActivate: [permisoGuard('CU02')] },
      { path: 'clientes', component: AdminClientes, canActivate: [permisoGuard('CU03')] },
      { path: 'sucursales', component: AdminSucursales, canActivate: [permisoGuard('CU04')] },
      { path: 'perfil', component: AdminPerfil },
      { path: 'sesiones', component: AdminSesiones, canActivate: [permisoGuard('CU01')] },
      { path: 'bitacora', component: AdminBitacora, canActivate: [permisoGuard('CU19')] },
    ],
  },
];
