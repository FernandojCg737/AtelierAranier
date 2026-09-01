import 'dart:io' show Platform;

/// URL base de la API de FastAPI según la plataforma de ejecución.
///
/// - Emulador Android: 10.0.2.2 apunta al localhost de la máquina host.
/// - iOS simulator / desktop / web: localhost funciona directo.
/// - Dispositivo físico: reemplazar por la IP de la máquina en la red local,
///   o por la URL pública una vez desplegado el backend (ej. en Render).
String get apiBaseUrl {
  if (Platform.isAndroid) {
    return 'http://10.0.2.2:8000/api/v1';
  }
  return 'http://localhost:8000/api/v1';
}
