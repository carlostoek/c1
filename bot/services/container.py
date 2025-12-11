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

        logger.debug("🏭 ServiceContainer inicializado (modo lazy)")

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
