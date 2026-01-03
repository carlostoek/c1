"""
Servicio de cálculo de descuentos del Gabinete.

Responsabilidades:
- Calcular descuentos por nivel de usuario
- Calcular descuentos por distintivos poseídos
- Calcular descuentos por reliquias poseídas
- Aplicar límite máximo de descuento (50%)
"""

from typing import Optional, List, Dict, Any, Set
import json
import logging

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from bot.shop.database.models import (
    ShopItem,
    UserInventory,
    UserInventoryItem,
)
from bot.gamification.database.models import UserGamification, Level

logger = logging.getLogger(__name__)


class DiscountService:
    """
    Servicio de cálculo de descuentos para el Gabinete.

    Los descuentos se calculan sumando:
    - Descuento base por nivel (0-20%)
    - Bonus por distintivos especiales (+5-15%)
    - Bonus por reliquias especiales (+3-20%)

    Descuento máximo: 50%
    """

    # Descuento base por nivel (según tabla en Fase 4)
    LEVEL_DISCOUNTS: Dict[int, float] = {
        1: 0.0,   # 0%
        2: 0.0,   # 0%
        3: 0.0,   # 0%
        4: 0.05,  # 5%
        5: 0.10,  # 10%
        6: 0.15,  # 15%
        7: 0.20,  # 20%
    }

    # Distintivos que otorgan bonus de descuento
    BADGE_DISCOUNTS: Dict[str, float] = {
        "recognized_emblem": 0.05,      # Emblema del Reconocido: +5%
        "confidant_mark": 0.10,         # Marca del Confidente: +10%
        "guardian_crown": 0.15,         # Corona del Guardián: +15%
    }

    # Reliquias que otorgan bonus de descuento
    RELIC_DISCOUNTS: Dict[str, float] = {
        "relic_01": 0.03,               # El Primer Secreto: +3%
        "master_key": 0.20,             # Llave Maestra: +20%
    }

    MAX_DISCOUNT: float = 0.50  # 50% máximo

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_discount(
        self,
        user_id: int
    ) -> float:
        """
        Calcula el descuento total de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Descuento total (0.0 a 0.50, donde 0.50 = 50%)
        """
        discount = 0.0

        # 1. Descuento por nivel
        level_discount = await self._get_level_discount(user_id)
        discount += level_discount

        # 2. Descuento por distintivos
        badge_discount = await self._get_badge_discount(user_id)
        discount += badge_discount

        # 3. Descuento por reliquias
        relic_discount = await self._get_relic_discount(user_id)
        discount += relic_discount

        # Aplicar máximo
        total = min(discount, self.MAX_DISCOUNT)

        logger.debug(
            f"User {user_id} discount: level={level_discount:.2%}, "
            f"badges={badge_discount:.2%}, relics={relic_discount:.2%}, "
            f"total={total:.2%}"
        )

        return total

    async def get_discount_breakdown(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Retorna el desglose detallado del descuento de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Diccionario con:
            - total: Descuento total
            - level_discount: Descuento por nivel
            - level_name: Nombre del nivel
            - badge_discount: Descuento por distintivos
            - badge_names: Lista de distintivos aplicables
            - relic_discount: Descuento por reliquias
            - relic_names: Lista de reliquias aplicables
            - is_capped: Si el descuento llegó al máximo (50%)
        """
        # Obtener componentes
        level_discount, level_name = await self._get_level_discount_with_name(user_id)
        badge_discount, badge_names = await self._get_badge_discount_with_names(user_id)
        relic_discount, relic_names = await self._get_relic_discount_with_names(user_id)

        # Calcular total
        raw_total = level_discount + badge_discount + relic_discount
        total = min(raw_total, self.MAX_DISCOUNT)

        return {
            "total": total,
            "level_discount": level_discount,
            "level_name": level_name,
            "badge_discount": badge_discount,
            "badge_names": badge_names,
            "relic_discount": relic_discount,
            "relic_names": relic_names,
            "is_capped": raw_total > self.MAX_DISCOUNT,
        }

    async def calculate_price_with_discount(
        self,
        user_id: int,
        item: ShopItem,
        quantity: int = 1
    ) -> Dict[str, Any]:
        """
        Calcula el precio final aplicando descuentos.

        Args:
            user_id: ID del usuario
            item: Item de la tienda
            quantity: Cantidad (default: 1)

        Returns:
            Diccionario con:
            - original_price: Precio sin descuento
            - discount: Descuento aplicado (0.0 a 0.5)
            - discount_percentage: Descuento como porcentaje (0 a 50)
            - final_price: Precio con descuento
            - savings: Besitos ahorrados
            - breakdown: Desglose del descuento
        """
        discount = await self.get_user_discount(user_id)
        breakdown = await self.get_discount_breakdown(user_id)

        original_price = item.price_besitos * quantity
        savings = int(original_price * discount)
        final_price = original_price - savings

        return {
            "original_price": original_price,
            "discount": discount,
            "discount_percentage": int(discount * 100),
            "final_price": final_price,
            "savings": savings,
            "breakdown": breakdown,
        }

    async def format_discount_message(
        self,
        user_id: int,
        item: ShopItem
    ) -> str:
        """
        Genera un mensaje formateado con el precio y descuentos.

        Args:
            user_id: ID del usuario
            item: Item de la tienda

        Returns:
            String HTML formateado para Telegram
        """
        pricing = await self.calculate_price_with_discount(user_id, item)
        breakdown = pricing["breakdown"]

        lines = []

        # Precio
        if pricing["discount_percentage"] > 0:
            lines.append(
                f"💰 Precio: <s>{pricing['original_price']}</s> → "
                f"<b>{pricing['final_price']}</b> Besitos"
            )
        else:
            lines.append(f"💰 Precio: {pricing['original_price']} Besitos")

        # Desglose de descuento
        if pricing["discount_percentage"] > 0:
            lines.append(f"\n✨ Descuentos aplicados:")

            if breakdown["level_discount"] > 0:
                lines.append(
                    f"   • Nivel {breakdown['level_name']}: "
                    f"+{breakdown['level_discount']*100:.0f}%"
                )

            if breakdown["badge_discount"] > 0:
                badge_list = ", ".join(breakdown["badge_names"])
                lines.append(
                    f"   • Distintivos ({badge_list}): "
                    f"+{breakdown['badge_discount']*100:.0f}%"
                )

            if breakdown["relic_discount"] > 0:
                relic_list = ", ".join(breakdown["relic_names"])
                lines.append(
                    f"   • Reliquias ({relic_list}): "
                    f"+{breakdown['relic_discount']*100:.0f}%"
                )

            total = breakdown["total"]
            lines.append(f"   • Total: {total*100:.0f}% de descuento")

            if breakdown["is_capped"]:
                lines.append(f"   ⚠️ Máximo alcanzado (50%)")

            # Ahorro
            lines.append(f"\n💵 Ahorras: {pricing['savings']} Besitos")

        return "\n".join(lines)

    # ========================================
    # MÉTODOS PRIVADOS
    # ========================================

    async def _get_level_discount(self, user_id: int) -> float:
        """Obtiene descuento por nivel de usuario."""
        user_gamif = await self.session.get(UserGamification, user_id)
        if not user_gamif or not user_gamif.current_level_id:
            return 0.0

        level = await self.session.get(Level, user_gamif.current_level_id)
        if not level:
            return 0.0

        return self.LEVEL_DISCOUNTS.get(level.order, 0.0)

    async def _get_level_discount_with_name(self, user_id: int) -> tuple[float, Optional[str]]:
        """Obtiene descuento y nombre del nivel."""
        user_gamif = await self.session.get(UserGamification, user_id)
        if not user_gamif or not user_gamif.current_level_id:
            return 0.0, None

        level = await self.session.get(Level, user_gamif.current_level_id)
        if not level:
            return 0.0, None

        discount = self.LEVEL_DISCOUNTS.get(level.order, 0.0)
        return discount, level.name

    async def _get_badge_discount(self, user_id: int) -> float:
        """Obtiene descuento total por distintivos."""
        discount = 0.0

        # Buscar items tipo COSMETIC en inventario
        stmt = (
            select(UserInventoryItem, ShopItem)
            .join(ShopItem, UserInventoryItem.item_id == ShopItem.id)
            .where(
                UserInventoryItem.user_id == user_id,
                ShopItem.item_type == "COSMETIC",
                UserInventoryItem.quantity > 0
            )
        )
        result = await self.session.execute(stmt)
        inventory_items = result.all()

        for inv_item, item in inventory_items:
            # Obtener badge_id del metadata
            if not item.item_metadata:
                continue

            try:
                metadata = json.loads(item.item_metadata)
                badge_id = metadata.get("badge_id")
                if badge_id in self.BADGE_DISCOUNTS:
                    discount += self.BADGE_DISCOUNTS[badge_id]
            except (json.JSONDecodeError, TypeError):
                continue

        return discount

    async def _get_badge_discount_with_names(self, user_id: int) -> tuple[float, List[str]]:
        """Obtiene descuento y nombres de distintivos."""
        discount = 0.0
        names = []

        stmt = (
            select(UserInventoryItem, ShopItem)
            .join(ShopItem, UserInventoryItem.item_id == ShopItem.id)
            .where(
                UserInventoryItem.user_id == user_id,
                ShopItem.item_type == "COSMETIC",
                UserInventoryItem.quantity > 0
            )
        )
        result = await self.session.execute(stmt)
        inventory_items = result.all()

        for inv_item, item in inventory_items:
            if not item.item_metadata:
                continue

            try:
                metadata = json.loads(item.item_metadata)
                badge_id = metadata.get("badge_id")
                if badge_id in self.BADGE_DISCOUNTS:
                    discount += self.BADGE_DISCOUNTS[badge_id]
                    names.append(item.name)
            except (json.JSONDecodeError, TypeError):
                continue

        return discount, names

    async def _get_relic_discount(self, user_id: int) -> float:
        """Obtiene descuento total por reliquias."""
        discount = 0.0

        # Buscar items tipo DIGITAL en inventario
        stmt = (
            select(UserInventoryItem, ShopItem)
            .join(ShopItem, UserInventoryItem.item_id == ShopItem.id)
            .where(
                UserInventoryItem.user_id == user_id,
                ShopItem.item_type == "DIGITAL",
                UserInventoryItem.quantity > 0
            )
        )
        result = await self.session.execute(stmt)
        inventory_items = result.all()

        for inv_item, item in inventory_items:
            # Obtener collectible_id del metadata
            if not item.item_metadata:
                continue

            try:
                metadata = json.loads(item.item_metadata)
                collectible_id = metadata.get("collectible_id")
                if collectible_id in self.RELIC_DISCOUNTS:
                    discount += self.RELIC_DISCOUNTS[collectible_id]
            except (json.JSONDecodeError, TypeError):
                continue

        return discount

    async def _get_relic_discount_with_names(self, user_id: int) -> tuple[float, List[str]]:
        """Obtiene descuento y nombres de reliquias."""
        discount = 0.0
        names = []

        stmt = (
            select(UserInventoryItem, ShopItem)
            .join(ShopItem, UserInventoryItem.item_id == ShopItem.id)
            .where(
                UserInventoryItem.user_id == user_id,
                ShopItem.item_type == "DIGITAL",
                UserInventoryItem.quantity > 0
            )
        )
        result = await self.session.execute(stmt)
        inventory_items = result.all()

        for inv_item, item in inventory_items:
            if not item.item_metadata:
                continue

            try:
                metadata = json.loads(item.item_metadata)
                collectible_id = metadata.get("collectible_id")
                if collectible_id in self.RELIC_DISCOUNTS:
                    discount += self.RELIC_DISCOUNTS[collectible_id]
                    names.append(item.name)
            except (json.JSONDecodeError, TypeError):
                continue

        return discount, names
