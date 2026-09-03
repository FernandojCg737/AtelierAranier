import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api_client.dart';
import '../../core/theme.dart';
import '../../widgets/password_strength.dart';
import 'auth_provider.dart';

enum _Step { email, code, choice, reset }

class RecuperarPasswordScreen extends ConsumerStatefulWidget {
  const RecuperarPasswordScreen({super.key});

  @override
  ConsumerState<RecuperarPasswordScreen> createState() => _RecuperarPasswordScreenState();
}

class _RecuperarPasswordScreenState extends ConsumerState<RecuperarPasswordScreen> {
  _Step _step = _Step.email;
  final _emailCtrl = TextEditingController();
  final _codeCtrl = TextEditingController();
  final _newPasswordCtrl = TextEditingController();
  final _confirmCtrl = TextEditingController();
  String? _resetToken;
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _emailCtrl.dispose();
    _codeCtrl.dispose();
    _newPasswordCtrl.dispose();
    _confirmCtrl.dispose();
    super.dispose();
  }

  Future<void> _run(Future<void> Function() action) async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await action();
    } catch (e) {
      setState(() => _error = extractErrorMessage(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _sendEmail() => _run(() async {
    if (_emailCtrl.text.trim().isEmpty) throw Exception('Ingresa tu correo.');
    await ref.read(authProvider.notifier).forgotPassword(_emailCtrl.text.trim());
    setState(() => _step = _Step.code);
  });

  Future<void> _verifyCode() => _run(() async {
    if (_codeCtrl.text.trim().length != 6) throw Exception('El codigo tiene 6 digitos.');
    final token = await ref
        .read(authProvider.notifier)
        .verifyResetCode(email: _emailCtrl.text.trim(), code: _codeCtrl.text.trim());
    _resetToken = token;
    setState(() => _step = _Step.choice);
  });

  Future<void> _loginDirecto() => _run(() async {
    await ref.read(authProvider.notifier).loginWithResetCode(_resetToken!);
    if (!mounted) return;
    final auth = ref.read(authProvider);
    context.go(auth.isStaff ? '/admin' : '/');
  });

  Future<void> _cambiarPassword() => _run(() async {
    if (!isPasswordValid(_newPasswordCtrl.text)) throw Exception('La contrasena no cumple los requisitos.');
    if (_newPasswordCtrl.text != _confirmCtrl.text) throw Exception('Las contrasenas no coinciden.');
    await ref.read(authProvider.notifier).resetPassword(resetToken: _resetToken!, newPassword: _newPasswordCtrl.text);
    if (!mounted) return;
    final auth = ref.read(authProvider);
    context.go(auth.isStaff ? '/admin' : '/');
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('RECUPERAR CONTRASENA')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              if (_error != null)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(12),
                  margin: const EdgeInsets.only(bottom: 16),
                  color: AppColors.dangerBg,
                  child: Text(_error!, style: const TextStyle(color: AppColors.danger, fontSize: 13)),
                ),
              ..._buildStep(),
            ],
          ),
        ),
      ),
    );
  }

  List<Widget> _buildStep() {
    switch (_step) {
      case _Step.email:
        return [
          const Text('Ingresa tu correo y te enviamos un codigo de verificacion.'),
          const SizedBox(height: 18),
          TextField(
            controller: _emailCtrl,
            keyboardType: TextInputType.emailAddress,
            decoration: const InputDecoration(labelText: 'CORREO ELECTRONICO'),
          ),
          const SizedBox(height: 24),
          ElevatedButton(onPressed: _loading ? null : _sendEmail, child: Text(_loading ? 'ENVIANDO...' : 'ENVIAR CODIGO')),
        ];
      case _Step.code:
        return [
          Text('Ingresa el codigo de 6 digitos que enviamos a ${_emailCtrl.text}.'),
          const SizedBox(height: 18),
          TextField(
            controller: _codeCtrl,
            keyboardType: TextInputType.number,
            maxLength: 6,
            decoration: const InputDecoration(labelText: 'CODIGO'),
          ),
          const SizedBox(height: 24),
          ElevatedButton(onPressed: _loading ? null : _verifyCode, child: Text(_loading ? 'VERIFICANDO...' : 'VERIFICAR CODIGO')),
        ];
      case _Step.choice:
        return [
          const Text('Codigo verificado. Que queres hacer?'),
          const SizedBox(height: 20),
          ElevatedButton(
            onPressed: _loading ? null : _loginDirecto,
            child: Text(_loading ? 'INGRESANDO...' : 'SOLO INICIAR SESION'),
          ),
          const SizedBox(height: 12),
          OutlinedButton(
            onPressed: _loading ? null : () => setState(() => _step = _Step.reset),
            child: const Text('CAMBIAR CONTRASENA'),
          ),
        ];
      case _Step.reset:
        return [
          TextField(
            controller: _newPasswordCtrl,
            obscureText: true,
            onChanged: (_) => setState(() {}),
            decoration: const InputDecoration(labelText: 'NUEVA CONTRASENA'),
          ),
          const SizedBox(height: 10),
          PasswordStrengthChecklist(password: _newPasswordCtrl.text),
          const SizedBox(height: 18),
          TextField(
            controller: _confirmCtrl,
            obscureText: true,
            decoration: const InputDecoration(labelText: 'CONFIRMAR CONTRASENA'),
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: _loading ? null : _cambiarPassword,
            child: Text(_loading ? 'GUARDANDO...' : 'GUARDAR NUEVA CONTRASENA'),
          ),
        ];
    }
  }
}
