import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/usuario.dart';
import '../auth/auth_provider.dart';
import 'admin_repository.dart';

final adminRepositoryProvider = Provider<AdminRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return AdminRepository(apiClient.dio);
});

/// CU01 es puramente de lectura (sin CRUD), asi que alcanza con un
/// FutureProvider — el resto de pantallas admin manejan su propio estado
/// local (busqueda/paginacion/tabs) dado el volumen de variantes distintas.
final sesionesActivasProvider = FutureProvider.autoDispose<List<Usuario>>((ref) {
  return ref.watch(adminRepositoryProvider).getSesionesActivas();
});
