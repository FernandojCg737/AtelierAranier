// Smoke test: la app arranca y muestra la pantalla de Home sin tirar
// excepciones (el bootstrap de sesion corre contra el ApiClient real, asi
// que este test no depende de que el backend este levantado).

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile_app/main.dart';

void main() {
  testWidgets('La app arranca y muestra la barra de navegacion', (WidgetTester tester) async {
    await tester.pumpWidget(const ProviderScope(child: AtelierAranierApp()));
    await tester.pump();

    expect(find.byType(BottomNavigationBar), findsOneWidget);
  });
}
