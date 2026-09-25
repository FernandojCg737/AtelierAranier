import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/venta.dart';
import '../auth/auth_provider.dart';

/// CU11, lado cliente: checkout del carrito. Soporta pago por QR (subis la
/// foto del comprobante y un cajero lo revisa despues) y PayPal/tarjeta de
/// credito -- este ultimo con los botones reales del JS SDK de PayPal
/// embebidos inline en un WebView chico (`/paypal-embed`, misma pagina que
/// el checkout web), no un boton propio: crear la orden lo hace esa pagina
/// sola con su propio fetch, este repositorio solo necesita capturarla
/// despues de que el cliente la aprueba (ver `checkout_screen.dart`).
class VentaCreada {
  const VentaCreada({required this.id, required this.estadoPago, required this.sucursalNombre});

  final int id;
  final String estadoPago;
  final String sucursalNombre;

  factory VentaCreada.fromJson(Map<String, dynamic> json) {
    return VentaCreada(
      id: json['id'] as int,
      estadoPago: json['estado_pago'] as String,
      sucursalNombre: json['sucursal_nombre'] as String,
    );
  }
}

class StockCheckoutItem {
  const StockCheckoutItem({
    required this.detalleId,
    required this.productoNombre,
    required this.tallaCodigo,
    required this.colorNombre,
    required this.sucursalNombre,
    required this.cantidadPedida,
    required this.cantidadDisponible,
    required this.disponible,
  });

  final int detalleId;
  final String productoNombre;
  final String tallaCodigo;
  final String colorNombre;
  final String sucursalNombre;
  final int cantidadPedida;
  final int cantidadDisponible;
  final bool disponible;

  factory StockCheckoutItem.fromJson(Map<String, dynamic> json) {
    return StockCheckoutItem(
      detalleId: json['detalle_id'] as int,
      productoNombre: json['producto_nombre'] as String,
      tallaCodigo: json['talla_codigo'] as String,
      colorNombre: json['color_nombre'] as String,
      sucursalNombre: json['sucursal_nombre'] as String,
      cantidadPedida: json['cantidad_pedida'] as int,
      cantidadDisponible: json['cantidad_disponible'] as int,
      disponible: json['disponible'] as bool,
    );
  }
}

class VentasRepository {
  VentasRepository(this._dio);

  final Dio _dio;

  // CU11, pedido del usuario: chequeo proactivo de stock ANTES de mostrar
  // los metodos de pago (antes solo se sabia al aprobar el pago en PayPal o
  // subir el comprobante QR, ya tarde). Cada item del carrito ya trae su
  // propia sucursal (elegida al agregarlo), asi que esto no necesita
  // parametro -- mismo endpoint que usa el checkout web.
  Future<List<StockCheckoutItem>> verificarStock() async {
    final res = await _dio.get('/ventas/checkout/verificar-stock');
    return (res.data as List<dynamic>)
        .map((e) => StockCheckoutItem.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  // Pedido del usuario: la sucursal de cada item ya quedo fija al agregarlo
  // al carrito -- si el carrito tiene items de mas de una sucursal, un solo
  // pago (comprobante QR o captura de PayPal) se reparte en varias ventas.
  Future<List<VentaCreada>> checkoutQr({required String filePath, required String fileName}) async {
    final form = FormData.fromMap({'file': await MultipartFile.fromFile(filePath, filename: fileName)});
    final res = await _dio.post('/ventas/checkout/qr', data: form);
    return (res.data as List<dynamic>).map((e) => VentaCreada.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<VentaCreada>> capturarOrdenPaypal({required String orderId}) async {
    final res = await _dio.post('/ventas/checkout/paypal/capturar/$orderId');
    return (res.data as List<dynamic>).map((e) => VentaCreada.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<Venta>> misCompras() async {
    final res = await _dio.get('/ventas/mias');
    return (res.data as List<dynamic>).map((e) => Venta.fromJson(e as Map<String, dynamic>)).toList();
  }

  // CU20: calificar una compra ya completada (estrellas 1-5 + comentario
  // opcional) -- una sola vez por venta, el backend lo rechaza si ya tiene.
  Future<void> calificar({required int ventaId, required int estrellas, String? comentario}) {
    return _dio.post('/calificaciones/venta/$ventaId', data: {'estrellas': estrellas, 'comentario': comentario});
  }

  // CU11: solicitar devolucion total o parcial de una compra (plazo 24h)
  Future<void> solicitarDevolucion({
    required int ventaId,
    required String motivo,
    required String tipo,
    required String metodoReembolso,
    String? observaciones,
    required List<Map<String, dynamic>> items,
  }) {
    return _dio.post(
      '/devoluciones/solicitar/$ventaId',
      data: {
        'motivo': motivo,
        'tipo': tipo,
        'metodo_reembolso': metodoReembolso,
        'observaciones': observaciones,
        'items': items,
      },
    );
  }
}

final ventasRepositoryProvider = Provider<VentasRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return VentasRepository(apiClient.dio);
});
