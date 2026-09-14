import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_client.dart';
import '../../core/theme.dart';
import '../../models/carrito.dart';
import '../../models/sucursal.dart';
import 'cart_provider.dart';
import 'catalogo_provider.dart';
import 'reservas_repository.dart';

enum _Estado { cargando, formulario, enviando, listo, error }

/// CU10 (desde el carrito): reserva TODOS los items del carrito de una sola
/// vez -- una unica reserva con un detalle por producto, reusando la talla y
/// color que el cliente ya eligio al agregarlos al carrito. Mismo criterio
/// que "Reservar para pagar y recoger en sucursal" en `carrito.ts`/`.html`
/// de la web: solo pide sucursal y horario, no talla/color/cantidad de
/// nuevo. Al confirmar, el carrito queda vacio (igual que en la web).
class ReservarCarritoScreen extends ConsumerStatefulWidget {
  const ReservarCarritoScreen({super.key, required this.items});

  final List<DetalleCarrito> items;

  @override
  ConsumerState<ReservarCarritoScreen> createState() => _ReservarCarritoScreenState();
}

class _ReservarCarritoScreenState extends ConsumerState<ReservarCarritoScreen> {
  _Estado _estado = _Estado.cargando;
  List<SucursalPublica> _sucursales = [];
  int? _sucursalId;
  DateTime? _horario;
  String _error = '';

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<void> _cargar() async {
    try {
      final sucursales = await ref.read(catalogoRepositoryProvider).listSucursales();
      if (!mounted) return;
      setState(() {
        _sucursales = sucursales;
        _sucursalId = sucursales.isNotEmpty ? sucursales.first.id : null;
        _estado = _Estado.formulario;
      });
    } catch (_) {
      if (mounted) setState(() => _estado = _Estado.error);
    }
  }

  Future<void> _elegirHorario() async {
    final ahora = DateTime.now();
    final fecha = await showDatePicker(
      context: context,
      initialDate: ahora.add(const Duration(hours: 1)),
      firstDate: ahora,
      lastDate: ahora.add(const Duration(days: 90)),
    );
    if (fecha == null || !mounted) return;

    final hora = await showTimePicker(context: context, initialTime: TimeOfDay.fromDateTime(ahora));
    if (hora == null || !mounted) return;

    setState(() => _horario = DateTime(fecha.year, fecha.month, fecha.day, hora.hour, hora.minute));
  }

  Future<void> _confirmar() async {
    final sucursalId = _sucursalId;
    final horario = _horario;
    if (sucursalId == null || horario == null) return;

    setState(() {
      _estado = _Estado.enviando;
      _error = '';
    });
    try {
      await ref.read(reservasRepositoryProvider).crearDesdeCarrito(
            sucursalId: sucursalId,
            horario: horario,
            items: widget.items,
          );
      await ref.read(cartProvider.notifier).vaciar();
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
      appBar: AppBar(title: const Text('RESERVAR')),
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
      case _Estado.error:
        return const Center(child: Text('No pudimos cargar las sucursales. Intenta de nuevo en unos segundos.'));
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
        const Text(
          'Reservar para pagar y recoger en sucursal',
          style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16, color: AppColors.brandDark),
        ),
        const SizedBox(height: 8),
        Text(
          '${widget.items.length} ${widget.items.length == 1 ? 'producto' : 'productos'} de tu carrito',
          style: const TextStyle(fontSize: 12, color: AppColors.grayTextDark),
        ),
        const SizedBox(height: 20),

        if (_error.isNotEmpty) ...[
          Container(
            padding: const EdgeInsets.all(12),
            color: AppColors.dangerBg,
            child: Text(_error, style: const TextStyle(color: AppColors.danger, fontSize: 13)),
          ),
          const SizedBox(height: 16),
        ],

        const Text('SUCURSAL', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.grayText)),
        const SizedBox(height: 6),
        DropdownButtonFormField<int>(
          initialValue: _sucursalId,
          isExpanded: true,
          items: _sucursales
              .map((s) => DropdownMenuItem(value: s.id, child: Text(s.nombre, overflow: TextOverflow.ellipsis)))
              .toList(),
          onChanged: (id) => setState(() => _sucursalId = id),
        ),
        const SizedBox(height: 20),

        const Text(
          'FECHA Y HORA EN QUE IRAS A PAGAR Y RECOGER',
          style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.grayText),
        ),
        const SizedBox(height: 6),
        OutlinedButton(
          onPressed: _elegirHorario,
          style: OutlinedButton.styleFrom(
            alignment: Alignment.centerLeft,
            side: const BorderSide(color: AppColors.grayBorder),
            shape: const RoundedRectangleBorder(),
          ),
          child: Text(
            _horario == null
                ? 'Elegir fecha y hora'
                : '${_horario!.day}/${_horario!.month}/${_horario!.year} - '
                    '${_horario!.hour.toString().padLeft(2, '0')}:${_horario!.minute.toString().padLeft(2, '0')}',
          ),
        ),
        const SizedBox(height: 28),

        Row(
          children: [
            Expanded(
              child: OutlinedButton(
                onPressed: () => Navigator.of(context).pop(),
                style: OutlinedButton.styleFrom(shape: const RoundedRectangleBorder(), minimumSize: const Size.fromHeight(48)),
                child: const Text('CANCELAR'),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: ElevatedButton(
                onPressed: (_estado == _Estado.enviando || _sucursalId == null || _horario == null) ? null : _confirmar,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.brandDark,
                  minimumSize: const Size.fromHeight(48),
                  shape: const RoundedRectangleBorder(),
                ),
                child: Text(_estado == _Estado.enviando ? 'RESERVANDO...' : 'CONFIRMAR RESERVA'),
              ),
            ),
          ],
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
          const Text('Tu reserva quedo registrada.', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 8),
          Text(
            'Se reservaron ${widget.items.length} ${widget.items.length == 1 ? 'producto' : 'productos'} de tu carrito. '
            'Te esperamos en la sucursal el dia y hora que elegiste.',
            textAlign: TextAlign.center,
            style: const TextStyle(color: AppColors.grayTextDark, fontSize: 13),
          ),
          const SizedBox(height: 20),
          OutlinedButton(
            onPressed: () => Navigator.of(context).pop(),
            style: OutlinedButton.styleFrom(shape: const RoundedRectangleBorder()),
            child: const Text('LISTO'),
          ),
        ],
      ),
    );
  }
}
