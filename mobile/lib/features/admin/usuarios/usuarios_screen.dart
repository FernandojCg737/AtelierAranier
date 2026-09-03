import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme.dart';
import '../../../models/empleado.dart';
import '../../../models/rol.dart';
import '../../../models/sucursal_admin.dart';
import '../admin_menu.dart';
import '../admin_provider.dart';
import '../widgets/admin_widgets.dart';

T? _firstWhereOrNull<T>(Iterable<T> iterable, bool Function(T) test) {
  for (final e in iterable) {
    if (test(e)) return e;
  }
  return null;
}

/// CU02 — Administrar Usuarios, Roles y Permisos. Dos pestanas: Usuarios
/// (sub-tabs por tipo) y Permisos (checkboxes por rol, agrupados por
/// paquete, igual que `admin-menu.ts`).
class UsuariosScreen extends StatefulWidget {
  const UsuariosScreen({super.key});

  @override
  State<UsuariosScreen> createState() => _UsuariosScreenState();
}

class _UsuariosScreenState extends State<UsuariosScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AdminScaffold(
      title: 'USUARIOS Y PERMISOS',
      body: Column(
        children: [
          TabBar(
            controller: _tabController,
            labelColor: AppColors.brandDark,
            unselectedLabelColor: AppColors.grayText,
            indicatorColor: AppColors.brandDark,
            tabs: const [Tab(text: 'USUARIOS'), Tab(text: 'PERMISOS')],
          ),
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: const [_UsuariosTab(), _PermisosTab()],
            ),
          ),
        ],
      ),
    );
  }
}

const _tiposTabs = [
  ('administrador', 'Administradores'),
  ('encargado_sucursal', 'Encargados'),
  ('cajero', 'Cajeros'),
];

const _rolNombrePorTipo = {
  'administrador': 'Administrador',
  'encargado_sucursal': 'Encargado de Sucursal',
  'cajero': 'Cajero',
};

class _UsuariosTab extends ConsumerStatefulWidget {
  const _UsuariosTab();

  @override
  ConsumerState<_UsuariosTab> createState() => _UsuariosTabState();
}

class _UsuariosTabState extends ConsumerState<_UsuariosTab> {
  String _tipo = 'administrador';
  String? _buscar;
  late Future<List<Empleado>> _future;
  List<SucursalAdmin> _sucursales = [];
  List<Rol> _roles = [];
  String? _error;
  bool _refLoaded = false;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (!_refLoaded) {
      _refLoaded = true;
      _cargarReferencias();
    }
  }

  Future<void> _cargarReferencias() async {
    final repo = ref.read(adminRepositoryProvider);
    try {
      final results = await Future.wait([repo.getSucursales(), repo.getRoles()]);
      if (!mounted) return;
      setState(() {
        _sucursales = results[0] as List<SucursalAdmin>;
        _roles = results[1] as List<Rol>;
      });
    } catch (_) {
      // Los selects quedaran vacios; el error real ya se muestra en la lista.
    }
  }

  Future<List<Empleado>> _load() => ref.read(adminRepositoryProvider).getEmpleados(tipo: _tipo, buscar: _buscar);

  void _reload({String? tipo, String? buscar}) {
    setState(() {
      if (tipo != null) {
        _tipo = tipo;
        _buscar = null;
      }
      if (buscar != null) _buscar = buscar.isEmpty ? null : buscar;
      _error = null;
      _future = _load();
    });
  }

  List<Rol> get _rolesDelTipo {
    final nombreEsperado = _rolNombrePorTipo[_tipo];
    final filtrados = _roles.where((r) => r.nombre == nombreEsperado).toList();
    return filtrados.isNotEmpty ? filtrados : _roles;
  }

  Future<void> _crear() async {
    final nombreCtrl = TextEditingController();
    final emailCtrl = TextEditingController();
    var sucursalId = _sucursales.isNotEmpty ? _sucursales.first.id : null;
    var rolId = _rolesDelTipo.isNotEmpty ? _rolesDelTipo.first.id : null;
    final requiereSucursal = _tipo != 'administrador';
    final formKey = GlobalKey<FormState>();

    await showAdminFormSheet(
      context,
      title: 'NUEVO ${_rolNombrePorTipo[_tipo]?.toUpperCase() ?? 'USUARIO'}',
      builder: (context) => StatefulBuilder(
        builder: (context, setSheetState) => Form(
          key: formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const AdminHintText('Se genera una contrasena temporal y se le envia por correo.'),
              TextFormField(
                controller: nombreCtrl,
                decoration: const InputDecoration(labelText: 'Nombre completo'),
                validator: (v) => (v == null || v.trim().length < 2) ? 'Requerido' : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: emailCtrl,
                decoration: const InputDecoration(labelText: 'Correo electronico'),
                keyboardType: TextInputType.emailAddress,
                validator: (v) => (v == null || !v.contains('@')) ? 'Correo invalido' : null,
              ),
              if (requiereSucursal) ...[
                const SizedBox(height: 16),
                DropdownButtonFormField<int>(
                  initialValue: sucursalId,
                  decoration: const InputDecoration(labelText: 'Sucursal'),
                  items: [for (final s in _sucursales) DropdownMenuItem(value: s.id, child: Text(s.nombre))],
                  onChanged: (v) => setSheetState(() => sucursalId = v),
                  validator: (v) => v == null ? 'Elegi una sucursal' : null,
                ),
              ],
              if (_rolesDelTipo.isNotEmpty) ...[
                const SizedBox(height: 16),
                DropdownButtonFormField<int>(
                  initialValue: rolId,
                  decoration: const InputDecoration(labelText: 'Rol'),
                  items: [for (final r in _rolesDelTipo) DropdownMenuItem(value: r.id, child: Text(r.nombre))],
                  onChanged: (v) => setSheetState(() => rolId = v),
                ),
              ],
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: () async {
                  if (!formKey.currentState!.validate()) return;
                  try {
                    await ref.read(adminRepositoryProvider).createEmpleado(
                          nombre: nombreCtrl.text.trim(),
                          email: emailCtrl.text.trim(),
                          tipo: _tipo,
                          sucursalId: requiereSucursal ? sucursalId : null,
                          rolId: rolId,
                        );
                    if (context.mounted) Navigator.pop(context);
                    _reload();
                  } catch (e) {
                    if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_extractUsuarioError(e))));
                  }
                },
                child: const Text('CREAR USUARIO'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _editar(Empleado empleado) async {
    final nombreCtrl = TextEditingController(text: empleado.nombre);
    var sucursalId = empleado.sucursalId;
    var rolId = empleado.rolId;
    var estado = empleado.estado;
    final requiereSucursal = empleado.tipo != 'administrador';
    final formKey = GlobalKey<FormState>();

    await showAdminFormSheet(
      context,
      title: 'EDITAR USUARIO',
      builder: (context) => StatefulBuilder(
        builder: (context, setSheetState) => Form(
          key: formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextFormField(
                controller: nombreCtrl,
                decoration: const InputDecoration(labelText: 'Nombre completo'),
                validator: (v) => (v == null || v.trim().length < 2) ? 'Requerido' : null,
              ),
              if (requiereSucursal) ...[
                const SizedBox(height: 16),
                DropdownButtonFormField<int>(
                  initialValue: sucursalId,
                  decoration: const InputDecoration(labelText: 'Sucursal'),
                  items: [for (final s in _sucursales) DropdownMenuItem(value: s.id, child: Text(s.nombre))],
                  onChanged: (v) => setSheetState(() => sucursalId = v),
                ),
              ],
              const SizedBox(height: 16),
              DropdownButtonFormField<int>(
                initialValue: rolId,
                decoration: const InputDecoration(labelText: 'Rol'),
                items: [for (final r in _roles) DropdownMenuItem(value: r.id, child: Text(r.nombre))],
                onChanged: (v) => setSheetState(() => rolId = v),
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                initialValue: estado,
                decoration: const InputDecoration(labelText: 'Estado'),
                items: const [
                  DropdownMenuItem(value: 'activo', child: Text('Activo')),
                  DropdownMenuItem(value: 'inactivo', child: Text('Inactivo')),
                ],
                onChanged: (v) => setSheetState(() => estado = v!),
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: () async {
                  if (!formKey.currentState!.validate()) return;
                  try {
                    await ref.read(adminRepositoryProvider).updateEmpleado(
                          id: empleado.id,
                          nombre: nombreCtrl.text.trim(),
                          sucursalId: requiereSucursal ? sucursalId : null,
                          rolId: rolId,
                          estado: estado,
                        );
                    if (context.mounted) Navigator.pop(context);
                    _reload();
                  } catch (e) {
                    if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_extractUsuarioError(e))));
                  }
                },
                child: const Text('GUARDAR CAMBIOS'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _toggleEstado(Empleado empleado) async {
    final activar = empleado.estado == 'inactivo';
    final ok = await confirmAdminAction(
      context,
      title: activar ? 'Activar usuario' : 'Desactivar usuario',
      message: 'Seguro que queres ${activar ? 'activar' : 'desactivar'} a ${empleado.nombre}?',
    );
    if (!ok) return;
    try {
      await ref.read(adminRepositoryProvider).updateEmpleado(
            id: empleado.id,
            nombre: empleado.nombre,
            sucursalId: empleado.sucursalId,
            rolId: empleado.rolId,
            estado: activar ? 'activo' : 'inactivo',
          );
      _reload();
    } catch (e) {
      setState(() => _error = _extractUsuarioError(e));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
          child: Wrap(
            spacing: 8,
            children: [
              for (final t in _tiposTabs)
                ChoiceChip(label: Text(t.$2), selected: _tipo == t.$1, onSelected: (_) => _reload(tipo: t.$1)),
            ],
          ),
        ),
        AdminSearchField(hintText: 'Buscar por nombre o correo...', onChanged: (v) => _reload(buscar: v)),
        if (_error != null) AdminErrorBanner(message: _error!),
        Expanded(
          child: FutureBuilder<List<Empleado>>(
            future: _future,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator());
              if (snapshot.hasError) return const Center(child: Text('No pudimos cargar los usuarios.'));
              final empleados = snapshot.data ?? [];
              if (empleados.isEmpty) return const Center(child: Text('No hay usuarios para este filtro.'));
              return ListView(
                padding: const EdgeInsets.symmetric(vertical: 8),
                children: [
                  for (final e in empleados)
                    _EmpleadoCard(empleado: e, onEditar: () => _editar(e), onToggle: () => _toggleEstado(e)),
                ],
              );
            },
          ),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
          child: SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(onPressed: _crear, icon: const Icon(Icons.add), label: const Text('NUEVO USUARIO')),
          ),
        ),
      ],
    );
  }
}

String _extractUsuarioError(Object e) {
  final s = e.toString();
  return s.contains('No pudimos conectar') ? s : 'No pudimos completar la accion.';
}

class _EmpleadoCard extends StatelessWidget {
  const _EmpleadoCard({required this.empleado, required this.onEditar, required this.onToggle});

  final Empleado empleado;
  final VoidCallback onEditar;
  final VoidCallback onToggle;

  @override
  Widget build(BuildContext context) {
    final activo = empleado.estado == 'activo';
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
                    Text(empleado.nombre, style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.brandDark)),
                    Text(empleado.email, style: const TextStyle(fontSize: 12, color: AppColors.grayTextDark)),
                  ],
                ),
              ),
              EstadoBadge(estado: empleado.estado, activo: activo),
            ],
          ),
          const SizedBox(height: 8),
          if (empleado.sucursalNombre != null) AdminInfoRow('Sucursal', empleado.sucursalNombre!),
          AdminInfoRow('Rol', empleado.rolNombre ?? '-'),
          AdminInfoRow('Metodo', empleado.metodoRegistro),
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

class _PermisosTab extends ConsumerStatefulWidget {
  const _PermisosTab();

  @override
  ConsumerState<_PermisosTab> createState() => _PermisosTabState();
}

class _PermisosTabState extends ConsumerState<_PermisosTab> {
  late Future<void> _future;
  List<Rol> _roles = [];
  int? _rolSeleccionadoId;
  Set<int> _seleccion = {};
  String? _error;
  bool _guardando = false;

  @override
  void initState() {
    super.initState();
    _future = _cargar();
  }

  Future<void> _cargar() async {
    final repo = ref.read(adminRepositoryProvider);
    final roles = await repo.getRoles();
    if (!mounted) return;
    setState(() {
      _roles = roles;
      _rolSeleccionadoId = roles.isNotEmpty ? roles.first.id : null;
      _seleccion = _idsDePermisos(roles.isNotEmpty ? roles.first : null);
    });
  }

  Set<int> _idsDePermisos(Rol? rol) {
    if (rol == null) return {};
    return _permisosCatalogo.where((p) => rol.permisos.contains(p.codigo)).map((p) => p.id).toSet();
  }

  // El catalogo de permisos (id<->codigo CU) se deriva de `adminMenu`: cada
  // CU con `route` es un permiso configurable. El id real lo pedimos aparte
  // (GET /roles/permisos) porque el backend es quien asigna esos ids.
  List<_PermisoCatalogoEntry> _permisosCatalogo = [];

  Rol? get _rolSeleccionado => _firstWhereOrNull(_roles, (r) => r.id == _rolSeleccionadoId);

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<void>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator());
        if (snapshot.hasError) {
          return const Center(child: Text('No pudimos cargar los roles y permisos.'));
        }
        return _PermisosCatalogoLoader(
          roles: _roles,
          onLoaded: (permisos) {
            if (_permisosCatalogo.isEmpty && permisos.isNotEmpty && mounted) {
              setState(() {
                _permisosCatalogo = permisos;
                _seleccion = _idsDePermisos(_rolSeleccionado);
              });
            }
          },
          child: _buildContent(),
        );
      },
    );
  }

  Widget _buildContent() {
    final rol = _rolSeleccionado;
    final esAdministrador = rol?.nombre == 'Administrador';

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
          child: Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              for (final r in _roles)
                ChoiceChip(
                  label: Text(r.nombre),
                  selected: _rolSeleccionadoId == r.id,
                  onSelected: (_) => setState(() {
                    _rolSeleccionadoId = r.id;
                    _seleccion = _idsDePermisos(r);
                  }),
                ),
            ],
          ),
        ),
        if (_error != null) AdminErrorBanner(message: _error!),
        if (esAdministrador)
          const Padding(
            padding: EdgeInsets.all(16),
            child: Text(
              'El rol Administrador tiene acceso total al sistema y no es configurable.',
              style: TextStyle(fontSize: 12, color: AppColors.grayTextDark, fontStyle: FontStyle.italic),
            ),
          )
        else if (rol?.nombre == 'Cliente')
          const Padding(
            padding: EdgeInsets.all(16),
            child: Text(
              'Los clientes no usan el panel administrativo; estos permisos quedan disponibles para uso futuro.',
              style: TextStyle(fontSize: 12, color: AppColors.grayTextDark, fontStyle: FontStyle.italic),
            ),
          ),
        Expanded(
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
            children: [
              for (final paquete in adminMenu) _PaqueteCheckboxes(paquete: paquete, permisosCatalogo: _permisosCatalogo, seleccion: _seleccion, disabled: esAdministrador, onToggle: _toggle),
            ],
          ),
        ),
        if (!esAdministrador)
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton(onPressed: _guardando ? null : _guardar, child: Text(_guardando ? 'GUARDANDO...' : 'GUARDAR PERMISOS')),
            ),
          ),
      ],
    );
  }

  void _toggle(int permisoId, bool valor) {
    setState(() {
      if (valor) {
        _seleccion.add(permisoId);
      } else {
        _seleccion.remove(permisoId);
      }
    });
  }

  Future<void> _guardar() async {
    final rolId = _rolSeleccionadoId;
    if (rolId == null) return;
    setState(() {
      _guardando = true;
      _error = null;
    });
    try {
      final actualizado = await ref.read(adminRepositoryProvider).updateRolPermisos(rolId, _seleccion.toList());
      setState(() {
        final idx = _roles.indexWhere((r) => r.id == rolId);
        if (idx != -1) _roles[idx] = actualizado;
        _guardando = false;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Permisos actualizados.')));
      }
    } catch (e) {
      setState(() {
        _guardando = false;
        _error = _extractUsuarioError(e);
      });
    }
  }
}

class _PermisoCatalogoEntry {
  const _PermisoCatalogoEntry(this.id, this.codigo);

  final int id;
  final String codigo;
}

/// Carga `GET /roles/permisos` una sola vez (necesita mapear codigo CU -> id
/// real del backend para poder armar `permiso_ids` al guardar).
class _PermisosCatalogoLoader extends ConsumerStatefulWidget {
  const _PermisosCatalogoLoader({required this.roles, required this.onLoaded, required this.child});

  final List<Rol> roles;
  final ValueChanged<List<_PermisoCatalogoEntry>> onLoaded;
  final Widget child;

  @override
  ConsumerState<_PermisosCatalogoLoader> createState() => _PermisosCatalogoLoaderState();
}

class _PermisosCatalogoLoaderState extends ConsumerState<_PermisosCatalogoLoader> {
  late Future<List<_PermisoCatalogoEntry>> _future;

  @override
  void initState() {
    super.initState();
    _future = ref.read(adminRepositoryProvider).getPermisosCatalogo().then(
          (permisos) => permisos.map((p) => _PermisoCatalogoEntry(p.id, p.nombre)).toList(),
        );
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<_PermisoCatalogoEntry>>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator());
        if (!snapshot.hasData) return const Center(child: Text('No pudimos cargar el catalogo de permisos.'));
        WidgetsBinding.instance.addPostFrameCallback((_) => widget.onLoaded(snapshot.data!));
        return widget.child;
      },
    );
  }
}

class _PaqueteCheckboxes extends StatelessWidget {
  const _PaqueteCheckboxes({
    required this.paquete,
    required this.permisosCatalogo,
    required this.seleccion,
    required this.disabled,
    required this.onToggle,
  });

  final AdminPackage paquete;
  final List<_PermisoCatalogoEntry> permisosCatalogo;
  final Set<int> seleccion;
  final bool disabled;
  final void Function(int permisoId, bool valor) onToggle;

  @override
  Widget build(BuildContext context) {
    final implementados = paquete.useCases.where((cu) => cu.route != null).toList();
    if (implementados.isEmpty) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '${paquete.code} · ${paquete.label}'.toUpperCase(),
            style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppColors.grayText, letterSpacing: 0.5),
          ),
          for (final cu in implementados)
            Builder(builder: (context) {
              final entry = _firstWhereOrNull(permisosCatalogo, (p) => p.codigo == cu.code);
              if (entry == null) return const SizedBox.shrink();
              return CheckboxListTile(
                dense: true,
                contentPadding: EdgeInsets.zero,
                controlAffinity: ListTileControlAffinity.leading,
                value: seleccion.contains(entry.id),
                onChanged: disabled ? null : (v) => onToggle(entry.id, v ?? false),
                title: Text('${cu.code} · ${cu.label}', style: const TextStyle(fontSize: 13)),
              );
            }),
        ],
      ),
    );
  }
}
