import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme.dart';
import '../../../models/recomendacion_admin.dart';
import '../admin_provider.dart';
import '../widgets/admin_widgets.dart';

const _origenLabel = {
  'compra_conjunta': 'Comprado junto a...',
  'similar_categoria': 'Similar a tus compras',
  'mas_vendido': 'Mas vendido',
};

/// CU18 "Recomendar Prendas por IA" -- panel de solo lectura: el ranking
/// lo calcula un motor de reglas en SQL y Gemini redacta la razon de cada
/// una; aca se audita que se recomendo y si termino en una compra real.
class RecomendacionesAdminScreen extends ConsumerStatefulWidget {
  const RecomendacionesAdminScreen({super.key});

  @override
  ConsumerState<RecomendacionesAdminScreen> createState() => _RecomendacionesAdminScreenState();
}

class _RecomendacionesAdminScreenState extends ConsumerState<RecomendacionesAdminScreen> {
  late Future<RecomendacionPage> _future;
  int _page = 1;
  String? _error;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<RecomendacionPage> _load() {
    final repo = ref.read(adminRepositoryProvider);
    return repo.getRecomendaciones(page: _page).catchError((Object e) {
      setState(() => _error = 'No pudimos cargar las recomendaciones.');
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
      title: 'RECOMENDACIONES',
      body: Column(
        children: [
          if (_error != null) AdminErrorBanner(message: _error!),
          Expanded(
            child: FutureBuilder<RecomendacionPage>(
              future: _future,
              builder: (context, snapshot) {
                if (snapshot.connectionState != ConnectionState.done) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (!snapshot.hasData) {
                  return const Center(child: Text('No pudimos cargar las recomendaciones.'));
                }
                final pagina = snapshot.data!;
                return ListView(
                  padding: const EdgeInsets.only(top: 8, bottom: 8),
                  children: [
                    _ResumenRow(resumen: pagina.resumen),
                    if (pagina.items.isEmpty)
                      const Padding(
                        padding: EdgeInsets.all(24),
                        child: Center(child: Text('No hay recomendaciones todavia.')),
                      )
                    else ...[
                      for (final r in pagina.items) _RecomendacionCard(recomendacion: r),
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

class _ResumenRow extends StatelessWidget {
  const _ResumenRow({required this.resumen});
  final RecomendacionResumen resumen;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
      child: Row(
        children: [
          Expanded(child: _StatBox(valor: '${resumen.totalActivas}', etiqueta: 'ACTIVAS')),
          const SizedBox(width: 10),
          Expanded(child: _StatBox(valor: '${resumen.convertidas}', etiqueta: 'CONVERTIDAS')),
          const SizedBox(width: 10),
          Expanded(child: _StatBox(valor: '${resumen.tasaConversion.toStringAsFixed(1)}%', etiqueta: 'TASA')),
        ],
      ),
    );
  }
}

class _StatBox extends StatelessWidget {
  const _StatBox({required this.valor, required this.etiqueta});
  final String valor;
  final String etiqueta;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12),
      decoration: BoxDecoration(border: Border.all(color: AppColors.grayBorderLight)),
      child: Column(
        children: [
          Text(valor, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18, color: AppColors.brandDark)),
          Text(etiqueta, style: const TextStyle(fontSize: 9, color: AppColors.grayText, fontWeight: FontWeight.w700)),
        ],
      ),
    );
  }
}

class _RecomendacionCard extends StatelessWidget {
  const _RecomendacionCard({required this.recomendacion});
  final RecomendacionAdmin recomendacion;

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
                    Text(recomendacion.clienteNombre, style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.brandDark)),
                    Text(recomendacion.clienteEmail, style: const TextStyle(fontSize: 11, color: AppColors.grayTextDark)),
                  ],
                ),
              ),
              if (recomendacion.convertido) const EstadoBadge(estado: 'Convertida', activo: true),
            ],
          ),
          const SizedBox(height: 8),
          AdminInfoRow('Producto', recomendacion.productoNombre),
          AdminInfoRow('Origen', _origenLabel[recomendacion.origen] ?? recomendacion.origen),
          if (recomendacion.razon != null) AdminInfoRow('Razon (IA)', recomendacion.razon!),
        ],
      ),
    );
  }
}
