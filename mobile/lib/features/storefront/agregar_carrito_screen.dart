import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api_client.dart';
import '../../core/theme.dart';
import 'cart_provider.dart';
import 'reservas_repository.dart';

enum _Estado { cargando, formulario, enviando, listo, error, sinStock }

/// Talla+color con el stock sumado entre sucursales -- la sucursal no
/// importa aca (se elige recien en el checkout), asi que agrupar por
/// sucursal como antes hacia que la misma combinacion talla/color apareciera
/// repetida una vez por sucursal en el dropdown.
class _Variante {
  const _Variante({required this.tallaId, required this.tallaCodigo, required this.colorId, required this.colorNombre, required this.cantidad});

  final int tallaId;
  final String tallaCodigo;
  final int colorId;
  final String colorNombre;
  final int cantidad;
}

/// CU11, lado cliente: elegir talla/color/cantidad antes de agregar al
/// carrito -- el backend lo exige (no se puede agregar un producto "en
/// general", tiene que ser una combinacion con stock real). Reusa el mismo
/// endpoint de disponibilidad que ya usa Reservar (CU10). Talla y color se
/// eligen por separado (pedido explicito del usuario): elegir la talla
/// primero filtra los colores que de verdad tienen stock en esa talla.
class AgregarCarritoScreen extends ConsumerStatefulWidget {
  const AgregarCarritoScreen({super.key, required this.productoId, required this.productoNombre});

  final int productoId;
  final String productoNombre;

  @override
  ConsumerState<AgregarCarritoScreen> createState() => _AgregarCarritoScreenState();
}

class _AgregarCarritoScreenState extends ConsumerState<AgregarCarritoScreen> {
  _Estado _estado = _Estado.cargando;
  List<_Variante> _variantes = [];
  int? _tallaId;
  int? _colorId;
  int _cantidad = 1;
  String _error = '';

  List<_Variante> get _tallas {
    final vistas = <int>{};
    final lista = <_Variante>[];
    for (final v in _variantes) {
      if (vistas.add(v.tallaId)) lista.add(v);
    }
    return lista;
  }

  List<_Variante> get _coloresParaTallaActual => _variantes.where((v) => v.tallaId == _tallaId).toList();

  _Variante? get _varianteActual {
    for (final v in _coloresParaTallaActual) {
      if (v.colorId == _colorId) return v;
    }
    return null;
  }

  Future<void> _cargar() async {
    try {
      final opciones = await ref.read(reservasRepositoryProvider).disponibilidad(widget.productoId);
      if (!mounted) return;
      if (opciones.isEmpty) {
        setState(() => _estado = _Estado.sinStock);
        return;
      }
      final porClave = <String, _Variante>{};
      for (final o in opciones) {
        final clave = '${o.tallaId}-${o.colorId}';
        final existente = porClave[clave];
        porClave[clave] = _Variante(
          tallaId: o.tallaId,
          tallaCodigo: o.tallaCodigo,
          colorId: o.colorId,
          colorNombre: o.colorNombre,
          cantidad: (existente?.cantidad ?? 0) + o.cantidad,
        );
      }
      final variantes = porClave.values.toList();
      setState(() {
        _variantes = variantes;
        _tallaId = variantes.first.tallaId;
        _colorId = variantes.first.colorId;
        _estado = _Estado.formulario;
      });
    } catch (_) {
      if (mounted) setState(() => _estado = _Estado.error);
    }
  }

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<void> _enviar() async {
    final variante = _varianteActual;
    if (variante == null) return;

    setState(() {
      _estado = _Estado.enviando;
      _error = '';
    });
    try {
      await ref.read(cartProvider.notifier).agregar(
            productoId: widget.productoId,
            tallaId: variante.tallaId,
            colorId: variante.colorId,
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

        const Text('TALLA', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.grey)),
        const SizedBox(height: 6),
        DropdownButtonFormField<int>(
          initialValue: _tallaId,
          isExpanded: true,
          items: _tallas.map((v) => DropdownMenuItem(value: v.tallaId, child: Text(v.tallaCodigo))).toList(),
          onChanged: (tallaId) {
            if (tallaId == null) return;
            setState(() {
              _tallaId = tallaId;
              // La talla nueva puede no tener el mismo color que estaba
              // elegido -- se cae al primero que si tenga stock en esta talla.
              _colorId = _variantes.firstWhere((v) => v.tallaId == tallaId).colorId;
              _cantidad = 1;
            });
          },
        ),
        const SizedBox(height: 20),

        const Text('COLOR', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.grey)),
        const SizedBox(height: 6),
        DropdownButtonFormField<int>(
          initialValue: _colorId,
          isExpanded: true,
          items: _coloresParaTallaActual
              .map((v) => DropdownMenuItem(value: v.colorId, child: Text('${v.colorNombre} (${v.cantidad} disponibles)', overflow: TextOverflow.ellipsis)))
              .toList(),
          onChanged: (colorId) {
            if (colorId == null) return;
            setState(() {
              _colorId = colorId;
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
              onPressed: (_varianteActual != null && _cantidad < _varianteActual!.cantidad)
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
