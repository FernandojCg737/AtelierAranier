import 'package:flutter/material.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:webview_flutter/webview_flutter.dart';

import '../../core/api_config.dart';
import '../../core/secure_storage.dart';

/// Probador virtual con realidad aumentada (CU09): mismo motor que la web
/// (Decart lucy-vton, en vivo por WebRTC). `@decartai/sdk` es un paquete
/// JS sin equivalente Dart, asi que en vez de reimplementar el protocolo
/// WebRTC de Decart a mano, esta pantalla reutiliza la misma pagina que ya
/// funciona en la web dentro de un WebView (servida por el backend en
/// `/ar-embed/<producto_id>`, ver `arEmbedUrl` en `api_config.dart`).
class ArTryonScreen extends StatefulWidget {
  const ArTryonScreen({super.key, required this.productoId});

  final int productoId;

  @override
  State<ArTryonScreen> createState() => _ArTryonScreenState();
}

class _ArTryonScreenState extends State<ArTryonScreen> {
  WebViewController? _controller;
  bool _sinPermiso = false;

  @override
  void initState() {
    super.initState();
    _iniciar();
  }

  Future<void> _iniciar() async {
    // WebViewController.onPermissionRequest solo reenvia el pedido de la
    // pagina al WebView: en Android 6+/iOS el permiso de camara del
    // sistema operativo (runtime) tiene que estar concedido antes, o el
    // grant() de mas abajo no sirve de nada.
    final estado = await Permission.camera.request();
    if (!mounted) return;
    if (!estado.isGranted) {
      setState(() => _sinPermiso = true);
      return;
    }

    // CU09 requiere sesion iniciada (queda registrado quien probo cada
    // prenda); esta pantalla ya solo se abre si hay sesion (ver el chequeo
    // en producto_detalle_screen.dart antes de navegar aca), pero el token
    // se lee igual aca porque quien arma la URL final es esta pantalla.
    final token = await SecureStorage().readToken();

    final controller = WebViewController(onPermissionRequest: (request) => request.grant())
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setBackgroundColor(Colors.black)
      ..setOnConsoleMessage((message) => debugPrint('[ar-embed] ${message.message}'))
      ..loadRequest(Uri.parse(arEmbedUrl(widget.productoId, token: token)));

    if (!mounted) return;
    setState(() => _controller = controller);
  }

  @override
  void dispose() {
    // Best-effort: corta la conexion con Decart y apaga la camara antes de
    // que se destruya el WebView (dispose es sincrono, no se puede esperar
    // el resultado). Si esto no llega a correr, destruir el WebView igual
    // corta la conexion nativa, solo que no tan prolijo.
    _controller?.runJavaScript('window.pararTodo && window.pararTodo()').catchError((_) {});
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final controller = _controller;

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          if (controller != null) WebViewWidget(controller: controller),
          if (_sinPermiso)
            Container(
              color: const Color(0xD9203C40),
              alignment: Alignment.center,
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text(
                    'No se pudo acceder a la camara.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Da permiso de camara en los ajustes de la app y vuelve a intentar.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Colors.white70, fontSize: 13),
                  ),
                  const SizedBox(height: 16),
                  OutlinedButton(
                    onPressed: openAppSettings,
                    style: OutlinedButton.styleFrom(foregroundColor: Colors.white, side: const BorderSide(color: Colors.white)),
                    child: const Text('ABRIR AJUSTES'),
                  ),
                ],
              ),
            ),
          Positioned(
            top: MediaQuery.of(context).padding.top + 8,
            right: 16,
            child: IconButton(
              icon: const CircleAvatar(
                backgroundColor: Colors.white70,
                child: Icon(Icons.close, color: Colors.black),
              ),
              onPressed: () => Navigator.of(context).pop(),
            ),
          ),
        ],
      ),
    );
  }
}
