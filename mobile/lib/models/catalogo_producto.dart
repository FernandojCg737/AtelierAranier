import '../core/api_config.dart';

/// Espejo de `CatalogoVarianteOut` — el `id` aca ES el id de la fila de
/// Inventario, usado para `PUT /productos/{id}/inventario/{varianteId}`.
class CatalogoVariante {
  const CatalogoVariante({required this.id, required this.tallaCodigo, required this.colorNombre, required this.cantidad});

  final int id;
  final String tallaCodigo;
  final String colorNombre;
  final int cantidad;

  CatalogoVariante copyWith({int? cantidad}) =>
      CatalogoVariante(id: id, tallaCodigo: tallaCodigo, colorNombre: colorNombre, cantidad: cantidad ?? this.cantidad);

  factory CatalogoVariante.fromJson(Map<String, dynamic> json) {
    return CatalogoVariante(
      id: json['id'] as int,
      tallaCodigo: json['talla_codigo'] as String,
      colorNombre: json['color_nombre'] as String,
      cantidad: json['cantidad'] as int,
    );
  }
}

/// Espejo de `CatalogoProductoOut` (GET /catalogo/sucursales/{id}/productos)
/// — CU08/CU12.
class CatalogoProducto {
  const CatalogoProducto({
    required this.id,
    required this.nombre,
    required this.marcaNombre,
    required this.categoriaNombre,
    required this.precio,
    this.imagenUrl,
    required this.cantidadTotal,
    required this.disponible,
    required this.variantes,
  });

  final int id;
  final String nombre;
  final String marcaNombre;
  final String categoriaNombre;
  final double precio;
  final String? imagenUrl;
  final int cantidadTotal;
  final bool disponible;
  final List<CatalogoVariante> variantes;

  CatalogoProducto recomputado(List<CatalogoVariante> nuevasVariantes) {
    final total = nuevasVariantes.fold<int>(0, (sum, v) => sum + v.cantidad);
    return CatalogoProducto(
      id: id,
      nombre: nombre,
      marcaNombre: marcaNombre,
      categoriaNombre: categoriaNombre,
      precio: precio,
      imagenUrl: imagenUrl,
      cantidadTotal: total,
      disponible: total > 0,
      variantes: nuevasVariantes,
    );
  }

  factory CatalogoProducto.fromJson(Map<String, dynamic> json) {
    return CatalogoProducto(
      id: json['id'] as int,
      nombre: json['nombre'] as String,
      marcaNombre: json['marca_nombre'] as String,
      categoriaNombre: json['categoria_nombre'] as String,
      precio: double.parse(json['precio'].toString()),
      imagenUrl: json['imagen_url'] == null ? null : resolveImageUrl(json['imagen_url'] as String),
      cantidadTotal: json['cantidad_total'] as int,
      disponible: json['disponible'] as bool,
      variantes: (json['variantes'] as List<dynamic>).map((e) => CatalogoVariante.fromJson(e as Map<String, dynamic>)).toList(),
    );
  }
}
