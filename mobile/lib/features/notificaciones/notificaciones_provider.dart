import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/notificacion.dart';
import '../auth/auth_provider.dart';

class NotificacionesRepository {
  NotificacionesRepository(this._dio);

  final Dio _dio;

  Future<List<Notificacion>> misNotificaciones() async {
    final res = await _dio.get('/notificaciones/mias');
    return (res.data as List<dynamic>).map((e) => Notificacion.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<void> marcarLeida(int id) => _dio.put('/notificaciones/mias/$id/leida');

  Future<void> marcarTodasLeidas() => _dio.post('/notificaciones/mias/marcar-todas-leidas');
}

final notificacionesRepositoryProvider = Provider<NotificacionesRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return NotificacionesRepository(apiClient.dio);
});

/// CU14: historial de notificaciones del cliente -- misma logica que
/// `services/notificaciones.ts` en la web (se recarga al cambiar la
/// sesion, ver el listener en `main.dart`).
class NotificacionesNotifier extends StateNotifier<List<Notificacion>> {
  NotificacionesNotifier(this._repo) : super(const []);

  final NotificacionesRepository _repo;

  Future<void> cargar() async {
    try {
      state = await _repo.misNotificaciones();
    } catch (_) {
      state = const [];
    }
  }

  void limpiarLocal() {
    state = const [];
  }

  Future<void> marcarLeida(int id) async {
    final coincidencias = state.where((n) => n.id == id);
    if (coincidencias.isEmpty || coincidencias.first.leida) return;
    state = [for (final n in state) if (n.id == id) n.copyWith(leida: true) else n];
    try {
      await _repo.marcarLeida(id);
    } catch (_) {
      await cargar();
    }
  }

  Future<void> marcarTodasLeidas() async {
    if (state.every((n) => n.leida)) return;
    state = [for (final n in state) n.copyWith(leida: true)];
    try {
      await _repo.marcarTodasLeidas();
    } catch (_) {
      await cargar();
    }
  }
}

final notificacionesProvider = StateNotifierProvider<NotificacionesNotifier, List<Notificacion>>((ref) {
  final repo = ref.watch(notificacionesRepositoryProvider);
  return NotificacionesNotifier(repo);
});

final notificacionesNoLeidasProvider = Provider<int>((ref) {
  return ref.watch(notificacionesProvider).where((n) => !n.leida).length;
});
