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
        self._points_service = None
        self._reactions_service = None
        self._streak_service = None
        self._shop_service = None
        self._badges_service = None
        self._levels_service = None
        self._media_sets_service = None
        self._missions_service = None

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

    # ===== POINTS SERVICE =====

    @property
    def points(self):
        """
        Service de gestión de puntos ("besitos").

        Se carga lazy (solo en primer acceso).

        Returns:
            PointsService: Instancia del service
        """
        if self._points_service is None:
            from bot.services.points import PointsService
            logger.debug("🔄 Lazy loading: PointsService")
            self._points_service = PointsService(self._session, self._bot)

        return self._points_service

    # ===== REACTIONS SERVICE =====

    @property
    def reactions(self):
        """
        Service de gestión de reacciones personalizadas.

        Se carga lazy (solo en primer acceso).

        Returns:
            ReactionService: Instancia del service
        """
        if self._reactions_service is None:
            from bot.services.reactions import ReactionService
            logger.debug("🔄 Lazy loading: ReactionService")
            self._reactions_service = ReactionService(self._session, self._bot)

        return self._reactions_service

    # ===== STREAK SERVICE =====

    @property
    def streak(self):
        """
        Service de gestión de rachas de participación.

        Se carga lazy (solo en primer acceso).

        Returns:
            StreakService: Instancia del service
        """
        if self._streak_service is None:
            from bot.services.streak import StreakService
            logger.debug("🔄 Lazy loading: StreakService")
            self._streak_service = StreakService(self._session, self._bot)

        return self._streak_service

    # ===== SHOP SERVICE =====

    @property
    def shop(self):
        """
        Service de gestión de tienda de gamificación.

        Se carga lazy (solo en primer acceso).

        Returns:
            ShopService: Instancia del service
        """
        if self._shop_service is None:
            from bot.services.shop import ShopService
            logger.debug("🔄 Lazy loading: ShopService")
            self._shop_service = ShopService(self._session, self._bot)

        return self._shop_service

    # ===== BADGES SERVICE =====

    @property
    def badges(self):
        """
        Service de gestión de badges/insignias.

        Se carga lazy (solo en primer acceso).

        Returns:
            BadgeService: Instancia del service
        """
        if self._badges_service is None:
            from bot.services.badges import BadgeService
            logger.debug("🔄 Lazy loading: BadgeService")
            self._badges_service = BadgeService(self._session)

        return self._badges_service

    # ===== LEVELS SERVICE =====

    @property
    def levels(self):
        """
        Service de gestión de niveles de usuario.

        Se carga lazy (solo en primer acceso).

        Returns:
            LevelService: Instancia del service
        """
        if self._levels_service is None:
            from bot.services.levels import LevelService
            logger.debug("🔄 Lazy loading: LevelService")
            self._levels_service = LevelService(self._session)

        return self._levels_service

    # ===== MEDIA SETS SERVICE =====

    @property
    def media_sets(self):
        """
        Service de gestión de sets multimedia (CMS).

        Se carga lazy (solo en primer acceso).

        Returns:
            MediaSetService: Instancia del service
        """
        if self._media_sets_service is None:
            from bot.services.media_sets import MediaSetService
            logger.debug("🔄 Lazy loading: MediaSetService")
            self._media_sets_service = MediaSetService(self._session, self._bot)

        return self._media_sets_service

    # ===== MISSIONS SERVICE =====

    @property
    def missions(self):
        """
        Service de gestión de misiones de gamificación.

        Se carga lazy (solo en primer acceso).

        Returns:
            MissionService: Instancia del service
        """
        if self._missions_service is None:
            from bot.services.missions import MissionService
            logger.debug("🔄 Lazy loading: MissionService")
            self._missions_service = MissionService(self._session)

        return self._missions_service

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
        if self._points_service is not None:
            loaded.append("points")
        if self._reactions_service is not None:
            loaded.append("reactions")
        if self._streak_service is not None:
            loaded.append("streak")
        if self._shop_service is not None:
            loaded.append("shop")
        if self._badges_service is not None:
            loaded.append("badges")
        if self._levels_service is not None:
            loaded.append("levels")
        if self._media_sets_service is not None:
            loaded.append("media_sets")
        if self._missions_service is not None:
            loaded.append("missions")

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
