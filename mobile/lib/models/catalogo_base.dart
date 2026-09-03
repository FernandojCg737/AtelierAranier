import 'opcion.dart';

/// Espejo de `CatalogoBaseOut` (GET /productos/catalogo-base) — CU05.
/// Alimenta todos los selects del formulario de producto.
class CatalogoBase {
  const CatalogoBase({
    required this.categorias,
    required this.marcas,
    required this.temporadas,
    required this.colecciones,
    required this.proveedores,
    required this.sucursales,
    required this.tallas,
    required this.colores,
  });

  final List<Opcion> categorias;
  final List<Opcion> marcas;
  final List<Opcion> temporadas;
  final List<Opcion> colecciones;
  final List<Opcion> proveedores;
  final List<Opcion> sucursales;
  final List<Opcion> tallas;
  final List<Opcion> colores;

  static List<Opcion> _list(Map<String, dynamic> json, String key) =>
      (json[key] as List<dynamic>).map((e) => Opcion.fromJson(e as Map<String, dynamic>)).toList();

  factory CatalogoBase.fromJson(Map<String, dynamic> json) {
    return CatalogoBase(
      categorias: _list(json, 'categorias'),
      marcas: _list(json, 'marcas'),
      temporadas: _list(json, 'temporadas'),
      colecciones: _list(json, 'colecciones'),
      proveedores: _list(json, 'proveedores'),
      sucursales: _list(json, 'sucursales'),
      tallas: _list(json, 'tallas'),
      colores: _list(json, 'colores'),
    );
  }
}
