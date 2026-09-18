import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/carrito.dart';
import '../auth/auth_provider.dart';

/// CU11: el carrito vive en el backend, ligado al cliente autenticado --
/// mismo contrato que `services/cart.ts` en la web.
class CarritoRepository {
  CarritoRepository(this._dio);

  final Dio _dio;

  Future<Carrito> obtener() async {
    final res = await _dio.get('/carrito');
    return Carrito.fromJson(res.data as Map<String, dynamic>);
  }

  Future<Carrito> agregar({
    required int productoId,
    required int tallaId,
    required int colorId,
    required int sucursalId,
    required int cantidad,
  }) async {
    final res = await _dio.post(
      '/carrito/items',
      data: {
        'producto_id': productoId,
        'talla_id': tallaId,
        'color_id': colorId,
        'sucursal_id': sucursalId,
        'cantidad': cantidad,
      },
    );
    return Carrito.fromJson(res.data as Map<String, dynamic>);
  }

  Future<Carrito> actualizarCantidad(int detalleId, int cantidad) async {
    final res = await _dio.put('/carrito/items/$detalleId', data: {'cantidad': cantidad});
    return Carrito.fromJson(res.data as Map<String, dynamic>);
  }

  Future<Carrito> eliminar(int detalleId) async {
    final res = await _dio.delete('/carrito/items/$detalleId');
    return Carrito.fromJson(res.data as Map<String, dynamic>);
  }

  Future<Carrito> vaciar() async {
    final res = await _dio.delete('/carrito');
    return Carrito.fromJson(res.data as Map<String, dynamic>);
  }
}

final carritoRepositoryProvider = Provider<CarritoRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return CarritoRepository(apiClient.dio);
});
