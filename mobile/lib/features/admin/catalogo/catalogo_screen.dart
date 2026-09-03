import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme.dart';
import '../../../models/catalogo_producto.dart';
import '../../../models/opcion.dart';
import '../admin_provider.dart';
import '../widgets/admin_widgets.dart';

/// CU08 — Consultar Catalogo y Disponibilidad. A diferencia del catalogo
/// publico, muestra stock exacto por talla/color/sucursal a personal
/// interno. Carga todas las sucursales en paralelo (igual que la web).
class CatalogoScreen extends ConsumerStatefulWidget {
  const CatalogoScreen({super.key});

  @override
  ConsumerState<CatalogoScreen> createState() => _CatalogoScreenState();
}

class _CatalogoScreenState extends ConsumerState<CatalogoScreen> {
  late Future<void> _future;
  List<Opcion> _sucursales = [];
  final Map<int, List<CatalogoProducto>> _porSucursal = {};
  final Set<int> _visibles = {};
  String _busqueda = '';
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
      setState(() => _error = 'No pudimos cargar el catalogo.');
    }
  }

  List<CatalogoProducto> _filtrar(List<CatalogoProducto> productos) {
    if (_busqueda.isEmpty) return productos;
    final q = _busqueda.toLowerCase();
    return productos
        .where((p) =>
            p.nombre.toLowerCase().contains(q) ||
            p.marcaNombre.toLowerCase().contains(q) ||
            p.categoriaNombre.toLowerCase().contains(q) ||
            p.variantes.any((v) => v.tallaCodigo.toLowerCase().contains(q) || v.colorNombre.toLowerCase().contains(q)))
        .toList();
  }

  @override
  Widget build(BuildContext context) {
    return AdminScaffold(
      title: 'CATALOGO POR SUCURSAL',
      body: FutureBuilder<void>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator());
          return Column(
            children: [
              AdminSearchField(hintText: 'Buscar producto, marca, talla, color...', onChanged: (v) => setState(() => _busqueda = v)),
              if (_error != null) AdminErrorBanner(message: _error!),
              if (_sucursales.length > _visibles.length)
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
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
                  padding: const EdgeInsets.only(bottom: 24),
                  children: [
                    for (final s in _sucursales.where((s) => _visibles.contains(s.id)))
                      _SucursalSection(
                        sucursal: s,
                        productos: _filtrar(_porSucursal[s.id] ?? []),
                        total: (_porSucursal[s.id] ?? []).length,
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

class _SucursalSection extends StatelessWidget {
  const _SucursalSection({required this.sucursal, required this.productos, required this.total, required this.onQuitar});

  final Opcion sucursal;
  final List<CatalogoProducto> productos;
  final int total;
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
                Text('${productos.length} de $total', style: const TextStyle(fontSize: 11, color: AppColors.grayText)),
                IconButton(icon: const Icon(Icons.close, size: 16), onPressed: onQuitar, tooltip: 'Quitar'),
              ],
            ),
          ),
          if (productos.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 16),
              child: Text('Sin productos para este filtro.', style: TextStyle(fontSize: 12, color: AppColors.grayText)),
            )
          else
            for (final p in productos) _ProductoCard(producto: p),
        ],
      ),
    );
  }
}

class _ProductoCard extends StatelessWidget {
  const _ProductoCard({required this.producto});

  final CatalogoProducto producto;

  @override
  Widget build(BuildContext context) {
    return AdminCard(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 56,
            height: 70,
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
                Text('${producto.marcaNombre} · ${producto.categoriaNombre}', style: const TextStyle(fontSize: 11, color: AppColors.grayTextDark)),
                Text('Bs ${producto.precio.toStringAsFixed(0)}', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppColors.brandDark)),
                const SizedBox(height: 6),
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: [for (final v in producto.variantes) NeutralBadge('${v.tallaCodigo}/${v.colorNombre}: ${v.cantidad}')],
                ),
                const SizedBox(height: 4),
                Text('Stock total: ${producto.cantidadTotal}', style: const TextStyle(fontSize: 11, color: AppColors.grayText)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
