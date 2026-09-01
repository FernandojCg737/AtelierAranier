import { Component } from '@angular/core';
import { Hero } from '../../components/hero/hero';
import { ProductGrid } from '../../components/product-grid/product-grid';
import { ShopFilters } from '../../components/shop-filters/shop-filters';

@Component({
  selector: 'app-tienda',
  imports: [Hero, ShopFilters, ProductGrid],
  templateUrl: './tienda.html',
  styleUrl: './tienda.scss',
})
export class Tienda {}
