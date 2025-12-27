# Referencia de API - Servicios del Módulo de Tienda y Mochila

## 📚 Índice

1. [ShopContainer](#shopcontainer)
2. [ShopService](#shopservice)
3. [InventoryService](#inventoryservice)

---

## ShopContainer

Contenedor de inyección de dependencias que gestiona todos los servicios del módulo de tienda con lazy loading para optimizar memoria.

### Instanciación

```python
from bot.shop.services.container import ShopContainer

container = ShopContainer(session, bot)
```

### Propiedades

- `shop` - Servicio de gestión de la tienda
- `inventory` - Servicio de gestión del inventario

---

## ShopService

Gestión completa de la tienda con operaciones CRUD para categorías y productos, validación de compras, procesamiento de transacciones y estadísticas de ventas.

### Métodos de Categorías

#### `create_category(name: str, description: str = None, emoji: str = "📦", order: int = 0) -> ItemCategory`
Crea una nueva categoría con validación de slug único.

```python
category = await container.shop.create_category(
    name="Cosméticos VIP",
    description="Items especiales para miembros VIP",
    emoji="👑",
    order=1
)
```

#### `get_category(category_id: int) -> Optional[ItemCategory]`
Obtiene categoría por ID.

```python
category = await container.shop.get_category(1)
```

#### `get_category_by_slug(slug: str) -> Optional[ItemCategory]`
Obtiene categoría por slug.

```python
category = await container.shop.get_category_by_slug("cosmeticos-vip")
```

#### `get_all_categories(active_only: bool = True) -> List[ItemCategory]`
Obtiene todas las categorías con posibilidad de filtrar por activas.

```python
categories = await container.shop.get_all_categories()
```

#### `update_category(category_id: int, **kwargs) -> Optional[ItemCategory]`
Actualiza campos de una categoría existente.

```python
updated = await container.shop.update_category(
    category_id=1,
    name="Nuevos Cosméticos",
    icon="✨"
)
```

#### `delete_category(category_id: int) -> bool`
Elimina una categoría si no tiene items activos asociados.

```python
deleted = await container.shop.delete_category(1)
```

### Métodos de Productos

#### `create_item(**kwargs) -> Tuple[bool, str, Optional[ShopItem]]`
Crea un nuevo producto con validación de categoría y precio.

```python
success, message, item = await container.shop.create_item(
    category_id=1,
    name="Avatar Dorado",
    description="Icono dorado para tu perfil",
    item_type=ItemType.COSMETIC,
    price_besitos=100,
    created_by=admin_user_id,
    rarity=ItemRarity.RARE,
    icon="👑"
)
```

#### `get_item(item_id: int) -> Optional[ShopItem]`
Obtiene producto por ID.

```python
item = await container.shop.get_item(1)
```

#### `get_item_by_slug(slug: str) -> Optional[ShopItem]`
Obtiene producto por slug.

```python
item = await container.shop.get_item_by_slug("avatar-dorado")
```

#### `get_items_by_category(category_id: int, active_only: bool = True) -> List[ShopItem]`
Obtiene productos de una categoría específica.

```python
items = await container.shop.get_items_by_category(1)
```

#### `get_all_items(active_only: bool = True, item_type: Optional[ItemType] = None, featured_only: bool = False) -> List[ShopItem]`
Obtiene todos los productos con filtros.

```python
rare_items = await container.shop.get_all_items(
    item_type=ItemType.RARE,
    active_only=True
)
```

#### `get_featured_items(limit: int = 5) -> List[ShopItem]`
Obtiene productos destacados.

```python
featured = await container.shop.get_featured_items(limit=10)
```

#### `update_item(item_id: int, **kwargs) -> Optional[ShopItem]`
Actualiza campos de un producto existente.

```python
updated = await container.shop.update_item(
    item_id=1,
    price_besitos=150,
    is_active=False
)
```

#### `delete_item(item_id: int) -> bool`
Elimina un producto (soft delete).

```python
deleted = await container.shop.delete_item(1)
```

#### `decrease_stock(item_id: int, quantity: int = 1) -> bool`
Disminuye el stock de un producto.

```python
success = await container.shop.decrease_stock(item_id=1, quantity=2)
```

### Métodos de Compras

#### `can_purchase(user_id: int, item_id: int, quantity: int = 1) -> Tuple[bool, str]`
Verifica si un usuario puede comprar un item y devuelve razón si no.

```python
can_buy, reason = await container.shop.can_purchase(user_id, item_id, 1)
if can_buy:
    success, message, purchase = await container.shop.purchase_item(user_id, item_id)
```

#### `purchase_item(user_id: int, item_id: int, quantity: int = 1) -> Tuple[bool, str, Optional[ItemPurchase]]`
Procesa la compra de un item y actualiza inventario.

```python
success, message, purchase = await container.shop.purchase_item(
    user_id=123456789,
    item_id=1,
    quantity=1
)

if success:
    print(f"Compra exitosa: {message}")
else:
    print(f"Error: {message}")
```

#### `refund_purchase(purchase_id: int, reason: str = None) -> Tuple[bool, str]`
Reembolsa una compra y actualiza inventario.

```python
success, message = await container.shop.refund_purchase(
    purchase_id=1,
    reason="Item defectuoso"
)
```

### Métodos de Estadísticas

#### `get_item_stats(item_id: int) -> Dict[str, Any]`
Obtiene estadísticas de un producto específico.

```python
stats = await container.shop.get_item_stats(1)
# {
#     "item_id": 1,
#     "name": "Nombre del Item",
#     "total_sold": 50,
#     "unique_owners": 30,
#     "total_revenue": 5000,
#     "current_stock": 10,
#     "is_active": True
# }
```

#### `get_shop_summary() -> Dict[str, Any]`
Obtiene resumen general de la tienda.

```python
summary = await container.shop.get_shop_summary()
# {
#     "total_items": 25,
#     "total_categories": 5,
#     "total_purchases": 150,
#     "total_revenue": 12500
# }
```

---

## InventoryService

Gestión del inventario personal del usuario (Mochila) con operaciones CRUD para items poseídos, verificación de posesión, uso de consumibles y equipado de cosméticos.

### Métodos de Inventario

#### `get_or_create_inventory(user_id: int) -> UserInventory`
Obtiene o crea el inventario del usuario.

```python
inventory = await container.inventory.get_or_create_inventory(123456789)
```

#### `get_inventory_items(user_id: int, item_type: Optional[ItemType] = None, equipped_only: bool = False) -> List[UserInventoryItem]`
Obtiene los items del inventario del usuario con filtros.

```python
# Todos los items
all_items = await container.inventory.get_inventory_items(123456789)

# Solo cosméticos
cosmetics = await container.inventory.get_inventory_items(
    user_id=123456789,
    item_type=ItemType.COSMETIC
)

# Solo equipados
equipped = await container.inventory.get_inventory_items(
    user_id=123456789,
    equipped_only=True
)
```

#### `get_inventory_summary(user_id: int) -> Dict[str, Any]`
Obtiene resumen del inventario del usuario.

```python
summary = await container.inventory.get_inventory_summary(123456789)
# {
#     "user_id": 123456789,
#     "total_items": 5,
#     "total_spent": 2500,
#     "favorite_item_id": 2,
#     "items_by_type": {
#         "cosmetic": {"count": 2, "quantity": 2},
#         "consumable": {"count": 1, "quantity": 5}
#     },
#     "equipped_count": 1,
#     "created_at": datetime_object
# }
```

### Métodos de Verificación de Posesión

#### `has_item(user_id: int, item_id: int) -> bool`
Verifica si el usuario posee un item específico.

```python
owns_item = await container.inventory.has_item(123456789, 1)
```

#### `has_item_by_slug(user_id: int, item_slug: str) -> bool`
Verifica si el usuario posee un item por slug.

```python
owns_item = await container.inventory.has_item_by_slug(123456789, "avatar-dorado")
```

#### `get_item_quantity(user_id: int, item_id: int) -> int`
Obtiene la cantidad de un item específico que posee el usuario.

```python
quantity = await container.inventory.get_item_quantity(123456789, 1)
```

#### `get_user_item(user_id: int, item_id: int) -> Optional[UserInventoryItem]`
Obtiene el registro de inventario de un item específico.

```python
inventory_item = await container.inventory.get_user_item(123456789, 1)
```

### Métodos de Uso de Items

#### `use_item(user_id: int, item_id: int, quantity: int = 1) -> Tuple[bool, str, Optional[Dict[str, Any]]]`
Usa un item consumible y aplica efecto.

```python
success, message, effect_data = await container.inventory.use_item(
    user_id=123456789,
    item_id=1,
    quantity=1
)

if success:
    print(f"Item usado: {message}")
    if effect_data["applied"]:
        print(f"Besitos otorgados: {effect_data['besitos_granted']}")
```

#### `equip_item(user_id: int, item_id: int) -> Tuple[bool, str]`
Equipa un item cosmético.

```python
success, message = await container.inventory.equip_item(123456789, 1)
```

#### `unequip_item(user_id: int, item_id: int) -> Tuple[bool, str]`
Desequipa un item cosmético.

```python
success, message = await container.inventory.unequip_item(123456789, 1)
```

### Métodos de Favoritos

#### `set_favorite_item(user_id: int, item_id: int) -> Tuple[bool, str]`
Establece un item como favorito.

```python
success, message = await container.inventory.set_favorite_item(123456789, 1)
```

#### `clear_favorite_item(user_id: int) -> bool`
Limpia el item favorito.

```python
success = await container.inventory.clear_favorite_item(123456789)
```

### Métodos de Items Narrativos

#### `get_narrative_items(user_id: int) -> List[UserInventoryItem]`
Obtiene los items narrativos del usuario.

```python
narrative_items = await container.inventory.get_narrative_items(123456789)
```

#### `get_unlocked_fragments(user_id: int) -> List[str]`
Obtiene lista de fragment_keys desbloqueados por items.

```python
unlocked_fragments = await container.inventory.get_unlocked_fragments(123456789)
```

#### `get_unlocked_chapters(user_id: int) -> List[str]`
Obtiene lista de slugs de capítulos desbloqueados por items.

```python
unlocked_chapters = await container.inventory.get_unlocked_chapters(123456789)
```

### Métodos de Otorgamiento

#### `grant_item(user_id: int, item_id: int, quantity: int = 1, obtained_via: str = "reward") -> Tuple[bool, str]`
Otorga un item a un usuario sin cobrar.

```python
success, message = await container.inventory.grant_item(
    user_id=123456789,
    item_id=1,
    quantity=3,
    obtained_via="mission_reward"
)
```

### Métodos de Historial

#### `get_purchase_history(user_id: int, limit: int = 10) -> List[ItemPurchase]`
Obtiene historial de compras del usuario.

```python
history = await container.inventory.get_purchase_history(123456789, limit=20)
```

---

**Última actualización:** 2025-12-27  
**Versión:** 1.0.0