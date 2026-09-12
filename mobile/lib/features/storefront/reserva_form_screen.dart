import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_client.dart';
import '../../core/theme.dart';
import 'reservas_repository.dart';

enum _Estado { cargando, formulario, enviando, listo, error, sinStock }

/// CU10, lado cliente: reservar una prenda para probarsela/recogerla en una
/// sucursal en un horario. Mismo flujo que `reserva-form.ts` en la web:
/// trae las combinaciones talla/color/sucursal que de verdad tienen stock
/// antes de mostrar el formulario.
class ReservaFormScreen extends ConsumerStatefulWidget {
  const ReservaFormScreen({super.key, required this.productoId, required this.productoNombre});

  final int productoId;
  final String productoNombre;

  @override
  ConsumerState<ReservaFormScreen> createState() => _ReservaFormScreenState();
}

class _ReservaFormScreenState extends ConsumerState<ReservaFormScreen> {
  _Estado _estado = _Estado.cargando;
  List<DisponibilidadItem> _opciones = [];
  DisponibilidadItem? _opcionSeleccionada;
  int _cantidad = 1;
  DateTime? _horario;
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

  Future<void> _enviar() async {
    final opcion = _opcionSeleccionada;
    final horario = _horario;
    if (opcion == null || horario == null) return;

    setState(() {
      _estado = _Estado.enviando;
      _error = '';
    });
    try {
      await ref.read(reservasRepositoryProvider).crear(
            productoId: widget.productoId,
            opcion: opcion,
            cantidad: _cantidad,
            horario: horario,
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
        const SizedBox(height: 20),

        const Text('FECHA Y HORA EN QUE IRAS A LA SUCURSAL',
            style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.grey)),
        const SizedBox(height: 6),
        OutlinedButton(
          onPressed: _elegirHorario,
          style: OutlinedButton.styleFrom(
            alignment: Alignment.centerLeft,
            side: const BorderSide(color: Colors.grey),
            shape: const RoundedRectangleBorder(),
          ),
          child: Text(
            _horario == null
                ? 'Elegir fecha y hora'
                : '${_horario!.day}/${_horario!.month}/${_horario!.year} - ${_horario!.hour.toString().padLeft(2, '0')}:${_horario!.minute.toString().padLeft(2, '0')}',
          ),
        ),
        const SizedBox(height: 28),

        ElevatedButton(
          onPressed: (_estado == _Estado.enviando || _horario == null) ? null : _enviar,
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.brandDark,
            minimumSize: const Size.fromHeight(48),
            shape: const RoundedRectangleBorder(),
          ),
          child: Text(_estado == _Estado.enviando ? 'RESERVANDO...' : 'CONFIRMAR RESERVA'),
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
          const Text(
            'Te esperamos en la sucursal el dia y hora que elegiste.',
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.grey, fontSize: 13),
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
