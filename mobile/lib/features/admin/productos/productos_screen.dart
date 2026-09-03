import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme.dart';
import '../../../models/catalogo_base.dart';
import '../../../models/producto_admin.dart';
import '../admin_provider.dart';
import '../widgets/admin_widgets.dart';
import 'producto_form_screen.dart';

/// CU05 — Administrar Catalogo de Productos. Pantalla de lista; el
/// formulario (crear/editar + imagenes + inventario) vive en
/// `producto_form_screen.dart` por su tamano.
class ProductosScreen extends ConsumerStatefulWidget {
  const ProductosScreen({super.key});

  @override
  ConsumerState<ProductosScreen> createState() => _ProductosScreenState();
}

class _ProductosScreenState extends ConsumerState<ProductosScreen> {
  late Future<List<ProductoAdmin>> _productosFuture;
  CatalogoBase? _catalogoBase;
  String? _buscar;
  String? _error;

  @override
  void initState() {
    super.initState();
    _productosFuture = _load();
    _cargarCatalogoBase();
  }

  Future<void> _cargarCatalogoBase() async {
    try {
      final base = await ref.read(adminRepositoryProvider).getCatalogoBase();
      if (mounted) setState(() => _catalogoBase = base);
    } catch (_) {
      // Se reintenta al abrir el formulario si hace falta.
    }
  }

  Future<List<ProductoAdmin>> _load() => ref.read(adminRepositoryProvider).getProductos(buscar: _buscar);

  void _reload({String? buscar}) {
    setState(() {
      if (buscar != null) _buscar = buscar.isEmpty ? null : buscar;
      _error = null;
      _productosFuture = _load();
    });
  }

  Future<void> _abrirFormulario({ProductoAdmin? producto}) async {
    var base = _catalogoBase;
    if (base == null) {
      try {
        base = await ref.read(adminRepositoryProvider).getCatalogoBase();
        if (mounted) setState(() => _catalogoBase = base);
      } catch (_) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('No pudimos cargar los datos del formulario.')));
        }
        return;
      }
    }
    if (!mounted) return;
    await Navigator.of(context).push(
      MaterialPageRoute(builder: (context) => ProductoFormScreen(catalogoBase: base!, producto: producto)),
    );
    _reload();
  }

  Future<void> _toggleEstado(ProductoAdmin producto) async {
    final activar = producto.estado == 'inactivo';
    final ok = await confirmAdminAction(
      context,
      title: activar ? 'Activar producto' : 'Desactivar producto',
      message: 'Seguro que queres ${activar ? 'activar' : 'desactivar'} ${producto.nombre}?',
    );
    if (!ok) return;
    try {
      await ref.read(adminRepositoryProvider).updateProducto(producto.id, {
        'nombre': producto.nombre,
        'descripcion': producto.descripcion,
        'precio': producto.precio,
        'precio_original': producto.precioOriginal,
        'categoria_id': producto.categoriaId,
        'marca_id': producto.marcaId,
        'proveedor_id': producto.proveedorId,
        'temporada_id': producto.temporadaId,
        'coleccion_id': producto.coleccionId,
        'estado': activar ? 'activo' : 'inactivo',
      });
      _reload();
    } catch (e) {
      setState(() => _error = 'No pudimos actualizar el estado.');
    }
  }

  @override
  Widget build(BuildContext context) {
    return AdminScaffold(
      title: 'PRODUCTOS',
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _abrirFormulario(),
        icon: const Icon(Icons.add),
        label: const Text('NUEVO'),
      ),
      body: Column(
        children: [
          AdminSearchField(hintText: 'Buscar por nombre...', onChanged: (v) => _reload(buscar: v)),
          if (_error != null) AdminErrorBanner(message: _error!),
          Expanded(
            child: FutureBuilder<List<ProductoAdmin>>(
              future: _productosFuture,
              builder: (context, snapshot) {
                if (snapshot.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator());
                if (snapshot.hasError) return const Center(child: Text('No pudimos cargar los productos.'));
                final productos = snapshot.data ?? [];
                if (productos.isEmpty) return const Center(child: Text('No hay productos registrados.'));
                return ListView(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  children: [
                    for (final p in productos)
                      _ProductoCard(
                        producto: p,
                        onEditar: () => _abrirFormulario(producto: p),
                        onToggle: () => _toggleEstado(p),
                      ),
                  ],
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _ProductoCard extends StatelessWidget {
  const _ProductoCard({required this.producto, required this.onEditar, required this.onToggle});

  final ProductoAdmin producto;
  final VoidCallback onEditar;
  final VoidCallback onToggle;

  @override
  Widget build(BuildContext context) {
    final activo = producto.estado == 'activo';
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
                    Text(producto.nombre, style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.brandDark)),
                    Text('${producto.temporadaNombre} · ${producto.coleccionNombre}', style: const TextStyle(fontSize: 11, color: AppColors.grayTextDark)),
                  ],
                ),
              ),
              EstadoBadge(estado: producto.estado, activo: activo),
            ],
          ),
          const SizedBox(height: 8),
          AdminInfoRow('Marca', producto.marcaNombre),
          AdminInfoRow('Categoria', producto.categoriaNombre),
          AdminInfoRow('Proveedor', producto.proveedorNombre),
          AdminInfoRow('Precio', 'Bs ${producto.precio.toStringAsFixed(0)}${producto.precioOriginal != null ? ' (antes Bs ${producto.precioOriginal!.toStringAsFixed(0)})' : ''}'),
          AdminInfoRow('Imagenes', '${producto.imagenes.length}'),
          const SizedBox(height: 6),
          if (producto.sucursalesDisponibles.isEmpty)
            const NeutralBadge('Sin stock')
          else
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: [
                for (final d in producto.sucursalesDisponibles) NeutralBadge('${d.sucursalNombre}: ${d.cantidad}'),
              ],
            ),
          const SizedBox(height: 10),
          Row(
            children: [
              TextButton.icon(onPressed: onEditar, icon: const Icon(Icons.edit_outlined, size: 16), label: const Text('Editar')),
              TextButton.icon(
                onPressed: onToggle,
                icon: Icon(activo ? Icons.block : Icons.check_circle_outline, size: 16),
                label: Text(activo ? 'Desactivar' : 'Activar'),
                style: TextButton.styleFrom(foregroundColor: activo ? AppColors.danger : AppColors.success),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
