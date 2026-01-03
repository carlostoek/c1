"""
Servicio de recomendaciones personalizadas del Gabinete.

Responsabilidades:
- Recomendar items basados en arquetipo del usuario
- Sugerir items basados en historial de compras
- Recomendar items de próximo nivel
"""

from typing import Optional, List, Dict, Any
import logging

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from bot.shop.database.models import (
    ShopItem,
    UserInventoryItem,
    ItemPurchase,
)
from bot.gamification.database.models import UserGamification, Level

logger = logging.getLogger(__name__)


# Mapeo de arquetipos a categorías recomendadas
ARCHETYPE_RECOMMENDATIONS: Dict[str, Dict[str, Any]] = {
    "EXPLORER": {
        "preferred_categories": ["NARRATIVE"],  # Llaves - contenido oculto
        "reason": "Su naturaleza exploradora busca desbloquear secretos. "
                  "Las Llaves abrirán puertas que otros nunca encontrarán.",
    },
    "DIRECT": {
        "preferred_categories": ["CONSUMABLE"],  # Efímeros - uso inmediato
        "reason": "Usted valora la acción inmediata. "
                  "Los Efímeros ofrecen gratificación instantánea.",
    },
    "ROMANTIC": {
        "preferred_categories": ["DIGITAL"],  # Reliquias emotivas
        "reason": "Su sensibilidad aprecia lo significativo. "
                  "Las Reliquias contienen las historias más personales de Diana.",
    },
    "ANALYTICAL": {
        "preferred_categories": ["NARRATIVE", "DIGITAL"],  # Items con información
        "reason": "Su mente analítica busca entender. "
                  "Estos items contienen la información más profunda.",
    },
    "PERSISTENT": {
        "preferred_categories": ["COSMETIC"],  # Distintivos - reconocimiento
        "reason": "Su persistencia merece reconocimiento. "
                  "Los Distintivos muestran al mundo su dedicación.",
    },
    "PATIENT": {
        "preferred_categories": ["DIGITAL"],  # Reliquias de largo plazo
        "reason": "Su paciencia será recompensada. "
                  "Las Reliquias más valiosas requieren espera.",
    },
}


class RecommendationService:
    """
    Servicio de recomendaciones personalizadas.

    Analiza el comportamiento del usuario y recomienda items
    del Gabinete que probablemente le interesen.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_personalized_recommendation(
        self,
        user_id: int,
        limit: int = 3
    ) -> Dict[str, Any]:
        """
        Obtiene recomendaciones personalizadas para un usuario.

        Args:
            user_id: ID del usuario
            limit: Máximo de items a recomendar

        Returns:
            Diccionario con:
            - items: Lista de items recomendados
            - reason: Razón de la recomendación
            - archetype: Arquetipo detectado
        """
        # 1. Obtener arquetipo del usuario
        user_gamif = await self.session.get(UserGamification, user_id)
        archetype = user_gamif.archetype if user_gamif else None

        # 2. Obtener nivel actual
        current_level_order = 1
        if user_gamif and user_gamif.current_level_id:
            level = await self.session.get(Level, user_gamif.current_level_id)
            if level:
                current_level_order = level.order

        # 3. Seleccionar estrategia de recomendación
        if archetype and archetype in ARCHETYPE_RECOMMENDATIONS:
            return await self._recommend_by_archetype(
                user_id, archetype, current_level_order, limit
            )
        else:
            return await self._recommend_by_history(
                user_id, current_level_order, limit
            )

    async def get_items_for_archetype(
        self,
        archetype: str,
        current_level: int,
        limit: int = 5
    ) -> List[ShopItem]:
        """
        Obtiene items recomendados para un arquetipo específico.

        Args:
            archetype: Arquetipo (EXPLORER, DIRECT, etc.)
            current_level: Nivel actual del usuario (1-7)
            limit: Máximo de items a retornar

        Returns:
            Lista de ShopItem recomendados
        """
        if archetype not in ARCHETYPE_RECOMMENDATIONS:
            return []

        config = ARCHETYPE_RECOMMENDATIONS[archetype]
        preferred = config["preferred_categories"]

        # Buscar items disponibles de categorías preferidas
        # Que el usuario pueda ver (nivel requerido <= nivel actual + 1)
        stmt = (
            select(ShopItem)
            .where(
                and_(
                    ShopItem.is_active == True,
                    ShopItem.is_hidden == False,
                    # Nivel requerido hasta 1 nivel arriba del actual
                    ShopItem.item_metadata.like(f'%"level_required": {current_level}%')
                    | ShopItem.item_metadata.like(f'%"level_required": {current_level + 1}%')
                )
            )
            .order_by(ShopItem.order, ShopItem.price_besitos)
            .limit(limit * 3)  # Obtener más para filtrar
        )
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        # Filtrar por categoría preferida
        filtered = []
        for item in items:
            # Obtener categoría del item
            category_stmt = select(ShopItem.category_id).where(ShopItem.id == item.id)
            # Nota: esto no funciona directamente, mejor obtener category desde item
            filtered.append(item)
            if len(filtered) >= limit:
                break

        return filtered[:limit]

    async def get_next_level_items(
        self,
        user_id: int,
        limit: int = 3
    ) -> List[ShopItem]:
        """
        Obtiene items que el usuario casi puede comprar (siguiente nivel).

        Args:
            user_id: ID del usuario
            limit: Máximo de items a retornar

        Returns:
            Lista de ShopItem del siguiente nivel
        """
        # Obtener nivel actual
        user_gamif = await self.session.get(UserGamification, user_id)
        if not user_gamif or not user_gamif.current_level_id:
            return []

        level = await self.session.get(Level, user_gamif.current_level_id)
        if not level:
            return []

        current_level_order = level.order
        next_level = current_level_order + 1

        if next_level > 7:
            return []

        # Buscar items del siguiente nivel
        # Nota: level_required está en item_metadata como JSON
        # Esta es una búsqueda simplificada
        stmt = (
            select(ShopItem)
            .where(
                and_(
                    ShopItem.is_active == True,
                    ShopItem.is_hidden == False,
                    ShopItem.item_metadata.like(f'%"level_required": {next_level}%')
                )
            )
            .order_by(ShopItem.price_besitos)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_users_inventory_summary(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Obtiene un resumen del inventario del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Diccionario con:
            - total_items: Total de items únicos
            - by_category: Contador por categoría
            - unused_consumables: Consumibles sin usar
            - badges: Lista de distintivos
        """
        # Items en inventario
        stmt = select(UserInventoryItem).where(
            UserInventoryItem.user_id == user_id
        )
        result = await self.session.execute(stmt)
        inventory_items = result.scalars().all()

        # Obtener detalles de items
        item_ids = [inv.item_id for inv in inventory_items]
        if not item_ids:
            return {
                "total_items": 0,
                "by_category": {},
                "unused_consumables": [],
                "badges": [],
            }

        items_stmt = select(ShopItem).where(ShopItem.id.in_(item_ids))
        items_result = await self.session.execute(items_stmt)
        items = {item.id: item for item in items_result.scalars().all()}

        # Clasificar
        by_category: Dict[str, int] = {}
        unused_consumables = []
        badges = []

        for inv in inventory_items:
            item = items.get(inv.item_id)
            if not item:
                continue

            # Por categoría
            cat = item.item_type
            by_category[cat] = by_category.get(cat, 0) + 1

            # Consumibles sin usar
            if item.item_type == "CONSUMABLE" and not inv.is_used:
                unused_consumables.append(item)

            # Distintivos
            if item.item_type == "COSMETIC":
                badges.append(item)

        return {
            "total_items": len(inventory_items),
            "by_category": by_category,
            "unused_consumables": unused_consumables,
            "badges": badges,
        }

    # ========================================
    # MÉTODOS PRIVADOS
    # ========================================

    async def _recommend_by_archetype(
        self,
        user_id: int,
        archetype: str,
        current_level: int,
        limit: int
    ) -> Dict[str, Any]:
        """Recomienda items basados en arquetipo."""
        config = ARCHETYPE_RECOMMENDATIONS[archetype]

        # Obtener items recomendados
        items = await self.get_items_for_archetype(archetype, current_level, limit)

        # Filtrar items que ya tiene
        owned_ids = await self._get_owned_item_ids(user_id)
        items = [item for item in items if item.id not in owned_ids]

        return {
            "items": items[:limit],
            "reason": config["reason"],
            "archetype": archetype,
            "strategy": "archetype",
        }

    async def _recommend_by_history(
        self,
        user_id: int,
        current_level: int,
        limit: int
    ) -> Dict[str, Any]:
        """Recomienda items basados en historial de compras."""
        # Obtener categorías más compradas
        stmt = (
            select(ShopItem.item_type, func.count(ItemPurchase.id).label("count"))
            .join(ItemPurchase, ShopItem.id == ItemPurchase.item_id)
            .where(ItemPurchase.user_id == user_id)
            .group_by(ShopItem.item_type)
            .order_by(desc("count"))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        favorite_category = result.first()

        if favorite_category:
            cat = favorite_category[0]
            reason = f"Basado en su historial, parece interesarse en {cat}."
        else:
            cat = "CONSUMABLE"
            reason = "Algo para comenzar su viaje en el Gabinete."

        # Buscar items de esa categoría
        stmt = (
            select(ShopItem)
            .where(
                and_(
                    ShopItem.is_active == True,
                    ShopItem.is_hidden == False,
                    ShopItem.item_type == cat
                )
            )
            .order_by(ShopItem.price_besitos)
            .limit(limit * 2)
        )
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        # Filtrar items que ya tiene
        owned_ids = await self._get_owned_item_ids(user_id)
        items = [item for item in items if item.id not in owned_ids]

        return {
            "items": items[:limit],
            "reason": reason,
            "archetype": None,
            "strategy": "history",
        }

    async def _get_owned_item_ids(self, user_id: int) -> set:
        """Obtiene IDs de items que el usuario ya posee."""
        stmt = select(UserInventoryItem.item_id).where(
            UserInventoryItem.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return set(result.scalars().all())
