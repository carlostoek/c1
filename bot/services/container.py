"""
Service Container con Dependency Injection y Lazy Loading.
Optimizado para consumo mínimo de memoria en Termux.
"""
import logging
from typing import Optional

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ServiceContainer:
    """
    Contenedor de servicios con lazy loading.

    Los servicios se instancian solo cuando se acceden por primera vez.
    Esto reduce el consumo de memoria inicial en Termux.

    Patrón: Dependency Injection + Lazy Initialization

    Uso:
        container = ServiceContainer(session, bot)

        # Primera vez: carga el service
        token = await container.subscription.generate_token(...)

        # Segunda vez: reutiliza instancia
        result = await container.subscription.validate_token(...)
    """

    def __init__(self, session: AsyncSession, bot: Bot):
        """
        Inicializa el container con dependencias base.

        Args:
            session: Sesión de base de datos SQLAlchemy
            bot: Instancia del bot de Telegram
        """
        assert session is not None, "session no puede ser None"
        assert bot is not None, "bot no puede ser None"

        self._session = session
        self._bot = bot

        # Services (cargados lazy)
        self._subscription_service = None
        self._channel_service = None
        self._config_service = None
        self._stats_service = None
        self._pricing_service = None
        self._user_service = None
        self._broadcast_service = None
        self._menu_service = None

        logger.debug("🏭 ServiceContainer inicializado (modo lazy)")

    # ===== PROPIEDADES PÚBLICAS PARA DEPENDENCIAS =====

    @property
    def session(self) -> AsyncSession:
        """
        Sesión de base de datos.

        Returns:
            AsyncSession: Sesión actual de BD
        """
        return self._session

    @property
    def bot(self) -> Bot:
        """
        Instancia del bot de Telegram.

        Returns:
            Bot: Instancia del bot
        """
        return self._bot

    # ===== SUBSCRIPTION SERVICE =====

    @property
    def subscription(self):
        """
        Service de gestión de suscripciones VIP/Free.

        Se carga lazy (solo en primer acceso).

        Returns:
            SubscriptionService: Instancia del service
        """
        if self._subscription_service is None:
            from bot.services.subscription import SubscriptionService
            logger.debug("🔄 Lazy loading: SubscriptionService")
            self._subscription_service = SubscriptionService(self._session, self._bot)

        return self._subscription_service

    # ===== CHANNEL SERVICE =====

    @property
    def channel(self):
        """
        Service de gestión de canales Telegram.

        Se carga lazy (solo en primer acceso).

        Returns:
            ChannelService: Instancia del service
        """
        if self._channel_service is None:
            from bot.services.channel import ChannelService
            logger.debug("🔄 Lazy loading: ChannelService")
            self._channel_service = ChannelService(self._session, self._bot)

        return self._channel_service

    # ===== CONFIG SERVICE =====

    @property
    def config(self):
        """
        Service de configuración del bot.

        Se carga lazy (solo en primer acceso).

        Returns:
            ConfigService: Instancia del service
        """
        if self._config_service is None:
            from bot.services.config import ConfigService
            logger.debug("🔄 Lazy loading: ConfigService")
            self._config_service = ConfigService(self._session)

        return self._config_service

    # ===== STATS SERVICE =====

    @property
    def stats(self):
        """
        Service de estadísticas.

        Se carga lazy (solo en primer acceso).

        Returns:
            StatsService: Instancia del service
        """
        if self._stats_service is None:
            from bot.services.stats import StatsService
            logger.debug("🔄 Lazy loading: StatsService")
            self._stats_service = StatsService(self._session)

        return self._stats_service

    # ===== PRICING SERVICE =====

    @property
    def pricing(self):
        """
        Service de gestión de planes de suscripción/tarifas.

        Se carga lazy (solo en primer acceso).

        Returns:
            PricingService: Instancia del service
        """
        if self._pricing_service is None:
            from bot.services.pricing import PricingService
            logger.debug("🔄 Lazy loading: PricingService")
            self._pricing_service = PricingService(self._session)

        return self._pricing_service

    # ===== USER SERVICE =====

    @property
    def user(self):
        """
        Service de gestión de usuarios y roles.

        Se carga lazy (solo en primer acceso).

        Returns:
            UserService: Instancia del service
        """
        if self._user_service is None:
            from bot.services.user import UserService
            logger.debug("🔄 Lazy loading: UserService")
            self._user_service = UserService(self._session)

        return self._user_service

    # ===== BROADCAST SERVICE =====

    @property
    def broadcast(self):
        """
        Service de broadcasting con gamificación.

        Se carga lazy (solo en primer acceso).

        Returns:
            BroadcastService: Instancia del service
        """
        if self._broadcast_service is None:
            from bot.services.broadcast import BroadcastService
            logger.debug("🔄 Lazy loading: BroadcastService")
            self._broadcast_service = BroadcastService(self._session, self._bot)

        return self._broadcast_service

    # ===== MENU SERVICE =====

    @property
    def menu(self):
        """
        Service de configuración de menús dinámicos.

        Se carga lazy (solo en primer acceso).

        Returns:
            MenuService: Instancia del service
        """
        if self._menu_service is None:
            from bot.services.menu_service import MenuService
            logger.debug("🔄 Lazy loading: MenuService")
            self._menu_service = MenuService(self._session)

        return self._menu_service

    # ===== UTILIDADES =====

    def get_loaded_services(self) -> list[str]:
        """
        Retorna lista de servicios ya cargados en memoria.

        Útil para debugging y monitoring de uso de memoria.

        Returns:
            Lista de nombres de services cargados
        """
        loaded = []

        if self._subscription_service is not None:
            loaded.append("subscription")
        if self._channel_service is not None:
            loaded.append("channel")
        if self._config_service is not None:
            loaded.append("config")
        if self._stats_service is not None:
            loaded.append("stats")
        if self._pricing_service is not None:
            loaded.append("pricing")
        if self._user_service is not None:
            loaded.append("user")
        if self._broadcast_service is not None:
            loaded.append("broadcast")
        if self._menu_service is not None:
            loaded.append("menu")

        return loaded

    async def preload_critical_services(self):
        """
        Precarga servicios críticos de forma explícita.

        Se puede llamar en background después del startup
        para "calentar" los services más usados.

        Críticos: subscription, config (usados frecuentemente)
        No críticos: channel, stats (usados ocasionalmente)
        """
        logger.info("🔥 Precargando services críticos...")

        # Trigger lazy load accediendo a las properties
        _ = self.subscription
        _ = self.config

        logger.info(f"✅ Services precargados: {self.get_loaded_services()}")
