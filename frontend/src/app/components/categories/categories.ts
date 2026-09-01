import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

interface Category {
  name: string;
  path: string;
  image: string;
}

@Component({
  selector: 'app-categories',
  imports: [RouterLink],
  templateUrl: './categories.html',
  styleUrl: './categories.scss',
})
export class Categories {
  protected readonly categories: Category[] = [
    { name: 'Poleras', path: '/poleras', image: '/img/categorias/poleras.jpg' },
    { name: 'Chaquetas', path: '/chaquetas', image: '/img/categorias/chaquetas.jpg' },
    { name: 'Pantalones', path: '/pantalones', image: '/img/categorias/pantalones.jpg' },
  ];
}
