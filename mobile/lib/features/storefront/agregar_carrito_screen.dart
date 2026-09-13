import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api_client.dart';
import '../../core/theme.dart';
import 'cart_provider.dart';
import 'reservas_repository.dart';

enum _Estado { cargando, formulario, enviando, listo, error, sinStock }

/// CU11, lado cliente: elegir talla/color/cantidad antes de agregar al
/// carrito -- el backend lo exige (no se puede agregar un producto "en
/// general", tiene que ser una combinacion con stock real). Reusa el mismo
/// endpoint de disponibilidad que ya usa Reservar (CU10).
class AgregarCarritoScreen extends ConsumerStatefulWidget {
  const AgregarCarritoScreen({super.key, required this.productoId, required this.productoNombre});

  final int productoId;
  final String productoNombre;

  @override
  ConsumerState<AgregarCarritoScreen> createState() => _AgregarCarritoScreenState();
}

class _AgregarCarritoScreenState extends ConsumerState<AgregarCarritoScreen> {
  _Estado _estado = _Estado.cargando;
  List<DisponibilidadItem> _opciones = [];
  DisponibilidadItem? _opcionSeleccionada;
  int _cantidad = 1;
  String _error = '';

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<void> _cargar() async {
    try {
      final opciones = await ref.read(reservasRepositoryProvider).disponibilidad(widget.productoId);
      if (!mounted) return;
      if (opciones.isEmpty) {
        setState(() => _estado = _Estado.sinStock);
        return;
      }
      setState(() {
        _opciones = opciones;
        _opcionSeleccionada = opciones.first;
        _estado = _Estado.formulario;
      });
    } catch (_) {
      if (mounted) setState(() => _estado = _Estado.error);
    }
  }

  Future<void> _enviar() async {
    final opcion = _opcionSeleccionada;
    if (opcion == null) return;

    setState(() {
      _estado = _Estado.enviando;
      _error = '';
    });
    try {
      await ref.read(cartProvider.notifier).agregar(
            productoId: widget.productoId,
            tallaId: opcion.tallaId,
            colorId: opcion.colorId,
            cantidad: _cantidad,
          );
      if (mounted) setState(() => _estado = _Estado.listo);
    } catch (err) {
      if (mounted) {
        setState(() {
          _error = extractErrorMessage(err);
          _estado = _Estado.formulario;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('AGREGAR AL CARRITO')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: _contenido(),
        ),
      ),
    );
  }

  Widget _contenido() {
    switch (_estado) {
      case _Estado.cargando:
        return const Center(child: CircularProgressIndicator());
      case _Estado.sinStock:
        return const Center(
          child: Text(
            'Este producto no tiene stock disponible en ninguna sucursal por ahora.',
            textAlign: TextAlign.center,
          ),
        );
      case _Estado.error:
        return const Center(
          child: Text('No pudimos cargar la disponibilidad. Intenta de nuevo en unos segundos.'),
        );
      case _Estado.formulario:
      case _Estado.enviando:
        return _formulario();
      case _Estado.listo:
        return _exito();
    }
  }

  Widget _formulario() {
    return ListView(
      children: [
        Text(widget.productoNombre, style: const TextStyle(color: Colors.grey, fontSize: 13)),
        const SizedBox(height: 20),

        if (_error.isNotEmpty) ...[
          Container(
            padding: const EdgeInsets.all(12),
            color: const Color(0xFFFDECEA),
            child: Text(_error, style: const TextStyle(color: Color(0xFFB3261E), fontSize: 13)),
          ),
          const SizedBox(height: 16),
        ],

        const Text('SUCURSAL, TALLA Y COLOR', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.grey)),
        const SizedBox(height: 6),
        DropdownButtonFormField<String>(
          initialValue: _opcionSeleccionada?.clave,
          isExpanded: true,
          items: _opciones
              .map(
                (o) => DropdownMenuItem(
                  value: o.clave,
                  child: Text(
                    '${o.sucursalNombre} · ${o.tallaCodigo} · ${o.colorNombre} (${o.cantidad} disponibles)',
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              )
              .toList(),
          onChanged: (clave) {
            setState(() {
              _opcionSeleccionada = _opciones.firstWhere((o) => o.clave == clave);
              _cantidad = 1;
            });
          },
        ),
        const SizedBox(height: 20),

        const Text('CANTIDAD', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.grey)),
        const SizedBox(height: 6),
        Row(
          children: [
            IconButton(
              onPressed: _cantidad > 1 ? () => setState(() => _cantidad--) : null,
              icon: const Icon(Icons.remove_circle_outline),
            ),
            Text('$_cantidad', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            IconButton(
              onPressed: (_opcionSeleccionada != null && _cantidad < _opcionSeleccionada!.cantidad)
                  ? () => setState(() => _cantidad++)
                  : null,
              icon: const Icon(Icons.add_circle_outline),
            ),
          ],
        ),
        const SizedBox(height: 28),

        ElevatedButton(
          onPressed: _estado == _Estado.enviando ? null : _enviar,
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.brandDark,
            minimumSize: const Size.fromHeight(48),
            shape: const RoundedRectangleBorder(),
          ),
          child: Text(_estado == _Estado.enviando ? 'AGREGANDO...' : 'AGREGAR AL CARRITO'),
        ),
      ],
    );
  }

  Widget _exito() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.check_circle_outline, size: 48, color: AppColors.brandDark),
          const SizedBox(height: 16),
          const Text('Se agrego a tu carrito.', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 20),
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              OutlinedButton(
                onPressed: () => Navigator.of(context).pop(),
                style: OutlinedButton.styleFrom(shape: const RoundedRectangleBorder()),
                child: const Text('SEGUIR COMPRANDO'),
              ),
              const SizedBox(width: 12),
              ElevatedButton(
                onPressed: () => context.go('/carrito'),
                style: ElevatedButton.styleFrom(shape: const RoundedRectangleBorder()),
                child: const Text('IR AL CARRITO'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
