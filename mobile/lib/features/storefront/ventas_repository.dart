import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/venta.dart';
import '../auth/auth_provider.dart';

/// CU11, lado cliente: checkout del carrito. Por ahora el mobile solo
/// soporta el pago por QR (subis la foto del comprobante y un cajero lo
/// revisa despues) -- PayPal queda pendiente porque necesita un WebView +
/// deep link de retorno a la app, algo que no se puede armar/probar sin un
/// dispositivo real a mano.
class VentaCreada {
  const VentaCreada({required this.id, required this.estadoPago});

  final int id;
  final String estadoPago;

  factory VentaCreada.fromJson(Map<String, dynamic> json) {
    return VentaCreada(id: json['id'] as int, estadoPago: json['estado_pago'] as String);
  }
}

class VentasRepository {
  VentasRepository(this._dio);

  final Dio _dio;

  Future<VentaCreada> checkoutQr({required int sucursalId, required String filePath, required String fileName}) async {
    final form = FormData.fromMap({
      'sucursal_id': sucursalId.toString(),
      'file': await MultipartFile.fromFile(filePath, filename: fileName),
    });
    final res = await _dio.post('/ventas/checkout/qr', data: form);
    return VentaCreada.fromJson(res.data as Map<String, dynamic>);
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
}

final ventasRepositoryProvider = Provider<VentasRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return VentasRepository(apiClient.dio);
});
