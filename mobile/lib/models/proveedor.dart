/// Espejo de `ProveedorOut` (GET/POST/PUT /proveedores) — CU06.
class Proveedor {
  const Proveedor({
    required this.id,
    required this.nombre,
    required this.email,
    required this.nit,
    this.contactoNombre,
    this.telefono,
    this.direccion,
    required this.estado,
    required this.fechaRegistro,
    required this.metodoRegistro,
  });

  final int id;
  final String nombre;
  final String email;
  final String nit;
  final String? contactoNombre;
  final String? telefono;
  final String? direccion;
  final String estado; // activo | inactivo
  final String fechaRegistro;
  final String metodoRegistro;

  factory Proveedor.fromJson(Map<String, dynamic> json) {
    return Proveedor(
      id: json['id'] as int,
      nombre: json['nombre'] as String,
      email: json['email'] as String,
      nit: json['nit'] as String,
      contactoNombre: json['contacto_nombre'] as String?,
      telefono: json['telefono'] as String?,
      direccion: json['direccion'] as String?,
      estado: json['estado'] as String,
      fechaRegistro: json['fecha_registro'] as String,
      metodoRegistro: json['metodo_registro'] as String,
    );
  }
}
