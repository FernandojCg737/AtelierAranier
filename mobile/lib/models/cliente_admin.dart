/// Espejo de `ClienteAdminOut` (GET/POST/PUT /clientes) — CU03.
class ClienteAdmin {
  const ClienteAdmin({
    required this.id,
    required this.nombre,
    required this.email,
    this.telefono,
    this.direccion,
    required this.estado,
    required this.fechaRegistro,
    required this.metodoRegistro,
  });

  final int id;
  final String nombre;
  final String email;
  final String? telefono;
  final String? direccion;
  final String estado; // activo | inactivo
  final String fechaRegistro;
  final String metodoRegistro;

  factory ClienteAdmin.fromJson(Map<String, dynamic> json) {
    return ClienteAdmin(
      id: json['id'] as int,
      nombre: json['nombre'] as String,
      email: json['email'] as String,
      telefono: json['telefono'] as String?,
      direccion: json['direccion'] as String?,
      estado: json['estado'] as String,
      fechaRegistro: json['fecha_registro'] as String,
      metodoRegistro: json['metodo_registro'] as String,
    );
  }
}
