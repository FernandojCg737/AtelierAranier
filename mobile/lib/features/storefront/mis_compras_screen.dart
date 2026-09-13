import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_client.dart';
import '../../core/theme.dart';
import '../../models/venta.dart';
import 'ventas_repository.dart';

const _metodoLabel = {'paypal': 'PayPal / Tarjeta', 'qr': 'QR (transferencia)', 'efectivo': 'Efectivo en sucursal'};

const _estadoColor = {
  'completado': AppColors.success,
  'verificando': Color(0xFFB26A00),
  'pendiente': Color(0xFFB26A00),
  'rechazado': AppColors.danger,
};

/// CU11 (historial) + CU20 (calificar): lista de compras del cliente, con
/// la opcion de calificar (estrellas + comentario) las que ya estan
/// completadas y todavia no tienen calificacion -- mismo criterio que la
/// tab "Mis Compras" del perfil en la web.
class MisComprasScreen extends ConsumerStatefulWidget {
  const MisComprasScreen({super.key});

  @override
  ConsumerState<MisComprasScreen> createState() => _MisComprasScreenState();
}

class _MisComprasScreenState extends ConsumerState<MisComprasScreen> {
  late Future<List<Venta>> _future;
  int? _calificandoVentaId;
  int _estrellas = 0;
  final _comentarioCtrl = TextEditingController();
  bool _guardando = false;
  String? _errorCalificacion;

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  void _cargar() {
    _future = ref.read(ventasRepositoryProvider).misCompras();
  }

  @override
  void dispose() {
    _comentarioCtrl.dispose();
    super.dispose();
  }

  void _abrirCalificar(Venta v) {
    setState(() {
      _calificandoVentaId = v.id;
      _estrellas = 0;
      _comentarioCtrl.clear();
      _errorCalificacion = null;
    });
  }

  Future<void> _enviarCalificacion(Venta v) async {
    if (_estrellas < 1) return;
    setState(() {
      _guardando = true;
      _errorCalificacion = null;
    });
    try {
      await ref.read(ventasRepositoryProvider).calificar(
            ventaId: v.id,
            estrellas: _estrellas,
            comentario: _comentarioCtrl.text.trim().isEmpty ? null : _comentarioCtrl.text.trim(),
          );
      if (!mounted) return;
      setState(() {
        _calificandoVentaId = null;
        _cargar();
      });
    } catch (e) {
      if (mounted) setState(() => _errorCalificacion = extractErrorMessage(e));
    } finally {
      if (mounted) setState(() => _guardando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('MIS COMPRAS')),
      body: SafeArea(
        child: FutureBuilder<List<Venta>>(
          future: _future,
          builder: (context, snapshot) {
            if (snapshot.connectionState != ConnectionState.done) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snapshot.hasError) {
              return const Center(child: Text('No pudimos cargar tus compras.'));
            }
            final compras = snapshot.data ?? [];
            if (compras.isEmpty) {
              return const Center(child: Text('Todavia no tienes compras.'));
            }
            return RefreshIndicator(
              onRefresh: () async {
                setState(_cargar);
                await _future;
              },
              child: ListView.separated(
                padding: const EdgeInsets.all(16),
                itemCount: compras.length,
                separatorBuilder: (_, _) => const SizedBox(height: 12),
                itemBuilder: (context, i) => _VentaCard(
                  venta: compras[i],
                  calificando: _calificandoVentaId == compras[i].id,
                  estrellasSeleccionadas: _estrellas,
                  comentarioCtrl: _comentarioCtrl,
                  guardando: _guardando,
                  error: _errorCalificacion,
                  onCalificar: () => _abrirCalificar(compras[i]),
                  onCancelar: () => setState(() => _calificandoVentaId = null),
                  onSeleccionarEstrella: (n) => setState(() => _estrellas = n),
                  onEnviar: () => _enviarCalificacion(compras[i]),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}

class _VentaCard extends StatelessWidget {
  const _VentaCard({
    required this.venta,
    required this.calificando,
    required this.estrellasSeleccionadas,
    required this.comentarioCtrl,
    required this.guardando,
    required this.error,
    required this.onCalificar,
    required this.onCancelar,
    required this.onSeleccionarEstrella,
    required this.onEnviar,
  });

  final Venta venta;
  final bool calificando;
  final int estrellasSeleccionadas;
  final TextEditingController comentarioCtrl;
  final bool guardando;
  final String? error;
  final VoidCallback onCalificar;
  final VoidCallback onCancelar;
  final ValueChanged<int> onSeleccionarEstrella;
  final VoidCallback onEnviar;

  @override
  Widget build(BuildContext context) {
    final colorEstado = _estadoColor[venta.estadoPago] ?? AppColors.grayText;

    return Container(
      decoration: BoxDecoration(border: Border.all(color: AppColors.grayBorderLight)),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  'Compra #${venta.id} · ${venta.total.toStringAsFixed(2)} Bs',
                  style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 14, color: AppColors.brandDark),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(color: colorEstado.withValues(alpha: 0.12)),
                child: Text(
                  '${_metodoLabel[venta.metodoPago] ?? venta.metodoPago} · ${venta.estadoPago}',
                  style: TextStyle(color: colorEstado, fontSize: 10, fontWeight: FontWeight.w700),
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            '${venta.fecha.day}/${venta.fecha.month}/${venta.fecha.year} · ${venta.sucursalNombre}',
            style: const TextStyle(fontSize: 12, color: AppColors.grayTextDark),
          ),
          const SizedBox(height: 8),
          for (final d in venta.detalles)
            Padding(
              padding: const EdgeInsets.only(bottom: 2),
              child: Text(
                '${d.cantidad}x ${d.productoNombre} (${d.tallaCodigo}, ${d.colorNombre})',
                style: const TextStyle(fontSize: 12, color: AppColors.grayTextDark),
              ),
            ),
          if (venta.completada) ...[
            const Divider(height: 24),
            if (venta.calificada)
              _EstrellasVista(estrellas: venta.calificacionEstrellas!, comentario: venta.calificacionComentario)
            else if (calificando)
              _CalificarForm(
                estrellas: estrellasSeleccionadas,
                comentarioCtrl: comentarioCtrl,
                guardando: guardando,
                error: error,
                onSeleccionarEstrella: onSeleccionarEstrella,
                onCancelar: onCancelar,
                onEnviar: onEnviar,
              )
            else
              OutlinedButton(
                onPressed: onCalificar,
                style: OutlinedButton.styleFrom(shape: const RoundedRectangleBorder(), minimumSize: const Size.fromHeight(40)),
                child: const Text('CALIFICAR ESTA COMPRA'),
              ),
          ],
        ],
      ),
    );
  }
}

class _EstrellasVista extends StatelessWidget {
  const _EstrellasVista({required this.estrellas, this.comentario});

  final int estrellas;
  final String? comentario;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: List.generate(
            5,
            (i) => Icon(i < estrellas ? Icons.star : Icons.star_border, size: 18, color: const Color(0xFFE8B923)),
          ),
        ),
        if (comentario != null && comentario!.isNotEmpty) ...[
          const SizedBox(height: 4),
          Text('"$comentario"', style: const TextStyle(fontSize: 12, fontStyle: FontStyle.italic, color: AppColors.grayTextDark)),
        ],
      ],
    );
  }
}

class _CalificarForm extends StatelessWidget {
  const _CalificarForm({
    required this.estrellas,
    required this.comentarioCtrl,
    required this.guardando,
    required this.error,
    required this.onSeleccionarEstrella,
    required this.onCancelar,
    required this.onEnviar,
  });

  final int estrellas;
  final TextEditingController comentarioCtrl;
  final bool guardando;
  final String? error;
  final ValueChanged<int> onSeleccionarEstrella;
  final VoidCallback onCancelar;
  final VoidCallback onEnviar;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (error != null) ...[
          Container(
            padding: const EdgeInsets.all(10),
            color: AppColors.dangerBg,
            child: Text(error!, style: const TextStyle(color: AppColors.danger, fontSize: 12)),
          ),
          const SizedBox(height: 10),
        ],
        Row(
          children: List.generate(
            5,
            (i) => IconButton(
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
              onPressed: () => onSeleccionarEstrella(i + 1),
              icon: Icon(
                i < estrellas ? Icons.star : Icons.star_border,
                color: const Color(0xFFE8B923),
                size: 26,
              ),
            ),
          ),
        ),
        TextField(
          controller: comentarioCtrl,
          maxLines: 3,
          decoration: const InputDecoration(labelText: 'Contanos tu experiencia (opcional)'),
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: OutlinedButton(
                onPressed: onCancelar,
                style: OutlinedButton.styleFrom(shape: const RoundedRectangleBorder()),
                child: const Text('CANCELAR'),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: ElevatedButton(
                onPressed: (estrellas < 1 || guardando) ? null : onEnviar,
                style: ElevatedButton.styleFrom(backgroundColor: AppColors.brandDark, shape: const RoundedRectangleBorder()),
                child: Text(guardando ? 'ENVIANDO...' : 'ENVIAR'),
              ),
            ),
          ],
        ),
      ],
    );
  }
}
