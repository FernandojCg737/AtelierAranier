import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

import '../../../core/theme.dart';
import '../../../models/catalogo_base.dart';
import '../../../models/inventario_item.dart';
import '../../../models/producto_admin.dart';
import '../admin_provider.dart';
import '../widgets/admin_widgets.dart';

const _marcaOtroId = -1;

/// Formulario de CU05 completo: datos del producto + (solo en edicion)
/// subida de imagenes e inventario por sucursal/talla/color — igual que el
/// modal de `productos.ts` en la web, pero como pantalla propia dado el
/// volumen de contenido.
class ProductoFormScreen extends ConsumerStatefulWidget {
  const ProductoFormScreen({super.key, required this.catalogoBase, this.producto});

  final CatalogoBase catalogoBase;
  final ProductoAdmin? producto;

  @override
  ConsumerState<ProductoFormScreen> createState() => _ProductoFormScreenState();
}

class _ProductoFormScreenState extends ConsumerState<ProductoFormScreen> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _nombreCtrl;
  late final TextEditingController _descripcionCtrl;
  late final TextEditingController _precioCtrl;
  late final TextEditingController _precioOriginalCtrl;
  late final TextEditingController _marcaNuevaCtrl;

  int? _categoriaId;
  int? _marcaId;
  int? _proveedorId;
  int? _temporadaId;
  int? _coleccionId;
  String _estado = 'activo';

  ProductoAdmin? _productoActual;
  bool _guardando = false;
  String? _error;

  List<InventarioItem>? _inventario;
  bool _cargandoInventario = false;
  bool _subiendoImagenes = false;

  @override
  void initState() {
    super.initState();
    final p = widget.producto;
    _productoActual = p;
    _nombreCtrl = TextEditingController(text: p?.nombre ?? '');
    _descripcionCtrl = TextEditingController(text: p?.descripcion ?? '');
    _precioCtrl = TextEditingController(text: p != null ? _trimZeros(p.precio) : '');
    _precioOriginalCtrl = TextEditingController(text: p?.precioOriginal != null ? _trimZeros(p!.precioOriginal!) : '');
    _marcaNuevaCtrl = TextEditingController();
    _categoriaId = p?.categoriaId;
    _marcaId = p?.marcaId;
    _proveedorId = p?.proveedorId;
    _temporadaId = p?.temporadaId;
    _coleccionId = p?.coleccionId;
    _estado = p?.estado ?? 'activo';
    if (p != null) _cargarInventario(p.id);
  }

  static String _trimZeros(double v) => v == v.roundToDouble() ? v.toStringAsFixed(0) : v.toString();

  @override
  void dispose() {
    _nombreCtrl.dispose();
    _descripcionCtrl.dispose();
    _precioCtrl.dispose();
    _precioOriginalCtrl.dispose();
    _marcaNuevaCtrl.dispose();
    super.dispose();
  }

  Future<void> _cargarInventario(int productoId) async {
    setState(() => _cargandoInventario = true);
    try {
      final inv = await ref.read(adminRepositoryProvider).getInventarioProducto(productoId);
      if (mounted) setState(() => _inventario = inv);
    } catch (_) {
      if (mounted) setState(() => _error = 'No pudimos cargar el inventario de este producto.');
    } finally {
      if (mounted) setState(() => _cargandoInventario = false);
    }
  }

  Future<void> _guardar() async {
    if (!_formKey.currentState!.validate()) return;
    if (_marcaId == _marcaOtroId && _marcaNuevaCtrl.text.trim().isEmpty) {
      setState(() => _error = 'Escribi el nombre de la nueva marca.');
      return;
    }
    setState(() {
      _guardando = true;
      _error = null;
    });

    final repo = ref.read(adminRepositoryProvider);
    try {
      var marcaId = _marcaId;
      if (marcaId == _marcaOtroId) {
        final nueva = await repo.createMarca(_marcaNuevaCtrl.text.trim());
        marcaId = nueva.id;
      }

      final body = <String, dynamic>{
        'nombre': _nombreCtrl.text.trim(),
        'descripcion': _descripcionCtrl.text.trim().isEmpty ? null : _descripcionCtrl.text.trim(),
        'precio': double.parse(_precioCtrl.text.trim()),
        'precio_original': _precioOriginalCtrl.text.trim().isEmpty ? null : double.parse(_precioOriginalCtrl.text.trim()),
        'categoria_id': _categoriaId,
        'marca_id': marcaId,
        'proveedor_id': _proveedorId,
        'temporada_id': _temporadaId,
        'coleccion_id': _coleccionId,
      };

      ProductoAdmin resultado;
      if (_productoActual == null) {
        resultado = await repo.createProducto(body);
      } else {
        resultado = await repo.updateProducto(_productoActual!.id, {...body, 'estado': _estado});
      }

      if (!mounted) return;
      setState(() {
        _productoActual = resultado;
        _marcaId = resultado.marcaId;
        _guardando = false;
      });
      if (_inventario == null) _cargarInventario(resultado.id);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(widget.producto == null ? 'Producto creado. Ahora podes agregar fotos e inventario.' : 'Cambios guardados.')),
      );
    } catch (e) {
      setState(() {
        _guardando = false;
        _error = 'No pudimos guardar el producto.';
      });
    }
  }

  Future<void> _agregarImagenes() async {
    final producto = _productoActual;
    if (producto == null) return;
    final picker = ImagePicker();
    final archivos = await picker.pickMultiImage(imageQuality: 85);
    if (archivos.isEmpty) return;

    setState(() => _subiendoImagenes = true);
    final repo = ref.read(adminRepositoryProvider);
    for (final archivo in archivos) {
      try {
        final imagen = await repo.subirImagen(producto.id, archivo.path, archivo.name);
        if (!mounted) return;
        setState(() {
          _productoActual = _conImagenAgregada(_productoActual!, imagen);
        });
      } catch (_) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('No pudimos subir una de las imagenes.')));
        }
      }
    }
    if (mounted) setState(() => _subiendoImagenes = false);
  }

  ProductoAdmin _conImagenAgregada(ProductoAdmin p, ImagenProducto nueva) {
    return ProductoAdmin(
      id: p.id,
      nombre: p.nombre,
      descripcion: p.descripcion,
      precio: p.precio,
      precioOriginal: p.precioOriginal,
      estado: p.estado,
      categoriaId: p.categoriaId,
      categoriaNombre: p.categoriaNombre,
      marcaId: p.marcaId,
      marcaNombre: p.marcaNombre,
      proveedorId: p.proveedorId,
      proveedorNombre: p.proveedorNombre,
      temporadaId: p.temporadaId,
      temporadaNombre: p.temporadaNombre,
      coleccionId: p.coleccionId,
      coleccionNombre: p.coleccionNombre,
      imagenes: [...p.imagenes, nueva],
      sucursalesDisponibles: p.sucursalesDisponibles,
    );
  }

  Future<void> _eliminarImagen(ImagenProducto imagen) async {
    final producto = _productoActual;
    if (producto == null) return;
    final ok = await confirmAdminAction(context, title: 'Eliminar imagen', message: 'Seguro que queres eliminar esta foto?');
    if (!ok) return;
    try {
      await ref.read(adminRepositoryProvider).eliminarImagen(producto.id, imagen.id);
      if (!mounted) return;
      setState(() {
        _productoActual = ProductoAdmin(
          id: producto.id,
          nombre: producto.nombre,
          descripcion: producto.descripcion,
          precio: producto.precio,
          precioOriginal: producto.precioOriginal,
          estado: producto.estado,
          categoriaId: producto.categoriaId,
          categoriaNombre: producto.categoriaNombre,
          marcaId: producto.marcaId,
          marcaNombre: producto.marcaNombre,
          proveedorId: producto.proveedorId,
          proveedorNombre: producto.proveedorNombre,
          temporadaId: producto.temporadaId,
          temporadaNombre: producto.temporadaNombre,
          coleccionId: producto.coleccionId,
          coleccionNombre: producto.coleccionNombre,
          imagenes: producto.imagenes.where((i) => i.id != imagen.id).toList(),
          sucursalesDisponibles: producto.sucursalesDisponibles,
        );
      });
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('No pudimos eliminar la imagen.')));
    }
  }

  Future<void> _actualizarCantidadInventario(InventarioItem item, int cantidad) async {
    final producto = _productoActual;
    if (producto == null) return;
    try {
      final actualizado = await ref.read(adminRepositoryProvider).actualizarCantidadInventario(
            productoId: producto.id,
            inventarioId: item.id,
            cantidad: cantidad,
          );
      if (!mounted) return;
      setState(() {
        final idx = _inventario!.indexWhere((i) => i.id == item.id);
        if (idx != -1) _inventario![idx] = actualizado;
      });
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('No pudimos actualizar la cantidad.')));
    }
  }

  Future<void> _agregarInventario({required int sucursalId, required int tallaId, required int colorId, required int cantidad}) async {
    final producto = _productoActual;
    if (producto == null) return;
    try {
      final item = await ref.read(adminRepositoryProvider).upsertInventario(
            productoId: producto.id,
            sucursalId: sucursalId,
            tallaId: tallaId,
            colorId: colorId,
            cantidad: cantidad,
          );
      if (!mounted) return;
      setState(() {
        final idx = _inventario!.indexWhere((i) => i.id == item.id);
        if (idx != -1) {
          _inventario![idx] = item;
        } else {
          _inventario!.add(item);
        }
      });
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('No pudimos agregar el inventario.')));
    }
  }

  @override
  Widget build(BuildContext context) {
    final base = widget.catalogoBase;
    final esEdicion = _productoActual != null;

    return Scaffold(
      appBar: AppBar(title: Text(widget.producto == null ? 'NUEVO PRODUCTO' : 'EDITAR PRODUCTO')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
        children: [
          if (_error != null) AdminErrorBanner(message: _error!),
          Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                TextFormField(
                  controller: _nombreCtrl,
                  decoration: const InputDecoration(labelText: 'Nombre'),
                  validator: (v) => (v == null || v.trim().length < 2) ? 'Requerido' : null,
                ),
                const SizedBox(height: 16),
                TextFormField(controller: _descripcionCtrl, decoration: const InputDecoration(labelText: 'Descripcion (opcional)'), maxLines: 3),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: TextFormField(
                        controller: _precioCtrl,
                        decoration: const InputDecoration(labelText: 'Precio (Bs)'),
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'^\d*\.?\d{0,2}'))],
                        validator: (v) {
                          final n = double.tryParse(v ?? '');
                          return (n == null || n <= 0) ? 'Precio invalido' : null;
                        },
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: TextFormField(
                        controller: _precioOriginalCtrl,
                        decoration: const InputDecoration(labelText: 'Precio original (opcional)'),
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'^\d*\.?\d{0,2}'))],
                        validator: (v) {
                          if (v == null || v.trim().isEmpty) return null;
                          final n = double.tryParse(v);
                          return (n == null || n <= 0) ? 'Precio invalido' : null;
                        },
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                DropdownButtonFormField<int>(
                  initialValue: _categoriaId,
                  decoration: const InputDecoration(labelText: 'Categoria'),
                  items: [for (final o in base.categorias) DropdownMenuItem(value: o.id, child: Text(o.nombre))],
                  onChanged: (v) => setState(() => _categoriaId = v),
                  validator: (v) => v == null ? 'Elegi una categoria' : null,
                ),
                const SizedBox(height: 16),
                DropdownButtonFormField<int>(
                  initialValue: _marcaId,
                  decoration: const InputDecoration(labelText: 'Marca'),
                  items: [
                    for (final o in base.marcas) DropdownMenuItem(value: o.id, child: Text(o.nombre)),
                    const DropdownMenuItem(value: _marcaOtroId, child: Text('Otro...')),
                  ],
                  onChanged: (v) => setState(() => _marcaId = v),
                  validator: (v) => v == null ? 'Elegi una marca' : null,
                ),
                if (_marcaId == _marcaOtroId) ...[
                  const SizedBox(height: 12),
                  TextFormField(controller: _marcaNuevaCtrl, decoration: const InputDecoration(labelText: 'Nombre de la marca nueva')),
                ],
                const SizedBox(height: 16),
                DropdownButtonFormField<int>(
                  initialValue: _proveedorId,
                  decoration: const InputDecoration(labelText: 'Proveedor'),
                  items: [for (final o in base.proveedores) DropdownMenuItem(value: o.id, child: Text(o.nombre))],
                  onChanged: (v) => setState(() => _proveedorId = v),
                  validator: (v) => v == null ? 'Elegi un proveedor' : null,
                ),
                const SizedBox(height: 16),
                DropdownButtonFormField<int>(
                  initialValue: _temporadaId,
                  decoration: const InputDecoration(labelText: 'Temporada'),
                  items: [for (final o in base.temporadas) DropdownMenuItem(value: o.id, child: Text(o.nombre))],
                  onChanged: (v) => setState(() => _temporadaId = v),
                  validator: (v) => v == null ? 'Elegi una temporada' : null,
                ),
                const SizedBox(height: 16),
                DropdownButtonFormField<int>(
                  initialValue: _coleccionId,
                  decoration: const InputDecoration(labelText: 'Coleccion'),
                  items: [for (final o in base.colecciones) DropdownMenuItem(value: o.id, child: Text(o.nombre))],
                  onChanged: (v) => setState(() => _coleccionId = v),
                  validator: (v) => v == null ? 'Elegi una coleccion' : null,
                ),
                if (esEdicion) ...[
                  const SizedBox(height: 16),
                  DropdownButtonFormField<String>(
                    initialValue: _estado,
                    decoration: const InputDecoration(labelText: 'Estado'),
                    items: const [
                      DropdownMenuItem(value: 'activo', child: Text('Activo')),
                      DropdownMenuItem(value: 'inactivo', child: Text('Inactivo')),
                    ],
                    onChanged: (v) => setState(() => _estado = v!),
                  ),
                ],
                const SizedBox(height: 24),
                ElevatedButton(
                  onPressed: _guardando ? null : _guardar,
                  child: Text(_guardando ? 'GUARDANDO...' : (esEdicion ? 'GUARDAR CAMBIOS' : 'CREAR PRODUCTO')),
                ),
              ],
            ),
          ),
          if (esEdicion) ...[
            const SizedBox(height: 32),
            const Divider(),
            const SizedBox(height: 16),
            _ImagenesSection(
              producto: _productoActual!,
              subiendo: _subiendoImagenes,
              onAgregar: _agregarImagenes,
              onEliminar: _eliminarImagen,
            ),
            const SizedBox(height: 32),
            const Divider(),
            const SizedBox(height: 16),
            _InventarioSection(
              base: base,
              cargando: _cargandoInventario,
              inventario: _inventario ?? const [],
              onCantidadChanged: _actualizarCantidadInventario,
              onAgregar: _agregarInventario,
            ),
          ] else ...[
            const SizedBox(height: 24),
            const Text(
              'Guarda el producto para poder agregar fotos e inventario por sucursal.',
              style: TextStyle(fontSize: 12, color: AppColors.grayText, fontStyle: FontStyle.italic),
            ),
          ],
        ],
      ),
    );
  }
}

class _ImagenesSection extends StatelessWidget {
  const _ImagenesSection({required this.producto, required this.subiendo, required this.onAgregar, required this.onEliminar});

  final ProductoAdmin producto;
  final bool subiendo;
  final VoidCallback onAgregar;
  final ValueChanged<ImagenProducto> onEliminar;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('IMAGENES', style: TextStyle(fontWeight: FontWeight.w800, color: AppColors.brandDark, letterSpacing: 0.4)),
        const SizedBox(height: 12),
        if (producto.imagenes.isEmpty)
          const Text('Todavia no hay fotos.', style: TextStyle(fontSize: 12, color: AppColors.grayText))
        else
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: [
              for (final img in producto.imagenes)
                Stack(
                  children: [
                    ClipRRect(
                      child: SizedBox(
                        width: 84,
                        height: 84,
                        child: CachedNetworkImage(imageUrl: img.url, fit: BoxFit.cover),
                      ),
                    ),
                    Positioned(
                      top: -6,
                      right: -6,
                      child: IconButton(
                        icon: const Icon(Icons.cancel, size: 20, color: AppColors.danger),
                        onPressed: () => onEliminar(img),
                      ),
                    ),
                  ],
                ),
            ],
          ),
        const SizedBox(height: 12),
        OutlinedButton.icon(
          onPressed: subiendo ? null : onAgregar,
          icon: subiendo ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.add_photo_alternate_outlined, size: 18),
          label: Text(subiendo ? 'SUBIENDO...' : 'AGREGAR FOTOS'),
        ),
      ],
    );
  }
}

class _InventarioSection extends StatefulWidget {
  const _InventarioSection({
    required this.base,
    required this.cargando,
    required this.inventario,
    required this.onCantidadChanged,
    required this.onAgregar,
  });

  final CatalogoBase base;
  final bool cargando;
  final List<InventarioItem> inventario;
  final void Function(InventarioItem item, int cantidad) onCantidadChanged;
  final Future<void> Function({required int sucursalId, required int tallaId, required int colorId, required int cantidad}) onAgregar;

  @override
  State<_InventarioSection> createState() => _InventarioSectionState();
}

class _InventarioSectionState extends State<_InventarioSection> {
  int? _sucursalId;
  int? _tallaId;
  int? _colorId;
  final _cantidadCtrl = TextEditingController();
  bool _agregando = false;

  @override
  void dispose() {
    _cantidadCtrl.dispose();
    super.dispose();
  }

  Future<void> _agregar() async {
    final cantidad = int.tryParse(_cantidadCtrl.text.trim());
    if (_sucursalId == null || _tallaId == null || _colorId == null || cantidad == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Completa sucursal, talla, color y cantidad.')));
      return;
    }
    setState(() => _agregando = true);
    await widget.onAgregar(sucursalId: _sucursalId!, tallaId: _tallaId!, colorId: _colorId!, cantidad: cantidad);
    if (mounted) {
      setState(() => _agregando = false);
      _cantidadCtrl.clear();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('INVENTARIO POR SUCURSAL', style: TextStyle(fontWeight: FontWeight.w800, color: AppColors.brandDark, letterSpacing: 0.4)),
        const SizedBox(height: 12),
        if (widget.cargando)
          const Center(child: Padding(padding: EdgeInsets.all(16), child: CircularProgressIndicator()))
        else if (widget.inventario.isEmpty)
          const Text('Sin stock cargado todavia.', style: TextStyle(fontSize: 12, color: AppColors.grayText))
        else
          for (final item in widget.inventario) _InventarioRow(item: item, onCantidadChanged: (c) => widget.onCantidadChanged(item, c)),
        const SizedBox(height: 16),
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(border: Border.all(color: AppColors.grayBorderLight)),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Agregar stock', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppColors.grayTextDark)),
              const SizedBox(height: 8),
              DropdownButtonFormField<int>(
                initialValue: _sucursalId,
                decoration: const InputDecoration(labelText: 'Sucursal', isDense: true),
                items: [for (final o in widget.base.sucursales) DropdownMenuItem(value: o.id, child: Text(o.nombre))],
                onChanged: (v) => setState(() => _sucursalId = v),
              ),
              const SizedBox(height: 10),
              Row(
                children: [
                  Expanded(
                    child: DropdownButtonFormField<int>(
                      initialValue: _tallaId,
                      decoration: const InputDecoration(labelText: 'Talla', isDense: true),
                      items: [for (final o in widget.base.tallas) DropdownMenuItem(value: o.id, child: Text(o.nombre))],
                      onChanged: (v) => setState(() => _tallaId = v),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: DropdownButtonFormField<int>(
                      initialValue: _colorId,
                      decoration: const InputDecoration(labelText: 'Color', isDense: true),
                      items: [for (final o in widget.base.colores) DropdownMenuItem(value: o.id, child: Text(o.nombre))],
                      onChanged: (v) => setState(() => _colorId = v),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _cantidadCtrl,
                      decoration: const InputDecoration(labelText: 'Cantidad', isDense: true),
                      keyboardType: TextInputType.number,
                      inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                    ),
                  ),
                  const SizedBox(width: 8),
                  ElevatedButton(onPressed: _agregando ? null : _agregar, child: Text(_agregando ? '...' : '+ AGREGAR')),
                ],
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _InventarioRow extends StatefulWidget {
  const _InventarioRow({required this.item, required this.onCantidadChanged});

  final InventarioItem item;
  final ValueChanged<int> onCantidadChanged;

  @override
  State<_InventarioRow> createState() => _InventarioRowState();
}

class _InventarioRowState extends State<_InventarioRow> {
  late final TextEditingController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = TextEditingController(text: '${widget.item.cantidad}');
  }

  @override
  void didUpdateWidget(covariant _InventarioRow oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.item.cantidad != widget.item.cantidad) _ctrl.text = '${widget.item.cantidad}';
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          Expanded(
            flex: 2,
            child: Text(widget.item.sucursalNombre, style: const TextStyle(fontSize: 12)),
          ),
          Expanded(child: Text('${widget.item.tallaCodigo} / ${widget.item.colorNombre}', style: const TextStyle(fontSize: 12))),
          SizedBox(
            width: 60,
            height: 36,
            child: TextField(
              controller: _ctrl,
              textAlign: TextAlign.center,
              keyboardType: TextInputType.number,
              inputFormatters: [FilteringTextInputFormatter.digitsOnly],
              style: const TextStyle(fontSize: 13),
              decoration: const InputDecoration(isDense: true, contentPadding: EdgeInsets.symmetric(vertical: 6)),
              onSubmitted: (v) => widget.onCantidadChanged(int.tryParse(v) ?? widget.item.cantidad),
              onEditingComplete: () {
                widget.onCantidadChanged(int.tryParse(_ctrl.text) ?? widget.item.cantidad);
                FocusScope.of(context).unfocus();
              },
            ),
          ),
        ],
      ),
    );
  }
}
