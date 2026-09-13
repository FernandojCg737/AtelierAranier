import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/chat_mensaje.dart';
import '../auth/auth_provider.dart';

class ChatbotRepository {
  ChatbotRepository(this._dio);

  final Dio _dio;

  Future<List<ChatMensaje>> misMensajes() async {
    final res = await _dio.get('/chatbot/mias');
    return (res.data as List<dynamic>).map((e) => ChatMensaje.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<ChatMensaje> enviar(String mensaje) async {
    final res = await _dio.post('/chatbot/mensajes', data: {'mensaje': mensaje});
    return ChatMensaje.fromJson(res.data as Map<String, dynamic>);
  }
}

final chatbotRepositoryProvider = Provider<ChatbotRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return ChatbotRepository(apiClient.dio);
});

class ChatbotState {
  const ChatbotState({this.mensajes = const [], this.enviando = false});

  final List<ChatMensaje> mensajes;
  final bool enviando;

  ChatbotState copyWith({List<ChatMensaje>? mensajes, bool? enviando}) {
    return ChatbotState(mensajes: mensajes ?? this.mensajes, enviando: enviando ?? this.enviando);
  }
}

/// CU19: historial de la conversacion con el asistente. El backend arma la
/// respuesta (motor de contexto real del catalogo/stock + Gemini); aca solo
/// se manda el mensaje y se muestra lo que vuelve -- igual que
/// `services/chatbot.ts` en la web.
class ChatbotNotifier extends StateNotifier<ChatbotState> {
  ChatbotNotifier(this._repo) : super(const ChatbotState());

  final ChatbotRepository _repo;

  Future<void> cargar() async {
    try {
      state = state.copyWith(mensajes: await _repo.misMensajes());
    } catch (_) {
      state = state.copyWith(mensajes: const []);
    }
  }

  void limpiarLocal() {
    state = const ChatbotState();
  }

  /// Devuelve el mensaje del bot (para que la pantalla lo lea en voz alta
  /// si corresponde) o null si fallo.
  Future<ChatMensaje?> enviar(String texto) async {
    final limpio = texto.trim();
    if (limpio.isEmpty) return null;

    final optimista = ChatMensaje(
      id: -DateTime.now().millisecondsSinceEpoch,
      remitente: 'cliente',
      mensaje: limpio,
      fecha: DateTime.now(),
    );
    state = state.copyWith(mensajes: [...state.mensajes, optimista], enviando: true);

    try {
      final respuesta = await _repo.enviar(limpio);
      state = state.copyWith(mensajes: [...state.mensajes, respuesta], enviando: false);
      return respuesta;
    } catch (_) {
      final fallback = ChatMensaje(
        id: -DateTime.now().millisecondsSinceEpoch,
        remitente: 'bot',
        mensaje: 'No pudimos conectar con el asistente. Intenta de nuevo en un momento.',
        fecha: DateTime.now(),
      );
      state = state.copyWith(mensajes: [...state.mensajes, fallback], enviando: false);
      return null;
    }
  }
}

final chatbotProvider = StateNotifierProvider<ChatbotNotifier, ChatbotState>((ref) {
  final repo = ref.watch(chatbotRepositoryProvider);
  return ChatbotNotifier(repo);
});
