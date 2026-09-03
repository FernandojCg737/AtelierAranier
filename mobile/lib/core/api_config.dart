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

/// URL base del frontend Angular. Algunas imagenes de producto (las que
/// vienen de los assets estaticos del frontend, ej. "/img/productos/x.jpg")
/// son rutas RELATIVAS: en un navegador se resuelven solas contra el
/// dominio de la pagina, pero una app nativa no tiene "origen" propio y
/// necesita la URL absoluta. Ver `resolveImageUrl`.
String get webAssetsBaseUrl {
  if (Platform.isAndroid) {
    return 'http://10.0.2.2:4200';
  }
  return 'http://localhost:4200';
}

/// Completa una URL de imagen relativa con `webAssetsBaseUrl`. Las URLs
/// absolutas (las que suben via CU05 a Supabase Storage) quedan intactas.
String resolveImageUrl(String url) {
  if (url.startsWith('http://') || url.startsWith('https://')) return url;
  return '$webAssetsBaseUrl$url';
}

/// Mismo Client ID "web" que usa el backend (`GOOGLE_CLIENT_ID` en
/// `backend/.env`) para validar el `id_token` de Google
/// (`id_token.verify_oauth2_token(..., audience=GOOGLE_CLIENT_ID)`). En
/// `google_sign_in` este valor va en `serverClientId`: hace que el token
/// que recibe la app tenga como `aud` este client id (no uno especifico de
/// Android), que es justo lo que el backend espera.
///
/// Para que el login con Google funcione en el emulador/dispositivo hace
/// falta, ademas, un cliente OAuth de tipo "Android" dado de alta en el
/// mismo proyecto de Google Cloud (paquete `com.atelieraranier.mobile_app`
/// + huella SHA-1 del keystore de debug/release) — sin eso Google devuelve
/// error 10 (DEVELOPER_ERROR) aunque el codigo este bien.
const googleServerClientId = '764852849297-30etrotk7lo3inebf4kk7j5pssov58vq.apps.googleusercontent.com';
