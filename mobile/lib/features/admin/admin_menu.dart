/// Espejo exacto de `pages/admin/admin-menu.ts` en la web: 5 paquetes con
/// sus CUs. Solo los CUs con `route` no nulo estan implementados (los demas
/// -CU09,10,11,13,14,16,18,19,20- no existen ni en la web ni en el backend).
class AdminUseCase {
  const AdminUseCase({required this.code, required this.label, this.route});

  final String code;
  final String label;
  final String? route;
}

class AdminPackage {
  const AdminPackage({required this.code, required this.label, required this.useCases});

  final String code;
  final String label;
  final List<AdminUseCase> useCases;
}

const adminMenu = <AdminPackage>[
  AdminPackage(
    code: 'P1',
    label: 'Gestion de Accesos y Seguridad',
    useCases: [
      AdminUseCase(code: 'CU01', label: 'Gestionar Inicio y Cierre de Sesion', route: '/admin/sesiones'),
      AdminUseCase(code: 'CU02', label: 'Administrar Usuarios, Roles y Permisos', route: '/admin/usuarios'),
      AdminUseCase(code: 'CU17', label: 'Auditar Operaciones (Bitacora)', route: '/admin/bitacora'),
    ],
  ),
  AdminPackage(
    code: 'P2',
    label: 'Gestion de Clientes y Sucursales',
    useCases: [
      AdminUseCase(code: 'CU03', label: 'Registrar y Administrar Clientes', route: '/admin/clientes'),
      AdminUseCase(code: 'CU04', label: 'Administrar Ciudades y Sucursales', route: '/admin/sucursales'),
      AdminUseCase(code: 'CU15', label: 'Actualizar Perfil de Usuario', route: '/perfil'),
    ],
  ),
  AdminPackage(
    code: 'P3',
    label: 'Gestion de Catalogo e Inventario',
    useCases: [
      AdminUseCase(code: 'CU05', label: 'Administrar Catalogo de Productos', route: '/admin/productos'),
      AdminUseCase(code: 'CU06', label: 'Administrar Proveedores', route: '/admin/proveedores'),
      AdminUseCase(code: 'CU07', label: 'Configurar Temporadas y Colecciones', route: '/admin/temporadas'),
      AdminUseCase(code: 'CU08', label: 'Consultar Catalogo y Disponibilidad', route: '/admin/catalogo'),
      AdminUseCase(code: 'CU12', label: 'Controlar Inventario por Sucursal', route: '/admin/inventario'),
    ],
  ),
  AdminPackage(
    code: 'P4',
    label: 'Gestion de Reservas y Ventas',
    useCases: [
      AdminUseCase(code: 'CU09', label: 'Visualizar Prenda con Realidad Aumentada'),
      AdminUseCase(code: 'CU10', label: 'Gestion de Reservas'),
      AdminUseCase(code: 'CU11', label: 'Gestion de Ventas'),
      AdminUseCase(code: 'CU13', label: 'Administrar Carrito de Compras'),
    ],
  ),
  AdminPackage(
    code: 'P5',
    label: 'Gestion de Experiencia y Analitica',
    useCases: [
      AdminUseCase(code: 'CU14', label: 'Enviar Notificaciones'),
      AdminUseCase(code: 'CU16', label: 'Gestion Reportes y Dashboards'),
      AdminUseCase(code: 'CU18', label: 'Recomendar Prendas por IA'),
      AdminUseCase(code: 'CU19', label: 'Atender Cliente con Chatbot'),
      AdminUseCase(code: 'CU20', label: 'Reputacion y Calificaciones'),
    ],
  ),
];
