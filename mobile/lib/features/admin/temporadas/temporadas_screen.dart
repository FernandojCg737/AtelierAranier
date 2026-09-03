import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme.dart';
import '../../../models/coleccion.dart';
import '../../../models/temporada.dart';
import '../admin_provider.dart';
import '../widgets/admin_widgets.dart';

/// CU07 — Configurar Temporadas y Colecciones. Dos pestanas, ambas con
/// CRUD + DELETE real (protegido por FK en el backend: 409 si hay
/// colecciones/productos asociados).
class TemporadasScreen extends ConsumerStatefulWidget {
  const TemporadasScreen({super.key});

  @override
  ConsumerState<TemporadasScreen> createState() => _TemporadasScreenState();
}

class _TemporadasScreenState extends ConsumerState<TemporadasScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  late Future<List<Temporada>> _temporadasFuture;
  late Future<List<Coleccion>> _coleccionesFuture;
  String? _error;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _temporadasFuture = ref.read(adminRepositoryProvider).getTemporadas();
    _coleccionesFuture = ref.read(adminRepositoryProvider).getColecciones();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  void _reloadTemporadas() => setState(() {
        _error = null;
        _temporadasFuture = ref.read(adminRepositoryProvider).getTemporadas();
      });

  void _reloadColecciones() => setState(() {
        _error = null;
        _coleccionesFuture = ref.read(adminRepositoryProvider).getColecciones();
      });

  Future<void> _formularioTemporada({Temporada? temporada}) async {
    final nombreCtrl = TextEditingController(text: temporada?.nombre ?? '');
    final inicioCtrl = TextEditingController(text: temporada != null ? _isoDate(temporada.fechaInicio) : '');
    final finCtrl = TextEditingController(text: temporada != null ? _isoDate(temporada.fechaFin) : '');
    final formKey = GlobalKey<FormState>();

    await showAdminFormSheet(
      context,
      title: temporada == null ? 'NUEVA TEMPORADA' : 'EDITAR TEMPORADA',
      builder: (context) => Form(
        key: formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            TextFormField(
              controller: nombreCtrl,
              decoration: const InputDecoration(labelText: 'Nombre'),
              validator: (v) => (v == null || v.trim().length < 2) ? 'Requerido' : null,
            ),
            const SizedBox(height: 16),
            _DateField(controller: inicioCtrl, label: 'Fecha de inicio'),
            const SizedBox(height: 16),
            _DateField(controller: finCtrl, label: 'Fecha de fin'),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: () async {
                if (!formKey.currentState!.validate()) return;
                if (inicioCtrl.text.isEmpty || finCtrl.text.isEmpty) {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Elegi ambas fechas.')));
                  return;
                }
                final repo = ref.read(adminRepositoryProvider);
                try {
                  if (temporada == null) {
                    await repo.createTemporada(nombre: nombreCtrl.text.trim(), fechaInicio: inicioCtrl.text, fechaFin: finCtrl.text);
                  } else {
                    await repo.updateTemporada(id: temporada.id, nombre: nombreCtrl.text.trim(), fechaInicio: inicioCtrl.text, fechaFin: finCtrl.text);
                  }
                  if (context.mounted) Navigator.pop(context);
                  _reloadTemporadas();
                } catch (e) {
                  if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_extractTemporadaError(e))));
                }
              },
              child: Text(temporada == null ? 'CREAR TEMPORADA' : 'GUARDAR CAMBIOS'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _eliminarTemporada(Temporada temporada) async {
    final ok = await confirmAdminAction(context, title: 'Eliminar temporada', message: 'Seguro que queres eliminar ${temporada.nombre}?');
    if (!ok) return;
    try {
      await ref.read(adminRepositoryProvider).deleteTemporada(temporada.id);
      _reloadTemporadas();
    } catch (e) {
      setState(() => _error = _extractTemporadaError(e));
    }
  }

  Future<void> _formularioColeccion(List<Temporada> temporadas, {Coleccion? coleccion}) async {
    final nombreCtrl = TextEditingController(text: coleccion?.nombre ?? '');
    final descripcionCtrl = TextEditingController(text: coleccion?.descripcion ?? '');
    var temporadaId = coleccion?.temporadaId ?? (temporadas.isNotEmpty ? temporadas.first.id : null);
    final formKey = GlobalKey<FormState>();

    await showAdminFormSheet(
      context,
      title: coleccion == null ? 'NUEVA COLECCION' : 'EDITAR COLECCION',
      builder: (context) => StatefulBuilder(
        builder: (context, setSheetState) => Form(
          key: formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              DropdownButtonFormField<int>(
                initialValue: temporadaId,
                decoration: const InputDecoration(labelText: 'Temporada'),
                items: [for (final t in temporadas) DropdownMenuItem(value: t.id, child: Text(t.nombre))],
                onChanged: (v) => setSheetState(() => temporadaId = v),
                validator: (v) => v == null ? 'Elegi una temporada' : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: nombreCtrl,
                decoration: const InputDecoration(labelText: 'Nombre'),
                validator: (v) => (v == null || v.trim().length < 2) ? 'Requerido' : null,
              ),
              const SizedBox(height: 16),
              TextFormField(controller: descripcionCtrl, decoration: const InputDecoration(labelText: 'Descripcion (opcional)'), maxLines: 3),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: () async {
                  if (!formKey.currentState!.validate()) return;
                  final repo = ref.read(adminRepositoryProvider);
                  try {
                    if (coleccion == null) {
                      await repo.createColeccion(
                        temporadaId: temporadaId!,
                        nombre: nombreCtrl.text.trim(),
                        descripcion: descripcionCtrl.text.trim().isEmpty ? null : descripcionCtrl.text.trim(),
                      );
                    } else {
                      await repo.updateColeccion(
                        id: coleccion.id,
                        temporadaId: temporadaId!,
                        nombre: nombreCtrl.text.trim(),
                        descripcion: descripcionCtrl.text.trim().isEmpty ? null : descripcionCtrl.text.trim(),
                      );
                    }
                    if (context.mounted) Navigator.pop(context);
                    _reloadColecciones();
                  } catch (e) {
                    if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_extractTemporadaError(e))));
                  }
                },
                child: Text(coleccion == null ? 'CREAR COLECCION' : 'GUARDAR CAMBIOS'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _eliminarColeccion(Coleccion coleccion) async {
    final ok = await confirmAdminAction(context, title: 'Eliminar coleccion', message: 'Seguro que queres eliminar ${coleccion.nombre}?');
    if (!ok) return;
    try {
      await ref.read(adminRepositoryProvider).deleteColeccion(coleccion.id);
      _reloadColecciones();
    } catch (e) {
      setState(() => _error = _extractTemporadaError(e));
    }
  }

  @override
  Widget build(BuildContext context) {
    return AdminScaffold(
      title: 'TEMPORADAS Y COLECCIONES',
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          if (_tabController.index == 0) {
            await _formularioTemporada();
          } else {
            final temporadas = await _temporadasFuture;
            if (context.mounted) await _formularioColeccion(temporadas);
          }
        },
        icon: const Icon(Icons.add),
        label: const Text('NUEVO'),
      ),
      body: Column(
        children: [
          TabBar(
            controller: _tabController,
            labelColor: AppColors.brandDark,
            unselectedLabelColor: AppColors.grayText,
            indicatorColor: AppColors.brandDark,
            tabs: const [Tab(text: 'TEMPORADAS'), Tab(text: 'COLECCIONES')],
          ),
          if (_error != null) AdminErrorBanner(message: _error!),
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                FutureBuilder<List<Temporada>>(
                  future: _temporadasFuture,
                  builder: (context, snapshot) {
                    if (snapshot.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator());
                    if (snapshot.hasError) return const Center(child: Text('No pudimos cargar las temporadas.'));
                    final temporadas = snapshot.data ?? [];
                    if (temporadas.isEmpty) return const Center(child: Text('No hay temporadas registradas.'));
                    return ListView(
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      children: [
                        for (final t in temporadas)
                          AdminCard(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(t.nombre, style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.brandDark)),
                                AdminInfoRow('Inicio', _isoDate(t.fechaInicio)),
                                AdminInfoRow('Fin', _isoDate(t.fechaFin)),
                                const SizedBox(height: 10),
                                Row(
                                  children: [
                                    TextButton.icon(
                                      onPressed: () => _formularioTemporada(temporada: t),
                                      icon: const Icon(Icons.edit_outlined, size: 16),
                                      label: const Text('Editar'),
                                    ),
                                    TextButton.icon(
                                      onPressed: () => _eliminarTemporada(t),
                                      icon: const Icon(Icons.delete_outline, size: 16),
                                      label: const Text('Eliminar'),
                                      style: TextButton.styleFrom(foregroundColor: AppColors.danger),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                      ],
                    );
                  },
                ),
                FutureBuilder<List<Coleccion>>(
                  future: _coleccionesFuture,
                  builder: (context, snapshot) {
                    if (snapshot.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator());
                    if (snapshot.hasError) return const Center(child: Text('No pudimos cargar las colecciones.'));
                    final colecciones = snapshot.data ?? [];
                    if (colecciones.isEmpty) return const Center(child: Text('No hay colecciones registradas.'));
                    return FutureBuilder<List<Temporada>>(
                      future: _temporadasFuture,
                      builder: (context, tempSnap) {
                        final temporadas = tempSnap.data ?? [];
                        return ListView(
                          padding: const EdgeInsets.symmetric(vertical: 8),
                          children: [
                            for (final c in colecciones)
                              AdminCard(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(c.nombre, style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.brandDark)),
                                    AdminInfoRow('Temporada', c.temporadaNombre),
                                    AdminInfoRow('Descripcion', c.descripcion ?? '-'),
                                    const SizedBox(height: 10),
                                    Row(
                                      children: [
                                        TextButton.icon(
                                          onPressed: () => _formularioColeccion(temporadas, coleccion: c),
                                          icon: const Icon(Icons.edit_outlined, size: 16),
                                          label: const Text('Editar'),
                                        ),
                                        TextButton.icon(
                                          onPressed: () => _eliminarColeccion(c),
                                          icon: const Icon(Icons.delete_outline, size: 16),
                                          label: const Text('Eliminar'),
                                          style: TextButton.styleFrom(foregroundColor: AppColors.danger),
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                          ],
                        );
                      },
                    );
                  },
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

String _isoDate(DateTime d) => '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

String _extractTemporadaError(Object e) {
  final s = e.toString();
  return s.contains('No pudimos conectar') ? s : 'No pudimos completar la accion.';
}

/// Campo de fecha simple: abre un `showDatePicker` y guarda el ISO string.
class _DateField extends StatelessWidget {
  const _DateField({required this.controller, required this.label});

  final TextEditingController controller;
  final String label;

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      controller: controller,
      readOnly: true,
      decoration: InputDecoration(labelText: label, suffixIcon: const Icon(Icons.calendar_today_outlined, size: 18)),
      validator: (v) => (v == null || v.isEmpty) ? 'Requerido' : null,
      onTap: () async {
        final initial = controller.text.isNotEmpty ? DateTime.tryParse(controller.text) ?? DateTime.now() : DateTime.now();
        final picked = await showDatePicker(
          context: context,
          initialDate: initial,
          firstDate: DateTime(2000),
          lastDate: DateTime(2100),
        );
        if (picked != null) controller.text = _isoDate(picked);
      },
    );
  }
}
