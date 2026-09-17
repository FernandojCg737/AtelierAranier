import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/recomendacion.dart';
import '../auth/auth_provider.dart';
import 'catalogo_provider.dart';
import 'recomendaciones_provider.dart' show ProductoRecomendado;

class RelacionadosRepository {
  RelacionadosRepository(this._dio);

  final Dio _dio;

  /// Informativo (alimenta la senal de "vistos juntos" a futuro): si falla
  /// -- sin sesion, red caida -- no debe romper la pantalla de detalle.
  Future<void> registrarVista(int productoId) async {
    try {
      await _dio.post('/recomendaciones/vista/$productoId');
    } catch (_) {
      // silencioso a proposito
    }
  }

  Future<List<Recomendacion>> relacionados(int productoId) async {
    final res = await _dio.get('/recomendaciones/relacionados/$productoId');
    return (res.data as List<dynamic>).map((e) => Recomendacion.fromJson(e as Map<String, dynamic>)).toList();
  }
}

final relacionadosRepositoryProvider = Provider<RelacionadosRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return RelacionadosRepository(apiClient.dio);
});

/// CU18 extendido: "Tambien te puede interesar" en el detalle de producto
/// -- a diferencia de productosRecomendadosProvider (Home, personalizado
/// por cliente y solo con sesion iniciada), esto se arma por PRODUCTO (que
/// otros productos vieron juntos los clientes que pasaron por este mismo)
/// y se muestra a cualquier visitante, tenga sesion o no. `family` sobre
/// productoId: cada producto visitado pide -- y cachea -- los suyos.
final relacionadosProvider = FutureProvider.family<List<ProductoRecomendado>, int>((ref, productoId) async {
  final repo = ref.watch(relacionadosRepositoryProvider);
  unawaited(repo.registrarVista(productoId));

  final catalogo = await ref.watch(productosPublicosProvider.future);
  final relacionados = await repo.relacionados(productoId);

  final porId = {for (final p in catalogo) p.id: p};
  return [
    for (final r in relacionados)
      if (porId[r.productoId] != null) ProductoRecomendado(producto: porId[r.productoId]!, razon: r.razon),
  ];
});
