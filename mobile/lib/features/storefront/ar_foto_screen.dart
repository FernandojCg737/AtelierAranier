import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

import '../auth/auth_provider.dart';

enum _Estado { eligiendo, subiendo, procesando, listo, error }

const _pollMs = 2500;

/// Probador CU09, modo VIRTUAL: a diferencia de ArTryonScreen (camara en
/// vivo via WebView), aca el cliente manda UNA sola foto -- tomada con la
/// camara del celular o elegida de la galeria (via image_picker, que ya
/// maneja permisos y UI nativa, sin necesidad de armar una vista de camara
/// propia como en la web) -- y el mismo backend/flujo que la web: sube el
/// archivo, consulta el estado cada _pollMs y muestra el resultado.
class ArFotoScreen extends ConsumerStatefulWidget {
  const ArFotoScreen({super.key, required this.productoId});

  final int productoId;

  @override
  ConsumerState<ArFotoScreen> createState() => _ArFotoScreenState();
}

class _ArFotoScreenState extends ConsumerState<ArFotoScreen> {
  _Estado _estado = _Estado.eligiendo;
  String? _resultadoUrl;
  Timer? _pollTimer;
  bool _disposed = false;

  Future<void> _elegir(ImageSource source) async {
    final XFile? archivo;
    try {
      archivo = await ImagePicker().pickImage(source: source, imageQuality: 85);
    } catch (_) {
      if (mounted) setState(() => _estado = _Estado.error);
      return;
    }
    if (archivo == null) return;
    await _subir(archivo);
  }

  Future<void> _subir(XFile archivo) async {
    setState(() => _estado = _Estado.subiendo);
    try {
      final dio = ref.read(apiClientProvider).dio;
      final form = FormData.fromMap({
        'file': await MultipartFile.fromFile(archivo.path, filename: archivo.name),
      });
      final res = await dio.post('/productos/${widget.productoId}/ar-foto', data: form);
      if (_disposed) return;
      final jobId = (res.data as Map<String, dynamic>)['job_id'] as String;
      setState(() => _estado = _Estado.procesando);
      _pollTimer = Timer.periodic(const Duration(milliseconds: _pollMs), (_) => _consultarEstado(jobId));
    } catch (_) {
      if (!_disposed) setState(() => _estado = _Estado.error);
    }
  }

  Future<void> _consultarEstado(String jobId) async {
    try {
      final dio = ref.read(apiClientProvider).dio;
      final res = await dio.get('/productos/ar-foto/$jobId');
      if (_disposed) return;
      final data = res.data as Map<String, dynamic>;
      if (data['error'] == true) {
        _pollTimer?.cancel();
        setState(() => _estado = _Estado.error);
        return;
      }
      if (data['listo'] == true) {
        _pollTimer?.cancel();
        final base = dio.options.baseUrl;
        setState(() {
          _resultadoUrl = '$base/productos/ar-foto/$jobId/resultado';
          _estado = _Estado.listo;
        });
      }
    } catch (_) {
      if (!_disposed) {
        _pollTimer?.cancel();
        setState(() => _estado = _Estado.error);
      }
    }
  }

  void _reintentar() {
    setState(() {
      _estado = _Estado.eligiendo;
      _resultadoUrl = null;
    });
  }

  @override
  void dispose() {
    _disposed = true;
    _pollTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: SafeArea(
        child: Stack(
          children: [
            Center(child: Padding(padding: const EdgeInsets.all(24), child: _contenido())),
            Positioned(
              top: 8,
              right: 16,
              child: IconButton(
                icon: const CircleAvatar(backgroundColor: Colors.white70, child: Icon(Icons.close, color: Colors.black)),
                onPressed: () => Navigator.of(context).pop(),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _contenido() {
    switch (_estado) {
      case _Estado.eligiendo:
        return Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              'Elegi una foto tuya',
              style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
            ),
            const SizedBox(height: 6),
            const Text(
              'De frente, medio cuerpo o cuerpo entero.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.white70, fontSize: 12),
            ),
            const SizedBox(height: 28),
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Expanded(child: _opcion(Icons.camera_alt_outlined, 'Tomar una foto', () => _elegir(ImageSource.camera))),
                const SizedBox(width: 16),
                Expanded(
                  child: _opcion(Icons.photo_library_outlined, 'Subir desde la galeria', () => _elegir(ImageSource.gallery)),
                ),
              ],
            ),
          ],
        );
      case _Estado.subiendo:
      case _Estado.procesando:
        return Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const CircularProgressIndicator(color: Colors.white),
            const SizedBox(height: 16),
            Text(
              _estado == _Estado.subiendo
                  ? 'Subiendo tu foto...'
                  : 'Generando el resultado, puede tardar unos segundos...',
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
            ),
          ],
        );
      case _Estado.listo:
        return Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (_resultadoUrl != null)
              ConstrainedBox(
                constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.65),
                child: Image.network(_resultadoUrl!),
              ),
            const SizedBox(height: 20),
            _botonSecundario('PROBAR CON OTRA FOTO', _reintentar),
          ],
        );
      case _Estado.error:
        return Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              'No se pudo generar el resultado.',
              style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
            ),
            const SizedBox(height: 6),
            const Text(
              'Proba con otra foto en unos segundos.',
              style: TextStyle(color: Colors.white70, fontSize: 12),
            ),
            const SizedBox(height: 20),
            _botonSecundario('INTENTAR DE NUEVO', _reintentar),
          ],
        );
    }
  }

  Widget _opcion(IconData icon, String label, VoidCallback onTap) {
    return OutlinedButton(
      onPressed: onTap,
      style: OutlinedButton.styleFrom(
        foregroundColor: Colors.white,
        side: const BorderSide(color: Colors.white54),
        padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 8),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 30),
          const SizedBox(height: 10),
          Text(label, textAlign: TextAlign.center, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Widget _botonSecundario(String label, VoidCallback onTap) {
    return OutlinedButton(
      onPressed: onTap,
      style: OutlinedButton.styleFrom(
        foregroundColor: Colors.white,
        side: const BorderSide(color: Colors.white),
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 28),
      ),
      child: Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 0.5)),
    );
  }
}
