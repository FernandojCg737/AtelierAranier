import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../auth/auth_provider.dart';

class DisponibilidadItem {
  const DisponibilidadItem({
    required this.sucursalId,
    required this.sucursalNombre,
    required this.tallaId,
    required this.tallaCodigo,
    required this.colorId,
    required this.colorNombre,
    required this.cantidad,
  });

  final int sucursalId;
  final String sucursalNombre;
  final int tallaId;
  final String tallaCodigo;
  final int colorId;
  final String colorNombre;
  final int cantidad;

  /// Clave unica de esta combinacion, para usar como value de un dropdown.
  String get clave => '$sucursalId-$tallaId-$colorId';

  factory DisponibilidadItem.fromJson(Map<String, dynamic> json) {
    return DisponibilidadItem(
      sucursalId: json['sucursal_id'] as int,
      sucursalNombre: json['sucursal_nombre'] as String,
      tallaId: json['talla_id'] as int,
      tallaCodigo: json['talla_codigo'] as String,
      colorId: json['color_id'] as int,
      colorNombre: json['color_nombre'] as String,
      cantidad: json['cantidad'] as int,
    );
  }
}

/// CU10, lado cliente: reservar una prenda para probarsela/recogerla en una
/// sucursal en un horario. Misma logica que `reserva-form.ts` en la web.
class ReservasRepository {
  ReservasRepository(this._dio);

  final Dio _dio;

  Future<List<DisponibilidadItem>> disponibilidad(int productoId) async {
    final res = await _dio.get('/reservas/disponibilidad/$productoId');
    return (res.data as List<dynamic>)
        .map((e) => DisponibilidadItem.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<void> crear({
    required int productoId,
    required DisponibilidadItem opcion,
    required int cantidad,
    required DateTime horario,
  }) {
    return _dio.post('/reservas', data: {
      'sucursal_id': opcion.sucursalId,
      'horario_atencion': horario.toUtc().toIso8601String(),
      'items': [
        {
          'producto_id': productoId,
          'talla_id': opcion.tallaId,
          'color_id': opcion.colorId,
          'cantidad': cantidad,
        },
      ],
    });
  }
}

final reservasRepositoryProvider = Provider<ReservasRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return ReservasRepository(apiClient.dio);
});
