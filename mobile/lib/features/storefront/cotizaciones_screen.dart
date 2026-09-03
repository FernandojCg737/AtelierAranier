import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/theme.dart';

const _whatsappNumero = '59173766956';

class CotizacionesScreen extends StatefulWidget {
  const CotizacionesScreen({super.key});

  @override
  State<CotizacionesScreen> createState() => _CotizacionesScreenState();
}

class _CotizacionesScreenState extends State<CotizacionesScreen> {
  final _nombreCtrl = TextEditingController();
  final _telefonoCtrl = TextEditingController();
  final _productoCtrl = TextEditingController();
  final _detallesCtrl = TextEditingController();
  final _presupuestoCtrl = TextEditingController();

  @override
  void dispose() {
    _nombreCtrl.dispose();
    _telefonoCtrl.dispose();
    _productoCtrl.dispose();
    _detallesCtrl.dispose();
    _presupuestoCtrl.dispose();
    super.dispose();
  }

  Future<void> _enviar() async {
    final buffer = StringBuffer('Hola, quiero solicitar una cotizacion.');
    if (_nombreCtrl.text.trim().isNotEmpty) buffer.write('\nNombre: ${_nombreCtrl.text.trim()}');
    if (_telefonoCtrl.text.trim().isNotEmpty) buffer.write('\nTelefono: ${_telefonoCtrl.text.trim()}');
    if (_productoCtrl.text.trim().isNotEmpty) buffer.write('\nProducto: ${_productoCtrl.text.trim()}');
    if (_detallesCtrl.text.trim().isNotEmpty) buffer.write('\nDetalles: ${_detallesCtrl.text.trim()}');
    if (_presupuestoCtrl.text.trim().isNotEmpty) buffer.write('\nPresupuesto: ${_presupuestoCtrl.text.trim()}');

    final uri = Uri.https('wa.me', '/$_whatsappNumero', {'text': buffer.toString()});
    await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('COTIZACIONES')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            const EyebrowText('Solicita tu cotizacion'),
            const SizedBox(height: 8),
            const Text(
              'Contanos que buscas y te respondemos por WhatsApp.',
              style: TextStyle(color: AppColors.grayTextDark),
            ),
            const SizedBox(height: 24),
            TextField(controller: _nombreCtrl, decoration: const InputDecoration(labelText: 'NOMBRE')),
            const SizedBox(height: 16),
            TextField(
              controller: _telefonoCtrl,
              keyboardType: TextInputType.phone,
              decoration: const InputDecoration(labelText: 'TELEFONO'),
            ),
            const SizedBox(height: 16),
            TextField(controller: _productoCtrl, decoration: const InputDecoration(labelText: 'PRODUCTO DE INTERES')),
            const SizedBox(height: 16),
            TextField(
              controller: _detallesCtrl,
              maxLines: 3,
              decoration: const InputDecoration(labelText: 'DETALLES'),
            ),
            const SizedBox(height: 16),
            TextField(controller: _presupuestoCtrl, decoration: const InputDecoration(labelText: 'PRESUPUESTO')),
            const SizedBox(height: 28),
            ElevatedButton.icon(
              onPressed: _enviar,
              icon: const Icon(Icons.chat),
              label: const Text('ENVIAR POR WHATSAPP'),
            ),
          ],
        ),
      ),
    );
  }
}
