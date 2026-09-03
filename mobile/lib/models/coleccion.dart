/// Espejo de `ColeccionOut` (GET/POST/PUT/DELETE /colecciones) — CU07.
class Coleccion {
  const Coleccion({
    required this.id,
    required this.temporadaId,
    required this.temporadaNombre,
    required this.nombre,
    this.descripcion,
  });

  final int id;
  final int temporadaId;
  final String temporadaNombre;
  final String nombre;
  final String? descripcion;

  factory Coleccion.fromJson(Map<String, dynamic> json) {
    return Coleccion(
      id: json['id'] as int,
      temporadaId: json['temporada_id'] as int,
      temporadaNombre: json['temporada_nombre'] as String,
      nombre: json['nombre'] as String,
      descripcion: json['descripcion'] as String?,
    );
  }
}
