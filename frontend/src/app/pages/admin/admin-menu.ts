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
      { code: 'CU19', label: 'Auditar Operaciones (Bitacora)', route: '/admin/bitacora' },
    ],
  },
  {
    code: 'P2',
    label: 'Gestion de Clientes y Sucursales',
    useCases: [
      { code: 'CU03', label: 'Registrar y Administrar Clientes', route: '/admin/clientes' },
      { code: 'CU04', label: 'Administrar Ciudades y Sucursales', route: '/admin/sucursales' },
      { code: 'CU17', label: 'Actualizar Perfil de Usuario', route: '/admin/perfil' },
    ],
  },
  {
    code: 'P3',
    label: 'Gestion de Catalogo e Inventario',
    useCases: [
      { code: 'CU05', label: 'Administrar Catalogo de Productos' },
      { code: 'CU06', label: 'Administrar Proveedores' },
      { code: 'CU07', label: 'Configurar Temporadas y Colecciones' },
      { code: 'CU08', label: 'Consultar Catalogo y Disponibilidad' },
      { code: 'CU12', label: 'Controlar Inventario por Sucursal' },
    ],
  },
  {
    code: 'P4',
    label: 'Gestion de Reservas y Ventas',
    useCases: [
      { code: 'CU09', label: 'Visualizar Prenda con Realidad Aumentada' },
      { code: 'CU10', label: 'Solicitar y Administrar Reservas' },
      { code: 'CU11', label: 'Atender Reservas en Sucursal' },
      { code: 'CU13', label: 'Administrar Carrito de Compras' },
      { code: 'CU14', label: 'Registrar Venta Presencial' },
      { code: 'CU15', label: 'Procesar Compra Digital' },
    ],
  },
  {
    code: 'P5',
    label: 'Gestion de Experiencia y Analitica',
    useCases: [
      { code: 'CU16', label: 'Enviar Notificaciones' },
      { code: 'CU18', label: 'Generar Reportes y Dashboards' },
      { code: 'CU20', label: 'Recomendar Prendas por IA' },
      { code: 'CU21', label: 'Atender Cliente con Chatbot' },
    ],
  },
];
