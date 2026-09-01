import { Component, computed, input } from '@angular/core';

@Component({
  selector: 'app-whatsapp-cta',
  imports: [],
  templateUrl: './whatsapp-cta.html',
  styleUrl: './whatsapp-cta.scss',
})
export class WhatsappCta {
  readonly phoneNumber = input('59173766956');
  readonly message = input('Hola, estoy buscando una prenda y no encontre mi talla en el catalogo.');

  protected readonly whatsappUrl = computed(
    () => `https://wa.me/${this.phoneNumber()}?text=${encodeURIComponent(this.message())}`,
  );
}
