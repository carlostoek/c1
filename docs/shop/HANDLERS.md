# Documentación de Handlers - Módulo de Tienda y Mochila

## 📋 Descripción General

Los handlers del módulo de tienda y mochila gestionan las interacciones entre usuarios y el sistema de e-commerce del bot. Incluyen flujos para navegar la tienda, comprar productos, y gestionar el inventario personal (Mochila).

## 🏗️ Estructura de Handlers

```
bot/shop/handlers/
├── __init__.py                    # Exports y registro
├── admin/                         # Handlers de administración de productos
│   ├── __init__.py               # Exportación de routers de admin
│   └── shop_config.py            # Configuración de productos y categorías
└── user/                          # Handlers de usuario (tienda e inventario)
    ├── __init__.py               # Exportación de routers de usuario
    ├── shop.py                   # Experiencia de compra en la tienda
    └── backpack.py               # Gestión del inventario personal (mochila)
```

## 🎯 Patrones de Handler

### Patrón General

Todos los handlers del módulo de tienda siguen este patrón:

```python
from aiogram import Router
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from bot.shop.services.container import ShopContainer

router = Router()

@router.message(Command("tienda"))
async def shop_main_handler(
    message: Message,
    session: AsyncSession
) -> None:
    """
    Handler para el comando /tienda.
    
    Muestra el catálogo de productos y permite al usuario explorar
    y comprar productos con besitos.
    """
    try:
        # 1. Crear contenedor de servicios
        container = ShopContainer(session)
        
        # 2. Obtener información necesaria
        user_besitos = await _get_user_besitos(session, message.from_user.id)
        shop_summary = await container.shop.get_shop_summary()
        
        # 3. Construir mensaje
        text = _format_shop_main_message(user_besitos, shop_summary)
        
        # 4. Enviar con teclado
        await message.answer(
            text=text,
            reply_markup=_build_shop_main_keyboard(),
            parse_mode="HTML"
        )
    
    except Exception as e:
        logger.error(f"Error en shop_main_handler: {e}", exc_info=True)
        await message.answer("❌ Error accediendo a la tienda")
```

### Patrón de Callback de Producto

Para detalles y compras de productos:

```python
@router.callback_query(F.data.startswith("shop:item:"))
async def shop_item_detail_handler(
    callback: CallbackQuery,
    session: AsyncSession
) -> None:
    """
    Muestra detalles de un producto y permite comprar.
    
    Callback data: "shop:item:{item_id}"
    """
    try:
        user_id = callback.from_user.id
        item_id = int(callback.data.split(":")[2])
        
        container = ShopContainer(session)
        
        # Obtener producto
        item = await container.shop.get_item(item_id)
        if not item:
            await callback.answer("Producto no encontrado", show_alert=True)
            return
        
        # Verificar si puede comprar
        can_buy, reason = await container.shop.can_purchase(user_id, item_id)
        
        # Obtener besitos del usuario
        user_besitos = await _get_user_besitos(session, user_id)
        
        # Construir texto
        text = _format_item_detail_message(item, user_besitos, can_buy, reason)
        
        # Enviar mensaje con acción
        await callback.message.edit_text(
            text=text,
            reply_markup=_build_item_detail_keyboard(item_id, can_buy, reason),
            parse_mode="HTML"
        )
        
        await callback.answer()
    
    except Exception as e:
        logger.error(f"Error en shop_item_detail_handler: {e}", exc_info=True)
        await callback.answer("❌ Error cargando producto", show_alert=True)
```

## 📚 Handlers de Usuario

### `shop.py` - Experiencia de Compra en la Tienda

#### `/tienda` - Comando de Acceso a la Tienda

**Responsabilidad:** Permite al usuario navegar el catálogo de productos y realizar compras con besitos.

```python
@shop_user_router.message(Command("tienda", "shop", "store"))
async def cmd_shop(
    message: Message,
    session: AsyncSession
) -> None:
    """
    Handler para el comando /tienda.
    
    Muestra la tienda principal con categorías y productos
    disponibles para compra.
    """
    container = ShopContainer(session)
    user_id = message.from_user.id
    
    try:
        # Obtener resumen del shop
        summary = await container.shop.get_shop_summary()
        
        # Obtener saldo de besitos del usuario
        user_besitos = await _get_user_besitos(session, user_id)
        
        text = (
            "🏪 <b>Tienda de Artefactos</b>\n\n"
            f"💋 Tu saldo: <b>{user_besitos}</b> besitos\n\n"
            f"📦 {summary['total_items']} productos disponibles\n"
            f"📁 {summary['total_categories']} categorías\n\n"
            "Selecciona una categoría para explorar:"
        )
        
        await message.answer(
            text,
            reply_markup=_build_shop_main_keyboard(),
            parse_mode="HTML"
        )
    
    except Exception as e:
        logger.error(f"Error en cmd_shop: {e}", exc_info=True)
        await message.answer("Hubo un error al cargar la tienda.")
```

#### Callback `shop:item:{id}` - Detalles de Producto

**Responsabilidad:** Muestra información detallada de un producto y permite comprarlo.

```python
@shop_user_router.callback_query(F.data.startswith("shop:item:"))
async def callback_shop_item_detail(
    callback: CallbackQuery,
    session: AsyncSession
) -> None:
    """
    Muestra detalles de un producto específico.
    
    Callback format: shop:item:{item_id}
    """
    user_id = callback.from_user.id
    item_id = int(callback.data.split(":")[2])
    
    container = ShopContainer(session)
    
    try:
        item = await container.shop.get_item(item_id)
        if not item:
            await callback.answer("Producto no encontrado", show_alert=True)
            return
        
        # Verificar si puede comprar
        can_buy, reason = await container.shop.can_purchase(user_id, item_id)
        
        # Obtener saldo de usuario
        user_besitos = await _get_user_besitos(session, user_id)
        
        # Construir mensaje
        rarity = ItemRarity(item.rarity)
        item_type = ItemType(item.item_type)
        
        text = (
            f"{item.icon} <b>{item.name}</b>\n"
            f"{rarity.emoji} {rarity.display_name} | {item_type.emoji} {item_type.display_name}\n\n"
            f"{item.description}\n"
        )
        
        if item.long_description:
            text += f"\n{item.long_description}\n"
        
        text += (
            f"\n💋 <b>Precio:</b> {item.price_besitos} besitos\n"
            f"💰 <b>Tu saldo:</b> {user_besitos} besitos\n"
        )
        
        if item.stock is not None:
            text += f"📦 <b>Stock:</b> {item.stock} disponibles\n"
        
        if item.requires_vip:
            text += "⭐ <b>Requiere:</b> Suscripción VIP\n"
        
        # Verificar si ya lo tiene
        has_item = await container.inventory.has_item(user_id, item_id)
        if has_item:
            text += "\n✅ <i>Ya tienes este producto en tu mochila</i>"
        
        await callback.message.edit_text(
            text,
            reply_markup=_build_item_detail_keyboard(item_id, can_buy, reason),
            parse_mode="HTML"
        )
        
        await callback.answer()
    
    except Exception as e:
        logger.error(f"Error en callback_shop_item_detail: {e}", exc_info=True)
        await callback.answer("❌ Error cargando producto", show_alert=True)
```

#### Callback `shop:buy:{id}` - Procesamiento de Compra

**Responsabilidad:** Procesa la compra de un producto y actualiza inventario del usuario.

```python
@shop_user_router.callback_query(F.data.startswith("shop:buy:"))
async def callback_shop_buy(
    callback: CallbackQuery,
    session: AsyncSession
) -> None:
    """
    Procesa la compra de un producto.
    
    Callback format: shop:buy:{item_id}
    """
    user_id = callback.from_user.id
    item_id = int(callback.data.split(":")[2])
    
    container = ShopContainer(session)
    
    try:
        # Intentar comprar
        success, message, purchase = await container.shop.purchase_item(user_id, item_id)
        
        if success:
            item = await container.shop.get_item(item_id)
            text = (
                f"🎉 <b>¡Compra exitosa!</b>\n\n"
                f"{item.icon} {item.name} ha sido agregado a tu mochila.\n\n"
                f"💋 Pagaste: {purchase.price_paid} besitos"
            )
            buttons = [
                [InlineKeyboardButton(text="🎒 Ver Mochila", callback_data="backpack:main")],
                [InlineKeyboardButton(text="🏪 Seguir Comprando", callback_data="shop:main")],
            ]
        else:
            text = f"❌ <b>No se pudo completar la compra</b>\n\n{message}"
            buttons = [[InlineKeyboardButton(text="🔙 Volver", callback_data="shop:main")]]

        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="HTML"
        )
        
        await callback.answer()
    
    except Exception as e:
        logger.error(f"Error en callback_shop_buy: {e}", exc_info=True)
        await callback.answer("❌ Error procesando compra", show_alert=True)
```

### `backpack.py` - Gestión del Inventario Personal (Mochila)

#### `/mochila` - Comando de Acceso al Inventario

**Responsabilidad:** Muestra el inventario personal del usuario con sus items poseídos.

```python
@backpack_router.message(Command("mochila", "backpack", "inventory"))
async def cmd_backpack(
    message: Message,
    session: AsyncSession
) -> None:
    """
    Handler para /mochila - Muestra el inventario del usuario.
    
    Muestra los items poseídos por el usuario con opciones
    para usar consumibles y equipar cosméticos.
    """
    container = ShopContainer(session)
    user_id = message.from_user.id
    
    try:
        # Obtener resumen del inventario
        summary = await container.inventory.get_inventory_summary(user_id)
        
        text = (
            "🎒 <b>Tu Mochila</b>\n\n"
            f"📦 Items totales: <b>{summary['total_items']}</b>\n"
            f"💋 Total gastado: <b>{summary['total_spent']}</b> besitos\n"
        )
        
        # Mostrar distribución por tipo
        if summary['items_by_type']:
            text += "\n<b>Por categoría:</b>\n"
            type_emojis = {
                "narrative": "📜",
                "digital": "💾",
                "consumable": "🧪",
                "cosmetic": "✨",
            }
            for type_name, data in summary['items_by_type'].items():
                emoji = type_emojis.get(type_name, "📦")
                text += f"  {emoji} {data['count']} items ({data['quantity']} total)\n"

        if summary['equipped_count'] > 0:
            text += f"\n✅ {summary['equipped_count']} item(s) equipado(s)"

        text += "\n\nSelecciona una categoría para ver tus items:"

        await message.answer(
            text,
            reply_markup=_build_backpack_main_keyboard(),
            parse_mode="HTML"
        )
    
    except Exception as e:
        logger.error(f"Error en cmd_backpack: {e}", exc_info=True)
        await message.answer("Hubo un error al cargar tu mochila.")
```

#### Callback `backpack:item:{id}` - Detalle de Item del Inventario

**Responsabilidad:** Muestra información detallada de un item poseído y opciones de uso/equipo.

```python
@backpack_router.callback_query(F.data.startswith("backpack:item:"))
async def callback_backpack_item_detail(
    callback: CallbackQuery,
    session: AsyncSession
) -> None:
    """
    Muestra detalle de un item en el inventario.
    
    Callback format: backpack:item:{inventory_item_id}
    """
    container = ShopContainer(session)
    user_id = callback.from_user.id
    
    inv_item_id = int(callback.data.split(":")[2])
    
    try:
        # Obtener el registro de inventario
        from sqlalchemy import select
        from bot.shop.database.models import UserInventoryItem

        stmt = (
            select(UserInventoryItem)
            .options(selectinload(UserInventoryItem.item))
            .where(
                UserInventoryItem.id == inv_item_id,
                UserInventoryItem.user_id == user_id
            )
        )
        result = await session.execute(stmt)
        inv_item = result.scalar_one_or_none()

        if not inv_item:
            await callback.answer("Item no encontrado", show_alert=True)
            return

        item = inv_item.item
        rarity = ItemRarity(item.rarity) if item.rarity else ItemRarity.COMMON
        item_type = ItemType(item.item_type)

        text = (
            f"{item.icon} <b>{item.name}</b>\n"
            f"{rarity.emoji} {rarity.display_name} | {item_type.emoji} {item_type.display_name}\n\n"
            f"{item.description}\n"
        )

        if item.long_description:
            text += f"\n{item.long_description}\n"

        text += f"\n📦 <b>Cantidad:</b> {inv_item.quantity}\n"
        text += f"📅 <b>Obtenido:</b> {inv_item.obtained_at.strftime('%d/%m/%Y')}\n"
        text += f"🔑 <b>Vía:</b> {inv_item.obtained_via}\n"

        if inv_item.is_equipped:
            text += "\n✅ <b>Estado:</b> Equipado"

        if inv_item.is_used:
            text += f"\n🕐 <b>Usado:</b> {inv_item.used_at.strftime('%d/%m/%Y') if inv_item.used_at else 'Sí'}"

        await callback.message.edit_text(
            text,
            reply_markup=_build_item_actions_keyboard(inv_item),
            parse_mode="HTML"
        )
        
        await callback.answer()
    
    except Exception as e:
        logger.error(f"Error en callback_backpack_item_detail: {e}", exc_info=True)
        await callback.answer("❌ Error cargando detalle", show_alert=True)
```

#### Callback `backpack:use:{id}` - Uso de Item Consumible

**Responsabilidad:** Procesa el uso de un item consumible del inventario.

```python
@backpack_router.callback_query(F.data.startswith("backpack:use:"))
async def callback_use_item(
    callback: CallbackQuery,
    session: AsyncSession
) -> None:
    """
    Usa un item consumible del inventario.
    
    Callback format: backpack:use:{inventory_item_id}
    """
    container = ShopContainer(session)
    user_id = callback.from_user.id

    inv_item_id = int(callback.data.split(":")[2])

    try:
        # Obtener el item_id desde el registro de inventario
        from sqlalchemy import select
        from bot.shop.database.models import UserInventoryItem

        stmt = select(UserInventoryItem).where(
            UserInventoryItem.id == inv_item_id,
            UserInventoryItem.user_id == user_id
        )
        result = await session.execute(stmt)
        inv_item = result.scalar_one_or_none()

        if not inv_item:
            await callback.answer("Item no encontrado", show_alert=True)
            return

        # Usar el item
        success, message, effect_data = await container.inventory.use_item(
            user_id, inv_item.item_id
        )

        if success:
            text = f"✅ <b>¡Item usado!</b>\n\n{message}"
            if effect_data and effect_data.get("applied"):
                if "besitos_granted" in effect_data:
                    text += f"\n\n+{effect_data['besitos_granted']} besitos"
        else:
            text = f"❌ <b>Error</b>\n\n{message}"

        buttons = [[InlineKeyboardButton(text="🔙 Volver", callback_data="backpack:main")]]

        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="HTML"
        )
        
        await callback.answer()
    
    except Exception as e:
        logger.error(f"Error en callback_use_item: {e}", exc_info=True)
        await callback.answer("❌ Error usando item", show_alert=True)
```

## 🛠️ Handlers de Administración

### `admin/shop_config.py` - Configuración de Productos

#### `/admin_shop` - Panel de Administración de Tienda

**Responsabilidad:** Panel para administradores para crear, editar y gestionar productos en la tienda.

```python
@admin_router.message(Command("admin_shop"))
async def admin_shop_panel(
    message: Message,
    session: AsyncSession
) -> None:
    """
    Panel de administración para gestionar la tienda.
    
    Permite a los admins crear/editar categorías y productos.
    """
    user_id = message.from_user.id
    
    if not Config.is_admin(user_id):
        await message.answer("❌ No tienes permisos para gestionar la tienda.")
        return
    
    container = ShopContainer(session)
    
    try:
        # Obtener estadísticas
        summary = await container.shop.get_shop_summary()
        
        text = (
            "<b>🏢 PANEL ADMINISTRACIÓN TIENDA</b>\n\n"
            f"📦 Productos: {summary['total_items']}\n"
            f"📁 Categorías: {summary['total_categories']}\n"
            f"💰 Ventas totales: {summary['total_purchases']}\n"
            f"💸 Ingresos: {summary['total_revenue']} besitos\n\n"
            "<b>Acciones disponibles:</b>\n"
            "• /crear_categoria - Crear nueva categoría\n"
            "• /crear_producto - Crear nuevo producto\n"
            "• /editar_producto - Editar producto existente\n"
            "• /ver_productos - Listar productos existentes"
        )
        
        await message.answer(text, parse_mode="HTML")
    
    except Exception as e:
        logger.error(f"Error en admin_shop_panel: {e}", exc_info=True)
        await message.answer("Error cargando panel de administración.")
```

## 🔄 Flujos de Usuario Típicos

### Flujo de Compra
1. **Usuario:** Envia `/tienda`
2. **Bot:** Muestra categorías disponibles
3. **Usuario:** Selecciona categoría
4. **Bot:** Muestra productos en categoría
5. **Usuario:** Selecciona producto
6. **Bot:** Muestra detalles y opciones de compra
7. **Usuario:** Confirma compra
8. **Bot:** Verifica saldo y procesa compra
9. **Bot:** Actualiza inventario y confirma

### Flujo de Uso de Item
1. **Usuario:** Envia `/mochila`
2. **Bot:** Muestra categorías de items
3. **Usuario:** Selecciona tipo de items
4. **Bot:** Muestra items poseídos
5. **Usuario:** Selecciona item consumible
6. **Bot:** Procesa uso y aplica efecto
7. **Bot:** Actualiza inventario

### Flujo de Equipado de Cosmético
1. **Usuario:** Navega a `/mochila`
2. **Bot:** Muestra categorías
3. **Usuario:** Selecciona cosméticos
4. **Usuario:** Elige item
5. **Usuario:** Selecciona equipar
6. **Bot:** Marca como equipado
7. **Bot:** Confirma cambios

## 🛡️ Validaciones y Seguridad

### Validaciones de Compra
- Usuario tenga saldo suficiente
- Producto esté activo
- Stock disponible
- Límites por usuario
- Requisitos especiales (VIP)

### Prevención de Fraude
- Control de velocidad de compras
- Validaciones de seguridad
- Registro de actividades sospechosas
- Verificación de integridad de datos

---

**Última actualización:** 2025-12-27  
**Versión:** 1.0.0