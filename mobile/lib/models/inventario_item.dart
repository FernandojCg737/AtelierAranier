/// Espejo de `InventarioOut` (GET/POST/PUT /productos/{id}/inventario) — CU05.
class InventarioItem {
  const InventarioItem({
    required this.id,
    required this.sucursalId,
    required this.sucursalNombre,
    required this.tallaId,
    required this.tallaCodigo,
    required this.colorId,
    required this.colorNombre,
    required this.cantidad,
  });

  final int id;
  final int sucursalId;
  final String sucursalNombre;
  final int tallaId;
  final String tallaCodigo;
  final int colorId;
  final String colorNombre;
  final int cantidad;

  factory InventarioItem.fromJson(Map<String, dynamic> json) {
    return InventarioItem(
      id: json['id'] as int,
      sucursalId: json['sucursal_id'] as int,
      sucursalNombre: json['sucursal_nombre'] as String,
      tallaId: json['talla_id'] as int,
      tallaCodigo: json['talla_codigo'] as String,
      colorId: json['color_id'] as int,
      colorNombre: json['color_nombre'] as String,
      cantidad: json['cantidad'] as int,
    );
  }
}
