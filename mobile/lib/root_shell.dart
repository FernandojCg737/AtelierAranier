import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'features/auth/auth_provider.dart';
import 'features/storefront/cart_provider.dart';
import 'widgets/whatsapp_float_button.dart';

/// Shell con bottom nav para toda la parte publica (Home, Tienda, Carrito,
/// Cuenta) — equivalente al `Header` + `RouterOutlet` de la web para las
/// rutas sin `hideChrome`.
class RootShell extends ConsumerStatefulWidget {
  const RootShell({super.key, required this.navigationShell});

  final StatefulNavigationShell navigationShell;

  @override
  ConsumerState<RootShell> createState() => _RootShellState();
}

class _RootShellState extends ConsumerState<RootShell> {
  // Igual que el signal `visible` de `whatsapp-float.ts`: arranca oculto y
  // se muestra apenas el usuario baja y el hero de Home sale del viewport
  // (en las demas pestañas, que no tienen hero, se ve siempre).
  bool _whatsappVisibleEnHome = false;

  @override
  Widget build(BuildContext context) {
    final cartCount = ref.watch(cartTotalItemsProvider);
    final auth = ref.watch(authProvider);
    final esClienteConSesion = auth.usuario?.isCliente ?? false;
    final enHome = widget.navigationShell.currentIndex == 0;
    final whatsappVisible = !enHome || _whatsappVisibleEnHome;

    return Scaffold(
      body: NotificationListener<ScrollNotification>(
        onNotification: (notification) {
          if (widget.navigationShell.currentIndex != 0) return false;
          // `HeroSize.full` (el que usa Home) mide 85% del alto de pantalla
          // -- ver `hero_widget.dart`. Pasado eso, el hero ya no se ve.
          final heroHeight = MediaQuery.of(context).size.height * 0.85;
          final pastHero = notification.metrics.pixels >= heroHeight;
          if (pastHero != _whatsappVisibleEnHome) {
            setState(() => _whatsappVisibleEnHome = pastHero);
          }
          return false;
        },
        child: Stack(
          children: [
            widget.navigationShell,
            // Equivalente al `app-whatsapp-float` que la web muestra en
            // TODAS las paginas: abajo a la DERECHA (el chatbot va a la
            // izquierda, mismos lados que en la web) y sin requerir sesion,
            // para que cualquier visitante pueda escribir.
            Positioned(
              right: 16,
              bottom: 16,
              child: IgnorePointer(
                ignoring: !whatsappVisible,
                child: AnimatedOpacity(
                  opacity: whatsappVisible ? 1 : 0,
                  duration: const Duration(milliseconds: 200),
                  child: const WhatsappFloatButton(),
                ),
              ),
            ),
          ],
        ),
      ),
      // CU19: burbuja flotante del chatbot -- equivalente al icono de la
      // web, solo para clientes con sesion iniciada (las conversaciones
      // quedan ligadas al cliente). Va a la izquierda (mismo lado que en la
      // web), para no pisarse con el de WhatsApp.
      floatingActionButton: esClienteConSesion
          ? FloatingActionButton(
              onPressed: () => context.push('/chatbot'),
              backgroundColor: const Color(0xFF203C40),
              child: const Icon(Icons.chat_bubble_outline, color: Colors.white),
            )
          : null,
      floatingActionButtonLocation: FloatingActionButtonLocation.startFloat,
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: widget.navigationShell.currentIndex,
        onTap: (index) =>
            widget.navigationShell.goBranch(index, initialLocation: index == widget.navigationShell.currentIndex),
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
