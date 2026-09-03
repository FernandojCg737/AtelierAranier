/// Espejo de `UsuarioOut` en el backend (mismo shape que `Cliente` en la web).
class Usuario {
  const Usuario({
    required this.id,
    required this.nombre,
    required this.email,
    this.telefono,
    this.direccion,
    required this.tipo,
    this.rol,
    required this.permisos,
  });

  final int id;
  final String nombre;
  final String email;
  final String? telefono;
  final String? direccion;
  final String tipo; // cliente | administrador | encargado_sucursal | cajero
  final String? rol;
  final List<String> permisos;

  bool get isCliente => tipo == 'cliente';
  bool get isAdministrador => tipo == 'administrador';
  bool get isStaff => tipo != 'cliente';

  bool hasPermiso(String codigo) => isAdministrador || permisos.contains(codigo);

  factory Usuario.fromJson(Map<String, dynamic> json) {
    return Usuario(
      id: json['id'] as int,
      nombre: json['nombre'] as String,
      email: json['email'] as String,
      telefono: json['telefono'] as String?,
      direccion: json['direccion'] as String?,
      tipo: json['tipo'] as String,
      rol: json['rol'] as String?,
      permisos: (json['permisos'] as List<dynamic>? ?? []).map((e) => e.toString()).toList(),
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'nombre': nombre,
    'email': email,
    'telefono': telefono,
    'direccion': direccion,
    'tipo': tipo,
    'rol': rol,
    'permisos': permisos,
  };
}

class TokenResponse {
  const TokenResponse({required this.accessToken, required this.usuario});

  final String accessToken;
  final Usuario usuario;

  factory TokenResponse.fromJson(Map<String, dynamic> json) {
    return TokenResponse(
      accessToken: json['access_token'] as String,
      usuario: Usuario.fromJson(json['usuario'] as Map<String, dynamic>),
    );
  }
}
