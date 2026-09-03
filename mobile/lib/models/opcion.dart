/// Espejo de `OpcionOut` — shape generico `{id, nombre}` reutilizado por
/// `catalogo-base` (categorias/marcas/temporadas/colecciones/proveedores/
/// sucursales/tallas/colores) y por listas simples como `/sucursales`.
class Opcion {
  const Opcion({required this.id, required this.nombre});

  final int id;
  final String nombre;

  factory Opcion.fromJson(Map<String, dynamic> json) {
    return Opcion(id: json['id'] as int, nombre: json['nombre'] as String);
  }
}
