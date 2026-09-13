import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme.dart';
import '../../models/producto_publico.dart';
import '../../widgets/product_card.dart';
import '../auth/auth_provider.dart';
import 'catalogo_provider.dart';
import 'hero_widget.dart';
import 'recomendaciones_provider.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final novedades = ref.watch(novedadesProvider);
    final descuentos = ref.watch(descuentosProvider);
    final productosAsync = ref.watch(productosPublicosProvider);
    final esClienteConSesion = ref.watch(authProvider).usuario?.isCliente ?? false;

    return RefreshIndicator(
      onRefresh: () async => ref.invalidate(productosPublicosProvider),
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          const HeroSection(),
          productosAsync.when(
            data: (_) => Column(
              children: [
                _Seccion(titulo: 'NOVEDADES', productos: novedades, badge: 'nuevo'),
                if (esClienteConSesion) const _RecomendacionesSection(),
                _Seccion(titulo: 'DESCUENTOS', productos: descuentos, badge: 'descuento'),
              ],
            ),
            loading: () => const Padding(
              padding: EdgeInsets.all(48),
              child: Center(child: CircularProgressIndicator()),
            ),
            error: (err, _) => const Padding(
              padding: EdgeInsets.all(24),
              child: Text('No pudimos cargar el catalogo.'),
            ),
          ),
          const SizedBox(height: 32),
        ],
      ),
    );
  }
}

/// CU18: "Recomendado para ti" -- solo se pinta si hay sesion de cliente
/// (ver el `if` en build()), asi que aca ya se puede mirar el provider
/// sin miedo a que dispare la llamada para invitados/staff.
class _RecomendacionesSection extends ConsumerWidget {
  const _RecomendacionesSection();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.watch(misRecomendacionesProvider);
    final recomendados = ref.watch(productosRecomendadosProvider);
    if (recomendados.isEmpty) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 32, 20, 0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'RECOMENDADO PARA TI',
            style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800, fontStyle: FontStyle.italic, color: AppColors.brandDark),
          ),
          const SizedBox(height: 4),
          const Text(
            'Elegido segun tus compras -- con ayuda de IA.',
            style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.grayText),
          ),
          const SizedBox(height: 16),
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: recomendados.length,
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              childAspectRatio: 0.56,
            ),
            itemBuilder: (context, i) {
              final r = recomendados[i];
              return ProductCard(
                producto: r.producto,
                caption: r.razon,
                onTap: () => context.push('/producto/${r.producto.id}'),
              );
            },
          ),
        ],
      ),
    );
  }
}

class _Seccion extends StatelessWidget {
  const _Seccion({required this.titulo, required this.productos, required this.badge});

  final String titulo;
  final List<ProductoPublico> productos;
  final String badge;

  @override
  Widget build(BuildContext context) {
    if (productos.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 32, 20, 0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            titulo,
            style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800, fontStyle: FontStyle.italic, color: AppColors.brandDark),
          ),
          const SizedBox(height: 16),
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: productos.length,
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              childAspectRatio: 0.62,
            ),
            itemBuilder: (context, i) {
              final producto = productos[i];
              return ProductCard(
                producto: producto,
                badge: badge,
                onTap: () => context.push('/producto/${producto.id}'),
              );
            },
          ),
        ],
      ),
    );
  }
}
