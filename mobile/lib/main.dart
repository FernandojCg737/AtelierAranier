import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/theme.dart';
import 'features/auth/auth_provider.dart';
import 'router.dart';

void main() {
  runApp(const ProviderScope(child: AtelierAranierApp()));
}

class AtelierAranierApp extends ConsumerStatefulWidget {
  const AtelierAranierApp({super.key});

  @override
  ConsumerState<AtelierAranierApp> createState() => _AtelierAranierAppState();
}

class _AtelierAranierAppState extends ConsumerState<AtelierAranierApp> {
  final _messengerKey = GlobalKey<ScaffoldMessengerState>();

  @override
  void initState() {
    super.initState();

    // El interceptor de Dio (api_client.dart) no puede llamar a authProvider
    // directamente sin crear un ciclo de providers, asi que escribe aca; este
    // listener hace el logout forzado real.
    ref.listenManual(unauthorizedEventProvider, (previous, next) {
      if (next != null) {
        ref.read(authProvider.notifier).forceLogout(next);
        ref.read(unauthorizedEventProvider.notifier).state = null;
      }
    });

    // Muestra el mensaje de sesion vencida / cerrada en otro dispositivo,
    // igual que el banner de `sessionMessage` en la web.
    ref.listenManual(authProvider, (previous, next) {
      final message = next.sessionMessage;
      if (message != null && message != previous?.sessionMessage) {
        _messengerKey.currentState?.showSnackBar(
          SnackBar(content: Text(message), backgroundColor: AppColors.danger),
        );
        ref.read(authProvider.notifier).dismissSessionMessage();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final router = ref.watch(routerProvider);

    return MaterialApp.router(
      title: 'Atelier Aranier',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      routerConfig: router,
      scaffoldMessengerKey: _messengerKey,
    );
  }
}
