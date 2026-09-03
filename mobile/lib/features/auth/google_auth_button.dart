import 'package:flutter/material.dart';

import '../../core/theme.dart';

/// Boton "Continuar con Google" / "Registrarse con Google" — mismo estilo
/// (borde fino, sin relleno) que el resto de botones secundarios de la app.
class GoogleAuthButton extends StatelessWidget {
  const GoogleAuthButton({super.key, required this.label, required this.onPressed, this.loading = false});

  final String label;
  final VoidCallback? onPressed;
  final bool loading;

  @override
  Widget build(BuildContext context) {
    return OutlinedButton(
      onPressed: loading ? null : onPressed,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          if (loading)
            const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
          else
            const Text('G', style: TextStyle(fontWeight: FontWeight.w900, fontSize: 16, color: Color(0xFF4285F4))),
          const SizedBox(width: 10),
          Text(label),
        ],
      ),
    );
  }
}

/// Separador "o" entre el formulario y el boton de Google.
class OrDivider extends StatelessWidget {
  const OrDivider({super.key});

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.symmetric(vertical: 20),
      child: Row(
        children: [
          Expanded(child: Divider(color: AppColors.grayBorderLight)),
          Padding(padding: EdgeInsets.symmetric(horizontal: 12), child: Text('O', style: TextStyle(color: AppColors.grayText, fontSize: 12))),
          Expanded(child: Divider(color: AppColors.grayBorderLight)),
        ],
      ),
    );
  }
}
