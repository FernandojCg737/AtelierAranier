import { Component } from '@angular/core';
import { Categories } from '../../components/categories/categories';
import { Discounts } from '../../components/discounts/discounts';
import { Hero } from '../../components/hero/hero';
import { InstagramCta } from '../../components/instagram-cta/instagram-cta';
import { NewArrivals } from '../../components/new-arrivals/new-arrivals';
import { WhatsappCta } from '../../components/whatsapp-cta/whatsapp-cta';

@Component({
  selector: 'app-home',
  imports: [Hero, Categories, InstagramCta, NewArrivals, WhatsappCta, Discounts],
  templateUrl: './home.html',
  styleUrl: './home.scss',
})
export class Home {}
