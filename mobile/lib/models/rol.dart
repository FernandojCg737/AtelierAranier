/// Espejo de `PermisoOut` y `RolOut` (GET /roles, GET /roles/permisos) — CU02.
class Permiso {
  const Permiso({required this.id, required this.nombre, this.descripcion});

  final int id;
  final String nombre; // codigo CU, ej. "CU05"
  final String? descripcion;

  factory Permiso.fromJson(Map<String, dynamic> json) {
    return Permiso(id: json['id'] as int, nombre: json['nombre'] as String, descripcion: json['descripcion'] as String?);
  }
}

class Rol {
  const Rol({required this.id, required this.nombre, this.descripcion, required this.permisos});

  final int id;
  final String nombre;
  final String? descripcion;
  final List<String> permisos; // lista de codigos CU

  factory Rol.fromJson(Map<String, dynamic> json) {
    return Rol(
      id: json['id'] as int,
      nombre: json['nombre'] as String,
      descripcion: json['descripcion'] as String?,
      permisos: (json['permisos'] as List<dynamic>? ?? []).map((e) => e.toString()).toList(),
    );
  }
}
