import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme.dart';
import '../../../models/carrito_admin.dart';
import '../admin_provider.dart';
import '../widgets/admin_widgets.dart';

const _pollSegundos = 15;

/// CU13 "Administrar Carrito de Compras" -- carritos activos en tiempo
/// real (con polling, igual que la web), quien los tiene y que articulos.
class CarritosScreen extends ConsumerStatefulWidget {
  const CarritosScreen({super.key});

  @override
  ConsumerState<CarritosScreen> createState() => _CarritosScreenState();
}

class _CarritosScreenState extends ConsumerState<CarritosScreen> {
  Future<List<CarritoAdmin>>? _future;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _cargar();
    _timer = Timer.periodic(const Duration(seconds: _pollSegundos), (_) => _cargar());
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  void _cargar() {
    setState(() {
      _future = ref.read(adminRepositoryProvider).getCarritosActivos();
    });
  }

  @override
  Widget build(BuildContext context) {
    return AdminScaffold(
      title: 'CARRITOS ACTIVOS',
      body: FutureBuilder<List<CarritoAdmin>>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return const Center(child: Text('No pudimos cargar los carritos.'));
          }
          final carritos = snapshot.data ?? [];
          if (carritos.isEmpty) {
            return const Center(child: Text('Ningun cliente tiene articulos en su carrito ahora mismo.'));
          }
          return RefreshIndicator(
            onRefresh: () async => _cargar(),
            child: ListView(
              padding: const EdgeInsets.only(top: 8, bottom: 8),
              children: [for (final c in carritos) _CarritoCard(carrito: c)],
            ),
          );
        },
      ),
    );
  }
}

class _CarritoCard extends StatelessWidget {
  const _CarritoCard({required this.carrito});
  final CarritoAdmin carrito;

  @override
  Widget build(BuildContext context) {
    return AdminCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(carrito.clienteNombre, style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.brandDark)),
                    Text(carrito.clienteEmail, style: const TextStyle(fontSize: 11, color: AppColors.grayTextDark)),
                  ],
                ),
              ),
              Text('${carrito.total.toStringAsFixed(2)} Bs', style: const TextStyle(fontWeight: FontWeight.w800, color: AppColors.brandDark)),
            ],
          ),
          const SizedBox(height: 8),
          AdminInfoRow('Articulos', '${carrito.cantidadItems}'),
          AdminInfoRow(
            'Ultima actividad',
            '${carrito.fechaActualizacion.hour.toString().padLeft(2, '0')}:${carrito.fechaActualizacion.minute.toString().padLeft(2, '0')}',
          ),
          const SizedBox(height: 4),
          for (final d in carrito.detalles) Text('· $d', style: const TextStyle(fontSize: 12, color: AppColors.grayTextDark)),
        ],
      ),
    );
  }
}
