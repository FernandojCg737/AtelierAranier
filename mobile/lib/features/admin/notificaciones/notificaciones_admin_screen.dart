import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme.dart';
import '../../../models/notificacion_admin.dart';
import '../admin_provider.dart';
import '../widgets/admin_widgets.dart';

const _tipoLabel = {
  'reserva_creada': 'Reserva creada',
  'reserva_cancelada': 'Reserva cancelada',
  'reserva_vencida': 'Reserva vencida',
  'reserva_por_vencer': 'Reserva por vencer',
  'compra_confirmada': 'Compra confirmada',
  'pago_rechazado': 'Pago rechazado',
};

/// CU14 "Enviar Notificaciones" -- panel de solo lectura: a quien se le
/// mando cada notificacion (generada sola por triggers en el backend), de
/// que tipo, cuando y con que mensaje.
class NotificacionesAdminScreen extends ConsumerStatefulWidget {
  const NotificacionesAdminScreen({super.key});

  @override
  ConsumerState<NotificacionesAdminScreen> createState() => _NotificacionesAdminScreenState();
}

class _NotificacionesAdminScreenState extends ConsumerState<NotificacionesAdminScreen> {
  late Future<NotificacionAdminPage> _future;
  int _page = 1;
  String? _error;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<NotificacionAdminPage> _load() {
    final repo = ref.read(adminRepositoryProvider);
    return repo.getNotificaciones(page: _page).catchError((Object e) {
      setState(() => _error = 'No pudimos cargar las notificaciones.');
      throw e;
    });
  }

  void _reload(int page) {
    setState(() {
      _error = null;
      _page = page;
      _future = _load();
    });
  }

  @override
  Widget build(BuildContext context) {
    return AdminScaffold(
      title: 'NOTIFICACIONES',
      body: Column(
        children: [
          if (_error != null) AdminErrorBanner(message: _error!),
          Expanded(
            child: FutureBuilder<NotificacionAdminPage>(
              future: _future,
              builder: (context, snapshot) {
                if (snapshot.connectionState != ConnectionState.done) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (!snapshot.hasData) {
                  return const Center(child: Text('No pudimos cargar las notificaciones.'));
                }
                final pagina = snapshot.data!;
                if (pagina.items.isEmpty) {
                  return const Center(child: Text('No hay notificaciones todavia.'));
                }
                return ListView(
                  padding: const EdgeInsets.only(top: 8, bottom: 8),
                  children: [
                    for (final n in pagina.items) _NotifCard(notificacion: n),
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          TextButton(onPressed: pagina.page > 1 ? () => _reload(pagina.page - 1) : null, child: const Text('Anterior')),
                          Text('Pagina ${pagina.page} de ${pagina.totalPages}', style: const TextStyle(fontSize: 12, color: AppColors.grayTextDark)),
                          TextButton(onPressed: pagina.page < pagina.totalPages ? () => _reload(pagina.page + 1) : null, child: const Text('Siguiente')),
                        ],
                      ),
                    ),
                  ],
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _NotifCard extends StatelessWidget {
  const _NotifCard({required this.notificacion});
  final NotificacionAdmin notificacion;

  @override
  Widget build(BuildContext context) {
    return AdminCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(notificacion.clienteNombre, style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.brandDark)),
                    Text(notificacion.clienteEmail, style: const TextStyle(fontSize: 11, color: AppColors.grayTextDark)),
                  ],
                ),
              ),
              NeutralBadge(_tipoLabel[notificacion.tipoEvento] ?? notificacion.tipoEvento),
            ],
          ),
          const SizedBox(height: 8),
          Text(notificacion.mensaje, style: const TextStyle(fontSize: 13, color: AppColors.brandDark)),
          const SizedBox(height: 6),
          AdminInfoRow(
            'Fecha',
            '${notificacion.fecha.day}/${notificacion.fecha.month}/${notificacion.fecha.year} ${notificacion.fecha.hour.toString().padLeft(2, '0')}:${notificacion.fecha.minute.toString().padLeft(2, '0')}',
          ),
          AdminInfoRow('Leida', notificacion.leida ? 'Si' : 'No'),
        ],
      ),
    );
  }
}
