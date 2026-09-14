import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'features/auth/auth_provider.dart';
import 'features/storefront/cart_provider.dart';
import 'widgets/whatsapp_float_button.dart';

/// Shell con bottom nav para toda la parte publica (Home, Tienda, Carrito,
/// Cuenta) — equivalente al `Header` + `RouterOutlet` de la web para las
/// rutas sin `hideChrome`.
class RootShell extends ConsumerWidget {
  const RootShell({super.key, required this.navigationShell});

  final StatefulNavigationShell navigationShell;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final cartCount = ref.watch(cartTotalItemsProvider);
    final auth = ref.watch(authProvider);
    final esClienteConSesion = auth.usuario?.isCliente ?? false;

    return Scaffold(
      body: Stack(
        children: [
          navigationShell,
          // Equivalente al `app-whatsapp-float` que la web muestra en TODAS
          // las paginas -- a diferencia del chatbot (abajo a la derecha),
          // este va abajo a la izquierda (mismos lados que en la web) y no
          // requiere sesion, para que cualquier visitante pueda escribir.
          const Positioned(left: 16, bottom: 16, child: WhatsappFloatButton()),
        ],
      ),
      // CU19: burbuja flotante del chatbot -- equivalente al icono de la
      // web, solo para clientes con sesion iniciada (las conversaciones
      // quedan ligadas al cliente).
      floatingActionButton: esClienteConSesion
          ? FloatingActionButton(
              onPressed: () => context.push('/chatbot'),
              backgroundColor: const Color(0xFF203C40),
              child: const Icon(Icons.chat_bubble_outline, color: Colors.white),
            )
          : null,
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: navigationShell.currentIndex,
        onTap: (index) => navigationShell.goBranch(index, initialLocation: index == navigationShell.currentIndex),
        items: [
          const BottomNavigationBarItem(icon: Icon(Icons.home_outlined), activeIcon: Icon(Icons.home), label: 'Inicio'),
          const BottomNavigationBarItem(icon: Icon(Icons.storefront_outlined), activeIcon: Icon(Icons.storefront), label: 'Tienda'),
          BottomNavigationBarItem(
            icon: Badge(
              label: Text('$cartCount'),
              isLabelVisible: cartCount > 0,
              child: const Icon(Icons.shopping_bag_outlined),
            ),
            activeIcon: const Icon(Icons.shopping_bag),
            label: 'Carrito',
          ),
          BottomNavigationBarItem(
            icon: Icon(auth.isAuthenticated ? Icons.person : Icons.person_outline),
            label: auth.isAuthenticated ? 'Cuenta' : 'Ingresar',
          ),
        ],
      ),
    );
  }
}

/// Pantalla "Cuenta": si hay sesion redirige a Perfil, si no muestra
/// login/registro — resuelto por el router mismo (ver router.dart).
class CuentaTabRedirect extends ConsumerWidget {
  const CuentaTabRedirect({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (auth.isAuthenticated) {
        context.go('/perfil');
      } else {
        context.go('/login');
      }
    });
    return const Scaffold(body: Center(child: CircularProgressIndicator()));
  }
}
