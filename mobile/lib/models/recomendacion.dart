/// Espejo de `RecomendacionOut` (backend, CU18). El ranking lo calcula un
/// motor de reglas en SQL (compra conjunta / similar / mas vendidos); la
/// IA (Gemini) solo redacta `razon`.
class Recomendacion {
  const Recomendacion({
    required this.productoId,
    required this.productoNombre,
    required this.origen,
    required this.razon,
  });

  final int productoId;
  final String productoNombre;
  final String origen;
  final String razon;

  factory Recomendacion.fromJson(Map<String, dynamic> json) {
    return Recomendacion(
      productoId: json['producto_id'] as int,
      productoNombre: json['producto_nombre'] as String,
      origen: json['origen'] as String,
      razon: json['razon'] as String,
    );
  }
}
