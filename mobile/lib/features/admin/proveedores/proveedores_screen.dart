import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme.dart';
import '../../../models/proveedor.dart';
import '../admin_provider.dart';
import '../widgets/admin_widgets.dart';

/// CU06 — Administrar Proveedores.
class ProveedoresScreen extends ConsumerStatefulWidget {
  const ProveedoresScreen({super.key});

  @override
  ConsumerState<ProveedoresScreen> createState() => _ProveedoresScreenState();
}

class _ProveedoresScreenState extends ConsumerState<ProveedoresScreen> {
  late Future<List<Proveedor>> _future;
  String? _buscar;
  String? _error;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<List<Proveedor>> _load() => ref.read(adminRepositoryProvider).getProveedores(buscar: _buscar);

  void _reload({String? buscar}) {
    setState(() {
      if (buscar != null) _buscar = buscar.isEmpty ? null : buscar;
      _error = null;
      _future = _load();
    });
  }

  Future<void> _crear() async {
    final nombreCtrl = TextEditingController();
    final emailCtrl = TextEditingController();
    final nitCtrl = TextEditingController();
    final contactoCtrl = TextEditingController();
    final telefonoCtrl = TextEditingController();
    final direccionCtrl = TextEditingController();
    final formKey = GlobalKey<FormState>();

    await showAdminFormSheet(
      context,
      title: 'NUEVO PROVEEDOR',
      builder: (context) => _ProveedorForm(
        formKey: formKey,
        nombreCtrl: nombreCtrl,
        emailCtrl: emailCtrl,
        nitCtrl: nitCtrl,
        contactoCtrl: contactoCtrl,
        telefonoCtrl: telefonoCtrl,
        direccionCtrl: direccionCtrl,
        isEdit: false,
        onSubmit: () async {
          if (!formKey.currentState!.validate()) return;
          try {
            await ref.read(adminRepositoryProvider).createProveedor(
                  nombre: nombreCtrl.text.trim(),
                  email: emailCtrl.text.trim(),
                  nit: nitCtrl.text.trim(),
                  contactoNombre: contactoCtrl.text.trim().isEmpty ? null : contactoCtrl.text.trim(),
                  telefono: telefonoCtrl.text.trim().isEmpty ? null : telefonoCtrl.text.trim(),
                  direccion: direccionCtrl.text.trim().isEmpty ? null : direccionCtrl.text.trim(),
                );
            if (context.mounted) Navigator.pop(context);
            _reload();
          } catch (e) {
            if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_extractProveedorError(e))));
          }
        },
      ),
    );
  }

  Future<void> _editar(Proveedor proveedor) async {
    final nombreCtrl = TextEditingController(text: proveedor.nombre);
    final nitCtrl = TextEditingController(text: proveedor.nit);
    final contactoCtrl = TextEditingController(text: proveedor.contactoNombre ?? '');
    final telefonoCtrl = TextEditingController(text: proveedor.telefono ?? '');
    final direccionCtrl = TextEditingController(text: proveedor.direccion ?? '');
    var estado = proveedor.estado;
    final formKey = GlobalKey<FormState>();

    await showAdminFormSheet(
      context,
      title: 'EDITAR PROVEEDOR',
      builder: (context) => StatefulBuilder(
        builder: (context, setSheetState) => _ProveedorForm(
          formKey: formKey,
          nombreCtrl: nombreCtrl,
          emailCtrl: null,
          nitCtrl: nitCtrl,
          contactoCtrl: contactoCtrl,
          telefonoCtrl: telefonoCtrl,
          direccionCtrl: direccionCtrl,
          isEdit: true,
          estado: estado,
          onEstadoChanged: (v) => setSheetState(() => estado = v!),
          onSubmit: () async {
            if (!formKey.currentState!.validate()) return;
            try {
              await ref.read(adminRepositoryProvider).updateProveedor(
                    id: proveedor.id,
                    nombre: nombreCtrl.text.trim(),
                    nit: nitCtrl.text.trim(),
                    contactoNombre: contactoCtrl.text.trim().isEmpty ? null : contactoCtrl.text.trim(),
                    telefono: telefonoCtrl.text.trim().isEmpty ? null : telefonoCtrl.text.trim(),
                    direccion: direccionCtrl.text.trim().isEmpty ? null : direccionCtrl.text.trim(),
                    estado: estado,
                  );
              if (context.mounted) Navigator.pop(context);
              _reload();
            } catch (e) {
              if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_extractProveedorError(e))));
            }
          },
        ),
      ),
    );
  }

  Future<void> _toggleEstado(Proveedor proveedor) async {
    final activar = proveedor.estado == 'inactivo';
    final ok = await confirmAdminAction(
      context,
      title: activar ? 'Activar proveedor' : 'Desactivar proveedor',
      message: 'Seguro que queres ${activar ? 'activar' : 'desactivar'} a ${proveedor.nombre}?',
    );
    if (!ok) return;
    try {
      await ref.read(adminRepositoryProvider).updateProveedor(
            id: proveedor.id,
            nombre: proveedor.nombre,
            nit: proveedor.nit,
            contactoNombre: proveedor.contactoNombre,
            telefono: proveedor.telefono,
            direccion: proveedor.direccion,
            estado: activar ? 'activo' : 'inactivo',
          );
      _reload();
    } catch (e) {
      setState(() => _error = _extractProveedorError(e));
    }
  }

  @override
  Widget build(BuildContext context) {
    return AdminScaffold(
      title: 'PROVEEDORES',
      floatingActionButton: FloatingActionButton.extended(onPressed: _crear, icon: const Icon(Icons.add), label: const Text('NUEVO')),
      body: Column(
        children: [
          AdminSearchField(hintText: 'Buscar por nombre, correo o NIT...', onChanged: (v) => _reload(buscar: v)),
          if (_error != null) AdminErrorBanner(message: _error!),
          Expanded(
            child: FutureBuilder<List<Proveedor>>(
              future: _future,
              builder: (context, snapshot) {
                if (snapshot.connectionState != ConnectionState.done) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (snapshot.hasError) return const Center(child: Text('No pudimos cargar los proveedores.'));
                final proveedores = snapshot.data ?? [];
                if (proveedores.isEmpty) return const Center(child: Text('No hay proveedores registrados.'));
                return ListView(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  children: [
                    for (final p in proveedores) _ProveedorCard(proveedor: p, onEditar: () => _editar(p), onToggle: () => _toggleEstado(p)),
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

String _extractProveedorError(Object e) {
  final s = e.toString();
  return s.contains('No pudimos conectar') ? s : 'No pudimos completar la accion.';
}

class _ProveedorCard extends StatelessWidget {
  const _ProveedorCard({required this.proveedor, required this.onEditar, required this.onToggle});

  final Proveedor proveedor;
  final VoidCallback onEditar;
  final VoidCallback onToggle;

  @override
  Widget build(BuildContext context) {
    final activo = proveedor.estado == 'activo';
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
                    Text(proveedor.nombre, style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.brandDark)),
                    Text(proveedor.email, style: const TextStyle(fontSize: 12, color: AppColors.grayTextDark)),
                  ],
                ),
              ),
              EstadoBadge(estado: proveedor.estado, activo: activo),
            ],
          ),
          const SizedBox(height: 8),
          AdminInfoRow('NIT', proveedor.nit),
          AdminInfoRow('Contacto', proveedor.contactoNombre ?? '-'),
          AdminInfoRow('Telefono', proveedor.telefono ?? '-'),
          const SizedBox(height: 10),
          Row(
            children: [
              TextButton.icon(onPressed: onEditar, icon: const Icon(Icons.edit_outlined, size: 16), label: const Text('Editar')),
              TextButton.icon(
                onPressed: onToggle,
                icon: Icon(activo ? Icons.block : Icons.check_circle_outline, size: 16),
                label: Text(activo ? 'Desactivar' : 'Activar'),
                style: TextButton.styleFrom(foregroundColor: activo ? AppColors.danger : AppColors.success),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _ProveedorForm extends StatelessWidget {
  const _ProveedorForm({
    required this.formKey,
    required this.nombreCtrl,
    required this.emailCtrl,
    required this.nitCtrl,
    required this.contactoCtrl,
    required this.telefonoCtrl,
    required this.direccionCtrl,
    required this.isEdit,
    required this.onSubmit,
    this.estado,
    this.onEstadoChanged,
  });

  final GlobalKey<FormState> formKey;
  final TextEditingController nombreCtrl;
  final TextEditingController? emailCtrl;
  final TextEditingController nitCtrl;
  final TextEditingController contactoCtrl;
  final TextEditingController telefonoCtrl;
  final TextEditingController direccionCtrl;
  final bool isEdit;
  final VoidCallback onSubmit;
  final String? estado;
  final ValueChanged<String?>? onEstadoChanged;

  @override
  Widget build(BuildContext context) {
    return Form(
      key: formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!isEdit) const AdminHintText('Se genera una contrasena temporal y se le envia por correo.'),
          TextFormField(
            controller: nombreCtrl,
            decoration: const InputDecoration(labelText: 'Razon social / Nombre'),
            validator: (v) => (v == null || v.trim().length < 2) ? 'Requerido (min. 2 caracteres)' : null,
          ),
          const SizedBox(height: 16),
          if (emailCtrl != null) ...[
            TextFormField(
              controller: emailCtrl,
              decoration: const InputDecoration(labelText: 'Correo electronico'),
              keyboardType: TextInputType.emailAddress,
              validator: (v) => (v == null || !v.contains('@')) ? 'Correo invalido' : null,
            ),
            const SizedBox(height: 16),
          ],
          TextFormField(
            controller: nitCtrl,
            decoration: const InputDecoration(labelText: 'NIT'),
            validator: (v) => (v == null || v.trim().isEmpty) ? 'Requerido' : null,
          ),
          const SizedBox(height: 16),
          TextFormField(controller: contactoCtrl, decoration: const InputDecoration(labelText: 'Nombre de contacto (opcional)')),
          const SizedBox(height: 16),
          TextFormField(controller: telefonoCtrl, decoration: const InputDecoration(labelText: 'Telefono (opcional)'), keyboardType: TextInputType.phone),
          const SizedBox(height: 16),
          TextFormField(controller: direccionCtrl, decoration: const InputDecoration(labelText: 'Direccion (opcional)')),
          if (isEdit) ...[
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              initialValue: estado,
              decoration: const InputDecoration(labelText: 'Estado'),
              items: const [
                DropdownMenuItem(value: 'activo', child: Text('Activo')),
                DropdownMenuItem(value: 'inactivo', child: Text('Inactivo')),
              ],
              onChanged: onEstadoChanged,
            ),
          ],
          const SizedBox(height: 24),
          ElevatedButton(onPressed: onSubmit, child: Text(isEdit ? 'GUARDAR CAMBIOS' : 'CREAR PROVEEDOR')),
        ],
      ),
    );
  }
}
