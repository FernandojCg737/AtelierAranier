import '../core/api_config.dart';

/// Espejo de `ImagenOut`.
class ImagenProducto {
  const ImagenProducto({required this.id, required this.url, required this.orden});

  final int id;
  final String url;
  final int orden;

  factory ImagenProducto.fromJson(Map<String, dynamic> json) {
    return ImagenProducto(
      id: json['id'] as int,
      url: resolveImageUrl(json['url'] as String),
      orden: json['orden'] as int,
    );
  }
}

/// Espejo de `DisponibilidadOut`.
class DisponibilidadSucursal {
  const DisponibilidadSucursal({required this.sucursalNombre, required this.cantidad});

  final String sucursalNombre;
  final int cantidad;

  factory DisponibilidadSucursal.fromJson(Map<String, dynamic> json) {
    return DisponibilidadSucursal(sucursalNombre: json['sucursal_nombre'] as String, cantidad: json['cantidad'] as int);
  }
}

/// Espejo de `ProductoOut` (GET/POST/PUT /productos, admin) — CU05. Distinto
/// de `ProductoPublico` (imagenes/disponibilidad son objetos, no strings).
class ProductoAdmin {
  const ProductoAdmin({
    required this.id,
    required this.nombre,
    this.descripcion,
    required this.precio,
    this.precioOriginal,
    required this.estado,
    required this.categoriaId,
    required this.categoriaNombre,
    required this.marcaId,
    required this.marcaNombre,
    required this.proveedorId,
    required this.proveedorNombre,
    required this.temporadaId,
    required this.temporadaNombre,
    required this.coleccionId,
    required this.coleccionNombre,
    required this.imagenes,
    required this.sucursalesDisponibles,
  });

  final int id;
  final String nombre;
  final String? descripcion;
  final double precio;
  final double? precioOriginal;
  final String estado; // activo | inactivo
  final int categoriaId;
  final String categoriaNombre;
  final int marcaId;
  final String marcaNombre;
  final int proveedorId;
  final String proveedorNombre;
  final int temporadaId;
  final String temporadaNombre;
  final int coleccionId;
  final String coleccionNombre;
  final List<ImagenProducto> imagenes;
  final List<DisponibilidadSucursal> sucursalesDisponibles;

  factory ProductoAdmin.fromJson(Map<String, dynamic> json) {
    return ProductoAdmin(
      id: json['id'] as int,
      nombre: json['nombre'] as String,
      descripcion: json['descripcion'] as String?,
      precio: double.parse(json['precio'].toString()),
      precioOriginal: json['precio_original'] == null ? null : double.parse(json['precio_original'].toString()),
      estado: json['estado'] as String,
      categoriaId: json['categoria_id'] as int,
      categoriaNombre: json['categoria_nombre'] as String,
      marcaId: json['marca_id'] as int,
      marcaNombre: json['marca_nombre'] as String,
      proveedorId: json['proveedor_id'] as int,
      proveedorNombre: json['proveedor_nombre'] as String,
      temporadaId: json['temporada_id'] as int,
      temporadaNombre: json['temporada_nombre'] as String,
      coleccionId: json['coleccion_id'] as int,
      coleccionNombre: json['coleccion_nombre'] as String,
      imagenes: (json['imagenes'] as List<dynamic>).map((e) => ImagenProducto.fromJson(e as Map<String, dynamic>)).toList(),
      sucursalesDisponibles: (json['sucursales_disponibles'] as List<dynamic>)
          .map((e) => DisponibilidadSucursal.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}
