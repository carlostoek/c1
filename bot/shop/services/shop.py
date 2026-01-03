"""
Servicio de gestión de la Tienda.

Responsabilidades:
- CRUD de categorías y productos
- Validación de compras
- Procesamiento de transacciones
- Estadísticas de ventas
"""

from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime, UTC
import json
import logging
import re

from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from bot.shop.database.models import (
    ItemCategory,
    ShopItem,
    UserInventory,
    UserInventoryItem,
    ItemPurchase,
)
from bot.shop.database.enums import (
    ItemType,
    ItemRarity,
    PurchaseStatus,
)

logger = logging.getLogger(__name__)


def slugify(text: str) -> str:
    """Convierte texto a slug URL-friendly."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text


class ShopService:
    """Servicio de gestión de la Tienda."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ========================================
    # CATEGORÍAS
    # ========================================

    async def create_category(
        self,
        name: str,
        description: Optional[str] = None,
        emoji: str = "📦",
        order: int = 0
    ) -> ItemCategory:
        """
        Crea una nueva categoría.

        Args:
            name: Nombre de la categoría
            description: Descripción opcional
            emoji: Emoji representativo
            order: Orden de visualización

        Returns:
            ItemCategory creada
        """
        slug = slugify(name)

        # Verificar slug único
        existing = await self.get_category_by_slug(slug)
        if existing:
            # Agregar sufijo numérico
            count = await self.session.execute(
                select(func.count()).select_from(ItemCategory)
                .where(ItemCategory.slug.like(f"{slug}%"))
            )
            slug = f"{slug}-{count.scalar() + 1}"

        category = ItemCategory(
            name=name,
            slug=slug,
            description=description,
            emoji=emoji,
            order=order,
            is_active=True
        )
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)

        logger.info(f"Created category: {name} (slug: {slug})")
        return category

    async def get_category(self, category_id: int) -> Optional[ItemCategory]:
        """Obtiene categoría por ID."""
        return await self.session.get(ItemCategory, category_id)

    async def get_category_by_slug(self, slug: str) -> Optional[ItemCategory]:
        """Obtiene categoría por slug."""
        stmt = select(ItemCategory).where(ItemCategory.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_categories(
        self,
        active_only: bool = True
    ) -> List[ItemCategory]:
        """
        Obtiene todas las categorías.

        Args:
            active_only: Si True, solo retorna categorías activas

        Returns:
            Lista de categorías ordenadas
        """
        stmt = select(ItemCategory).order_by(ItemCategory.order)
        if active_only:
            stmt = stmt.where(ItemCategory.is_active == True)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_category(
        self,
        category_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        emoji: Optional[str] = None,
        order: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> Optional[ItemCategory]:
        """Actualiza una categoría."""
        category = await self.get_category(category_id)
        if not category:
            return None

        if name is not None:
            category.name = name
        if description is not None:
            category.description = description
        if emoji is not None:
            category.emoji = emoji
        if order is not None:
            category.order = order
        if is_active is not None:
            category.is_active = is_active

        await self.session.commit()
        await self.session.refresh(category)

        logger.info(f"Updated category {category_id}: {category.name}")
        return category

    async def delete_category(self, category_id: int) -> bool:
        """
        Elimina una categoría (soft delete).

        Returns:
            True si se eliminó correctamente
        """
        category = await self.get_category(category_id)
        if not category:
            return False

        # Verificar que no tenga items activos
        item_count = await self.session.execute(
            select(func.count()).select_from(ShopItem)
            .where(ShopItem.category_id == category_id, ShopItem.is_active == True)
        )
        if item_count.scalar() > 0:
            logger.warning(f"Cannot delete category {category_id}: has active items")
            return False

        category.is_active = False
        await self.session.commit()

        logger.info(f"Deleted category {category_id}")
        return True

    # ========================================
    # PRODUCTOS
    # ========================================

    async def create_item(
        self,
        category_id: int,
        name: str,
        description: str,
        item_type: ItemType,
        price_besitos: int,
        created_by: int,
        long_description: Optional[str] = None,
        rarity: ItemRarity = ItemRarity.COMMON,
        icon: str = "📦",
        image_file_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        stock: Optional[int] = None,
        max_per_user: Optional[int] = None,
        requires_vip: bool = False,
        is_featured: bool = False,
        order: int = 0
    ) -> Tuple[bool, str, Optional[ShopItem]]:
        """
        Crea un nuevo producto.

        Args:
            category_id: ID de la categoría
            name: Nombre del producto
            description: Descripción corta
            item_type: Tipo de item
            price_besitos: Precio en besitos
            created_by: ID del admin que lo crea
            ... (otros parámetros opcionales)

        Returns:
            (success, message, item)
        """
        # Validar categoría
        category = await self.get_category(category_id)
        if not category:
            return False, "Categoría no encontrada", None

        # Validar precio
        if price_besitos < 0:
            return False, "El precio no puede ser negativo", None

        # Generar slug
        slug = slugify(name)
        existing = await self.get_item_by_slug(slug)
        if existing:
            count = await self.session.execute(
                select(func.count()).select_from(ShopItem)
                .where(ShopItem.slug.like(f"{slug}%"))
            )
            slug = f"{slug}-{count.scalar() + 1}"

        item = ShopItem(
            category_id=category_id,
            name=name,
            slug=slug,
            description=description,
            long_description=long_description,
            item_type=item_type.value,
            rarity=rarity.value,
            price_besitos=price_besitos,
            icon=icon,
            image_file_id=image_file_id,
            item_metadata=json.dumps(metadata) if metadata else None,
            stock=stock,
            max_per_user=max_per_user,
            requires_vip=requires_vip,
            is_featured=is_featured,
            is_active=True,
            order=order,
            created_by=created_by
        )
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)

        logger.info(f"Created item: {name} (slug: {slug}, price: {price_besitos})")
        return True, f"Producto '{name}' creado exitosamente", item

    async def get_item(self, item_id: int) -> Optional[ShopItem]:
        """Obtiene producto por ID."""
        return await self.session.get(ShopItem, item_id)

    async def get_item_by_slug(self, slug: str) -> Optional[ShopItem]:
        """Obtiene producto por slug."""
        stmt = select(ShopItem).where(ShopItem.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_items_by_category(
        self,
        category_id: int,
        active_only: bool = True
    ) -> List[ShopItem]:
        """Obtiene productos de una categoría."""
        stmt = (
            select(ShopItem)
            .where(ShopItem.category_id == category_id)
            .order_by(ShopItem.order, ShopItem.name)
        )
        if active_only:
            stmt = stmt.where(ShopItem.is_active == True)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_items(
        self,
        active_only: bool = True,
        item_type: Optional[ItemType] = None,
        featured_only: bool = False
    ) -> List[ShopItem]:
        """
        Obtiene todos los productos con filtros.

        Args:
            active_only: Solo productos activos
            item_type: Filtrar por tipo
            featured_only: Solo productos destacados

        Returns:
            Lista de productos
        """
        stmt = select(ShopItem).order_by(ShopItem.order, ShopItem.name)

        if active_only:
            stmt = stmt.where(ShopItem.is_active == True)
        if item_type:
            stmt = stmt.where(ShopItem.item_type == item_type.value)
        if featured_only:
            stmt = stmt.where(ShopItem.is_featured == True)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_featured_items(self, limit: int = 5) -> List[ShopItem]:
        """Obtiene productos destacados."""
        stmt = (
            select(ShopItem)
            .where(ShopItem.is_active == True, ShopItem.is_featured == True)
            .order_by(ShopItem.order)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_item(
        self,
        item_id: int,
        **kwargs
    ) -> Optional[ShopItem]:
        """
        Actualiza un producto.

        Args:
            item_id: ID del producto
            **kwargs: Campos a actualizar

        Returns:
            ShopItem actualizado o None
        """
        item = await self.get_item(item_id)
        if not item:
            return None

        # Campos permitidos
        allowed_fields = {
            'name', 'description', 'long_description', 'price_besitos',
            'icon', 'image_file_id', 'stock', 'max_per_user',
            'requires_vip', 'is_featured', 'is_active', 'order', 'rarity'
        }

        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                if field == 'rarity' and isinstance(value, ItemRarity):
                    value = value.value
                setattr(item, field, value)

        # Manejar metadata especialmente
        if 'metadata' in kwargs:
            item.item_metadata = json.dumps(kwargs['metadata']) if kwargs['metadata'] else None

        await self.session.commit()
        await self.session.refresh(item)

        logger.info(f"Updated item {item_id}: {item.name}")
        return item

    async def delete_item(self, item_id: int) -> bool:
        """Elimina un producto (soft delete)."""
        item = await self.get_item(item_id)
        if not item:
            return False

        item.is_active = False
        await self.session.commit()

        logger.info(f"Deleted item {item_id}")
        return True

    async def decrease_stock(self, item_id: int, quantity: int = 1) -> bool:
        """
        Disminuye el stock de un producto.

        Returns:
            True si había stock suficiente y se decrementó
        """
        item = await self.get_item(item_id)
        if not item or item.stock is None:
            return True  # Stock ilimitado

        if item.stock < quantity:
            return False

        item.stock -= quantity
        await self.session.commit()
        return True

    # ========================================
    # COMPRAS
    # ========================================

    async def can_purchase(
        self,
        user_id: int,
        item_id: int,
        quantity: int = 1
    ) -> Tuple[bool, str]:
        """
        Verifica si un usuario puede comprar un item.

        Args:
            user_id: ID del usuario
            item_id: ID del item
            quantity: Cantidad a comprar

        Returns:
            (can_purchase, reason)
        """
        item = await self.get_item(item_id)
        if not item:
            return False, "Producto no encontrado"

        if not item.is_active:
            return False, "Producto no disponible"

        # Verificar stock
        if item.stock is not None and item.stock < quantity:
            return False, f"Stock insuficiente (disponible: {item.stock})"

        # Verificar máximo por usuario
        if item.max_per_user is not None:
            owned = await self._get_user_item_quantity(user_id, item_id)
            if owned + quantity > item.max_per_user:
                return False, f"Máximo {item.max_per_user} por usuario (tienes {owned})"

        # Verificar VIP si es requerido
        if item.requires_vip:
            is_vip = await self._check_vip_status(user_id)
            if not is_vip:
                return False, "Este producto requiere ser VIP"

        # Verificar besitos
        user_besitos = await self._get_user_besitos(user_id)
        total_price = item.price_besitos * quantity
        if user_besitos < total_price:
            return False, f"Besitos insuficientes (necesitas {total_price}, tienes {user_besitos})"

        return True, "OK"

    async def purchase_item(
        self,
        user_id: int,
        item_id: int,
        quantity: int = 1
    ) -> Tuple[bool, str, Optional[ItemPurchase]]:
        """
        Procesa la compra de un item.

        Args:
            user_id: ID del usuario
            item_id: ID del item
            quantity: Cantidad a comprar

        Returns:
            (success, message, purchase)
        """
        # Verificar si puede comprar
        can_buy, reason = await self.can_purchase(user_id, item_id, quantity)
        if not can_buy:
            return False, reason, None

        item = await self.get_item(item_id)
        total_price = item.price_besitos * quantity

        # Deducir besitos
        from bot.gamification.services.besito import BesitoService
        from bot.gamification.database.enums import TransactionType

        besito_service = BesitoService(self.session)
        success, msg, _ = await besito_service.deduct_besitos(
            user_id=user_id,
            amount=total_price,
            transaction_type=TransactionType.PURCHASE,
            description=f"Compra: {item.name} x{quantity}"
        )

        if not success:
            return False, msg, None

        # Decrementar stock
        if item.stock is not None:
            await self.decrease_stock(item_id, quantity)

        # Crear registro de compra
        purchase = ItemPurchase(
            user_id=user_id,
            item_id=item_id,
            quantity=quantity,
            price_paid=total_price,
            status=PurchaseStatus.COMPLETED.value
        )
        self.session.add(purchase)

        # Agregar al inventario
        await self._add_to_inventory(user_id, item_id, quantity, "purchase")

        await self.session.commit()
        await self.session.refresh(purchase)

        logger.info(
            f"User {user_id} purchased {item.name} x{quantity} for {total_price} besitos"
        )

        return True, f"¡Compraste {item.name}!", purchase

    async def refund_purchase(
        self,
        purchase_id: int,
        reason: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Reembolsa una compra.

        Args:
            purchase_id: ID de la compra
            reason: Razón del reembolso

        Returns:
            (success, message)
        """
        stmt = select(ItemPurchase).where(ItemPurchase.id == purchase_id)
        result = await self.session.execute(stmt)
        purchase = result.scalar_one_or_none()

        if not purchase:
            return False, "Compra no encontrada"

        if purchase.status != PurchaseStatus.COMPLETED.value:
            return False, "Esta compra ya fue reembolsada o cancelada"

        # Devolver besitos
        from bot.gamification.services.besito import BesitoService
        from bot.gamification.database.enums import TransactionType

        besito_service = BesitoService(self.session)
        await besito_service.grant_besitos(
            user_id=purchase.user_id,
            amount=purchase.price_paid,
            transaction_type=TransactionType.REFUND,
            description=f"Reembolso: {reason or 'Sin razón especificada'}"
        )

        # Actualizar compra
        purchase.status = PurchaseStatus.REFUNDED.value
        purchase.refunded_at = datetime.now(UTC)
        purchase.notes = reason

        # Quitar del inventario
        await self._remove_from_inventory(
            purchase.user_id,
            purchase.item_id,
            purchase.quantity
        )

        # Restaurar stock
        item = await self.get_item(purchase.item_id)
        if item and item.stock is not None:
            item.stock += purchase.quantity

        await self.session.commit()

        logger.info(f"Refunded purchase {purchase_id} for user {purchase.user_id}")
        return True, "Compra reembolsada exitosamente"

    # ========================================
    # HELPERS PRIVADOS
    # ========================================

    async def _get_user_item_quantity(self, user_id: int, item_id: int) -> int:
        """Obtiene la cantidad de un item que tiene el usuario."""
        stmt = (
            select(func.coalesce(func.sum(UserInventoryItem.quantity), 0))
            .where(
                UserInventoryItem.user_id == user_id,
                UserInventoryItem.item_id == item_id
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def _check_vip_status(self, user_id: int) -> bool:
        """Verifica si el usuario es VIP activo."""
        try:
            from bot.database.models import VIPSubscriber
            stmt = select(VIPSubscriber).where(
                VIPSubscriber.user_id == user_id,
                VIPSubscriber.status == "active"
            )
            result = await self.session.execute(stmt)
            vip = result.scalar_one_or_none()
            if vip and vip.expiry_date > datetime.utcnow():
                return True
            return False
        except Exception as e:
            logger.error(f"Error checking VIP status: {e}")
            return False

    async def _get_user_besitos(self, user_id: int) -> int:
        """Obtiene el balance de besitos del usuario."""
        try:
            from bot.gamification.database.models import UserGamification
            user_gamif = await self.session.get(UserGamification, user_id)
            return user_gamif.total_besitos if user_gamif else 0
        except Exception as e:
            logger.error(f"Error getting user besitos: {e}")
            return 0

    async def _add_to_inventory(
        self,
        user_id: int,
        item_id: int,
        quantity: int,
        obtained_via: str
    ) -> None:
        """Agrega item al inventario del usuario."""
        # Asegurar que existe el inventario
        inventory = await self.session.get(UserInventory, user_id)
        if not inventory:
            inventory = UserInventory(user_id=user_id)
            self.session.add(inventory)
            await self.session.flush()

        # Buscar si ya tiene el item
        stmt = select(UserInventoryItem).where(
            UserInventoryItem.user_id == user_id,
            UserInventoryItem.item_id == item_id
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        item = await self.get_item(item_id)

        if existing:
            # Incrementar cantidad
            existing.quantity += quantity
        else:
            # Crear nuevo registro
            inventory_item = UserInventoryItem(
                user_id=user_id,
                item_id=item_id,
                quantity=quantity,
                obtained_via=obtained_via
            )
            self.session.add(inventory_item)
            inventory.total_items += 1

        # Actualizar total gastado
        inventory.total_spent += item.price_besitos * quantity

    async def _remove_from_inventory(
        self,
        user_id: int,
        item_id: int,
        quantity: int
    ) -> None:
        """Quita item del inventario del usuario."""
        stmt = select(UserInventoryItem).where(
            UserInventoryItem.user_id == user_id,
            UserInventoryItem.item_id == item_id
        )
        result = await self.session.execute(stmt)
        inventory_item = result.scalar_one_or_none()

        if not inventory_item:
            return

        if inventory_item.quantity <= quantity:
            await self.session.delete(inventory_item)
            # Decrementar total de items
            inventory = await self.session.get(UserInventory, user_id)
            if inventory:
                inventory.total_items = max(0, inventory.total_items - 1)
        else:
            inventory_item.quantity -= quantity

    # ========================================
    # ESTADÍSTICAS
    # ========================================

    async def get_item_stats(self, item_id: int) -> Dict[str, Any]:
        """Obtiene estadísticas de un item."""
        item = await self.get_item(item_id)
        if not item:
            return {}

        # Total vendido
        stmt = select(func.sum(ItemPurchase.quantity)).where(
            ItemPurchase.item_id == item_id,
            ItemPurchase.status == PurchaseStatus.COMPLETED.value
        )
        result = await self.session.execute(stmt)
        total_sold = result.scalar() or 0

        # Usuarios que lo tienen
        stmt = select(func.count(func.distinct(UserInventoryItem.user_id))).where(
            UserInventoryItem.item_id == item_id
        )
        result = await self.session.execute(stmt)
        unique_owners = result.scalar() or 0

        # Revenue
        stmt = select(func.sum(ItemPurchase.price_paid)).where(
            ItemPurchase.item_id == item_id,
            ItemPurchase.status == PurchaseStatus.COMPLETED.value
        )
        result = await self.session.execute(stmt)
        total_revenue = result.scalar() or 0

        return {
            "item_id": item_id,
            "name": item.name,
            "total_sold": total_sold,
            "unique_owners": unique_owners,
            "total_revenue": total_revenue,
            "current_stock": item.stock,
            "is_active": item.is_active
        }

    async def get_shop_summary(self) -> Dict[str, Any]:
        """Obtiene resumen general de la tienda."""
        # Total de productos
        stmt = select(func.count()).select_from(ShopItem).where(ShopItem.is_active == True)
        result = await self.session.execute(stmt)
        total_items = result.scalar() or 0

        # Total de categorías
        stmt = select(func.count()).select_from(ItemCategory).where(ItemCategory.is_active == True)
        result = await self.session.execute(stmt)
        total_categories = result.scalar() or 0

        # Total de ventas
        stmt = select(func.count()).select_from(ItemPurchase).where(
            ItemPurchase.status == PurchaseStatus.COMPLETED.value
        )
        result = await self.session.execute(stmt)
        total_purchases = result.scalar() or 0

        # Revenue total
        stmt = select(func.sum(ItemPurchase.price_paid)).where(
            ItemPurchase.status == PurchaseStatus.COMPLETED.value
        )
        result = await self.session.execute(stmt)
        total_revenue = result.scalar() or 0

        return {
            "total_items": total_items,
            "total_categories": total_categories,
            "total_purchases": total_purchases,
            "total_revenue": total_revenue
        }

    # ========================================
    # ITEMS OCULTOS Y VISIBILIDAD
    # ========================================

    async def get_items_for_user(
        self,
        user_id: int,
        active_only: bool = True,
        item_type: Optional[ItemType] = None,
        category_id: Optional[int] = None
    ) -> List[ShopItem]:
        """
        Obtiene items visibles para un usuario específico.

        Filtra items ocultos (is_hidden=True) si el usuario no tiene
        nivel suficiente (nivel 6+ requerido).

        Args:
            user_id: ID del usuario
            active_only: Solo productos activos
            item_type: Filtrar por tipo (opcional)
            category_id: Filtrar por categoría (opcional)

        Returns:
            Lista de items visibles para el usuario
        """
        stmt = select(ShopItem).order_by(ShopItem.order, ShopItem.name)

        if active_only:
            stmt = stmt.where(ShopItem.is_active == True)
        if item_type:
            stmt = stmt.where(ShopItem.item_type == item_type.value)
        if category_id:
            stmt = stmt.where(ShopItem.category_id == category_id)

        result = await self.session.execute(stmt)
        all_items = list(result.scalars().all())

        # Filtrar items ocultos si el usuario no tiene nivel suficiente
        if not await self._can_see_hidden_items(user_id):
            items = [item for item in all_items if not item.is_hidden]
        else:
            items = all_items

        return items

    async def _can_see_hidden_items(self, user_id: int) -> bool:
        """
        Verifica si un usuario puede ver items ocultos.

        Los items ocultos requieren nivel 6+ (Confidente o Guardian).

        Args:
            user_id: ID del usuario

        Returns:
            True si el usuario puede ver items ocultos
        """
        try:
            from bot.gamification.database.models import UserGamification
            from bot.gamification.database.models import Level

            user_gamif = await self.session.get(UserGamification, user_id)
            if not user_gamif or not user_gamif.current_level_id:
                return False

            level = await self.session.get(Level, user_gamif.current_level_id)
            if not level:
                return False

            # Nivel 6+ puede ver items ocultos
            return level.order >= 6

        except Exception as e:
            logger.error(f"Error checking if user {user_id} can see hidden items: {e}")
            return False

    async def get_user_level_order(self, user_id: int) -> int:
        """
        Obtiene el nivel (orden) de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Orden del nivel (1-7) o 1 si no se puede determinar
        """
        try:
            from bot.gamification.database.models import UserGamification
            from bot.gamification.database.models import Level

            user_gamif = await self.session.get(UserGamification, user_id)
            if not user_gamif or not user_gamif.current_level_id:
                return 1

            level = await self.session.get(Level, user_gamif.current_level_id)
            if not level:
                return 1

            return level.order

        except Exception as e:
            logger.error(f"Error getting user {user_id} level: {e}")
            return 1

    async def can_purchase_item(
        self,
        user_id: int,
        item_id: int,
        quantity: int = 1
    ) -> Tuple[bool, str]:
        """
        Verifica si un usuario puede comprar un item (versión mejorada).

        Esta versión incluye verificación de:
        - Nivel requerido (level_required en metadata)
        - Items ocultos
        - Stock
        - Maximum por usuario
        - VIP requerido
        - Besitos suficientes

        Args:
            user_id: ID del usuario
            item_id: ID del item
            quantity: Cantidad a comprar

        Returns:
            (can_purchase, reason)
        """
        item = await self.get_item(item_id)
        if not item:
            return False, "Producto no encontrado"

        if not item.is_active:
            return False, "Producto no disponible"

        # Verificar disponibilidad temporal
        if not item.is_available:
            if item.available_from and not item.is_available:
                return False, "Este item aún no está disponible"
            if item.available_until and not item.is_available:
                return False, "Este item ya no está disponible"

        # Verificar items ocultos
        if item.is_hidden and not await self._can_see_hidden_items(user_id):
            return False, "Este item requiere nivel 6+ (Confidente)"

        # Verificar nivel requerido (está en metadata)
        if item.item_metadata:
            try:
                import json
                metadata = json.loads(item.item_metadata)
                level_required = metadata.get("level_required")
                if level_required:
                    user_level = await self.get_user_level_order(user_id)
                    if user_level < level_required:
                        return False, f"Este item requiere nivel {level_required}"
            except (json.JSONDecodeError, TypeError):
                pass

        # Verificar stock
        if item.stock is not None and item.stock < quantity:
            return False, f"Stock insuficiente (disponible: {item.stock})"

        # Verificar máximo por usuario
        if item.max_per_user is not None:
            owned = await self._get_user_item_quantity(user_id, item_id)
            if owned + quantity > item.max_per_user:
                return False, f"Máximo {item.max_per_user} por usuario (tienes {owned})"

        # Verificar VIP si es requerido
        if item.requires_vip:
            is_vip = await self._check_vip_status(user_id)
            if not is_vip:
                return False, "Este producto requiere ser VIP"

        # Verificar besitos
        user_besitos = await self._get_user_besitos(user_id)
        total_price = item.price_besitos * quantity
        if user_besitos < total_price:
            return False, f"Besitos insuficientes (necesitas {total_price}, tienes {user_besitos})"

        return True, "OK"

    # ========================================
    # ITEMS TEMPORALES Y LIMITADOS
    # ========================================

    async def get_temporal_items(
        self,
        active_only: bool = True
    ) -> List[ShopItem]:
        """
        Obtiene items temporales (con fechas de disponibilidad).

        Args:
            active_only: Solo productos activos

        Returns:
            Lista de items temporales
        """
        stmt = select(ShopItem).where(
            ShopItem.available_from != None
        ).order_by(ShopItem.available_until)

        if active_only:
            stmt = stmt.where(ShopItem.is_active == True)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_expiring_soon(
        self,
        hours: int = 24
    ) -> List[ShopItem]:
        """
        Obtiene items que expiran pronto.

        Args:
            hours: Horas restantes para considerar "pronto"

        Returns:
            Lista de items que expiran pronto
        """
        from datetime import timedelta

        soon = datetime.now(UTC) + timedelta(hours=hours)

        stmt = select(ShopItem).where(
            ShopItem.is_active == True,
            ShopItem.available_until != None,
            ShopItem.available_until <= soon
        ).order_by(ShopItem.available_until)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_low_stock_items(
        self,
        threshold: int = 10
    ) -> List[ShopItem]:
        """
        Obtiene items con stock bajo.

        Args:
            threshold: Umbral de stock bajo

        Returns:
            Lista de items con stock <= threshold
        """
        stmt = select(ShopItem).where(
            ShopItem.is_active == True,
            ShopItem.stock != None,
            ShopItem.stock <= threshold,
            ShopItem.stock > 0
        ).order_by(ShopItem.stock)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())
