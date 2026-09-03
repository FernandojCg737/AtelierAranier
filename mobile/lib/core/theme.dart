import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Paleta y tipografia identicas a `frontend/src/styles.scss` y al
/// lenguaje visual del resto de la web (esquinas rectas, headings en
/// mayuscula, inputs con solo borde inferior).
class AppColors {
  AppColors._();

  static const brandDark = Color(0xFF203C40);
  static const brandCharcoal = Color(0xFF2B2B2B);
  static const brandWhite = Color(0xFFFFFFFF);

  static const grayText = Color(0xFF999999);
  static const grayTextDark = Color(0xFF777777);
  static const grayBorder = Color(0xFFCCCCCC);
  static const grayBorderLight = Color(0xFFEEEEEE);

  static const danger = Color(0xFFB3261E);
  static const dangerBg = Color(0xFFFDECEA);
  static const success = Color(0xFF2E7D32);
  static const successBg = Color(0xFFEAF6EC);
}

class AppTheme {
  AppTheme._();

  static ThemeData light() {
    final textTheme = GoogleFonts.interTextTheme();

    return ThemeData(
      useMaterial3: true,
      scaffoldBackgroundColor: AppColors.brandWhite,
      colorScheme: ColorScheme.fromSeed(
        seedColor: AppColors.brandDark,
        primary: AppColors.brandDark,
        surface: AppColors.brandWhite,
      ),
      textTheme: textTheme.apply(
        bodyColor: AppColors.brandCharcoal,
        displayColor: AppColors.brandDark,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: AppColors.brandWhite,
        foregroundColor: AppColors.brandDark,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: GoogleFonts.inter(
          color: AppColors.brandDark,
          fontWeight: FontWeight.w800,
          fontSize: 18,
          letterSpacing: 0.5,
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: false,
        contentPadding: const EdgeInsets.symmetric(vertical: 10),
        border: const UnderlineInputBorder(
          borderSide: BorderSide(color: AppColors.grayBorder),
        ),
        enabledBorder: const UnderlineInputBorder(
          borderSide: BorderSide(color: AppColors.grayBorder),
        ),
        focusedBorder: const UnderlineInputBorder(
          borderSide: BorderSide(color: AppColors.brandDark, width: 2),
        ),
        errorBorder: const UnderlineInputBorder(
          borderSide: BorderSide(color: AppColors.danger),
        ),
        labelStyle: const TextStyle(color: AppColors.grayText),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.brandDark,
          foregroundColor: AppColors.brandWhite,
          shape: const RoundedRectangleBorder(),
          padding: const EdgeInsets.symmetric(vertical: 15),
          textStyle: GoogleFonts.inter(
            fontWeight: FontWeight.w700,
            letterSpacing: 1,
            fontSize: 13,
          ),
          elevation: 0,
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.brandDark,
          side: const BorderSide(color: AppColors.grayBorder),
          shape: const RoundedRectangleBorder(),
          padding: const EdgeInsets.symmetric(vertical: 15),
          textStyle: GoogleFonts.inter(
            fontWeight: FontWeight.w700,
            letterSpacing: 1,
            fontSize: 13,
          ),
        ),
      ),
      cardTheme: const CardThemeData(
        color: AppColors.brandWhite,
        elevation: 0,
        shape: RoundedRectangleBorder(
          side: BorderSide(color: AppColors.grayBorderLight),
        ),
        margin: EdgeInsets.zero,
      ),
      dividerTheme: const DividerThemeData(color: AppColors.grayBorderLight),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: AppColors.brandWhite,
        selectedItemColor: AppColors.brandDark,
        unselectedItemColor: AppColors.grayText,
        type: BottomNavigationBarType.fixed,
        showUnselectedLabels: true,
      ),
    );
  }
}

/// Estilo "eyebrow" que se repite en toda la web: mayuscula, chico,
/// letter-spacing, gris, negrita.
class EyebrowText extends StatelessWidget {
  const EyebrowText(this.text, {super.key, this.color = AppColors.grayText});

  final String text;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Text(
      text.toUpperCase(),
      style: TextStyle(
        fontSize: 11,
        fontWeight: FontWeight.w700,
        letterSpacing: 1.2,
        color: color,
      ),
    );
  }
}
