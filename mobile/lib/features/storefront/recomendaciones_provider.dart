import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/producto_publico.dart';
import '../../models/recomendacion.dart';
import '../auth/auth_provider.dart';
import 'catalogo_provider.dart';

class RecomendacionesRepository {
  RecomendacionesRepository(this._dio);

  final Dio _dio;

  Future<List<Recomendacion>> misRecomendaciones() async {
    final res = await _dio.get('/recomendaciones/mias');
    return (res.data as List<dynamic>).map((e) => Recomendacion.fromJson(e as Map<String, dynamic>)).toList();
  }
}

final recomendacionesRepositoryProvider = Provider<RecomendacionesRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return RecomendacionesRepository(apiClient.dio);
});

/// CU18: "Recomendado para ti" en el Home -- solo para clientes con sesion
/// iniciada (las recomendaciones son por cliente). Se cruza con el
/// catalogo publico ya cargado para tener imagen/precio listos, igual que
/// en la web.
final misRecomendacionesProvider = FutureProvider<List<Recomendacion>>((ref) {
  return ref.watch(recomendacionesRepositoryProvider).misRecomendaciones();
});

class ProductoRecomendado {
  const ProductoRecomendado({required this.producto, required this.razon});
  final ProductoPublico producto;
  final String razon;
}

final productosRecomendadosProvider = Provider<List<ProductoRecomendado>>((ref) {
  final catalogo = ref.watch(productosPublicosProvider).valueOrNull ?? [];
  final recomendaciones = ref.watch(misRecomendacionesProvider).valueOrNull ?? [];
  if (catalogo.isEmpty || recomendaciones.isEmpty) return [];

  final porId = {for (final p in catalogo) p.id: p};
  return [
    for (final r in recomendaciones)
      if (porId[r.productoId] != null) ProductoRecomendado(producto: porId[r.productoId]!, razon: r.razon),
  ];
});
