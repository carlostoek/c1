"""
Servicio de notificaciones del Gabinete.

Responsabilidades:
- Notificar a usuarios sobre items nuevos
- Alertar sobre stock bajo de items
- Recordar items temporales por expirar
"""

from typing import List, Dict, Any, Optional, Set
from datetime import datetime, UTC, timedelta
import logging

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.shop.database.models import ShopItem, ItemPurchase, UserInventoryItem
from bot.gamification.database.models import UserGamification

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Servicio de notificaciones para el Gabinete.

    Genera notificaciones personalizadas sobre:
    - Items nuevos disponibles
    - Items con stock bajo
    - Items temporales por expirar
    """

    # Umbrales para notificaciones
    LOW_STOCK_THRESHOLD = 10  # Items con stock <= 10 generan alerta
    EXPIRY_SOON_HOURS = 24  # Items que expiran en 24h generan recordatorio

    def __init__(self, session: AsyncSession, bot: Optional[Bot] = None):
        """
        Inicializa el servicio de notificaciones.

        Args:
            session: Sesión async de SQLAlchemy
            bot: Instancia del bot de Telegram (opcional, para envío directo)
        """
        self.session = session
        self.bot = bot

    async def get_new_items_notification(
        self,
        since_hours: int = 24,
        user_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Genera notificación sobre items nuevos.

        Args:
            since_hours: Horas atrás para buscar items nuevos
            user_id: ID del usuario (para personalizar descuentos)

        Returns:
            Diccionario con:
            - has_new: True si hay items nuevos
            - items: Lista de items nuevos
            - message: Mensaje formateado
            - keyboard: InlineKeyboard con links
        """
        since = datetime.now(UTC) - timedelta(hours=since_hours)

        stmt = select(ShopItem).where(
            and_(
                ShopItem.is_active == True,
                ShopItem.created_at >= since
            )
        ).order_by(ShopItem.created_at.desc())

        result = await self.session.execute(stmt)
        new_items = list(result.scalars().all())

        if not new_items:
            return None

        # Generar mensaje
        item_list = []
        for item in new_items[:5]:  # Máximo 5 items
            item_list.append(
                f"{item.icon} <b>{item.name}</b>\n"
                f"{item.description}\n"
                f"💰 {item.price_besitos} Besitos\n"
            )

        message = (
            "✨ <b>El Gabinete tiene algo nuevo</b>\n\n"
            f"{len(new_items)} item(s) añadido(s):\n\n"
            + "\n".join(item_list)
        )

        if len(new_items) > 5:
            message += f"\n\n... y {len(new_items) - 5} más."

        # Generar keyboard
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Ver en el Gabinete", callback_data="shop:browse")]
        ])

        return {
            "has_new": True,
            "items": new_items,
            "count": len(new_items),
            "message": message,
            "keyboard": keyboard,
        }

    async def get_low_stock_notification(
        self,
        user_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Genera notificación sobre items con stock bajo.

        Args:
            user_id: ID del usuario (para filtrar items que le interesan)

        Returns:
            Diccionario con notificación o None si no hay stock bajo
        """
        stmt = select(ShopItem).where(
            and_(
                ShopItem.is_active == True,
                ShopItem.stock != None,
                ShopItem.stock <= self.LOW_STOCK_THRESHOLD,
                ShopItem.stock > 0
            )
        ).order_by(ShopItem.stock)

        result = await self.session.execute(stmt)
        low_stock_items = list(result.scalars().all())

        if not low_stock_items:
            return None

        # Generar mensaje
        item_list = []
        for item in low_stock_items[:5]:
            item_list.append(
                f"⚠️ {item.icon} <b>{item.name}</b>\n"
                f"   Quedan: <b>{item.stock}</b> unidades\n"
            )

        message = (
            "🚨 <b>Aviso del Gabinete</b>\n\n"
            "Los siguientes items están casi agotados:\n\n"
            + "\n".join(item_list)
        )

        if len(low_stock_items) > 5:
            message += f"\n\n... y {len(low_stock_items) - 5} más."

        message += "\n\nSi los deseaba... el momento es ahora."

        # Generar keyboard
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Ir al Gabinete", callback_data="shop:browse")]
        ])

        return {
            "has_low_stock": True,
            "items": low_stock_items,
            "count": len(low_stock_items),
            "message": message,
            "keyboard": keyboard,
        }

    async def get_expiring_soon_notification(
        self,
        user_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Genera notificación sobre items temporales por expirar.

        Args:
            user_id: ID del usuario (para personalizar)

        Returns:
            Diccionario con notificación o None si no hay items por expirar
        """
        soon = datetime.now(UTC) + timedelta(hours=self.EXPIRY_SOON_HOURS)

        stmt = select(ShopItem).where(
            and_(
                ShopItem.is_active == True,
                ShopItem.available_until != None,
                ShopItem.available_until <= soon,
                ShopItem.available_until > datetime.now(UTC)
            )
        ).order_by(ShopItem.available_until)

        result = await self.session.execute(stmt)
        expiring_items = list(result.scalars().all())

        if not expiring_items:
            return None

        # Generar mensaje
        item_list = []
        for item in expiring_items[:5]:
            hours_left = int((item.available_until - datetime.now(UTC)).total_seconds() / 3600)
            item_list.append(
                f"⏰ {item.icon} <b>{item.name}</b>\n"
                f"   Expira en: <b>{hours_left}h</b>\n"
            )

        message = (
            "⏳ <b>Recordatorio del Gabinete</b>\n\n"
            "Los siguientes items dejarán de estar disponibles pronto:\n\n"
            + "\n".join(item_list)
        )

        if len(expiring_items) > 5:
            message += f"\n\n... y {len(expiring_items) - 5} más."

        message += "\n\nEs la última oportunidad."

        # Generar keyboard
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏃‍♂️ Ver ahora", callback_data="shop:browse")]
        ])

        return {
            "has_expiring": True,
            "items": expiring_items,
            "count": len(expiring_items),
            "message": message,
            "keyboard": keyboard,
        }

    async def get_all_notifications(
        self,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """
        Obtiene todas las notificaciones pendientes para un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Lista de notificaciones
        """
        notifications = []

        # Items nuevos
        new_items = await self.get_new_items_notification(user_id=user_id)
        if new_items and new_items["has_new"]:
            notifications.append({
                "type": "new_items",
                "priority": "high",
                **new_items
            })

        # Stock bajo
        low_stock = await self.get_low_stock_notification(user_id=user_id)
        if low_stock and low_stock["has_low_stock"]:
            notifications.append({
                "type": "low_stock",
                "priority": "medium",
                **low_stock
            })

        # Items por expirar
        expiring = await self.get_expiring_soon_notification(user_id=user_id)
        if expiring and expiring["has_expiring"]:
            notifications.append({
                "type": "expiring_soon",
                "priority": "high",
                **expiring
            })

        return notifications

    async def send_notification_to_user(
        self,
        user_id: int,
        notification: Dict[str, Any]
    ) -> bool:
        """
        Envía una notificación a un usuario.

        Args:
            user_id: ID del usuario
            notification: Notificación a enviar

        Returns:
            True si se envió correctamente
        """
        if not self.bot:
            logger.warning("No bot instance available to send notification")
            return False

        try:
            from aiogram.types import InlineKeyboardMarkup

            # Reconstruir keyboard desde el dict
            keyboard_dict = notification.get("keyboard")
            keyboard = None
            if keyboard_dict:
                keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_dict.get("inline_keyboard", []))

            await self.bot.send_message(
                chat_id=user_id,
                text=notification["message"],
                parse_mode="HTML",
                reply_markup=keyboard
            )

            logger.info(f"Sent {notification['type']} notification to user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {e}")
            return False

    async def notify_users_about_new_item(
        self,
        item: ShopItem,
        user_ids: Optional[List[int]] = None
    ) -> int:
        """
        Notifica a usuarios sobre un item nuevo.

        Args:
            item: Item nuevo a notificar
            user_ids: Lista de usuarios a notificar (None = todos los VIPs)

        Returns:
            Cantidad de usuarios notificados
        """
        if not self.bot:
            return 0

        # Si no se especifican usuarios, notificar a VIPs
        if user_ids is None:
            user_ids = await self._get_vip_user_ids()

        message = (
            f"🆕 <b>Nuevo en el Gabinete</b>\n\n"
            f"{item.icon} <b>{item.name}</b>\n\n"
            f"{item.description}\n\n"
            f"💰 Precio: {item.price_besitos} Besitos\n"
        )

        # Agregar info de stock limitado si aplica
        if item.stock is not None and item.stock < 50:
            message += f"⚠️ Edición limitada: solo {item.stock} disponibles\n"

        # Agregar info de temporal si aplica
        if item.available_until:
            hours_left = int((item.available_until - datetime.now(UTC)).total_seconds() / 3600)
            message += f"⏰ Disponible por {hours_left} horas\n"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Ver item", callback_data=f"shop:item:{item.id}")]
        ])

        sent = 0
        for user_id in user_ids:
            try:
                await self.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
                sent += 1
            except Exception as e:
                logger.error(f"Error notifying user {user_id}: {e}")

        logger.info(f"Notified {sent} users about new item {item.name}")
        return sent

    async def _get_vip_user_ids(self) -> List[int]:
        """Obtiene IDs de usuarios VIP activos."""
        try:
            from bot.database.models import VIPSubscriber

            stmt = select(VIPSubscriber.user_id).where(
                and_(
                    VIPSubscriber.status == "active",
                    VIPSubscriber.expiry_date > datetime.now(UTC)
                )
            )
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting VIP users: {e}")
            return []
