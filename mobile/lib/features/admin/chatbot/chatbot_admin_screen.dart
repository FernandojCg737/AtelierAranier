import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme.dart';
import '../../../models/chat_mensaje.dart';
import '../../../models/chatbot_usuario.dart';
import '../admin_provider.dart';
import '../widgets/admin_widgets.dart';

/// CU19 "Atender Cliente con Chatbot" -- lista de clientes que usaron el
/// asistente virtual; al tocar uno se ve la conversacion completa.
class ChatbotAdminScreen extends ConsumerStatefulWidget {
  const ChatbotAdminScreen({super.key});

  @override
  ConsumerState<ChatbotAdminScreen> createState() => _ChatbotAdminScreenState();
}

class _ChatbotAdminScreenState extends ConsumerState<ChatbotAdminScreen> {
  late Future<List<ChatbotUsuario>> _future;

  @override
  void initState() {
    super.initState();
    _future = ref.read(adminRepositoryProvider).getChatbotUsuarios();
  }

  @override
  Widget build(BuildContext context) {
    return AdminScaffold(
      title: 'CHATBOT',
      body: FutureBuilder<List<ChatbotUsuario>>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return const Center(child: Text('No pudimos cargar los usuarios del chatbot.'));
          }
          final usuarios = snapshot.data ?? [];
          if (usuarios.isEmpty) {
            return const Center(child: Text('Todavia nadie uso el chatbot.'));
          }
          return ListView(
            padding: const EdgeInsets.only(top: 8, bottom: 8),
            children: [for (final u in usuarios) _UsuarioCard(usuario: u)],
          );
        },
      ),
    );
  }
}

class _UsuarioCard extends StatelessWidget {
  const _UsuarioCard({required this.usuario});
  final ChatbotUsuario usuario;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () => Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => ChatbotTranscripcionScreen(clienteId: usuario.clienteId, clienteNombre: usuario.clienteNombre)),
      ),
      child: AdminCard(
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(usuario.clienteNombre, style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.brandDark)),
                  Text(usuario.clienteEmail, style: const TextStyle(fontSize: 11, color: AppColors.grayTextDark)),
                  const SizedBox(height: 4),
                  Text('${usuario.totalMensajes} mensajes', style: const TextStyle(fontSize: 11, color: AppColors.grayText)),
                ],
              ),
            ),
            const Icon(Icons.chevron_right, color: AppColors.grayText),
          ],
        ),
      ),
    );
  }
}

class ChatbotTranscripcionScreen extends ConsumerStatefulWidget {
  const ChatbotTranscripcionScreen({super.key, required this.clienteId, required this.clienteNombre});

  final int clienteId;
  final String clienteNombre;

  @override
  ConsumerState<ChatbotTranscripcionScreen> createState() => _ChatbotTranscripcionScreenState();
}

class _ChatbotTranscripcionScreenState extends ConsumerState<ChatbotTranscripcionScreen> {
  late Future<List<ChatMensaje>> _future;

  @override
  void initState() {
    super.initState();
    _future = ref.read(adminRepositoryProvider).getChatbotTranscripcion(widget.clienteId);
  }

  @override
  Widget build(BuildContext context) {
    return AdminScaffold(
      title: widget.clienteNombre.toUpperCase(),
      body: FutureBuilder<List<ChatMensaje>>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return const Center(child: Text('No pudimos cargar la conversacion.'));
          }
          final mensajes = snapshot.data ?? [];
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [for (final m in mensajes) _MensajeBubble(mensaje: m)],
          );
        },
      ),
    );
  }
}

class _MensajeBubble extends StatelessWidget {
  const _MensajeBubble({required this.mensaje});
  final ChatMensaje mensaje;

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: mensaje.esBot ? Alignment.centerLeft : Alignment.centerRight,
      child: Container(
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.78),
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: mensaje.esBot ? Colors.white : AppColors.brandDark,
          border: mensaje.esBot ? Border.all(color: AppColors.grayBorderLight) : null,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(mensaje.esBot ? 'ASISTENTE' : 'CLIENTE', style: TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: mensaje.esBot ? AppColors.grayText : Colors.white70)),
            const SizedBox(height: 2),
            Text(mensaje.mensaje, style: TextStyle(fontSize: 13, color: mensaje.esBot ? AppColors.brandDark : Colors.white)),
          ],
        ),
      ),
    );
  }
}
