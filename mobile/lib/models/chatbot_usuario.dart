/// Espejo de `ChatbotUsuarioOut` (GET /chatbot) -- CU19 admin.
class ChatbotUsuario {
  const ChatbotUsuario({
    required this.clienteId,
    required this.clienteNombre,
    required this.clienteEmail,
    required this.totalMensajes,
    required this.ultimaActividad,
  });

  final int clienteId;
  final String clienteNombre;
  final String clienteEmail;
  final int totalMensajes;
  final DateTime ultimaActividad;

  factory ChatbotUsuario.fromJson(Map<String, dynamic> json) {
    return ChatbotUsuario(
      clienteId: json['cliente_id'] as int,
      clienteNombre: json['cliente_nombre'] as String,
      clienteEmail: json['cliente_email'] as String,
      totalMensajes: json['total_mensajes'] as int,
      ultimaActividad: DateTime.parse(json['ultima_actividad'] as String),
    );
  }
}
