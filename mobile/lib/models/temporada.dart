/// Espejo de `TemporadaOut` (GET /temporadas/publico).
class Temporada {
  const Temporada({required this.id, required this.nombre, required this.fechaInicio, required this.fechaFin});

  final int id;
  final String nombre;
  final DateTime fechaInicio;
  final DateTime fechaFin;

  factory Temporada.fromJson(Map<String, dynamic> json) {
    return Temporada(
      id: json['id'] as int,
      nombre: json['nombre'] as String,
      fechaInicio: DateTime.parse(json['fecha_inicio'] as String),
      fechaFin: DateTime.parse(json['fecha_fin'] as String),
    );
  }
}
