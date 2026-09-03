import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:video_player/video_player.dart';

import '../../core/theme.dart';

/// Alineacion del contenido del hero, igual que `align` en `hero.ts`.
enum HeroAlign { left, center }

/// Alto del hero, igual que `size` en `hero.ts` (`full` = 100vh, `half` = 50vh).
enum HeroSize { full, half }

/// Replica generica de `components/hero/hero.ts` en la web: video de fondo en
/// loop y muteado, overlay oscuro en gradiente, eyebrow opcional + titulo en
/// mayuscula/italica/negrita + subtitulo, y CTAs opcionales hacia la tienda.
/// Se usa tanto en Home (video hero.mp4, alineado a la izquierda, con CTAs)
/// como en Tienda (video tienda-hero.mp4, centrado, sin CTAs, mitad de alto).
class HeroSection extends StatefulWidget {
  const HeroSection({
    super.key,
    this.videoAsset = 'assets/video/hero.mp4',
    this.eyebrow = 'LA TIENDA #1 DE ROPA PARA HOMBRES EN BOLIVIA',
    this.title = 'ESTILO QUE\nSE NOTA',
    this.subtitle = 'Prendas pensadas para el hombre que no pasa desapercibido.',
    this.showCta = true,
    this.align = HeroAlign.left,
    this.size = HeroSize.full,
  });

  final String videoAsset;
  final String eyebrow;
  final String title;
  final String subtitle;
  final bool showCta;
  final HeroAlign align;
  final HeroSize size;

  @override
  State<HeroSection> createState() => _HeroSectionState();
}

class _HeroSectionState extends State<HeroSection> {
  late VideoPlayerController _controller;
  bool _ready = false;

  @override
  void initState() {
    super.initState();
    _initVideo();
  }

  void _initVideo() {
    _controller = VideoPlayerController.asset(widget.videoAsset)
      ..setLooping(true)
      ..setVolume(0)
      ..initialize().then((_) {
        if (!mounted) return;
        setState(() => _ready = true);
        _controller.play();
      });
  }

  @override
  void didUpdateWidget(covariant HeroSection oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.videoAsset != widget.videoAsset) {
      _controller.dispose();
      _ready = false;
      _initVideo();
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final screenHeight = MediaQuery.of(context).size.height;
    final height = widget.size == HeroSize.full ? screenHeight * 0.85 : screenHeight * 0.5;
    final isCenter = widget.align == HeroAlign.center;

    return SizedBox(
      height: height,
      width: double.infinity,
      child: Stack(
        fit: StackFit.expand,
        children: [
          // Fondo solido mientras el video carga (mismo gradiente que usa
          // `.hero` en la web si el video no llega a reproducir).
          const DecoratedBox(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [AppColors.brandDark, Color(0xFF0F1E20)],
              ),
            ),
          ),
          if (_ready)
            FittedBox(
              fit: BoxFit.cover,
              child: SizedBox(
                width: _controller.value.size.width,
                height: _controller.value.size.height,
                child: VideoPlayer(_controller),
              ),
            ),
          // Overlay oscuro para que el texto blanco siempre sea legible.
          const DecoratedBox(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [Color(0x73000000), Color(0x59000000), Color(0x8C000000)],
                stops: [0, 0.4, 1],
              ),
            ),
          ),
          Padding(
            padding: EdgeInsets.fromLTRB(20, 20, 20, widget.showCta ? 140 : 20),
            child: Align(
              alignment: isCenter ? Alignment.center : Alignment.centerLeft,
              child: ConstrainedBox(
                constraints: BoxConstraints(maxWidth: isCenter ? 420 : 500),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: isCenter ? CrossAxisAlignment.center : CrossAxisAlignment.start,
                  children: [
                    if (widget.eyebrow.isNotEmpty) ...[
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
                        decoration: BoxDecoration(
                          border: Border.all(color: Colors.white.withValues(alpha: 0.5)),
                          color: Colors.black.withValues(alpha: 0.12),
                        ),
                        child: Text(
                          widget.eyebrow,
                          textAlign: isCenter ? TextAlign.center : TextAlign.left,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 1,
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                    ],
                    Text(
                      widget.title,
                      textAlign: isCenter ? TextAlign.center : TextAlign.left,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 40,
                        fontWeight: FontWeight.w800,
                        fontStyle: FontStyle.italic,
                        letterSpacing: -0.5,
                        height: 1.05,
                      ),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      widget.subtitle,
                      textAlign: isCenter ? TextAlign.center : TextAlign.left,
                      style: TextStyle(color: Colors.white.withValues(alpha: 0.9), fontSize: 14, height: 1.4),
                    ),
                  ],
                ),
              ),
            ),
          ),
          if (widget.showCta)
            Positioned(
              left: 20,
              right: 20,
              bottom: 32,
              child: Column(
                children: [
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(backgroundColor: const Color(0xCC080C0C)),
                      onPressed: () => context.go('/tienda'),
                      child: const Text('IR A TIENDA'),
                    ),
                  ),
                  const SizedBox(height: 3),
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton(
                      style: OutlinedButton.styleFrom(
                        side: BorderSide(color: Colors.white.withValues(alpha: 0.7)),
                        foregroundColor: Colors.white,
                      ),
                      onPressed: () => context.go('/tienda'),
                      child: const Text('EXPLORAR COLECCION'),
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}
