class EstadoAsistencia {
  const EstadoAsistencia({
    required this.liberado,
    required this.ventanaCerrada,
    required this.horaLiberacion,
    required this.codigoFecha,
    required this.codigo,
  });

  final bool liberado;
  final bool ventanaCerrada;
  final String horaLiberacion;
  final String codigoFecha;
  final String? codigo;

  factory EstadoAsistencia.fromJson(Map<String, dynamic> json) => EstadoAsistencia(
        liberado: json['liberado'] as bool,
        ventanaCerrada: json['ventana_cerrada'] as bool,
        horaLiberacion: (json['hora_liberacion'] as String).substring(0, 5),
        codigoFecha: json['codigo_fecha'] as String,
        codigo: json['codigo'] as String?,
      );
}

class MarcadoHoy {
  const MarcadoHoy({
    required this.empleadoId,
    required this.empleadoNombre,
    required this.sucursalNombre,
    required this.marco,
    required this.horaMarcado,
    required this.estado,
  });

  final int empleadoId;
  final String empleadoNombre;
  final String? sucursalNombre;
  final bool marco;
  final DateTime? horaMarcado;
  final String estado; // "marco" | "pendiente" | "falta"

  factory MarcadoHoy.fromJson(Map<String, dynamic> json) => MarcadoHoy(
        empleadoId: json['empleado_id'] as int,
        empleadoNombre: json['empleado_nombre'] as String,
        sucursalNombre: json['sucursal_nombre'] as String?,
        marco: json['marco'] as bool,
        horaMarcado: json['hora_marcado'] != null ? DateTime.parse(json['hora_marcado'] as String) : null,
        estado: json['estado'] as String,
      );
}

class Marcado {
  const Marcado({
    required this.id,
    required this.empleadoId,
    required this.empleadoNombre,
    required this.sucursalNombre,
    required this.fecha,
    required this.horaMarcado,
    required this.latitud,
    required this.longitud,
    required this.fotoUrl,
  });

  final int id;
  final int empleadoId;
  final String empleadoNombre;
  final String? sucursalNombre;
  final String fecha;
  final DateTime horaMarcado;
  final double latitud;
  final double longitud;
  final String? fotoUrl;

  factory Marcado.fromJson(Map<String, dynamic> json) => Marcado(
        id: json['id'] as int,
        empleadoId: json['empleado_id'] as int,
        empleadoNombre: json['empleado_nombre'] as String,
        sucursalNombre: json['sucursal_nombre'] as String?,
        fecha: json['fecha'] as String,
        horaMarcado: DateTime.parse(json['hora_marcado'] as String),
        latitud: (json['latitud'] as num).toDouble(),
        longitud: (json['longitud'] as num).toDouble(),
        fotoUrl: json['foto_url'] as String?,
      );
}
