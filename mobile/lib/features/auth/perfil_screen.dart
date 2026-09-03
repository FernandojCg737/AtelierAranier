import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api_client.dart';
import '../../core/theme.dart';
import '../../widgets/password_strength.dart';
import 'auth_provider.dart';

class PerfilScreen extends ConsumerStatefulWidget {
  const PerfilScreen({super.key});

  @override
  ConsumerState<PerfilScreen> createState() => _PerfilScreenState();
}

class _PerfilScreenState extends ConsumerState<PerfilScreen> {
  late final TextEditingController _nombreCtrl;
  late final TextEditingController _telefonoCtrl;
  late final TextEditingController _direccionCtrl;
  final _actualCtrl = TextEditingController();
  final _nuevaCtrl = TextEditingController();
  bool _savingPerfil = false;
  bool _savingPassword = false;
  String? _errorPerfil;
  String? _errorPassword;
  String? _successPerfil;
  String? _successPassword;

  @override
  void initState() {
    super.initState();
    final usuario = ref.read(authProvider).usuario;
    _nombreCtrl = TextEditingController(text: usuario?.nombre ?? '');
    _telefonoCtrl = TextEditingController(text: usuario?.telefono ?? '');
    _direccionCtrl = TextEditingController(text: usuario?.direccion ?? '');
  }

  @override
  void dispose() {
    _nombreCtrl.dispose();
    _telefonoCtrl.dispose();
    _direccionCtrl.dispose();
    _actualCtrl.dispose();
    _nuevaCtrl.dispose();
    super.dispose();
  }

  Future<void> _guardarPerfil() async {
    setState(() {
      _savingPerfil = true;
      _errorPerfil = null;
      _successPerfil = null;
    });
    try {
      await ref.read(authProvider.notifier).updateProfile(
        nombre: _nombreCtrl.text.trim(),
        telefono: _telefonoCtrl.text.trim().isEmpty ? null : _telefonoCtrl.text.trim(),
        direccion: _direccionCtrl.text.trim().isEmpty ? null : _direccionCtrl.text.trim(),
      );
      setState(() => _successPerfil = 'Perfil actualizado.');
    } catch (e) {
      setState(() => _errorPerfil = extractErrorMessage(e));
    } finally {
      if (mounted) setState(() => _savingPerfil = false);
    }
  }

  Future<void> _cambiarPassword() async {
    if (!isPasswordValid(_nuevaCtrl.text)) {
      setState(() => _errorPassword = 'La nueva contrasena no cumple los requisitos.');
      return;
    }
    setState(() {
      _savingPassword = true;
      _errorPassword = null;
      _successPassword = null;
    });
    try {
      await ref.read(authProvider.notifier).changePassword(actual: _actualCtrl.text, nueva: _nuevaCtrl.text);
      _actualCtrl.clear();
      _nuevaCtrl.clear();
      setState(() => _successPassword = 'Contrasena actualizada.');
    } catch (e) {
      setState(() => _errorPassword = extractErrorMessage(e));
    } finally {
      if (mounted) setState(() => _savingPassword = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final usuario = ref.watch(authProvider).usuario;
    final isCliente = usuario?.isCliente ?? false;

    return Scaffold(
      appBar: AppBar(
        title: const Text('MI PERFIL'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              await ref.read(authProvider.notifier).logout();
              if (context.mounted) context.go('/');
            },
          ),
        ],
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            const EyebrowText('Datos personales'),
            const SizedBox(height: 12),
            if (_errorPerfil != null) _ErrorBanner(_errorPerfil!),
            if (_successPerfil != null) _SuccessBanner(_successPerfil!),
            TextField(controller: _nombreCtrl, decoration: const InputDecoration(labelText: 'NOMBRE')),
            const SizedBox(height: 14),
            TextFormField(
              initialValue: usuario?.email,
              enabled: false,
              decoration: const InputDecoration(labelText: 'CORREO'),
            ),
            if (isCliente) ...[
              const SizedBox(height: 14),
              TextField(controller: _telefonoCtrl, decoration: const InputDecoration(labelText: 'TELEFONO')),
              const SizedBox(height: 14),
              TextField(controller: _direccionCtrl, decoration: const InputDecoration(labelText: 'DIRECCION')),
            ],
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: _savingPerfil ? null : _guardarPerfil,
              child: Text(_savingPerfil ? 'GUARDANDO...' : 'GUARDAR CAMBIOS'),
            ),
            const SizedBox(height: 36),
            const EyebrowText('Cambiar contrasena'),
            const SizedBox(height: 12),
            if (_errorPassword != null) _ErrorBanner(_errorPassword!),
            if (_successPassword != null) _SuccessBanner(_successPassword!),
            TextField(
              controller: _actualCtrl,
              obscureText: true,
              decoration: const InputDecoration(labelText: 'CONTRASENA ACTUAL'),
            ),
            const SizedBox(height: 14),
            TextField(
              controller: _nuevaCtrl,
              obscureText: true,
              onChanged: (_) => setState(() {}),
              decoration: const InputDecoration(labelText: 'NUEVA CONTRASENA'),
            ),
            const SizedBox(height: 10),
            PasswordStrengthChecklist(password: _nuevaCtrl.text),
            const SizedBox(height: 20),
            OutlinedButton(
              onPressed: _savingPassword ? null : _cambiarPassword,
              child: Text(_savingPassword ? 'GUARDANDO...' : 'ACTUALIZAR CONTRASENA'),
            ),
          ],
        ),
      ),
    );
  }
}

class _ErrorBanner extends StatelessWidget {
  const _ErrorBanner(this.message);
  final String message;

  @override
  Widget build(BuildContext context) => Container(
    width: double.infinity,
    padding: const EdgeInsets.all(12),
    margin: const EdgeInsets.only(bottom: 14),
    color: AppColors.dangerBg,
    child: Text(message, style: const TextStyle(color: AppColors.danger, fontSize: 13)),
  );
}

class _SuccessBanner extends StatelessWidget {
  const _SuccessBanner(this.message);
  final String message;

  @override
  Widget build(BuildContext context) => Container(
    width: double.infinity,
    padding: const EdgeInsets.all(12),
    margin: const EdgeInsets.only(bottom: 14),
    color: AppColors.successBg,
    child: Text(message, style: const TextStyle(color: AppColors.success, fontSize: 13)),
  );
}
