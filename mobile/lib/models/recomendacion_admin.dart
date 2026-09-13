/// Espejo de `RecomendacionAdminOut`/`RecomendacionPage` (GET /recomendaciones)
/// -- CU18 admin.
class RecomendacionAdmin {
  const RecomendacionAdmin({
    required this.id,
    required this.clienteNombre,
    required this.clienteEmail,
    required this.productoNombre,
    required this.origen,
    this.razon,
    required this.convertido,
    required this.fecha,
  });

  final int id;
  final String clienteNombre;
  final String clienteEmail;
  final String productoNombre;
  final String origen;
  final String? razon;
  final bool convertido;
  final DateTime fecha;

  factory RecomendacionAdmin.fromJson(Map<String, dynamic> json) {
    return RecomendacionAdmin(
      id: json['id'] as int,
      clienteNombre: json['cliente_nombre'] as String,
      clienteEmail: json['cliente_email'] as String,
      productoNombre: json['producto_nombre'] as String,
      origen: json['origen'] as String,
      razon: json['razon'] as String?,
      convertido: json['convertido'] as bool,
      fecha: DateTime.parse(json['fecha'] as String),
    );
  }
}

class RecomendacionResumen {
  const RecomendacionResumen({required this.totalActivas, required this.convertidas, required this.tasaConversion});

  final int totalActivas;
  final int convertidas;
  final double tasaConversion;

  factory RecomendacionResumen.fromJson(Map<String, dynamic> json) {
    return RecomendacionResumen(
      totalActivas: json['total_activas'] as int,
      convertidas: json['convertidas'] as int,
      tasaConversion: num.parse(json['tasa_conversion'].toString()).toDouble(),
    );
  }
}

class RecomendacionPage {
  const RecomendacionPage({required this.resumen, required this.items, required this.total, required this.page, required this.pageSize});

  final RecomendacionResumen resumen;
  final List<RecomendacionAdmin> items;
  final int total;
  final int page;
  final int pageSize;

  int get totalPages => (total / pageSize).ceil().clamp(1, 999999);

  factory RecomendacionPage.fromJson(Map<String, dynamic> json) {
    return RecomendacionPage(
      resumen: RecomendacionResumen.fromJson(json['resumen'] as Map<String, dynamic>),
      items: (json['items'] as List<dynamic>).map((e) => RecomendacionAdmin.fromJson(e as Map<String, dynamic>)).toList(),
      total: json['total'] as int,
      page: json['page'] as int,
      pageSize: json['page_size'] as int,
    );
  }
}
