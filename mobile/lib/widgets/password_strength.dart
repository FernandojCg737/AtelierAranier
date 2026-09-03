import 'package:flutter/material.dart';

import '../core/theme.dart';

/// Mismas 5 reglas que `validate_password_strength` en el backend / el
/// checklist de `utils/password.ts` en la web.
class PasswordRule {
  const PasswordRule(this.label, this.test);

  final String label;
  final bool Function(String) test;
}

final passwordRules = <PasswordRule>[
  PasswordRule('Minimo 8 caracteres', (p) => p.length >= 8),
  PasswordRule('Una mayuscula', (p) => p.contains(RegExp(r'[A-Z]'))),
  PasswordRule('Una minuscula', (p) => p.contains(RegExp(r'[a-z]'))),
  PasswordRule('Un numero', (p) => p.contains(RegExp(r'[0-9]'))),
  PasswordRule('Un caracter especial', (p) => p.contains(RegExp(r'[^\w\s]'))),
];

bool isPasswordValid(String password) => passwordRules.every((r) => r.test(password));

class PasswordStrengthChecklist extends StatelessWidget {
  const PasswordStrengthChecklist({super.key, required this.password});

  final String password;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (final rule in passwordRules)
          Padding(
            padding: const EdgeInsets.only(bottom: 4),
            child: Row(
              children: [
                Icon(
                  rule.test(password) ? Icons.check_circle : Icons.circle_outlined,
                  size: 16,
                  color: rule.test(password) ? AppColors.success : AppColors.grayText,
                ),
                const SizedBox(width: 8),
                Text(
                  rule.label,
                  style: TextStyle(
                    fontSize: 12,
                    color: rule.test(password) ? AppColors.success : AppColors.grayText,
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }
}
