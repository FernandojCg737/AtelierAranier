import 'package:dio/dio.dart';

import '../../models/bitacora_item.dart';
import '../../models/catalogo_base.dart';
import '../../models/catalogo_producto.dart';
import '../../models/cliente_admin.dart';
import '../../models/coleccion.dart';
import '../../models/empleado.dart';
import '../../models/inventario_item.dart';
import '../../models/opcion.dart';
import '../../models/producto_admin.dart';
import '../../models/proveedor.dart';
import '../../models/rol.dart';
import '../../models/sucursal_admin.dart';
import '../../models/temporada.dart';
import '../../models/usuario.dart';

/// Todas las llamadas HTTP del panel admin (CU01,02,03,04,05,06,07,08,12,19),
/// en un solo repositorio dado el volumen de entidades — mismos endpoints
/// que `frontend/src/app/services/*` y confirmados contra los routers de
/// FastAPI (`backend/app/api/v1/endpoints/*`).
class AdminRepository {
  AdminRepository(this._dio);

  final Dio _dio;

  // ---------------------------------------------------------------- CU01
  Future<List<Usuario>> getSesionesActivas() async {
    final res = await _dio.get('/sesiones/activas');
    return (res.data as List<dynamic>).map((e) => Usuario.fromJson(e as Map<String, dynamic>)).toList();
  }

  // ---------------------------------------------------------------- CU02
  Future<List<Empleado>> getEmpleados({required String tipo, String? buscar}) async {
    final res = await _dio.get('/empleados', queryParameters: {'tipo': tipo, if (buscar != null && buscar.isNotEmpty) 'buscar': buscar});
    return (res.data as List<dynamic>).map((e) => Empleado.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<Empleado> createEmpleado({
    required String nombre,
    required String email,
    required String tipo,
    int? sucursalId,
    int? rolId,
  }) async {
    final res = await _dio.post('/empleados', data: {
      'nombre': nombre,
      'email': email,
      'tipo': tipo,
      'sucursal_id': sucursalId,
      'rol_id': rolId,
    });
    return Empleado.fromJson(res.data as Map<String, dynamic>);
  }

  Future<Empleado> updateEmpleado({
    required int id,
    required String nombre,
    int? sucursalId,
    int? rolId,
    required String estado,
  }) async {
    final res = await _dio.put('/empleados/$id', data: {
      'nombre': nombre,
      'sucursal_id': sucursalId,
      'rol_id': rolId,
      'estado': estado,
    });
    return Empleado.fromJson(res.data as Map<String, dynamic>);
  }

  Future<List<Rol>> getRoles() async {
    final res = await _dio.get('/roles');
    return (res.data as List<dynamic>).map((e) => Rol.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<Permiso>> getPermisosCatalogo() async {
    final res = await _dio.get('/roles/permisos');
    return (res.data as List<dynamic>).map((e) => Permiso.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<Rol> updateRolPermisos(int rolId, List<int> permisoIds) async {
    final res = await _dio.put('/roles/$rolId/permisos', data: {'permiso_ids': permisoIds});
    return Rol.fromJson(res.data as Map<String, dynamic>);
  }

  // ---------------------------------------------------------------- CU17
  Future<BitacoraPage> getBitacora({int page = 1, int pageSize = 20, String? buscar}) async {
    final res = await _dio.get('/bitacora', queryParameters: {
      'page': page,
      'page_size': pageSize,
      if (buscar != null && buscar.isNotEmpty) 'buscar': buscar,
    });
    return BitacoraPage.fromJson(res.data as Map<String, dynamic>);
  }

  // ---------------------------------------------------------------- CU03
  Future<List<ClienteAdmin>> getClientes({String? buscar}) async {
    final res = await _dio.get('/clientes', queryParameters: {if (buscar != null && buscar.isNotEmpty) 'buscar': buscar});
    return (res.data as List<dynamic>).map((e) => ClienteAdmin.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<ClienteAdmin> createCliente({required String nombre, required String email, String? telefono, String? direccion}) async {
    final res = await _dio.post('/clientes', data: {'nombre': nombre, 'email': email, 'telefono': telefono, 'direccion': direccion});
    return ClienteAdmin.fromJson(res.data as Map<String, dynamic>);
  }

  Future<ClienteAdmin> updateCliente({
    required int id,
    required String nombre,
    String? telefono,
    String? direccion,
    required String estado,
  }) async {
    final res = await _dio.put('/clientes/$id', data: {'nombre': nombre, 'telefono': telefono, 'direccion': direccion, 'estado': estado});
    return ClienteAdmin.fromJson(res.data as Map<String, dynamic>);
  }

  // ---------------------------------------------------------------- CU04
  Future<List<SucursalAdmin>> getSucursales() async {
    final res = await _dio.get('/sucursales');
    return (res.data as List<dynamic>).map((e) => SucursalAdmin.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<SucursalAdmin> createSucursal({
    required String nombre,
    required String ciudadNombre,
    required String departamento,
    required String direccion,
    String? horarioAtencion,
    String? telefono,
    String estado = 'activa',
  }) async {
    final res = await _dio.post('/sucursales', data: {
      'nombre': nombre,
      'ciudad_nombre': ciudadNombre,
      'departamento': departamento,
      'direccion': direccion,
      'horario_atencion': horarioAtencion,
      'telefono': telefono,
      'estado': estado,
    });
    return SucursalAdmin.fromJson(res.data as Map<String, dynamic>);
  }

  Future<SucursalAdmin> updateSucursal({
    required int id,
    required String nombre,
    required String ciudadNombre,
    required String departamento,
    required String direccion,
    String? horarioAtencion,
    String? telefono,
    required String estado,
  }) async {
    final res = await _dio.put('/sucursales/$id', data: {
      'nombre': nombre,
      'ciudad_nombre': ciudadNombre,
      'departamento': departamento,
      'direccion': direccion,
      'horario_atencion': horarioAtencion,
      'telefono': telefono,
      'estado': estado,
    });
    return SucursalAdmin.fromJson(res.data as Map<String, dynamic>);
  }

  Future<void> deleteSucursal(int id) => _dio.delete('/sucursales/$id');

  // ---------------------------------------------------------------- CU05
  Future<CatalogoBase> getCatalogoBase() async {
    final res = await _dio.get('/productos/catalogo-base');
    return CatalogoBase.fromJson(res.data as Map<String, dynamic>);
  }

  Future<List<ProductoAdmin>> getProductos({String? buscar}) async {
    final res = await _dio.get('/productos', queryParameters: {if (buscar != null && buscar.isNotEmpty) 'buscar': buscar});
    return (res.data as List<dynamic>).map((e) => ProductoAdmin.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<ProductoAdmin> createProducto(Map<String, dynamic> body) async {
    final res = await _dio.post('/productos', data: body);
    return ProductoAdmin.fromJson(res.data as Map<String, dynamic>);
  }

  Future<ProductoAdmin> updateProducto(int id, Map<String, dynamic> body) async {
    final res = await _dio.put('/productos/$id', data: body);
    return ProductoAdmin.fromJson(res.data as Map<String, dynamic>);
  }

  Future<Opcion> createMarca(String nombre) async {
    final res = await _dio.post('/productos/marcas', data: {'nombre': nombre});
    return Opcion.fromJson(res.data as Map<String, dynamic>);
  }

  Future<ImagenProducto> subirImagen(int productoId, String filePath, String fileName) async {
    final form = FormData.fromMap({'file': await MultipartFile.fromFile(filePath, filename: fileName)});
    final res = await _dio.post('/productos/$productoId/imagenes', data: form);
    return ImagenProducto.fromJson(res.data as Map<String, dynamic>);
  }

  Future<void> eliminarImagen(int productoId, int imagenId) => _dio.delete('/productos/$productoId/imagenes/$imagenId');

  Future<List<InventarioItem>> getInventarioProducto(int productoId) async {
    final res = await _dio.get('/productos/$productoId/inventario');
    return (res.data as List<dynamic>).map((e) => InventarioItem.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<InventarioItem> upsertInventario({
    required int productoId,
    required int sucursalId,
    required int tallaId,
    required int colorId,
    required int cantidad,
  }) async {
    final res = await _dio.post('/productos/$productoId/inventario', data: {
      'sucursal_id': sucursalId,
      'talla_id': tallaId,
      'color_id': colorId,
      'cantidad': cantidad,
    });
    return InventarioItem.fromJson(res.data as Map<String, dynamic>);
  }

  Future<InventarioItem> actualizarCantidadInventario({required int productoId, required int inventarioId, required int cantidad}) async {
    final res = await _dio.put('/productos/$productoId/inventario/$inventarioId', data: {'cantidad': cantidad});
    return InventarioItem.fromJson(res.data as Map<String, dynamic>);
  }

  // ---------------------------------------------------------------- CU06
  Future<List<Proveedor>> getProveedores({String? buscar}) async {
    final res = await _dio.get('/proveedores', queryParameters: {if (buscar != null && buscar.isNotEmpty) 'buscar': buscar});
    return (res.data as List<dynamic>).map((e) => Proveedor.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<Proveedor> createProveedor({
    required String nombre,
    required String email,
    required String nit,
    String? contactoNombre,
    String? telefono,
    String? direccion,
  }) async {
    final res = await _dio.post('/proveedores', data: {
      'nombre': nombre,
      'email': email,
      'nit': nit,
      'contacto_nombre': contactoNombre,
      'telefono': telefono,
      'direccion': direccion,
    });
    return Proveedor.fromJson(res.data as Map<String, dynamic>);
  }

  Future<Proveedor> updateProveedor({
    required int id,
    required String nombre,
    required String nit,
    String? contactoNombre,
    String? telefono,
    String? direccion,
    required String estado,
  }) async {
    final res = await _dio.put('/proveedores/$id', data: {
      'nombre': nombre,
      'nit': nit,
      'contacto_nombre': contactoNombre,
      'telefono': telefono,
      'direccion': direccion,
      'estado': estado,
    });
    return Proveedor.fromJson(res.data as Map<String, dynamic>);
  }

  // ---------------------------------------------------------------- CU07
  Future<List<Temporada>> getTemporadas() async {
    final res = await _dio.get('/temporadas');
    return (res.data as List<dynamic>).map((e) => Temporada.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<Temporada> createTemporada({required String nombre, required String fechaInicio, required String fechaFin}) async {
    final res = await _dio.post('/temporadas', data: {'nombre': nombre, 'fecha_inicio': fechaInicio, 'fecha_fin': fechaFin});
    return Temporada.fromJson(res.data as Map<String, dynamic>);
  }

  Future<Temporada> updateTemporada({required int id, required String nombre, required String fechaInicio, required String fechaFin}) async {
    final res = await _dio.put('/temporadas/$id', data: {'nombre': nombre, 'fecha_inicio': fechaInicio, 'fecha_fin': fechaFin});
    return Temporada.fromJson(res.data as Map<String, dynamic>);
  }

  Future<void> deleteTemporada(int id) => _dio.delete('/temporadas/$id');

  Future<List<Coleccion>> getColecciones() async {
    final res = await _dio.get('/colecciones');
    return (res.data as List<dynamic>).map((e) => Coleccion.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<Coleccion> createColeccion({required int temporadaId, required String nombre, String? descripcion}) async {
    final res = await _dio.post('/colecciones', data: {'temporada_id': temporadaId, 'nombre': nombre, 'descripcion': descripcion});
    return Coleccion.fromJson(res.data as Map<String, dynamic>);
  }

  Future<Coleccion> updateColeccion({required int id, required int temporadaId, required String nombre, String? descripcion}) async {
    final res = await _dio.put('/colecciones/$id', data: {'temporada_id': temporadaId, 'nombre': nombre, 'descripcion': descripcion});
    return Coleccion.fromJson(res.data as Map<String, dynamic>);
  }

  Future<void> deleteColeccion(int id) => _dio.delete('/colecciones/$id');

  // ------------------------------------------------------------ CU08/CU12
  Future<List<Opcion>> getCatalogoSucursales() async {
    final res = await _dio.get('/catalogo/sucursales');
    return (res.data as List<dynamic>).map((e) => Opcion.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<CatalogoProducto>> getCatalogoProductosPorSucursal(int sucursalId) async {
    final res = await _dio.get('/catalogo/sucursales/$sucursalId/productos');
    return (res.data as List<dynamic>).map((e) => CatalogoProducto.fromJson(e as Map<String, dynamic>)).toList();
  }
}
