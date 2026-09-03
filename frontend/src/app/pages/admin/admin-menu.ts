export interface AdminUseCase {
  code: string;
  label: string;
  route?: string;
}

export interface AdminPackage {
  code: string;
  label: string;
  useCases: AdminUseCase[];
}

export const ADMIN_MENU: AdminPackage[] = [
  {
    code: 'P1',
    label: 'Gestion de Accesos y Seguridad',
    useCases: [
      { code: 'CU01', label: 'Gestionar Inicio y Cierre de Sesion', route: '/admin/sesiones' },
      { code: 'CU02', label: 'Administrar Usuarios, Roles y Permisos', route: '/admin/usuarios' },
      { code: 'CU17', label: 'Auditar Operaciones (Bitacora)', route: '/admin/bitacora' },
    ],
  },
  {
    code: 'P2',
    label: 'Gestion de Clientes y Sucursales',
    useCases: [
      { code: 'CU03', label: 'Registrar y Administrar Clientes', route: '/admin/clientes' },
      { code: 'CU04', label: 'Administrar Ciudades y Sucursales', route: '/admin/sucursales' },
      { code: 'CU15', label: 'Actualizar Perfil de Usuario', route: '/admin/perfil' },
    ],
  },
  {
    code: 'P3',
    label: 'Gestion de Catalogo e Inventario',
    useCases: [
      { code: 'CU05', label: 'Administrar Catalogo de Productos', route: '/admin/productos' },
      { code: 'CU06', label: 'Administrar Proveedores', route: '/admin/proveedores' },
      { code: 'CU07', label: 'Configurar Temporadas y Colecciones', route: '/admin/temporadas' },
      { code: 'CU08', label: 'Consultar Catalogo y Disponibilidad', route: '/admin/catalogo' },
      { code: 'CU12', label: 'Controlar Inventario por Sucursal', route: '/admin/inventario' },
    ],
  },
  {
    code: 'P4',
    label: 'Gestion de Reservas y Ventas',
    useCases: [
      { code: 'CU09', label: 'Visualizar Prenda con Realidad Aumentada' },
      { code: 'CU10', label: 'Gestion de Reservas' },
      { code: 'CU11', label: 'Gestion de Ventas' },
      { code: 'CU13', label: 'Administrar Carrito de Compras' },
    ],
  },
  {
    code: 'P5',
    label: 'Gestion de Experiencia y Analitica',
    useCases: [
      { code: 'CU14', label: 'Enviar Notificaciones' },
      { code: 'CU16', label: 'Gestion Reportes y Dashboards' },
      { code: 'CU18', label: 'Recomendar Prendas por IA' },
      { code: 'CU19', label: 'Atender Cliente con Chatbot' },
      { code: 'CU20', label: 'Reputacion y Calificaciones' },
    ],
  },
];
