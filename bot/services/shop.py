"""
Shop Service - Gestión de tienda de gamificación.

Maneja:
- Items de tienda
- Compras de usuarios
- Entrega de recompensas
"""
import logging
from typing import List, Tuple, Optional
from datetime import datetime

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
        """
        # Obtener item
        item = await self.get_item(item_id)
        if item is None:
            return False, "Item no encontrado", None

        if not item.active:
            return False, "Este item no está disponible", None

        # Verificar stock
        if item.stock >= 0 and item.stock == 0:
            return False, "Este item está agotado", None

        # Verificar puntos suficientes
        from bot.services.points import PointsService
        points_service = PointsService(self._session, self._bot)
        points = await points_service.get_balance(user_id)

        if points is None or points.balance < item.price_points:
            return False, f"Puntos insuficientes (necesitas: {item.price_points})", None

        # Descontar puntos
        success, msg = await points_service.spend_points(
            user_id=user_id,
            amount=item.price_points,
            transaction_type="shop_purchase",
            description=f"Compra: {item.name}",
            reference_id=item_id
        )

        if not success:
            return False, msg, None

        # Entregar recompensa
        reward_success, reward_msg = await self.deliver_reward(user_id, item)

        if not reward_success:
            # Reembolsar puntos si falla la entrega
            await points_service.award_points(
                user_id=user_id,
                amount=item.price_points,
                transaction_type="shop_purchase",
                description=f"Reembolso: {item.name}",
                reference_id=item_id
            )
            return False, f"Error al entregar recompensa: {reward_msg}", None

        # Actualizar stock si es limitado
        if item.stock > 0:
            item.stock -= 1

        # Crear registro de compra
        purchase = ShopPurchase(
            user_id=user_id,
            item_id=item_id,
            points_spent=item.price_points,
            purchased_at=datetime.utcnow()
        )

        self._session.add(purchase)
        await self._session.commit()

        logger.info(
            f"🛒 Compra: user {user_id} → {item.name} "
            f"({item.price_points} pts)"
        )

        return True, f"¡Compraste {item.name}! {reward_msg}", purchase

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
        """
        if item.item_type == ShopItemType.BADGE:
            # Otorgar badge
            from bot.services.badges import BadgeService
            badge_service = BadgeService(self._session)
            return await badge_service.award_badge(user_id, item.reference_id)

        elif item.item_type == ShopItemType.LEVEL:
            # Los niveles son automáticos según puntos
            # No se pueden "comprar" directamente
            return False, "Los niveles se obtienen automáticamente con puntos"

        elif item.item_type == ShopItemType.VIP_DAYS:
            # Extender suscripción VIP
            from bot.services.subscription import SubscriptionService
            subscription_service = SubscriptionService(self._session, self._bot)

            # Obtener suscriptor actual
            subscriber = await subscription_service.get_vip_subscriber(user_id)

            if subscriber and subscription_service.is_vip_active(user_id):
                # Extender suscripción existente
                from datetime import timedelta
                subscriber.expiry_date = subscriber.expiry_date + timedelta(days=item.vip_days)
                await self._session.commit()
                return True, f"+{item.vip_days} días de VIP añadidos"
            else:
                # Crear nueva suscripción
                from datetime import timedelta, datetime
                expiry = datetime.utcnow() + timedelta(days=item.vip_days)
                new_subscriber = await subscription_service.create_vip_subscriber(
                    user_id=user_id,
                    expiry_date=expiry
                )
                return True, f"¡Suscripción VIP de {item.vip_days} días activada!"

        elif item.item_type == ShopItemType.MEDIA_SET:
            # Enviar contenido del media set
            from bot.services.media_sets import MediaSetService
            media_set_service = MediaSetService(self._session, self._bot)
            return await media_set_service.send_set_to_user(user_id, item.reference_id)

        else:
            return False, f"Tipo de item no soportado: {item.item_type}"
