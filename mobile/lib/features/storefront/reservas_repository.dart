import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/carrito.dart';
import '../../models/reserva.dart';
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

/// Convierte el horario elegido en el date/time picker (los numeros que el
/// usuario ve y tipeo, sin ninguna nocion de zona horaria) a UTC asumiendo
/// que esos numeros son hora de Bolivia (UTC-4 fijo, sin horario de verano)
/// -- NO se usa `DateTime.toUtc()` porque eso depende de la zona horaria del
/// dispositivo, y un celular/emulador configurado en otra zona (ej. UTC)
/// mandaria un horario corrido (bug real detectado: 4:00 pm elegido en el
/// picker llegaba al backend como 4:00 pm UTC en vez de 8:00 pm UTC, y la
/// web -que sí asume Bolivia fija al mostrar- lo mostraba como 12:00 pm).
String _horarioBoliviaAUtcIso(DateTime horario) {
  return DateTime.utc(horario.year, horario.month, horario.day, horario.hour + 4, horario.minute).toIso8601String();
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
      'horario_atencion': _horarioBoliviaAUtcIso(horario),
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

  /// Reserva TODO el carrito de una sola vez -- una unica reserva con un
  /// detalle por cada item, reusando la talla/color/cantidad que el cliente
  /// ya eligio al agregarlos al carrito (solo se pide sucursal y horario).
  /// Mismo endpoint y mismo payload que usa la web en `carrito.ts`
  /// (`confirmarReserva`), asi que el backend ya lo soporta sin cambios.
  Future<void> crearDesdeCarrito({
    required int sucursalId,
    required DateTime horario,
    required List<DetalleCarrito> items,
  }) {
    return _dio.post('/reservas', data: {
      'sucursal_id': sucursalId,
      'horario_atencion': _horarioBoliviaAUtcIso(horario),
      'items': items
          .map((i) => {
                'producto_id': i.productoId,
                'talla_id': i.tallaId,
                'color_id': i.colorId,
                'cantidad': i.cantidad,
              })
          .toList(),
    });
  }

  // ---------- Mi cuenta (dashboard del cliente) ----------
  Future<List<Reserva>> misReservas() async {
    final res = await _dio.get('/reservas/mias');
    return (res.data as List<dynamic>).map((e) => Reserva.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<void> cancelar(int reservaId) => _dio.post('/reservas/$reservaId/cancelar');
}

final reservasRepositoryProvider = Provider<ReservasRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return ReservasRepository(apiClient.dio);
});
