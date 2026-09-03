import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme.dart';
import '../../models/producto_publico.dart';
import 'cart_provider.dart';
import 'catalogo_provider.dart';

class ProductoDetalleScreen extends ConsumerStatefulWidget {
  const ProductoDetalleScreen({super.key, required this.productoId});

  final int productoId;

  @override
  ConsumerState<ProductoDetalleScreen> createState() => _ProductoDetalleScreenState();
}

class _ProductoDetalleScreenState extends ConsumerState<ProductoDetalleScreen> {
  late Future<ProductoPublico> _future;
  int _activeImage = 0;
  bool _added = false;

  @override
  void initState() {
    super.initState();
    _future = ref.read(catalogoRepositoryProvider).getProducto(widget.productoId);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('PRODUCTO')),
      body: FutureBuilder<ProductoPublico>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError || !snapshot.hasData) {
            return const Center(child: Text('Producto no encontrado.'));
          }
          final p = snapshot.data!;
          final imagenes = p.imagenes.isEmpty ? <String>[] : p.imagenes;

          return ListView(
            padding: EdgeInsets.only(bottom: 32 + MediaQuery.of(context).padding.bottom),
            children: [
              AspectRatio(
                aspectRatio: 1,
                child: imagenes.isEmpty
                    ? Container(color: AppColors.grayBorderLight)
                    : CachedNetworkImage(imageUrl: imagenes[_activeImage], fit: BoxFit.cover),
              ),
              if (imagenes.length > 1)
                SizedBox(
                  height: 64,
                  child: ListView.separated(
                    scrollDirection: Axis.horizontal,
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    itemCount: imagenes.length,
                    separatorBuilder: (_, _) => const SizedBox(width: 8),
                    itemBuilder: (context, i) => GestureDetector(
                      onTap: () => setState(() => _activeImage = i),
                      child: Container(
                        width: 56,
                        decoration: BoxDecoration(
                          border: Border.all(color: i == _activeImage ? AppColors.brandDark : AppColors.grayBorderLight, width: 2),
                        ),
                        child: CachedNetworkImage(imageUrl: imagenes[i], fit: BoxFit.cover),
                      ),
                    ),
                  ),
                ),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                      decoration: BoxDecoration(border: Border.all(color: p.agotado ? AppColors.danger : AppColors.grayBorder)),
                      child: Text(
                        p.agotado ? 'AGOTADO' : 'EN STOCK',
                        style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: p.agotado ? AppColors.danger : AppColors.grayTextDark),
                      ),
                    ),
                    const SizedBox(height: 12),
                    EyebrowText(p.marcaNombre),
                    Text(
                      p.nombre,
                      style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: AppColors.brandDark),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        if (p.tieneDescuento) ...[
                          Text(
                            '${p.precioOriginal!.toStringAsFixed(0)} Bs',
                            style: const TextStyle(color: AppColors.grayText, decoration: TextDecoration.lineThrough),
                          ),
                          const SizedBox(width: 8),
                        ],
                        Text(
                          '${p.precio.toStringAsFixed(0)} Bs',
                          style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: AppColors.brandDark),
                        ),
                      ],
                    ),
                    const Divider(height: 32),
                    Text(p.descripcion ?? 'Este producto no tiene una descripcion detallada todavia.'),
                    const Divider(height: 32),
                    ElevatedButton(
                      onPressed: p.agotado
                          ? null
                          : () {
                              ref.read(cartProvider.notifier).addItem(
                                id: p.id.toString(),
                                name: p.nombre,
                                brand: p.marcaNombre,
                                price: p.precio,
                                image: imagenes.isEmpty ? '' : imagenes.first,
                              );
                              setState(() => _added = true);
                              Future.delayed(const Duration(milliseconds: 1600), () {
                                if (mounted) setState(() => _added = false);
                              });
                            },
                      child: Text(p.agotado ? 'SIN STOCK' : (_added ? 'AGREGADO' : 'ANADIR AL CARRITO')),
                    ),
                    const SizedBox(height: 20),
                    Row(
                      children: [
                        const Text('Sucursales con stock: ', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 12)),
                        Expanded(
                          child: Text(
                            p.sucursalesDisponibles.isEmpty ? 'Sin stock por el momento' : p.sucursalesDisponibles.join(', '),
                            style: const TextStyle(fontSize: 12, color: AppColors.grayTextDark),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Row(
                      children: [
                        const Text('Categoria: ', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 12)),
                        Text(p.categoriaNombre, style: const TextStyle(fontSize: 12, color: AppColors.grayTextDark)),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Row(
                      children: [
                        const Text('Temporada: ', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 12)),
                        Text(p.temporadaNombre, style: const TextStyle(fontSize: 12, color: AppColors.grayTextDark)),
                      ],
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
