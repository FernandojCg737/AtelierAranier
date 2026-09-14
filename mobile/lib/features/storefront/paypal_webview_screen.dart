import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

/// Estas dos URLs tienen que ser identicas a `PAYPAL_MOBILE_RETURN_URL` /
/// `PAYPAL_MOBILE_CANCEL_URL` en `ventas.py` -- son las que el backend le
/// pide a PayPal que use para redirigir despues de que el cliente aprueba o
/// cancela. Nunca se llegan a cargar de verdad: se intercepta la navegacion
/// justo antes.
const _kPaypalReturnUrl = 'https://atelieraranier-frontend.onrender.com/paypal-retorno';
const _kPaypalCancelUrl = 'https://atelieraranier-frontend.onrender.com/paypal-cancelado';

/// CU11, lado cliente: abre el link "approve" de una orden de PayPal (creado
/// con `crearOrdenPaypal`) dentro de un WebView -- el equivalente movil del
/// popup de botones que usa la web (que corre el JS SDK de PayPal, algo que
/// no tiene equivalente Dart). El cliente inicia sesion / paga con tarjeta
/// de credito de invitado ahi mismo; cuando termina, PayPal intenta navegar
/// a `return_url` o `cancel_url`, y esta pantalla lo detecta y se cierra
/// sola devolviendo el resultado -- esas URLs nunca llegan a cargar.
class PaypalWebviewScreen extends StatefulWidget {
  const PaypalWebviewScreen({super.key, required this.approveUrl});

  final String approveUrl;

  @override
  State<PaypalWebviewScreen> createState() => _PaypalWebviewScreenState();
}

class _PaypalWebviewScreenState extends State<PaypalWebviewScreen> {
  late final WebViewController _controller;
  bool _cargando = true;
  bool _resuelto = false;

  @override
  void initState() {
    super.initState();
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(
        NavigationDelegate(
          onPageStarted: (_) {
            if (mounted) setState(() => _cargando = true);
          },
          onPageFinished: (_) {
            if (mounted) setState(() => _cargando = false);
          },
          onNavigationRequest: (request) {
            if (request.url.startsWith(_kPaypalReturnUrl)) {
              _resolver(true);
              return NavigationDecision.prevent;
            }
            if (request.url.startsWith(_kPaypalCancelUrl)) {
              _resolver(false);
              return NavigationDecision.prevent;
            }
            return NavigationDecision.navigate;
          },
        ),
      )
      ..loadRequest(Uri.parse(widget.approveUrl));
  }

  void _resolver(bool aprobado) {
    if (_resuelto) return;
    _resuelto = true;
    Navigator.of(context).pop(aprobado);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('PAGAR CON PAYPAL'),
        leading: IconButton(icon: const Icon(Icons.close), onPressed: () => _resolver(false)),
      ),
      body: Stack(
        children: [
          WebViewWidget(controller: _controller),
          if (_cargando) const LinearProgressIndicator(),
        ],
      ),
    );
  }
}
