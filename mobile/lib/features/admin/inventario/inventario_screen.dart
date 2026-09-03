import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme.dart';
import '../../../models/catalogo_producto.dart';
import '../../../models/opcion.dart';
import '../admin_provider.dart';
import '../widgets/admin_widgets.dart';

/// CU12 — Controlar Inventario por Sucursal. Comparte el modelo de datos
/// con CU08 (mismos endpoints de lectura) pero la cantidad de cada variante
/// es editable inline; al confirmar dispara
/// `PUT /productos/{id}/inventario/{varianteId}`.
class InventarioScreen extends ConsumerStatefulWidget {
  const InventarioScreen({super.key});

  @override
  ConsumerState<InventarioScreen> createState() => _InventarioScreenState();
}

class _InventarioScreenState extends ConsumerState<InventarioScreen> {
  late Future<void> _future;
  List<Opcion> _sucursales = [];
  final Map<int, List<CatalogoProducto>> _porSucursal = {};
  final Set<int> _visibles = {};
  String? _error;

  @override
  void initState() {
    super.initState();
    _future = _cargarTodo();
  }

  Future<void> _cargarTodo() async {
    final repo = ref.read(adminRepositoryProvider);
    try {
      final sucursales = await repo.getCatalogoSucursales();
      final resultados = await Future.wait(sucursales.map((s) => repo.getCatalogoProductosPorSucursal(s.id)));
      if (!mounted) return;
      setState(() {
        _sucursales = sucursales;
        for (var i = 0; i < sucursales.length; i++) {
          _porSucursal[sucursales[i].id] = resultados[i];
        }
        _visibles.addAll(sucursales.map((s) => s.id));
      });
    } catch (_) {
      setState(() => _error = 'No pudimos cargar el inventario.');
    }
  }

  Future<void> _actualizarCantidad({
    required int sucursalId,
    required int productoIndex,
    required int productoId,
    required int varianteIndex,
    required int inventarioId,
    required int nuevaCantidad,
  }) async {
    try {
      await ref.read(adminRepositoryProvider).actualizarCantidadInventario(
            productoId: productoId,
            inventarioId: inventarioId,
            cantidad: nuevaCantidad,
          );
      if (!mounted) return;
      setState(() {
        final lista = _porSucursal[sucursalId]!;
        final producto = lista[productoIndex];
        final nuevasVariantes = [...producto.variantes];
        nuevasVariantes[varianteIndex] = nuevasVariantes[varianteIndex].copyWith(cantidad: nuevaCantidad);
        lista[productoIndex] = producto.recomputado(nuevasVariantes);
      });
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('No pudimos actualizar la cantidad.')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AdminScaffold(
      title: 'INVENTARIO POR SUCURSAL',
      body: FutureBuilder<void>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator());
          return Column(
            children: [
              if (_error != null) AdminErrorBanner(message: _error!),
              if (_sucursales.length > _visibles.length)
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: PopupMenuButton<int>(
                      onSelected: (id) => setState(() => _visibles.add(id)),
                      itemBuilder: (context) => [
                        for (final s in _sucursales.where((s) => !_visibles.contains(s.id)))
                          PopupMenuItem(value: s.id, child: Text(s.nombre)),
                      ],
                      child: const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [Icon(Icons.add, size: 18), SizedBox(width: 4), Text('Agregar sucursal')],
                      ),
                    ),
                  ),
                ),
              Expanded(
                child: ListView(
                  padding: const EdgeInsets.only(top: 8, bottom: 24),
                  children: [
                    for (final s in _sucursales.where((s) => _visibles.contains(s.id)))
                      _SucursalInventarioSection(
                        sucursal: s,
                        productos: _porSucursal[s.id] ?? [],
                        onCantidadChanged: (productoIndex, productoId, varianteIndex, inventarioId, cantidad) => _actualizarCantidad(
                          sucursalId: s.id,
                          productoIndex: productoIndex,
                          productoId: productoId,
                          varianteIndex: varianteIndex,
                          inventarioId: inventarioId,
                          nuevaCantidad: cantidad,
                        ),
                        onQuitar: () => setState(() => _visibles.remove(s.id)),
                      ),
                  ],
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

typedef _OnCantidadChanged = void Function(int productoIndex, int productoId, int varianteIndex, int inventarioId, int cantidad);

class _SucursalInventarioSection extends StatelessWidget {
  const _SucursalInventarioSection({required this.sucursal, required this.productos, required this.onCantidadChanged, required this.onQuitar});

  final Opcion sucursal;
  final List<CatalogoProducto> productos;
  final _OnCantidadChanged onCantidadChanged;
  final VoidCallback onQuitar;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 4),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    sucursal.nombre.toUpperCase(),
                    style: const TextStyle(fontWeight: FontWeight.w800, color: AppColors.brandDark, letterSpacing: 0.3),
                  ),
                ),
                IconButton(icon: const Icon(Icons.close, size: 16), onPressed: onQuitar, tooltip: 'Quitar'),
              ],
            ),
          ),
          if (productos.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 16),
              child: Text('Sin productos en esta sucursal.', style: TextStyle(fontSize: 12, color: AppColors.grayText)),
            )
          else
            for (var i = 0; i < productos.length; i++)
              _ProductoInventarioCard(
                producto: productos[i],
                onCantidadChanged: (varianteIndex, inventarioId, cantidad) =>
                    onCantidadChanged(i, productos[i].id, varianteIndex, inventarioId, cantidad),
              ),
        ],
      ),
    );
  }
}

class _ProductoInventarioCard extends StatelessWidget {
  const _ProductoInventarioCard({required this.producto, required this.onCantidadChanged});

  final CatalogoProducto producto;
  final void Function(int varianteIndex, int inventarioId, int cantidad) onCantidadChanged;

  @override
  Widget build(BuildContext context) {
    return AdminCard(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 52,
            height: 66,
            child: producto.imagenUrl != null
                ? CachedNetworkImage(imageUrl: producto.imagenUrl!, fit: BoxFit.cover)
                : Container(color: AppColors.grayBorderLight),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(producto.nombre, style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.brandDark)),
                    ),
                    EstadoBadge(estado: producto.disponible ? 'Disponible' : 'Agotado', activo: producto.disponible),
                  ],
                ),
                Text('${producto.marcaNombre} · ${producto.categoriaNombre} · Bs ${producto.precio.toStringAsFixed(0)}',
                    style: const TextStyle(fontSize: 11, color: AppColors.grayTextDark)),
                const SizedBox(height: 8),
                for (var v = 0; v < producto.variantes.length; v++)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 6),
                    child: Row(
                      children: [
                        Expanded(
                          child: Text('${producto.variantes[v].tallaCodigo} / ${producto.variantes[v].colorNombre}', style: const TextStyle(fontSize: 12)),
                        ),
                        SizedBox(
                          width: 64,
                          height: 36,
                          child: TextFormField(
                            key: ValueKey(producto.variantes[v].id),
                            initialValue: '${producto.variantes[v].cantidad}',
                            textAlign: TextAlign.center,
                            keyboardType: TextInputType.number,
                            inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                            style: const TextStyle(fontSize: 13),
                            decoration: const InputDecoration(isDense: true, contentPadding: EdgeInsets.symmetric(vertical: 6)),
                            onFieldSubmitted: (value) {
                              final cantidad = int.tryParse(value) ?? producto.variantes[v].cantidad;
                              onCantidadChanged(v, producto.variantes[v].id, cantidad);
                            },
                            onEditingComplete: () => FocusScope.of(context).unfocus(),
                          ),
                        ),
                      ],
                    ),
                  ),
                Text('Stock total: ${producto.cantidadTotal}', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppColors.grayText)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
