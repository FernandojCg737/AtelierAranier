import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Persistencia de sesion (token + usuario cacheado), equivalente a las
/// claves `atelieraranier_token` / `atelieraranier_cliente` que usa la web
/// en localStorage, pero cifrado en vez de texto plano.
class SecureStorage {
  SecureStorage() : _storage = const FlutterSecureStorage();

  final FlutterSecureStorage _storage;

  static const _tokenKey = 'atelieraranier_token';
  static const _usuarioKey = 'atelieraranier_usuario';

  Future<String?> readToken() => _storage.read(key: _tokenKey);

  Future<void> saveToken(String token) => _storage.write(key: _tokenKey, value: token);

  Future<Map<String, dynamic>?> readUsuario() async {
    final raw = await _storage.read(key: _usuarioKey);
    if (raw == null) return null;
    return jsonDecode(raw) as Map<String, dynamic>;
  }

  Future<void> saveUsuario(Map<String, dynamic> usuario) =>
      _storage.write(key: _usuarioKey, value: jsonEncode(usuario));

  Future<void> clear() async {
    await _storage.delete(key: _tokenKey);
    await _storage.delete(key: _usuarioKey);
  }
}
