/// Espejo de `EmpleadoOut` (GET/POST/PUT /empleados) — CU02.
class Empleado {
  const Empleado({
    required this.id,
    required this.nombre,
    required this.email,
    required this.tipo,
    required this.estado,
    required this.fechaRegistro,
    required this.metodoRegistro,
    this.sucursalId,
    this.sucursalNombre,
    this.rolId,
    this.rolNombre,
  });

  final int id;
  final String nombre;
  final String email;
  final String tipo; // administrador | encargado_sucursal | cajero
  final String estado; // activo | inactivo
  final String fechaRegistro;
  final String metodoRegistro;
  final int? sucursalId;
  final String? sucursalNombre;
  final int? rolId;
  final String? rolNombre;

  factory Empleado.fromJson(Map<String, dynamic> json) {
    return Empleado(
      id: json['id'] as int,
      nombre: json['nombre'] as String,
      email: json['email'] as String,
      tipo: json['tipo'] as String,
      estado: json['estado'] as String,
      fechaRegistro: json['fecha_registro'] as String,
      metodoRegistro: json['metodo_registro'] as String,
      sucursalId: json['sucursal_id'] as int?,
      sucursalNombre: json['sucursal_nombre'] as String?,
      rolId: json['rol_id'] as int?,
      rolNombre: json['rol_nombre'] as String?,
    );
  }
}
