import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme.dart';
import '../../../models/usuario.dart';
import '../admin_provider.dart';
import '../widgets/admin_widgets.dart';

/// CU01 — Gestionar Inicio y Cierre de Sesion. Puramente de lectura: el
/// backend no expone ningun endpoint para revocar una sesion (confirmado
/// contra `sesiones.py`/`auth.py`), asi que esta pantalla solo lista quien
/// esta actualmente logueado (`session_id IS NOT NULL`).
class SesionesScreen extends ConsumerWidget {
  const SesionesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final sesionesAsync = ref.watch(sesionesActivasProvider);

    return AdminScaffold(
      title: 'SESIONES ACTIVAS',
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(sesionesActivasProvider),
        child: sesionesAsync.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (err, _) => ListView(
            children: [AdminErrorBanner(message: 'No pudimos cargar las sesiones activas.')],
          ),
          data: (sesiones) {
            return ListView(
              padding: const EdgeInsets.fromLTRB(0, 16, 0, 32),
              children: [
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 16),
                  child: Text(
                    'Cada login reemplaza la sesion anterior (una sola sesion por cuenta) y expira sola a los 60 minutos.',
                    style: TextStyle(fontSize: 12, color: AppColors.grayTextDark, fontStyle: FontStyle.italic),
                  ),
                ),
                const SizedBox(height: 16),
                if (sesiones.isEmpty)
                  const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 16),
                    child: Text('No hay sesiones activas.'),
                  )
                else
                  for (final u in sesiones) _SesionCard(usuario: u),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _SesionCard extends StatelessWidget {
  const _SesionCard({required this.usuario});

  final Usuario usuario;

  @override
  Widget build(BuildContext context) {
    return AdminCard(
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(usuario.nombre, style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.brandDark)),
                Text(usuario.email, style: const TextStyle(fontSize: 12, color: AppColors.grayTextDark)),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              NeutralBadge(usuario.tipo.replaceAll('_', ' ')),
              if (usuario.rol != null) ...[
                const SizedBox(height: 4),
                Text(usuario.rol!, style: const TextStyle(fontSize: 11, color: AppColors.grayText)),
              ],
            ],
          ),
        ],
      ),
    );
  }
}
