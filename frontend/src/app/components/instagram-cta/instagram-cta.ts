import { Component, input } from '@angular/core';

@Component({
  selector: 'app-instagram-cta',
  imports: [],
  templateUrl: './instagram-cta.html',
  styleUrl: './instagram-cta.scss',
})
export class InstagramCta {
  readonly instagramUrl = input('https://instagram.com/');
}
