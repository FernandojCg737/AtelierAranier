import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Igual a `services/cart.ts`: 100% local, no hay endpoint de carrito
/// todavia. Persiste en `shared_preferences` bajo la misma idea de clave
/// que usaba localStorage en la web.
class CartItem {
  const CartItem({
    required this.id,
    required this.name,
    this.brand,
    required this.price,
    required this.image,
    required this.quantity,
  });

  final String id;
  final String name;
  final String? brand;
  final double price;
  final String image;
  final int quantity;

  CartItem copyWith({int? quantity}) => CartItem(
    id: id,
    name: name,
    brand: brand,
    price: price,
    image: image,
    quantity: quantity ?? this.quantity,
  );

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'brand': brand,
    'price': price,
    'image': image,
    'quantity': quantity,
  };

  factory CartItem.fromJson(Map<String, dynamic> json) => CartItem(
    id: json['id'] as String,
    name: json['name'] as String,
    brand: json['brand'] as String?,
    price: (json['price'] as num).toDouble(),
    image: json['image'] as String,
    quantity: json['quantity'] as int,
  );
}

const _storageKey = 'atelieraranier_cart';

class CartNotifier extends StateNotifier<List<CartItem>> {
  CartNotifier() : super(const []) {
    _load();
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_storageKey);
    if (raw == null) return;
    final list = (jsonDecode(raw) as List<dynamic>)
        .map((e) => CartItem.fromJson(e as Map<String, dynamic>))
        .toList();
    state = list;
  }

  Future<void> _persist() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_storageKey, jsonEncode(state.map((e) => e.toJson()).toList()));
  }

  void addItem({required String id, required String name, String? brand, required double price, required String image, int quantity = 1}) {
    final existing = state.indexWhere((e) => e.id == id);
    if (existing == -1) {
      state = [...state, CartItem(id: id, name: name, brand: brand, price: price, image: image, quantity: quantity)];
    } else {
      state = [
        for (final item in state)
          if (item.id == id) item.copyWith(quantity: item.quantity + quantity) else item,
      ];
    }
    _persist();
  }

  void updateQuantity(String id, int quantity) {
    if (quantity <= 0) {
      removeItem(id);
      return;
    }
    state = [
      for (final item in state)
        if (item.id == id) item.copyWith(quantity: quantity) else item,
    ];
    _persist();
  }

  void removeItem(String id) {
    state = state.where((e) => e.id != id).toList();
    _persist();
  }

  void clear() {
    state = [];
    _persist();
  }
}

final cartProvider = StateNotifierProvider<CartNotifier, List<CartItem>>((ref) => CartNotifier());

final cartTotalItemsProvider = Provider<int>((ref) {
  final items = ref.watch(cartProvider);
  return items.fold(0, (sum, item) => sum + item.quantity);
});

final cartTotalPriceProvider = Provider<double>((ref) {
  final items = ref.watch(cartProvider);
  return items.fold(0.0, (sum, item) => sum + item.price * item.quantity);
});
