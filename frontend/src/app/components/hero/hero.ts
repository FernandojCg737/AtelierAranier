import { AfterViewInit, Component, ElementRef, input, viewChild } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-hero',
  imports: [RouterLink],
  templateUrl: './hero.html',
  styleUrl: './hero.scss',
})
export class Hero implements AfterViewInit {
  readonly videoSrc = input('/video/hero.mp4');
  readonly posterSrc = input('/img/hero-poster.jpg');
  readonly eyebrow = input('LA TIENDA #1 DE ROPA PARA HOMBRES EN BOLIVIA');
  readonly title = input('ESTILO QUE SE NOTA');
  readonly subtitle = input('Prendas pensadas para el hombre que no pasa desapercibido.');
  readonly showCta = input(true);
  readonly align = input<'left' | 'center'>('left');
  readonly size = input<'full' | 'half'>('full');

  private readonly videoRef = viewChild<ElementRef<HTMLVideoElement>>('heroVideo');

  ngAfterViewInit(): void {
    const video = this.videoRef()?.nativeElement;
    if (!video) return;

    // No usamos el atributo HTML "autoplay": compite con esta llamada y el
    // navegador puede interrumpir una a la otra, dejando el video trabado en
    // pausa. Se controla 100% por codigo: forzamos muted como propiedad (no
    // solo atributo) porque algunos navegadores lo exigen justo antes de
    // play() para permitir el autoplay sin gesto del usuario.
    video.muted = true;
    video.play().catch(() => {
      // Si aun asi el navegador lo bloquea, no pasa nada visualmente: queda
      // el degradado de fondo del hero.
    });
  }
}
