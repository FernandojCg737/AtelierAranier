import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme.dart';
import '../../../models/cliente_admin.dart';
import '../admin_provider.dart';
import '../widgets/admin_widgets.dart';

/// CU03 — Registrar y Administrar Clientes.
class ClientesScreen extends ConsumerStatefulWidget {
  const ClientesScreen({super.key});

  @override
  ConsumerState<ClientesScreen> createState() => _ClientesScreenState();
}

class _ClientesScreenState extends ConsumerState<ClientesScreen> {
  late Future<List<ClienteAdmin>> _future;
  String? _buscar;
  String? _error;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<List<ClienteAdmin>> _load() => ref.read(adminRepositoryProvider).getClientes(buscar: _buscar);

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
    final telefonoCtrl = TextEditingController();
    final direccionCtrl = TextEditingController();
    final formKey = GlobalKey<FormState>();

    await showAdminFormSheet(
      context,
      title: 'NUEVO CLIENTE',
      builder: (context) => _ClienteForm(
        formKey: formKey,
        nombreCtrl: nombreCtrl,
        emailCtrl: emailCtrl,
        telefonoCtrl: telefonoCtrl,
        direccionCtrl: direccionCtrl,
        isEdit: false,
        onSubmit: () async {
          if (!formKey.currentState!.validate()) return;
          try {
            await ref.read(adminRepositoryProvider).createCliente(
                  nombre: nombreCtrl.text.trim(),
                  email: emailCtrl.text.trim(),
                  telefono: telefonoCtrl.text.trim().isEmpty ? null : telefonoCtrl.text.trim(),
                  direccion: direccionCtrl.text.trim().isEmpty ? null : direccionCtrl.text.trim(),
                );
            if (context.mounted) Navigator.pop(context);
            _reload();
          } catch (e) {
            if (context.mounted) {
              ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_extractError(e))));
            }
          }
        },
      ),
    );
  }

  Future<void> _editar(ClienteAdmin cliente) async {
    final nombreCtrl = TextEditingController(text: cliente.nombre);
    final telefonoCtrl = TextEditingController(text: cliente.telefono ?? '');
    final direccionCtrl = TextEditingController(text: cliente.direccion ?? '');
    var estado = cliente.estado;
    final formKey = GlobalKey<FormState>();

    await showAdminFormSheet(
      context,
      title: 'EDITAR CLIENTE',
      builder: (context) => StatefulBuilder(
        builder: (context, setSheetState) => _ClienteForm(
          formKey: formKey,
          nombreCtrl: nombreCtrl,
          emailCtrl: null,
          telefonoCtrl: telefonoCtrl,
          direccionCtrl: direccionCtrl,
          isEdit: true,
          estado: estado,
          onEstadoChanged: (v) => setSheetState(() => estado = v!),
          onSubmit: () async {
            if (!formKey.currentState!.validate()) return;
            try {
              await ref.read(adminRepositoryProvider).updateCliente(
                    id: cliente.id,
                    nombre: nombreCtrl.text.trim(),
                    telefono: telefonoCtrl.text.trim().isEmpty ? null : telefonoCtrl.text.trim(),
                    direccion: direccionCtrl.text.trim().isEmpty ? null : direccionCtrl.text.trim(),
                    estado: estado,
                  );
              if (context.mounted) Navigator.pop(context);
              _reload();
            } catch (e) {
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_extractError(e))));
              }
            }
          },
        ),
      ),
    );
  }

  Future<void> _toggleEstado(ClienteAdmin cliente) async {
    final activar = cliente.estado == 'inactivo';
    final ok = await confirmAdminAction(
      context,
      title: activar ? 'Activar cliente' : 'Desactivar cliente',
      message: 'Seguro que queres ${activar ? 'activar' : 'desactivar'} a ${cliente.nombre}?',
    );
    if (!ok) return;
    try {
      await ref.read(adminRepositoryProvider).updateCliente(
            id: cliente.id,
            nombre: cliente.nombre,
            telefono: cliente.telefono,
            direccion: cliente.direccion,
            estado: activar ? 'activo' : 'inactivo',
          );
      _reload();
    } catch (e) {
      setState(() => _error = _extractError(e));
    }
  }

  @override
  Widget build(BuildContext context) {
    return AdminScaffold(
      title: 'CLIENTES',
      floatingActionButton: FloatingActionButton.extended(onPressed: _crear, icon: const Icon(Icons.add), label: const Text('NUEVO')),
      body: Column(
        children: [
          AdminSearchField(hintText: 'Buscar por nombre o correo...', onChanged: (v) => _reload(buscar: v)),
          if (_error != null) AdminErrorBanner(message: _error!),
          Expanded(
            child: FutureBuilder<List<ClienteAdmin>>(
              future: _future,
              builder: (context, snapshot) {
                if (snapshot.connectionState != ConnectionState.done) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (snapshot.hasError) {
                  return const Center(child: Text('No pudimos cargar los clientes.'));
                }
                final clientes = snapshot.data ?? [];
                if (clientes.isEmpty) {
                  return const Center(child: Text('No hay clientes registrados.'));
                }
                return ListView(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  children: [for (final c in clientes) _ClienteCard(cliente: c, onEditar: () => _editar(c), onToggle: () => _toggleEstado(c))],
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

String _extractError(Object e) {
  final s = e.toString();
  return s.contains('No pudimos conectar') ? s : 'No pudimos completar la accion.';
}

class _ClienteCard extends StatelessWidget {
  const _ClienteCard({required this.cliente, required this.onEditar, required this.onToggle});

  final ClienteAdmin cliente;
  final VoidCallback onEditar;
  final VoidCallback onToggle;

  @override
  Widget build(BuildContext context) {
    final activo = cliente.estado == 'activo';
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
                    Text(cliente.nombre, style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.brandDark)),
                    Text(cliente.email, style: const TextStyle(fontSize: 12, color: AppColors.grayTextDark)),
                  ],
                ),
              ),
              EstadoBadge(estado: cliente.estado, activo: activo),
            ],
          ),
          const SizedBox(height: 8),
          AdminInfoRow('Telefono', cliente.telefono ?? '-'),
          AdminInfoRow('Direccion', cliente.direccion ?? '-'),
          AdminInfoRow('Metodo', cliente.metodoRegistro),
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

class _ClienteForm extends StatelessWidget {
  const _ClienteForm({
    required this.formKey,
    required this.nombreCtrl,
    required this.emailCtrl,
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
            decoration: const InputDecoration(labelText: 'Nombre completo'),
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
          ElevatedButton(onPressed: onSubmit, child: Text(isEdit ? 'GUARDAR CAMBIOS' : 'CREAR CLIENTE')),
        ],
      ),
    );
  }
}
