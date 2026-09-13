/// Espejo de `NotificacionAdminOut`/`NotificacionPage` (GET /notificaciones)
/// -- CU14 admin.
class NotificacionAdmin {
  const NotificacionAdmin({
    required this.id,
    required this.tipoEvento,
    required this.mensaje,
    required this.fecha,
    required this.leida,
    required this.clienteNombre,
    required this.clienteEmail,
  });

  final int id;
  final String tipoEvento;
  final String mensaje;
  final DateTime fecha;
  final bool leida;
  final String clienteNombre;
  final String clienteEmail;

  factory NotificacionAdmin.fromJson(Map<String, dynamic> json) {
    return NotificacionAdmin(
      id: json['id'] as int,
      tipoEvento: json['tipo_evento'] as String,
      mensaje: json['mensaje'] as String,
      fecha: DateTime.parse(json['fecha'] as String),
      leida: json['leida'] as bool,
      clienteNombre: json['cliente_nombre'] as String,
      clienteEmail: json['cliente_email'] as String,
    );
  }
}

class NotificacionAdminPage {
  const NotificacionAdminPage({required this.items, required this.total, required this.page, required this.pageSize});

  final List<NotificacionAdmin> items;
  final int total;
  final int page;
  final int pageSize;

  int get totalPages => (total / pageSize).ceil().clamp(1, 999999);

  factory NotificacionAdminPage.fromJson(Map<String, dynamic> json) {
    return NotificacionAdminPage(
      items: (json['items'] as List<dynamic>).map((e) => NotificacionAdmin.fromJson(e as Map<String, dynamic>)).toList(),
      total: json['total'] as int,
      page: json['page'] as int,
      pageSize: json['page_size'] as int,
    );
  }
}
