/// Espejo de `SucursalPublicaOut` (GET /sucursales/publico).
class SucursalPublica {
  const SucursalPublica({
    required this.id,
    required this.nombre,
    required this.direccion,
    this.horarioAtencion,
  });

  final int id;
  final String nombre;
  final String direccion;
  final String? horarioAtencion;

  factory SucursalPublica.fromJson(Map<String, dynamic> json) {
    return SucursalPublica(
      id: json['id'] as int,
      nombre: json['nombre'] as String,
      direccion: json['direccion'] as String,
      horarioAtencion: json['horario_atencion'] as String?,
    );
  }
}
