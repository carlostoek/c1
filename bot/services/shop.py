"""
Shop Service - Gestión de tienda de gamificación.

Maneja:
- Items de tienda
- Compras de usuarios
- Entrega de recompensas

NOTE: Implementación básica para SPRINT 1.
SPRINT 3 completará la funcionalidad completa.
"""
import logging
from typing import List, Tuple, Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot

from bot.database.gamification_models import ShopItem, ShopPurchase
from bot.database.enums import ShopItemType, TransactionType

logger = logging.getLogger(__name__)


class ShopService:
    """
    Servicio para gestión de tienda de gamificación.

    Attributes:
        _session: Sesión de base de datos SQLAlchemy
        _bot: Instancia del bot de Telegram
    """

    def __init__(self, session: AsyncSession, bot: Bot):
        """
        Inicializa el ShopService.

        Args:
            session: Sesión de base de datos SQLAlchemy
            bot: Instancia del bot de Telegram
        """
        self._session = session
        self._bot = bot

    # ===== ITEMS =====

    async def get_active_items(
        self,
        item_type: Optional[ShopItemType] = None
    ) -> List[ShopItem]:
        """
        Obtiene items activos de la tienda.

        Args:
            item_type: Filtrar por tipo (opcional)

        Returns:
            List[ShopItem]: Lista de items
        """
        query = select(ShopItem).where(ShopItem.active == True)

        if item_type:
            query = query.where(ShopItem.item_type == item_type)

        query = query.order_by(ShopItem.price_points)

        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_item(self, item_id: int) -> Optional[ShopItem]:
        """
        Obtiene un item por ID.

        Args:
            item_id: ID del item

        Returns:
            ShopItem o None si no existe
        """
        result = await self._session.execute(
            select(ShopItem).where(ShopItem.id == item_id)
        )
        return result.scalar_one_or_none()

    # ===== COMPRAS =====

    async def purchase_item(
        self,
        user_id: int,
        item_id: int
    ) -> Tuple[bool, str, Optional[ShopPurchase]]:
        """
        Compra un item de la tienda.

        Args:
            user_id: ID del usuario
            item_id: ID del item a comprar

        Returns:
            Tuple[bool, str, ShopPurchase]: (éxito, mensaje, compra)

        NOTE: Implementación completa en SPRINT 3
        """
        # TODO: Implementar lógica completa de compra
        # - Verificar stock
        # - Verificar puntos suficientes
        # - Descontar puntos
        # - Entregar recompensa
        return False, "Implementación pendiente (SPRINT 3)", None

    # ===== ENTREGA DE RECOMPENSAS =====

    async def deliver_reward(
        self,
        user_id: int,
        item: ShopItem
    ) -> Tuple[bool, str]:
        """
        Entrega la recompensa de un item comprado.

        Args:
            user_id: ID del usuario
            item: Item comprado

        Returns:
            Tuple[bool, str]: (éxito, mensaje)

        NOTE: Implementación completa en SPRINT 3
        """
        # TODO: Implementar según item_type:
        # - BADGE: Otorgar badge
        # - LEVEL: Asignar nivel
        # - VIP_DAYS: Extender suscripción
        # - MEDIA_SET: Enviar contenido
        return False, "Implementación pendiente (SPRINT 3)"
