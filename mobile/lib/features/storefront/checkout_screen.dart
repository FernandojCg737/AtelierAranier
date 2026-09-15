import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:webview_flutter/webview_flutter.dart';

import '../../core/api_client.dart';
import '../../core/api_config.dart';
import '../../core/secure_storage.dart';
import '../../core/theme.dart';
import '../../models/sucursal.dart';
import 'cart_provider.dart';
import 'catalogo_provider.dart';
import 'ventas_repository.dart';

enum _Estado { formulario, subiendo, listo }

enum _Metodo { paypal, qr }

/// CU11, lado cliente: checkout del carrito. Dos metodos de pago, igual que
/// la web: PayPal/tarjeta de credito y QR por transferencia (subis la foto
/// del comprobante, un cajero/encargado la revisa despues). PayPal se
/// muestra INLINE con los botones reales del JS SDK (misma pagina que usa
/// la web, embebida en un WebView chico -- ver `/paypal-embed` en el
/// backend), en vez de un boton propio que abra algo aparte: asi el
/// cliente ve, ahi mismo, tanto "Pagar con PayPal" como "Pagar con tarjeta
/// de debito/credito" (el SDK agrega este segundo boton solo cuando
/// corresponde), igual que en la web.
class CheckoutScreen extends ConsumerStatefulWidget {
  const CheckoutScreen({super.key});

  @override
  ConsumerState<CheckoutScreen> createState() => _CheckoutScreenState();
}

class _CheckoutScreenState extends ConsumerState<CheckoutScreen> {
  _Estado _estado = _Estado.formulario;
  _Metodo _metodo = _Metodo.paypal;
  _Metodo? _metodoUsado;
  SucursalPublica? _sucursal;
  XFile? _comprobante;
  String _error = '';
  int? _ventaId;
  WebViewController? _paypalController;
  // Arranca chico (solo los botones) y despues la pagina misma le avisa
  // (canal PaypalHeightChannel) cuanto mide de verdad cuando el formulario
  // de tarjeta se despliega -- asi no hace falta scroll DENTRO del WebView
  // (que quedaba atrapado por el scroll de la pagina de afuera y no dejaba
  // ver el boton de pagar, reportado por el usuario) porque el WebView
  // termina siendo tan alto como su contenido real, y es la pagina entera
  // del checkout la unica que scrollea.
  double _paypalWebviewHeight = 130;

  @override
  void initState() {
    super.initState();
    _iniciarPaypalWebview();
  }

  Future<void> _iniciarPaypalWebview() async {
    if (_paypalController != null) return;
    final token = await SecureStorage().readToken();
    if (token == null || !mounted) return;
    final controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setBackgroundColor(Colors.transparent)
      // El SDK de PayPal detecta que esta corriendo dentro de un WebView
      // embebido (no un navegador de verdad) por el user-agent por defecto
      // de Android WebView, y por prevencion de phishing degrada la
      // experiencia a un cartel generico "Pagar con PayPal" sin los
      // botones reales -- confirmado comparando contra Chrome normal en el
      // mismo emulador, donde se ve perfecto. Se le pone un user-agent de
      // Chrome de escritorio/movil normal (sin el marcador propio de
      // WebView) para que el SDK lo trate como un navegador real.
      ..setUserAgent(
        'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/133.0.6943.137 Mobile Safari/537.36',
      )
      ..addJavaScriptChannel('PaypalResultChannel', onMessageReceived: (msg) => _onPaypalMensaje(msg.message))
      ..addJavaScriptChannel('PaypalHeightChannel', onMessageReceived: (msg) => _onPaypalAltura(msg.message))
      ..setNavigationDelegate(NavigationDelegate(onPageFinished: _onPaypalNavego))
      ..loadRequest(Uri.parse(paypalEmbedUrl(token)));
    setState(() => _paypalController = controller);
  }

  // El boton "PayPal" (ver paypal_embed.py) navega, dentro de este mismo
  // WebView, al checkout real de PayPal (otro dominio, fuera de nuestro
  // control) -- esa pagina no tiene el script que le avisa a Flutter su
  // alto real (PaypalHeightChannel es nuestro, solo esta en /paypal-embed),
  // asi que el WebView se quedaba con el ultimo alto chico de ANTES de
  // navegar y el campo de correo del login de PayPal quedaba fuera de vista
  // (invisible, no realmente "no funcionaba" -- reportado por el usuario
  // como que no se podia escribir nada ahi). Mientras la pagina cargada sea
  // de otro dominio, se usa el alto completo de la pantalla a ciegas; al
  // volver a nuestro dominio (retorno/cancelado) el propio script de esas
  // paginas vuelve a reportar su alto real y se encoge de nuevo.
  void _onPaypalNavego(String url) {
    if (!mounted) return;
    final esNuestroDominio = Uri.parse(url).host == Uri.parse(paypalEmbedUrl('')).host;
    if (!esNuestroDominio) {
      setState(() => _paypalWebviewHeight = MediaQuery.of(context).size.height);
    }
  }

  void _onPaypalAltura(String raw) {
    final alto = double.tryParse(raw);
    if (alto == null || !mounted) return;
    // Clamps: nunca mas chico que los botones solos, ni mas grande que la
    // pantalla completa (por si algun campo de direccion la infla de mas).
    // El 0.75 anterior le cortaba el formulario justo antes del boton de
    // "Pagar" final (con direccion de facturacion completa, numero + venc.
    // + CSC + nombre/direccion/ciudad/estado/zip/telefono no entraban).
    final maxAlto = MediaQuery.of(context).size.height;
    final nuevo = alto.clamp(130.0, maxAlto).toDouble();
    if ((nuevo - _paypalWebviewHeight).abs() > 2) {
      setState(() => _paypalWebviewHeight = nuevo);
    }
  }

  void _onPaypalMensaje(String raw) {
    Map<String, dynamic> data;
    try {
      data = jsonDecode(raw) as Map<String, dynamic>;
    } catch (_) {
      return;
    }
    switch (data['status']) {
      case 'approved':
        final orderId = data['orderId'] as String?;
        if (orderId != null) _capturarPaypal(orderId);
      case 'error':
        if (mounted) setState(() => _error = (data['message'] as String?) ?? 'Ocurrio un error con PayPal.');
    }
  }

  Future<void> _capturarPaypal(String orderId) async {
    final sucursal = _sucursal;
    if (sucursal == null) return;

    setState(() {
      _estado = _Estado.subiendo;
      _error = '';
    });
    try {
      final venta = await ref.read(ventasRepositoryProvider).capturarOrdenPaypal(orderId: orderId, sucursalId: sucursal.id);
      await ref.read(cartProvider.notifier).cargar();
      if (mounted) {
        setState(() {
          _ventaId = venta.id;
          _metodoUsado = _Metodo.paypal;
          _estado = _Estado.listo;
        });
      }
    } catch (err) {
      if (mounted) {
        setState(() {
          _error = extractErrorMessage(err);
          _estado = _Estado.formulario;
        });
      }
    }
  }

  Future<void> _elegirFoto(ImageSource source) async {
    try {
      final archivo = await ImagePicker().pickImage(source: source, imageQuality: 85);
      if (archivo != null && mounted) setState(() => _comprobante = archivo);
    } catch (_) {
      // El usuario cancelo el picker o no dio permiso -- no hace falta avisar.
    }
  }

  Future<void> _confirmar() async {
    final sucursal = _sucursal;
    final comprobante = _comprobante;
    if (sucursal == null || comprobante == null) return;

    setState(() {
      _estado = _Estado.subiendo;
      _error = '';
    });
    try {
      final venta = await ref.read(ventasRepositoryProvider).checkoutQr(
            sucursalId: sucursal.id,
            filePath: comprobante.path,
            fileName: comprobante.name,
          );
      await ref.read(cartProvider.notifier).cargar();
      if (mounted) {
        setState(() {
          _ventaId = venta.id;
          _metodoUsado = _Metodo.qr;
          _estado = _Estado.listo;
        });
      }
    } catch (err) {
      if (mounted) {
        setState(() {
          _error = extractErrorMessage(err);
          _estado = _Estado.formulario;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final cart = ref.watch(cartProvider);
    final sucursalesAsync = ref.watch(sucursalesPublicasProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('FINALIZAR COMPRA')),
      body: SafeArea(
        child: _estado == _Estado.listo
            ? _exito()
            : cart.items.isEmpty
                ? const Center(child: Text('Tu carrito esta vacio.'))
                : sucursalesAsync.when(
                    loading: () => const Center(child: CircularProgressIndicator()),
                    error: (_, _) => const Center(child: Text('No pudimos cargar las sucursales.')),
                    data: (sucursales) {
                      _sucursal ??= sucursales.isEmpty ? null : sucursales.first;
                      return _formulario(cart.total, sucursales);
                    },
                  ),
      ),
    );
  }

  Widget _formulario(double total, List<SucursalPublica> sucursales) {
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        const Text('RESUMEN', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.grey)),
        const SizedBox(height: 8),
        Text('${total.toStringAsFixed(2)} Bs', style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: AppColors.brandDark)),
        const Divider(height: 32),

        if (_error.isNotEmpty) ...[
          Container(
            padding: const EdgeInsets.all(12),
            color: const Color(0xFFFDECEA),
            child: Text(_error, style: const TextStyle(color: Color(0xFFB3261E), fontSize: 13)),
          ),
          const SizedBox(height: 16),
        ],

        const Text('SUCURSAL DONDE RECOGES TU PEDIDO', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.grey)),
        const SizedBox(height: 6),
        DropdownButtonFormField<int>(
          initialValue: _sucursal?.id,
          isExpanded: true,
          items: sucursales
              .map((s) => DropdownMenuItem(value: s.id, child: Text('${s.nombre} · ${s.direccion}', overflow: TextOverflow.ellipsis)))
              .toList(),
          onChanged: (id) => setState(() => _sucursal = sucursales.firstWhere((s) => s.id == id)),
        ),
        const SizedBox(height: 24),

        const Text('METODO DE PAGO', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.grey)),
        const SizedBox(height: 6),
        Row(
          children: [
            Expanded(
              child: _MetodoOpcion(
                icon: Icons.account_balance_wallet_outlined,
                label: 'PayPal / Tarjeta',
                selected: _metodo == _Metodo.paypal,
                onTap: () {
                  setState(() => _metodo = _Metodo.paypal);
                  _iniciarPaypalWebview();
                },
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: _MetodoOpcion(
                icon: Icons.qr_code_2,
                label: 'QR (transferencia)',
                selected: _metodo == _Metodo.qr,
                onTap: () => setState(() => _metodo = _Metodo.qr),
              ),
            ),
          ],
        ),
        const SizedBox(height: 20),

        if (_metodo == _Metodo.paypal) ...[
          const Text(
            'Paga con tu cuenta de PayPal o con tarjeta de credito/debito como invitado.',
            style: TextStyle(fontSize: 12, color: AppColors.grayTextDark),
          ),
          const SizedBox(height: 12),
          if (_estado == _Estado.subiendo)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 24),
              child: Center(
                child: Column(
                  children: [
                    CircularProgressIndicator(),
                    SizedBox(height: 12),
                    Text('Confirmando tu pago...', style: TextStyle(fontSize: 12, color: AppColors.grayTextDark)),
                  ],
                ),
              ),
            )
          else if (_paypalController == null)
            const Padding(padding: EdgeInsets.symmetric(vertical: 24), child: Center(child: CircularProgressIndicator()))
          else
            // Alto dinamico (ver PaypalHeightChannel/_onPaypalAltura): con
            // un alto fijo, el boton "Debit or Credit Card" abria un
            // formulario (numero, vencimiento, CSC, direccion) mas alto que
            // el recuadro, y como el WebView esta anidado en esta misma
            // lista que scrollea, no habia forma de scrollear DENTRO del
            // WebView para llegar al boton de pagar -- quedaba atrapado.
            AnimatedContainer(
              duration: const Duration(milliseconds: 180),
              height: _paypalWebviewHeight,
              child: WebViewWidget(controller: _paypalController!),
            ),
        ] else ...[
          const Text(
            'Transferi a nuestro QR y despues subi la foto del comprobante. Un cajero lo revisa y confirma tu compra.',
            style: TextStyle(fontSize: 12, color: AppColors.grayTextDark),
          ),
          const SizedBox(height: 12),
          // El QR es de monto libre (ALTOKE/BancoSol no nos da forma de
          // generarlo con el monto ya puesto), asi que se lo repetimos bien
          // grande aca al lado para que no se equivoquen al escanearlo.
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(12),
            color: const Color(0xFFF7F7F5),
            child: Column(
              children: [
                const Text(
                  'MONTO EXACTO A TRANSFERIR',
                  style: TextStyle(fontSize: 10.5, fontWeight: FontWeight.w700, letterSpacing: 0.8, color: Colors.grey),
                ),
                const SizedBox(height: 2),
                Text(
                  '${total.toStringAsFixed(2)} Bs',
                  style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w800, color: AppColors.brandDark),
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          Image.asset('assets/qr-transferencia.png', height: 180, errorBuilder: (_, _, _) => const SizedBox.shrink()),
          const SizedBox(height: 6),
          const Text(
            'Este QR es de monto libre: escribi vos el monto de arriba al escanearlo. Si transferis un monto distinto, la revision de tu comprobante se va a demorar mas.',
            style: TextStyle(fontSize: 11, color: Color(0xFFB3261E)),
          ),
          const SizedBox(height: 20),

          const Text('COMPROBANTE DE TRANSFERENCIA', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.grey)),
          const SizedBox(height: 6),
          if (_comprobante != null) ...[
            Image.file(File(_comprobante!.path), height: 160, fit: BoxFit.cover),
            const SizedBox(height: 8),
          ],
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => _elegirFoto(ImageSource.camera),
                  icon: const Icon(Icons.photo_camera_outlined),
                  label: const Text('CAMARA'),
                  style: OutlinedButton.styleFrom(shape: const RoundedRectangleBorder()),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => _elegirFoto(ImageSource.gallery),
                  icon: const Icon(Icons.photo_library_outlined),
                  label: const Text('GALERIA'),
                  style: OutlinedButton.styleFrom(shape: const RoundedRectangleBorder()),
                ),
              ),
            ],
          ),
          const SizedBox(height: 28),
          ElevatedButton(
            onPressed: (_estado == _Estado.subiendo || _sucursal == null || _comprobante == null) ? null : _confirmar,
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.brandDark, minimumSize: const Size.fromHeight(48), shape: const RoundedRectangleBorder()),
            child: Text(_estado == _Estado.subiendo ? 'ENVIANDO...' : 'CONFIRMAR PAGO'),
          ),
        ],
      ],
    );
  }

  Widget _exito() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.check_circle_outline, size: 56, color: AppColors.brandDark),
            const SizedBox(height: 16),
            Text('Compra #$_ventaId registrada.', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            const SizedBox(height: 8),
            Text(
              _metodoUsado == _Metodo.paypal
                  ? 'Tu pago con PayPal quedo confirmado. Ya podes pasar a recoger tu pedido por la sucursal elegida.'
                  : 'Tu comprobante quedo en revision. Te avisamos apenas un cajero lo confirme.',
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.grey, fontSize: 13),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () => context.go('/'),
              style: ElevatedButton.styleFrom(backgroundColor: AppColors.brandDark, shape: const RoundedRectangleBorder()),
              child: const Text('VOLVER AL INICIO'),
            ),
          ],
        ),
      ),
    );
  }
}

class _MetodoOpcion extends StatelessWidget {
  const _MetodoOpcion({required this.icon, required this.label, required this.selected, required this.onTap});

  final IconData icon;
  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(border: Border.all(color: selected ? AppColors.brandDark : const Color(0xFFCCCCCC), width: selected ? 1.5 : 1)),
        child: Row(
          children: [
            Icon(icon, color: selected ? AppColors.brandDark : Colors.grey, size: 20),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                label,
                style: TextStyle(fontWeight: selected ? FontWeight.w700 : FontWeight.normal, fontSize: 13, color: selected ? AppColors.brandDark : Colors.black87),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
