/// Espejo de `CarritoAdminOut` (GET /carritos) -- CU13 admin.
class CarritoAdmin {
  const CarritoAdmin({
    required this.id,
    required this.clienteNombre,
    required this.clienteEmail,
    required this.cantidadItems,
    required this.total,
    required this.fechaActualizacion,
    required this.detalles,
  });

  final int id;
  final String clienteNombre;
  final String clienteEmail;
  final int cantidadItems;
  final double total;
  final DateTime fechaActualizacion;
  final List<String> detalles;

  factory CarritoAdmin.fromJson(Map<String, dynamic> json) {
    final detalles = (json['detalles'] as List<dynamic>)
        .map((e) => '${e['cantidad']}x ${e['producto_nombre']}')
        .toList();
    return CarritoAdmin(
      id: json['id'] as int,
      clienteNombre: json['cliente_nombre'] as String,
      clienteEmail: json['cliente_email'] as String,
      cantidadItems: json['cantidad_items'] as int,
      total: num.parse(json['total'].toString()).toDouble(),
      fechaActualizacion: DateTime.parse(json['fecha_actualizacion'] as String),
      detalles: detalles,
    );
  }
}
