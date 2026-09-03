import '../core/api_config.dart';

/// Espejo de `ProductoPublicoOut` (GET /productos/publico[/:id]).
class ProductoPublico {
  const ProductoPublico({
    required this.id,
    required this.nombre,
    this.descripcion,
    required this.precio,
    this.precioOriginal,
    required this.marcaNombre,
    required this.categoriaNombre,
    required this.temporadaNombre,
    required this.imagenes,
    required this.sucursalesDisponibles,
  });

  final int id;
  final String nombre;
  final String? descripcion;
  final double precio;
  final double? precioOriginal;
  final String marcaNombre;
  final String categoriaNombre;
  final String temporadaNombre;
  final List<String> imagenes;
  final List<String> sucursalesDisponibles;

  bool get agotado => sucursalesDisponibles.isEmpty;

  bool get tieneDescuento => precioOriginal != null && precioOriginal! > precio;

  int? get porcentajeDescuento {
    if (!tieneDescuento) return null;
    return (100 - (precio / precioOriginal! * 100)).round();
  }

  String? get imagenPrincipal => imagenes.isEmpty ? null : imagenes.first;

  factory ProductoPublico.fromJson(Map<String, dynamic> json) {
    return ProductoPublico(
      id: json['id'] as int,
      nombre: json['nombre'] as String,
      descripcion: json['descripcion'] as String?,
      precio: double.parse(json['precio'].toString()),
      precioOriginal:
          json['precio_original'] == null ? null : double.parse(json['precio_original'].toString()),
      marcaNombre: json['marca_nombre'] as String,
      categoriaNombre: json['categoria_nombre'] as String,
      temporadaNombre: json['temporada_nombre'] as String,
      imagenes: (json['imagenes'] as List<dynamic>? ?? []).map((e) => resolveImageUrl(e.toString())).toList(),
      sucursalesDisponibles:
          (json['sucursales_disponibles'] as List<dynamic>? ?? []).map((e) => e.toString()).toList(),
    );
  }
}
