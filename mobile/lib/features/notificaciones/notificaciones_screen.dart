import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme.dart';
import '../../models/notificacion.dart';
import 'notificaciones_provider.dart';

/// CU14, lado cliente: historial de notificaciones -- mismo criterio que
/// la tab "Notificaciones" del perfil en la web (aca no hay un header
/// persistente para poner una campana con dropdown, asi que se accede
/// desde Mi Perfil como una pantalla propia).
class NotificacionesScreen extends ConsumerStatefulWidget {
  const NotificacionesScreen({super.key});

  @override
  ConsumerState<NotificacionesScreen> createState() => _NotificacionesScreenState();
}

class _NotificacionesScreenState extends ConsumerState<NotificacionesScreen> {
  bool _cargando = true;

  @override
  void initState() {
    super.initState();
    ref.read(notificacionesProvider.notifier).cargar().whenComplete(() {
      if (mounted) setState(() => _cargando = false);
    });
  }

  @override
  Widget build(BuildContext context) {
    final notificaciones = ref.watch(notificacionesProvider);
    final noLeidas = ref.watch(notificacionesNoLeidasProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('NOTIFICACIONES'),
        actions: [
          if (noLeidas > 0)
            TextButton(
              onPressed: () => ref.read(notificacionesProvider.notifier).marcarTodasLeidas(),
              child: const Text('MARCAR TODAS', style: TextStyle(color: AppColors.brandDark, fontSize: 11)),
            ),
        ],
      ),
      body: SafeArea(
        child: _cargando
            ? const Center(child: CircularProgressIndicator())
            : notificaciones.isEmpty
                ? const Center(child: Text('Todavia no tienes notificaciones.'))
                : RefreshIndicator(
                    onRefresh: () => ref.read(notificacionesProvider.notifier).cargar(),
                    child: ListView.separated(
                      itemCount: notificaciones.length,
                      separatorBuilder: (_, _) => const Divider(height: 1),
                      itemBuilder: (context, i) => _NotifTile(notificacion: notificaciones[i]),
                    ),
                  ),
      ),
    );
  }
}

class _NotifTile extends ConsumerWidget {
  const _NotifTile({required this.notificacion});

  final Notificacion notificacion;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Container(
      color: notificacion.leida ? null : const Color(0xFFF5F8F7),
      child: ListTile(
        onTap: () => ref.read(notificacionesProvider.notifier).marcarLeida(notificacion.id),
        leading: Icon(
          notificacion.leida ? Icons.notifications_none : Icons.notifications,
          color: notificacion.leida ? AppColors.grayText : AppColors.brandDark,
        ),
        title: Text(notificacion.mensaje, style: const TextStyle(fontSize: 13, color: AppColors.brandDark)),
        subtitle: Text(
          '${notificacion.fechaEnvio.day}/${notificacion.fechaEnvio.month} · ${notificacion.fechaEnvio.hour.toString().padLeft(2, '0')}:${notificacion.fechaEnvio.minute.toString().padLeft(2, '0')}',
          style: const TextStyle(fontSize: 11, color: AppColors.grayText),
        ),
      ),
    );
  }
}
