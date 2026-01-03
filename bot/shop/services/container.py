"""
Container de servicios del módulo de Tienda.

Implementa el patrón de Dependency Injection con lazy loading
para los servicios de la tienda.
"""

from typing import Optional, TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from aiogram import Bot
    from bot.shop.services.shop import ShopService
    from bot.shop.services.inventory import InventoryService
    from bot.shop.services.discounts import DiscountService
    from bot.shop.services.recommendations import RecommendationService
    from bot.shop.services.notifications import NotificationService


# Instancia global del container
_shop_container: Optional["ShopContainer"] = None


class ShopContainer:
    """
    Container de servicios para el módulo de tienda.

    Implementa lazy loading para cargar servicios solo cuando se necesitan.

    Uso:
        container = ShopContainer(session, bot)
        items = await container.shop.get_all_items()
        has_item = await container.inventory.has_item(user_id, item_id)
    """

    def __init__(self, session: AsyncSession, bot: Optional["Bot"] = None):
        """
        Inicializa el container.

        Args:
            session: Sesión async de SQLAlchemy
            bot: Instancia del bot de Telegram (opcional)
        """
        self._session = session
        self._bot = bot

        # Instancias lazy
        self._shop: Optional["ShopService"] = None
        self._inventory: Optional["InventoryService"] = None
        self._discounts: Optional["DiscountService"] = None
        self._recommendations: Optional["RecommendationService"] = None
        self._notifications: Optional["NotificationService"] = None

    @property
    def shop(self) -> "ShopService":
        """Obtiene el servicio de tienda (lazy loading)."""
        if self._shop is None:
            from bot.shop.services.shop import ShopService
            self._shop = ShopService(self._session)
        return self._shop

    @property
    def inventory(self) -> "InventoryService":
        """Obtiene el servicio de inventario (lazy loading)."""
        if self._inventory is None:
            from bot.shop.services.inventory import InventoryService
            self._inventory = InventoryService(self._session)
        return self._inventory

    @property
    def discounts(self) -> "DiscountService":
        """Obtiene el servicio de descuentos (lazy loading)."""
        if self._discounts is None:
            from bot.shop.services.discounts import DiscountService
            self._discounts = DiscountService(self._session)
        return self._discounts

    @property
    def recommendations(self) -> "RecommendationService":
        """Obtiene el servicio de recomendaciones (lazy loading)."""
        if self._recommendations is None:
            from bot.shop.services.recommendations import RecommendationService
            self._recommendations = RecommendationService(self._session)
        return self._recommendations

    @property
    def notifications(self) -> "NotificationService":
        """Obtiene el servicio de notificaciones (lazy loading)."""
        if self._notifications is None:
            from bot.shop.services.notifications import NotificationService
            self._notifications = NotificationService(self._session, self._bot)
        return self._notifications

    def get_loaded_services(self) -> list:
        """Retorna lista de servicios actualmente cargados."""
        loaded = []
        if self._shop is not None:
            loaded.append("shop")
        if self._inventory is not None:
            loaded.append("inventory")
        if self._discounts is not None:
            loaded.append("discounts")
        if self._recommendations is not None:
            loaded.append("recommendations")
        if self._notifications is not None:
            loaded.append("notifications")
        return loaded


def get_shop_container(
    session: Optional[AsyncSession] = None,
    bot: Optional["Bot"] = None
) -> ShopContainer:
    """
    Obtiene la instancia global del container de tienda.

    Si no existe, la crea con la sesión proporcionada.

    Args:
        session: Sesión de SQLAlchemy (requerida en primera llamada)
        bot: Instancia del bot

    Returns:
        ShopContainer configurado

    Raises:
        ValueError: Si no hay sesión en primera llamada
    """
    global _shop_container

    if _shop_container is None:
        if session is None:
            raise ValueError("Session is required for first initialization")
        _shop_container = ShopContainer(session, bot)
    elif session is not None:
        # Actualizar sesión si se proporciona una nueva
        _shop_container._session = session
        # Reset de servicios para usar nueva sesión
        _shop_container._shop = None
        _shop_container._inventory = None
        _shop_container._discounts = None
        _shop_container._recommendations = None
        _shop_container._notifications = None

    return _shop_container


def reset_shop_container() -> None:
    """Resetea el container global (útil para testing)."""
    global _shop_container
    _shop_container = None
