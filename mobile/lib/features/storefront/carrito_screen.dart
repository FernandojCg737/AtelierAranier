import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme.dart';
import 'cart_provider.dart';

/// Replica de `pages/carrito/carrito.html` en la web: mismo header, mismo
/// estado vacio (fondo gris, eyebrow + titulo + boton con flecha) y misma
/// lista de items + resumen con total y boton de checkout deshabilitado.
class CarritoScreen extends ConsumerWidget {
  const CarritoScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final items = ref.watch(cartProvider);
    final total = ref.watch(cartTotalPriceProvider);
    final totalItems = ref.watch(cartTotalItemsProvider);

    return CustomScrollView(
      slivers: [
        SliverPadding(
          padding: EdgeInsets.fromLTRB(20, MediaQuery.of(context).padding.top + 20, 20, 0),
          sliver: SliverToBoxAdapter(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'CARRITO DE COMPRAS',
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w800,
                    fontStyle: FontStyle.italic,
                    color: AppColors.brandDark,
                    letterSpacing: -0.2,
                  ),
                ),
                const SizedBox(height: 10),
                const Text(
                  'Revisa tus articulos seleccionados antes de finalizar la compra.',
                  style: TextStyle(fontSize: 14, color: AppColors.grayTextDark),
                ),
              ],
            ),
          ),
        ),
        SliverPadding(
          padding: const EdgeInsets.fromLTRB(20, 24, 20, 32),
          sliver: SliverFillRemaining(
            hasScrollBody: false,
            child: Center(
              child: items.isEmpty
                  ? const _CarritoEmpty()
                  : _CarritoContent(items: items, total: total, totalItems: totalItems),
            ),
          ),
        ),
      ],
    );
  }
}

class _CarritoEmpty extends StatelessWidget {
  const _CarritoEmpty();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      color: const Color(0xFFF7F7F5),
      padding: const EdgeInsets.symmetric(vertical: 56, horizontal: 20),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const EyebrowText('Carrito', color: Color(0xFF9AA5AC)),
          const SizedBox(height: 12),
          const Text(
            'TU CARRITO ESTA VACIO',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: AppColors.brandDark),
          ),
          const SizedBox(height: 12),
          const Text(
            'Agrega productos a tu carrito para comenzar',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 14, color: AppColors.grayTextDark),
          ),
          const SizedBox(height: 28),
          ElevatedButton(
            onPressed: () => context.go('/tienda'),
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text('CONTINUAR COMPRANDO'),
                SizedBox(width: 10),
                Icon(Icons.arrow_forward, size: 16),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _CarritoContent extends ConsumerWidget {
  const _CarritoContent({required this.items, required this.total, required this.totalItems});

  final List<CartItem> items;
  final double total;
  final int totalItems;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        DecoratedBox(
          decoration: const BoxDecoration(border: Border(top: BorderSide(color: Color(0xFFE5E5E5)))),
          child: Column(
            children: [
              for (final item in items) _CarritoItemRow(item: item),
            ],
          ),
        ),
        const SizedBox(height: 24),
        Container(
          width: double.infinity,
          color: const Color(0xFFF7F7F5),
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                crossAxisAlignment: CrossAxisAlignment.baseline,
                textBaseline: TextBaseline.alphabetic,
                children: [
                  Text(
                    'TOTAL ($totalItems ARTICULOS)',
                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: Color(0xFF666666), letterSpacing: 0.4),
                  ),
                  Text(
                    '${total.toStringAsFixed(0)} Bs',
                    style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: AppColors.brandDark),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: null,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.brandDark.withValues(alpha: 0.6),
                  disabledBackgroundColor: AppColors.brandDark.withValues(alpha: 0.6),
                  foregroundColor: Colors.white,
                  disabledForegroundColor: Colors.white,
                ),
                child: const Text('FINALIZAR COMPRA (PROXIMAMENTE)'),
              ),
              const SizedBox(height: 12),
              Center(
                child: TextButton(
                  onPressed: () => context.go('/tienda'),
                  child: const Text(
                    'Continuar comprando',
                    style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.brandDark, decoration: TextDecoration.underline),
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _CarritoItemRow extends ConsumerWidget {
  const _CarritoItemRow({required this.item});

  final CartItem item;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final subtotal = item.price * item.quantity;
    return DecoratedBox(
      decoration: const BoxDecoration(border: Border(bottom: BorderSide(color: Color(0xFFE5E5E5)))),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 14),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Container(
              width: 60,
              height: 76,
              color: AppColors.grayBorderLight,
              child: item.image.isNotEmpty
                  ? Image.network(item.image, fit: BoxFit.cover)
                  : const Icon(Icons.image_not_supported_outlined, color: AppColors.grayText, size: 20),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (item.brand != null)
                    Text(
                      item.brand!.toUpperCase(),
                      style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: Color(0xFF9A9A9A), letterSpacing: 0.4),
                    ),
                  Text(
                    item.name,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: AppColors.brandDark),
                  ),
                  const SizedBox(height: 4),
                  Text('${item.price.toStringAsFixed(0)} Bs', style: const TextStyle(fontSize: 12, color: Color(0xFF888888))),
                ],
              ),
            ),
            const SizedBox(width: 8),
            _QtyStepper(
              quantity: item.quantity,
              onDecrease: () => ref.read(cartProvider.notifier).updateQuantity(item.id, item.quantity - 1),
              onIncrease: () => ref.read(cartProvider.notifier).updateQuantity(item.id, item.quantity + 1),
            ),
            const SizedBox(width: 12),
            SizedBox(
              width: 64,
              child: Text(
                '${subtotal.toStringAsFixed(0)} Bs',
                textAlign: TextAlign.right,
                style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w800, color: AppColors.brandDark),
              ),
            ),
            IconButton(
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
              icon: const Icon(Icons.close, size: 16, color: AppColors.grayText),
              onPressed: () => ref.read(cartProvider.notifier).removeItem(item.id),
            ),
          ],
        ),
      ),
    );
  }
}

class _QtyStepper extends StatelessWidget {
  const _QtyStepper({required this.quantity, required this.onDecrease, required this.onIncrease});

  final int quantity;
  final VoidCallback onDecrease;
  final VoidCallback onIncrease;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        _QtyButton(label: '−', onTap: onDecrease),
        SizedBox(
          width: 22,
          child: Text('$quantity', textAlign: TextAlign.center, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: AppColors.brandDark)),
        ),
        _QtyButton(label: '+', onTap: onIncrease),
      ],
    );
  }
}

class _QtyButton extends StatelessWidget {
  const _QtyButton({required this.label, required this.onTap});

  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 26,
        height: 26,
        alignment: Alignment.center,
        decoration: BoxDecoration(border: Border.all(color: AppColors.grayBorder)),
        child: Text(label, style: const TextStyle(fontSize: 14, color: AppColors.brandDark)),
      ),
    );
  }
}
