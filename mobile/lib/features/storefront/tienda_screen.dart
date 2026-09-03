import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme.dart';
import '../../models/producto_publico.dart';
import 'catalogo_provider.dart';
import 'hero_widget.dart';

class TiendaScreen extends ConsumerStatefulWidget {
  const TiendaScreen({super.key});

  @override
  ConsumerState<TiendaScreen> createState() => _TiendaScreenState();
}

class _TiendaScreenState extends ConsumerState<TiendaScreen> {
  final _buscarCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();
  bool _scrolled = false;

  @override
  void initState() {
    super.initState();
    _scrollCtrl.addListener(_onScroll);
  }

  void _onScroll() {
    final scrolled = _scrollCtrl.offset > 40;
    if (scrolled != _scrolled) setState(() => _scrolled = scrolled);
  }

  @override
  void dispose() {
    _scrollCtrl.removeListener(_onScroll);
    _scrollCtrl.dispose();
    _buscarCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final productosAsync = ref.watch(productosPublicosProvider);
    final visibles = ref.watch(productosFiltradosProvider);
    final filtros = ref.watch(tiendaFiltrosProvider);
    final hayFiltrosActivos = filtros.categoria != null ||
        filtros.marcas.isNotEmpty ||
        filtros.sucursal != null ||
        filtros.temporada != null ||
        filtros.precioMin != null ||
        filtros.precioMax != null;

    return Stack(
      children: [
        CustomScrollView(
          controller: _scrollCtrl,
          slivers: [
            const SliverToBoxAdapter(
              child: HeroSection(
                videoAsset: 'assets/video/tienda-hero.mp4',
                eyebrow: '',
                title: 'CATALOGO',
                subtitle: 'Explora la coleccion completa. Todos nuestros productos disponibles en un solo lugar.',
                showCta: false,
                align: HeroAlign.center,
                size: HeroSize.half,
              ),
            ),
            productosAsync.when(
              loading: () => const SliverToBoxAdapter(
                child: Padding(padding: EdgeInsets.all(48), child: Center(child: CircularProgressIndicator())),
              ),
              error: (err, _) => const SliverToBoxAdapter(
                child: Padding(padding: EdgeInsets.all(24), child: Center(child: Text('No pudimos cargar el catalogo.'))),
              ),
              data: (_) {
                if (visibles.isEmpty) {
                  return const SliverToBoxAdapter(
                    child: Padding(
                      padding: EdgeInsets.all(24),
                      child: Center(child: Text('No encontramos productos con estos filtros.')),
                    ),
                  );
                }
                return SliverPadding(
                  padding: const EdgeInsets.all(16),
                  sliver: SliverGrid(
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      mainAxisSpacing: 14,
                      crossAxisSpacing: 14,
                      childAspectRatio: 0.62,
                    ),
                    delegate: SliverChildBuilderDelegate(
                      (context, i) => _TiendaCard(producto: visibles[i]),
                      childCount: visibles.length,
                    ),
                  ),
                );
              },
            ),
          ],
        ),
        Positioned(
          top: 0,
          left: 0,
          right: 0,
          child: _TiendaHeader(
            scrolled: _scrolled,
            buscarCtrl: _buscarCtrl,
            hayFiltrosActivos: hayFiltrosActivos,
            onBuscarChanged: (v) => ref.read(tiendaFiltrosProvider.notifier).setBusqueda(v),
            onFilterTap: () => _openFilters(context),
          ),
        ),
      ],
    );
  }

  void _openFilters(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (_) => const _FiltrosSheet(),
    );
  }
}

/// Encabezado flotante de la Tienda: transparente sobre el hero, blanco
/// solido apenas se hace scroll — igual que `.site-header.scrolled` en la
/// web (`header.scss`). El buscador y el icono de filtros permanecen
/// visibles en todo momento, solo cambia el color de fondo/texto.
class _TiendaHeader extends StatelessWidget {
  const _TiendaHeader({
    required this.scrolled,
    required this.buscarCtrl,
    required this.hayFiltrosActivos,
    required this.onBuscarChanged,
    required this.onFilterTap,
  });

  final bool scrolled;
  final TextEditingController buscarCtrl;
  final bool hayFiltrosActivos;
  final ValueChanged<String> onBuscarChanged;
  final VoidCallback onFilterTap;

  @override
  Widget build(BuildContext context) {
    final fg = scrolled ? AppColors.brandDark : Colors.white;
    final hint = scrolled ? AppColors.grayText : Colors.white.withValues(alpha: 0.7);
    final border = scrolled ? AppColors.grayBorder : Colors.white.withValues(alpha: 0.6);

    return AnimatedContainer(
      duration: const Duration(milliseconds: 220),
      curve: Curves.easeOut,
      color: scrolled ? AppColors.brandWhite : Colors.transparent,
      child: SafeArea(
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 6, 8, 6),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: buscarCtrl,
                  onChanged: onBuscarChanged,
                  style: TextStyle(color: fg),
                  cursorColor: fg,
                  decoration: InputDecoration(
                    hintText: 'Buscar por nombre o marca...',
                    hintStyle: TextStyle(color: hint),
                    prefixIcon: Icon(Icons.search, size: 20, color: fg),
                    enabledBorder: UnderlineInputBorder(borderSide: BorderSide(color: border)),
                    focusedBorder: UnderlineInputBorder(borderSide: BorderSide(color: fg, width: 2)),
                  ),
                ),
              ),
              IconButton(
                icon: Icon(
                  Icons.filter_list,
                  color: hayFiltrosActivos && scrolled ? AppColors.brandDark : fg,
                ),
                onPressed: onFilterTap,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _TiendaCard extends StatelessWidget {
  const _TiendaCard({required this.producto});
  final ProductoPublico producto;

  @override
  Widget build(BuildContext context) {
    final imagen = producto.imagenPrincipal;
    return GestureDetector(
      onTap: () => context.push('/producto/${producto.id}'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Container(
              width: double.infinity,
              decoration: BoxDecoration(border: Border.all(color: AppColors.grayBorderLight)),
              child: imagen != null
                  ? Image.network(imagen, fit: BoxFit.cover)
                  : const Icon(Icons.image_not_supported_outlined, color: AppColors.grayText),
            ),
          ),
          const SizedBox(height: 6),
          EyebrowText(producto.marcaNombre),
          Text(producto.nombre, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w700)),
          Text('${producto.precio.toStringAsFixed(0)} Bs', style: const TextStyle(fontWeight: FontWeight.w800, color: AppColors.brandDark)),
        ],
      ),
    );
  }
}

class _FiltrosSheet extends ConsumerWidget {
  const _FiltrosSheet();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final categorias = ref.watch(categoriasDisponiblesProvider);
    final marcas = ref.watch(marcasDisponiblesProvider);
    final sucursales = ref.watch(sucursalesPublicasProvider).valueOrNull ?? [];
    final temporadas = ref.watch(temporadasPublicasProvider).valueOrNull ?? [];
    final filtros = ref.watch(tiendaFiltrosProvider);
    final notifier = ref.read(tiendaFiltrosProvider.notifier);

    return DraggableScrollableSheet(
      initialChildSize: 0.85,
      expand: false,
      builder: (context, scrollController) {
        return SafeArea(
          child: ListView(
            controller: scrollController,
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('FILTROS', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
                  TextButton(onPressed: notifier.limpiarTodo, child: const Text('Limpiar')),
                ],
              ),
              const SizedBox(height: 8),
              const EyebrowText('Categoria'),
              Wrap(
                spacing: 8,
                children: [
                  ChoiceChip(
                    label: const Text('Todas'),
                    selected: filtros.categoria == null,
                    onSelected: (_) => notifier.setCategoria(null),
                  ),
                  for (final c in categorias)
                    ChoiceChip(
                      label: Text(c),
                      selected: filtros.categoria == c,
                      onSelected: (_) => notifier.setCategoria(c),
                    ),
                ],
              ),
              const SizedBox(height: 16),
              const EyebrowText('Marca'),
              Wrap(
                spacing: 8,
                children: [
                  for (final m in marcas)
                    FilterChip(
                      label: Text(m),
                      selected: filtros.marcas.contains(m),
                      onSelected: (_) => notifier.toggleMarca(m),
                    ),
                ],
              ),
              const SizedBox(height: 16),
              const EyebrowText('Sucursal'),
              Wrap(
                spacing: 8,
                children: [
                  ChoiceChip(
                    label: const Text('Todas'),
                    selected: filtros.sucursal == null,
                    onSelected: (_) => notifier.setSucursal(null),
                  ),
                  for (final s in sucursales)
                    ChoiceChip(
                      label: Text(s.nombre),
                      selected: filtros.sucursal == s.nombre,
                      onSelected: (_) => notifier.setSucursal(s.nombre),
                    ),
                ],
              ),
              const SizedBox(height: 16),
              const EyebrowText('Temporada'),
              Wrap(
                spacing: 8,
                children: [
                  ChoiceChip(
                    label: const Text('Todas'),
                    selected: filtros.temporada == null,
                    onSelected: (_) => notifier.setTemporada(null),
                  ),
                  for (final t in temporadas)
                    ChoiceChip(
                      label: Text(t.nombre),
                      selected: filtros.temporada == t.nombre,
                      onSelected: (_) => notifier.setTemporada(t.nombre),
                    ),
                ],
              ),
              const SizedBox(height: 24),
              ElevatedButton(onPressed: () => Navigator.pop(context), child: const Text('VER RESULTADOS')),
            ],
          ),
        );
      },
    );
  }
}
