import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:url_launcher/url_launcher.dart';

/// Boton flotante de WhatsApp, equivalente al `app-whatsapp-float` que la
/// web muestra en TODAS las paginas (`app.html`), a diferencia de la
/// burbuja del chatbot de IA que solo se ve con sesion de cliente iniciada
/// -- este es para cualquiera, incluso un visitante sin cuenta.
class WhatsappFloatButton extends StatelessWidget {
  const WhatsappFloatButton({super.key});

  // Mismo numero y mensaje por defecto que `whatsapp-float.ts` en la web.
  static const _phoneNumber = '59173766956';
  static const _mensaje = 'Hola, tengo una consulta sobre un producto.';

  Future<void> _abrirWhatsapp() async {
    final uri = Uri.parse('https://wa.me/$_phoneNumber?text=${Uri.encodeComponent(_mensaje)}');
    await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  @override
  Widget build(BuildContext context) {
    return Material(
      color: const Color(0xFF25D366),
      shape: const CircleBorder(),
      elevation: 4,
      child: InkWell(
        customBorder: const CircleBorder(),
        onTap: _abrirWhatsapp,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: SizedBox(
            width: 26,
            height: 26,
            child: SvgPicture.asset('assets/whatsapp.svg', semanticsLabel: 'Chatear por WhatsApp'),
          ),
        ),
      ),
    );
  }
}
