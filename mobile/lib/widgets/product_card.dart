import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';

import '../core/theme.dart';
import '../models/producto_publico.dart';

/// Tarjeta de producto: imagen + badge Agotado/Nuevo/Descuento + nombre +
/// precio (con precio tachado si hay descuento) — mismo lenguaje visual
/// que `.product-tile` / `.discount-card` en la web (esquinas rectas).
class ProductCard extends StatelessWidget {
  const ProductCard({super.key, required this.producto, required this.onTap, this.badge});

  final ProductoPublico producto;
  final VoidCallback onTap;

  /// 'nuevo' | 'descuento' | null — cual badge mostrar cuando corresponde
  /// (el de Agotado siempre tiene prioridad si no hay stock).
  final String? badge;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(border: Border.all(color: AppColors.grayBorderLight)),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Expanded (no AspectRatio fijo): dentro de una grilla con
            // childAspectRatio fijo, un alto fijo de imagen + texto de largo
            // variable puede desbordar la celda. Con Expanded la imagen
            // siempre ocupa lo que sobra despues del texto, sin overflow.
            Expanded(
              child: Stack(
                fit: StackFit.expand,
                children: [
                  if (producto.imagenPrincipal != null)
                    CachedNetworkImage(
                      imageUrl: producto.imagenPrincipal!,
                      fit: BoxFit.cover,
                      errorWidget: (_, _, _) => Container(color: AppColors.grayBorderLight),
                    )
                  else
                    Container(color: AppColors.grayBorderLight),
                  if (producto.agotado)
                    _Badge(text: 'Agotado', color: AppColors.danger)
                  else if (badge == 'nuevo')
                    const _Badge(text: 'Nuevo', color: AppColors.brandDark)
                  else if (badge == 'descuento' && producto.porcentajeDescuento != null)
                    _Badge(text: '-${producto.porcentajeDescuento}%', color: const Color(0xFFD32F2F)),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 10, 12, 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  EyebrowText(producto.marcaNombre),
                  const SizedBox(height: 2),
                  Text(
                    producto.nombre,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontWeight: FontWeight.w800,
                      fontStyle: FontStyle.italic,
                      color: AppColors.brandDark,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Row(
                    children: [
                      if (producto.tieneDescuento) ...[
                        Text(
                          '${producto.precioOriginal!.toStringAsFixed(0)} Bs',
                          style: const TextStyle(
                            fontSize: 12,
                            color: AppColors.grayText,
                            decoration: TextDecoration.lineThrough,
                          ),
                        ),
                        const SizedBox(width: 6),
                      ],
                      Text(
                        '${producto.precio.toStringAsFixed(0)} Bs',
                        style: TextStyle(
                          fontWeight: FontWeight.w800,
                          color: producto.tieneDescuento ? const Color(0xFFD32F2F) : AppColors.brandDark,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Badge extends StatelessWidget {
  const _Badge({required this.text, required this.color});

  final String text;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Positioned(
      top: 8,
      left: 8,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        color: color,
        child: Text(
          text.toUpperCase(),
          style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.w700, letterSpacing: 0.5),
        ),
      ),
    );
  }
}
