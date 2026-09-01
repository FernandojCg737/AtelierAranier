import { Component, computed, signal } from '@angular/core';

interface PasoProceso {
  numero: string;
  titulo: string;
  descripcion: string;
  icono: 'lapiz' | 'globo' | 'escudo';
}

// TODO: reemplazar con el numero real de WhatsApp de la tienda si cambia.
const WHATSAPP_NUMERO = '59173766956';

@Component({
  selector: 'app-cotizaciones',
  imports: [],
  templateUrl: './cotizaciones.html',
  styleUrl: './cotizaciones.scss',
})
export class Cotizaciones {
  protected readonly pasos: PasoProceso[] = [
    {
      numero: '1',
      titulo: 'Solicitud',
      descripcion:
        'Completa el formulario con la prenda especifica, talla, color y tu presupuesto. Cuantos mas detalles, mejor.',
      icono: 'lapiz',
    },
    {
      numero: '2',
      titulo: 'Busqueda',
      descripcion:
        'Activamos nuestra red de proveedores y distribuidores para conseguir la prenda que buscas al mejor precio del mercado.',
      icono: 'globo',
    },
    {
      numero: '3',
      titulo: 'Verificacion y Entrega',
      descripcion:
        'Incluye verificacion de calidad. Entrega segura en Santa Cruz de la Sierra o a cualquier ciudad de Bolivia en 5-10 dias.',
      icono: 'escudo',
    },
  ];

  protected readonly nombre = signal('');
  protected readonly telefono = signal('');
  protected readonly producto = signal('');
  protected readonly detalles = signal('');
  protected readonly presupuesto = signal('');

  protected readonly whatsappUrl = computed(() => {
    const lineas = [
      'Hola, quiero solicitar una cotizacion:',
      this.nombre() ? `Nombre: ${this.nombre()}` : null,
      this.telefono() ? `Telefono: ${this.telefono()}` : null,
      this.producto() ? `Producto: ${this.producto()}` : null,
      this.detalles() ? `Detalles: ${this.detalles()}` : null,
      this.presupuesto() ? `Presupuesto maximo: Bs ${this.presupuesto()}` : null,
    ].filter((linea): linea is string => !!linea);

    const mensaje = lineas.join('\n');
    return `https://wa.me/${WHATSAPP_NUMERO}?text=${encodeURIComponent(mensaje)}`;
  });
}
