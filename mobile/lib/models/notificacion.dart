/// Espejo de `NotificacionOut` (backend, CU14). Generadas automaticamente
/// por triggers (reserva creada/cancelada/vencida, pago confirmado/
/// rechazado) mas un barrido perezoso para las que estan por vencer -- el
/// cliente solo las lee y las marca como leidas, no las crea.
class Notificacion {
  const Notificacion({
    required this.id,
    required this.tipoEvento,
    required this.mensaje,
    required this.fechaEnvio,
    required this.leida,
    this.entidadTipo,
    this.entidadId,
  });

  final int id;
  final String tipoEvento;
  final String mensaje;
  final DateTime fechaEnvio;
  final bool leida;
  final String? entidadTipo;
  final int? entidadId;

  Notificacion copyWith({bool? leida}) => Notificacion(
    id: id,
    tipoEvento: tipoEvento,
    mensaje: mensaje,
    fechaEnvio: fechaEnvio,
    leida: leida ?? this.leida,
    entidadTipo: entidadTipo,
    entidadId: entidadId,
  );

  factory Notificacion.fromJson(Map<String, dynamic> json) {
    return Notificacion(
      id: json['id'] as int,
      tipoEvento: json['tipo_evento'] as String,
      mensaje: json['mensaje'] as String,
      fechaEnvio: DateTime.parse(json['fecha_envio'] as String),
      leida: json['leida'] as bool,
      entidadTipo: json['entidad_tipo'] as String?,
      entidadId: json['entidad_id'] as int?,
    );
  }
}
