import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../models/asistencia.dart';
import '../../auth/auth_provider.dart';

class AsistenciaRepository {
  AsistenciaRepository(this._dio);

  final Dio _dio;

  Future<EstadoAsistencia> estado() async {
    final res = await _dio.get('/asistencia/estado');
    return EstadoAsistencia.fromJson(res.data as Map<String, dynamic>);
  }

  Future<EstadoAsistencia> configurarHora(String horaLiberacion) async {
    final res = await _dio.put('/asistencia/hora', data: {'hora_liberacion': '$horaLiberacion:00'});
    return EstadoAsistencia.fromJson(res.data as Map<String, dynamic>);
  }

  Future<EstadoAsistencia> liberarManual() async {
    final res = await _dio.post('/asistencia/liberar');
    return EstadoAsistencia.fromJson(res.data as Map<String, dynamic>);
  }

  Future<Marcado> marcar({
    required String codigo,
    required double latitud,
    required double longitud,
    required String fotoPath,
  }) async {
    final form = FormData.fromMap({
      'codigo': codigo,
      'latitud': latitud,
      'longitud': longitud,
      'foto': await MultipartFile.fromFile(fotoPath, filename: 'asistencia.jpg'),
    });
    final res = await _dio.post('/asistencia/marcar', data: form);
    return Marcado.fromJson(res.data as Map<String, dynamic>);
  }

  Future<List<Marcado>> miHistorial() async {
    final res = await _dio.get('/asistencia/mia');
    return (res.data as List<dynamic>).map((e) => Marcado.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<MarcadoHoy>> marcadosHoy() async {
    final res = await _dio.get('/asistencia/hoy');
    return (res.data as List<dynamic>).map((e) => MarcadoHoy.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<Marcado>> historial() async {
    final res = await _dio.get('/asistencia/historial');
    return (res.data as List<dynamic>).map((e) => Marcado.fromJson(e as Map<String, dynamic>)).toList();
  }
}

final asistenciaRepositoryProvider = Provider<AsistenciaRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return AsistenciaRepository(apiClient.dio);
});
