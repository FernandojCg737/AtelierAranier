/// Espejo de `MensajeOut` (backend, CU19).
class ChatMensaje {
  const ChatMensaje({required this.id, required this.remitente, required this.mensaje, required this.fecha});

  final int id;
  final String remitente; // 'cliente' | 'bot'
  final String mensaje;
  final DateTime fecha;

  bool get esBot => remitente == 'bot';

  factory ChatMensaje.fromJson(Map<String, dynamic> json) {
    return ChatMensaje(
      id: json['id'] as int,
      remitente: json['remitente'] as String,
      mensaje: json['mensaje'] as String,
      fecha: DateTime.parse(json['fecha'] as String),
    );
  }
}
