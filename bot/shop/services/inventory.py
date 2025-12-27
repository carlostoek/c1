"""
Servicio de gestión del Inventario del Usuario (Mochila).

Responsabilidades:
- Gestión del inventario personal
- Verificación de posesión de items
- Uso de items consumibles
- Equipar/desequipar items cosméticos
"""

from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime, UTC
import json
import logging

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from bot.shop.database.models import (
    ShopItem,
    UserInventory,
    UserInventoryItem,
    ItemPurchase,
)
from bot.shop.database.enums import ItemType

logger = logging.getLogger(__name__)


class InventoryService:
    """Servicio de gestión del inventario del usuario."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ========================================
    # INVENTARIO
    # ========================================

    async def get_or_create_inventory(self, user_id: int) -> UserInventory:
        """
        Obtiene o crea el inventario del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            UserInventory del usuario
        """
        inventory = await self.session.get(UserInventory, user_id)
        if not inventory:
            inventory = UserInventory(user_id=user_id)
            self.session.add(inventory)
            await self.session.commit()
            await self.session.refresh(inventory)
            logger.debug(f"Created inventory for user {user_id}")

        return inventory

    async def get_inventory_items(
        self,
        user_id: int,
        item_type: Optional[ItemType] = None,
        equipped_only: bool = False
    ) -> List[UserInventoryItem]:
        """
        Obtiene los items del inventario del usuario.

        Args:
            user_id: ID del usuario
            item_type: Filtrar por tipo de item
            equipped_only: Solo items equipados

        Returns:
            Lista de UserInventoryItem con ShopItem cargado
        """
        # Asegurar que existe el inventario
        await self.get_or_create_inventory(user_id)

        stmt = (
            select(UserInventoryItem)
            .options(selectinload(UserInventoryItem.item))
            .where(UserInventoryItem.user_id == user_id)
        )

        if equipped_only:
            stmt = stmt.where(UserInventoryItem.is_equipped == True)

        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        # Filtrar por tipo si se especifica
        if item_type:
            items = [i for i in items if i.item.item_type == item_type.value]

        return items

    async def get_inventory_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Obtiene un resumen del inventario del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Dict con estadísticas del inventario
        """
        inventory = await self.get_or_create_inventory(user_id)

        # Contar items por tipo
        items = await self.get_inventory_items(user_id)

        by_type = {}
        for item in items:
            item_type = item.item.item_type
            if item_type not in by_type:
                by_type[item_type] = {"count": 0, "quantity": 0}
            by_type[item_type]["count"] += 1
            by_type[item_type]["quantity"] += item.quantity

        # Items equipados
        equipped = [i for i in items if i.is_equipped]

        return {
            "user_id": user_id,
            "total_items": inventory.total_items,
            "total_spent": inventory.total_spent,
            "favorite_item_id": inventory.favorite_item_id,
            "items_by_type": by_type,
            "equipped_count": len(equipped),
            "created_at": inventory.created_at,
        }

    # ========================================
    # POSESIÓN DE ITEMS
    # ========================================

    async def has_item(self, user_id: int, item_id: int) -> bool:
        """
        Verifica si el usuario posee un item.

        Args:
            user_id: ID del usuario
            item_id: ID del item

        Returns:
            True si el usuario tiene al menos 1 del item
        """
        stmt = select(func.count()).select_from(UserInventoryItem).where(
            UserInventoryItem.user_id == user_id,
            UserInventoryItem.item_id == item_id,
            UserInventoryItem.quantity > 0
        )
        result = await self.session.execute(stmt)
        return result.scalar() > 0

    async def has_item_by_slug(self, user_id: int, item_slug: str) -> bool:
        """
        Verifica si el usuario posee un item por su slug.

        Args:
            user_id: ID del usuario
            item_slug: Slug del item

        Returns:
            True si el usuario tiene al menos 1 del item
        """
        stmt = (
            select(func.count())
            .select_from(UserInventoryItem)
            .join(ShopItem, UserInventoryItem.item_id == ShopItem.id)
            .where(
                UserInventoryItem.user_id == user_id,
                ShopItem.slug == item_slug,
                UserInventoryItem.quantity > 0
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() > 0

    async def get_item_quantity(self, user_id: int, item_id: int) -> int:
        """
        Obtiene la cantidad de un item que tiene el usuario.

        Args:
            user_id: ID del usuario
            item_id: ID del item

        Returns:
            Cantidad del item (0 si no lo tiene)
        """
        stmt = (
            select(func.coalesce(func.sum(UserInventoryItem.quantity), 0))
            .where(
                UserInventoryItem.user_id == user_id,
                UserInventoryItem.item_id == item_id
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_user_item(
        self,
        user_id: int,
        item_id: int
    ) -> Optional[UserInventoryItem]:
        """
        Obtiene el registro de inventario de un item específico.

        Args:
            user_id: ID del usuario
            item_id: ID del item

        Returns:
            UserInventoryItem o None
        """
        stmt = (
            select(UserInventoryItem)
            .options(selectinload(UserInventoryItem.item))
            .where(
                UserInventoryItem.user_id == user_id,
                UserInventoryItem.item_id == item_id
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ========================================
    # USO DE ITEMS CONSUMIBLES
    # ========================================

    async def use_item(
        self,
        user_id: int,
        item_id: int,
        quantity: int = 1
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Usa un item consumible.

        Args:
            user_id: ID del usuario
            item_id: ID del item
            quantity: Cantidad a usar

        Returns:
            (success, message, effect_data)
        """
        inventory_item = await self.get_user_item(user_id, item_id)

        if not inventory_item:
            return False, "No tienes este item", None

        if inventory_item.quantity < quantity:
            return False, f"No tienes suficientes (tienes {inventory_item.quantity})", None

        item = inventory_item.item

        # Solo consumibles pueden usarse
        if item.item_type != ItemType.CONSUMABLE.value:
            return False, "Este item no es consumible", None

        # Aplicar efecto
        effect_data = await self._apply_consumable_effect(user_id, item)

        # Decrementar cantidad
        inventory_item.quantity -= quantity
        inventory_item.is_used = True
        inventory_item.used_at = datetime.now(UTC)

        # Si ya no tiene, actualizar inventario
        if inventory_item.quantity <= 0:
            inventory = await self.session.get(UserInventory, user_id)
            if inventory:
                inventory.total_items = max(0, inventory.total_items - 1)

        await self.session.commit()

        logger.info(f"User {user_id} used item {item.name}")
        return True, f"¡Usaste {item.name}!", effect_data

    async def _apply_consumable_effect(
        self,
        user_id: int,
        item: ShopItem
    ) -> Dict[str, Any]:
        """
        Aplica el efecto de un item consumible.

        Args:
            user_id: ID del usuario
            item: ShopItem consumible

        Returns:
            Dict con datos del efecto aplicado
        """
        effect_data = {"item_name": item.name, "applied": False}

        if not item.item_metadata:
            return effect_data

        try:
            metadata = json.loads(item.item_metadata)
            effect_type = metadata.get("effect_type")
            effect_value = metadata.get("effect_value", 0)

            if effect_type == "besitos_boost":
                # Otorgar besitos extra
                from bot.gamification.services.besito import BesitoService
                from bot.gamification.database.enums import TransactionType

                besito_service = BesitoService(self.session)
                await besito_service.grant_besitos(
                    user_id=user_id,
                    amount=effect_value,
                    transaction_type=TransactionType.ADMIN_GRANT,
                    description=f"Efecto de item: {item.name}"
                )
                effect_data["applied"] = True
                effect_data["besitos_granted"] = effect_value

            # Otros efectos pueden agregarse aquí

        except Exception as e:
            logger.error(f"Error applying consumable effect: {e}")

        return effect_data

    # ========================================
    # EQUIPAR/DESEQUIPAR ITEMS
    # ========================================

    async def equip_item(
        self,
        user_id: int,
        item_id: int
    ) -> Tuple[bool, str]:
        """
        Equipa un item cosmético.

        Args:
            user_id: ID del usuario
            item_id: ID del item

        Returns:
            (success, message)
        """
        inventory_item = await self.get_user_item(user_id, item_id)

        if not inventory_item:
            return False, "No tienes este item"

        item = inventory_item.item

        # Solo cosméticos pueden equiparse
        if item.item_type != ItemType.COSMETIC.value:
            return False, "Este item no puede equiparse"

        if inventory_item.is_equipped:
            return False, "Este item ya está equipado"

        inventory_item.is_equipped = True
        await self.session.commit()

        logger.info(f"User {user_id} equipped {item.name}")
        return True, f"¡Equipaste {item.name}!"

    async def unequip_item(
        self,
        user_id: int,
        item_id: int
    ) -> Tuple[bool, str]:
        """
        Desequipa un item cosmético.

        Args:
            user_id: ID del usuario
            item_id: ID del item

        Returns:
            (success, message)
        """
        inventory_item = await self.get_user_item(user_id, item_id)

        if not inventory_item:
            return False, "No tienes este item"

        if not inventory_item.is_equipped:
            return False, "Este item no está equipado"

        inventory_item.is_equipped = False
        await self.session.commit()

        logger.info(f"User {user_id} unequipped {inventory_item.item.name}")
        return True, f"Desequipaste {inventory_item.item.name}"

    # ========================================
    # FAVORITOS
    # ========================================

    async def set_favorite_item(
        self,
        user_id: int,
        item_id: int
    ) -> Tuple[bool, str]:
        """
        Establece un item como favorito.

        Args:
            user_id: ID del usuario
            item_id: ID del item

        Returns:
            (success, message)
        """
        # Verificar que tiene el item
        has = await self.has_item(user_id, item_id)
        if not has:
            return False, "No tienes este item"

        inventory = await self.get_or_create_inventory(user_id)
        inventory.favorite_item_id = item_id
        await self.session.commit()

        return True, "Item favorito actualizado"

    async def clear_favorite_item(self, user_id: int) -> bool:
        """Limpia el item favorito."""
        inventory = await self.session.get(UserInventory, user_id)
        if inventory:
            inventory.favorite_item_id = None
            await self.session.commit()
            return True
        return False

    # ========================================
    # ITEMS NARRATIVOS
    # ========================================

    async def get_narrative_items(
        self,
        user_id: int
    ) -> List[UserInventoryItem]:
        """
        Obtiene los items narrativos del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Lista de items narrativos con su metadata
        """
        return await self.get_inventory_items(user_id, item_type=ItemType.NARRATIVE)

    async def get_unlocked_fragments(self, user_id: int) -> List[str]:
        """
        Obtiene lista de fragment_keys desbloqueados por items.

        Args:
            user_id: ID del usuario

        Returns:
            Lista de fragment_keys
        """
        narrative_items = await self.get_narrative_items(user_id)
        unlocked = []

        for inv_item in narrative_items:
            if inv_item.item.item_metadata:
                try:
                    metadata = json.loads(inv_item.item.item_metadata)
                    if "unlocks_fragment_key" in metadata:
                        unlocked.append(metadata["unlocks_fragment_key"])
                except json.JSONDecodeError:
                    pass

        return unlocked

    async def get_unlocked_chapters(self, user_id: int) -> List[str]:
        """
        Obtiene lista de chapter_slugs desbloqueados por items.

        Args:
            user_id: ID del usuario

        Returns:
            Lista de chapter_slugs
        """
        narrative_items = await self.get_narrative_items(user_id)
        unlocked = []

        for inv_item in narrative_items:
            if inv_item.item.item_metadata:
                try:
                    metadata = json.loads(inv_item.item.item_metadata)
                    if "unlocks_chapter_slug" in metadata:
                        unlocked.append(metadata["unlocks_chapter_slug"])
                except json.JSONDecodeError:
                    pass

        return unlocked

    # ========================================
    # OTORGAR ITEMS (PARA ADMIN/REWARDS)
    # ========================================

    async def grant_item(
        self,
        user_id: int,
        item_id: int,
        quantity: int = 1,
        obtained_via: str = "reward"
    ) -> Tuple[bool, str]:
        """
        Otorga un item a un usuario (sin cobrar).

        Args:
            user_id: ID del usuario
            item_id: ID del item
            quantity: Cantidad a otorgar
            obtained_via: Cómo se obtuvo

        Returns:
            (success, message)
        """
        from bot.shop.services.shop import ShopService

        shop_service = ShopService(self.session)
        item = await shop_service.get_item(item_id)

        if not item:
            return False, "Item no encontrado"

        # Verificar máximo por usuario
        if item.max_per_user is not None:
            current = await self.get_item_quantity(user_id, item_id)
            if current + quantity > item.max_per_user:
                return False, f"Máximo {item.max_per_user} por usuario"

        # Agregar al inventario
        await self._add_to_inventory(user_id, item_id, quantity, obtained_via)
        await self.session.commit()

        logger.info(f"Granted {item.name} x{quantity} to user {user_id}")
        return True, f"¡Recibiste {item.name}!"

    async def _add_to_inventory(
        self,
        user_id: int,
        item_id: int,
        quantity: int,
        obtained_via: str
    ) -> None:
        """Helper para agregar item al inventario."""
        # Asegurar inventario
        inventory = await self.get_or_create_inventory(user_id)

        # Buscar si ya tiene el item
        existing = await self.get_user_item(user_id, item_id)

        if existing:
            existing.quantity += quantity
        else:
            inv_item = UserInventoryItem(
                user_id=user_id,
                item_id=item_id,
                quantity=quantity,
                obtained_via=obtained_via
            )
            self.session.add(inv_item)
            inventory.total_items += 1

    # ========================================
    # HISTORIAL DE COMPRAS
    # ========================================

    async def get_purchase_history(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[ItemPurchase]:
        """
        Obtiene el historial de compras del usuario.

        Args:
            user_id: ID del usuario
            limit: Límite de resultados

        Returns:
            Lista de compras ordenadas por fecha
        """
        stmt = (
            select(ItemPurchase)
            .options(selectinload(ItemPurchase.item))
            .where(ItemPurchase.user_id == user_id)
            .order_by(ItemPurchase.purchased_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
