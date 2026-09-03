/// Espejo de `SucursalOut` (GET/POST/PUT/DELETE /sucursales) — CU04.
/// Nota: el estado de sucursal usa "activa/inactiva" (no "activo/inactivo"
/// como el resto de entidades).
class SucursalAdmin {
  const SucursalAdmin({
    required this.id,
    required this.nombre,
    required this.ciudadId,
    required this.ciudadNombre,
    required this.departamento,
    required this.direccion,
    this.horarioAtencion,
    this.telefono,
    required this.estado,
    required this.fechaCreacion,
  });

  final int id;
  final String nombre;
  final int ciudadId;
  final String ciudadNombre;
  final String departamento;
  final String direccion;
  final String? horarioAtencion;
  final String? telefono;
  final String estado; // activa | inactiva
  final String fechaCreacion;

  factory SucursalAdmin.fromJson(Map<String, dynamic> json) {
    return SucursalAdmin(
      id: json['id'] as int,
      nombre: json['nombre'] as String,
      ciudadId: json['ciudad_id'] as int,
      ciudadNombre: json['ciudad_nombre'] as String,
      departamento: json['departamento'] as String,
      direccion: json['direccion'] as String,
      horarioAtencion: json['horario_atencion'] as String?,
      telefono: json['telefono'] as String?,
      estado: json['estado'] as String,
      fechaCreacion: json['fecha_creacion'] as String,
    );
  }
}
