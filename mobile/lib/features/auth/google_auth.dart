import 'package:google_sign_in/google_sign_in.dart';

import '../../core/api_config.dart';

/// Wrapper fino sobre `google_sign_in`: obtiene el `idToken` de Google, que
/// es lo que el backend espera en `POST /auth/google { credential }`
/// (verifica el token con `GOOGLE_CLIENT_ID`, no un access token).
class GoogleAuthResult {
  const GoogleAuthResult.success(this.idToken) : cancelled = false;
  const GoogleAuthResult.cancelled() : idToken = null, cancelled = true;

  final String? idToken;
  final bool cancelled;
}

final _googleSignIn = GoogleSignIn(serverClientId: googleServerClientId, scopes: const ['email']);

/// Lanza el selector de cuenta nativo. Devuelve `cancelled` si el usuario
/// cierra el selector sin elegir cuenta; lanza si Google Play Services
/// rechaza la solicitud (ej. falta el cliente OAuth "Android" en Google
/// Cloud Console — ver nota en `api_config.dart`).
Future<GoogleAuthResult> signInWithGoogle() async {
  final cuenta = await _googleSignIn.signIn();
  if (cuenta == null) return const GoogleAuthResult.cancelled();
  final auth = await cuenta.authentication;
  final idToken = auth.idToken;
  if (idToken == null) {
    throw StateError('Google no devolvio un id_token valido.');
  }
  return GoogleAuthResult.success(idToken);
}

Future<void> signOutGoogleSilently() async {
  try {
    await _googleSignIn.signOut();
  } catch (_) {
    // best-effort, no bloquea el logout local
  }
}
