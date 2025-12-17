"""
Service Container con Dependency Injection y Lazy Loading.
Optimizado para consumo mínimo de memoria en Termux.
"""
import logging
from typing import Optional

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.points import PointsService
from bot.services.levels import LevelsService

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
        self._notification_service = None
        self._gamification_service = None
        self._reactions_service = None
        self._points = None
        self._levels = None
        self._badges = None
        self._rewards = None
        self._missions = None

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

    # ===== NOTIFICATION SERVICE =====

    @property
    def notifications(self):
        """
        Service de notificaciones.

        Se carga lazy (solo en primer acceso).

        Returns:
            NotificationService: Instancia del service
        """
        if self._notification_service is None:
            from bot.notifications.service import NotificationService
            logger.debug("🔄 Lazy loading: NotificationService")
            self._notification_service = NotificationService(self._session, self._bot)

        return self._notification_service

    # ===== GAMIFICATION SERVICE =====

    @property
    def gamification(self):
        """
        Service de gamificación.

        Se carga lazy (solo en primer acceso).

        Returns:
            GamificationService: Instancia del service
        """
        if self._gamification_service is None:
            from bot.gamification.service import GamificationService
            logger.debug("🔄 Lazy loading: GamificationService")
            self._gamification_service = GamificationService(self._session)

        return self._gamification_service

    # ===== REACTIONS SERVICE =====

    @property
    def reactions(self):
        """
        Service de gestión de reacciones inline a mensajes.

        Se carga lazy (solo en primer acceso).

        Returns:
            ReactionService: Instancia del service

        Example:
            >>> container = ServiceContainer(session, bot)
            >>> active = await container.reactions.get_active_reactions()
            >>> await container.reactions.record_user_reaction(
            ...     channel_id=-1001234567890,
            ...     message_id=12345,
            ...     user_id=987654321,
            ...     emoji="❤️"
            ... )
        """
        if self._reactions_service is None:
            from bot.services.reactions import ReactionService
            logger.debug("🔄 Lazy loading: ReactionService")
            self._reactions_service = ReactionService(self._session)

        return self._reactions_service

    # ===== POINTS SERVICE =====

    @property
    def points(self) -> PointsService:
        """
        Servicio de gestión de puntos (besitos).

        Proporciona:
        - Otorgamiento de puntos con multiplicadores
        - Deducción de puntos para canjes
        - Consulta de saldo y estadísticas
        - Histórico de transacciones
        - Analytics del sistema

        Returns:
            Instancia de PointsService

        Example:
            >>> # En un handler
            >>> container = ServiceContainer(session, bot)
            >>> await container.points.award_points(
            ...     user_id=123,
            ...     amount=10,
            ...     reason="Reacción a publicación"
            ... )
        """
        if self._points is None:
            logger.debug("🔄 Lazy loading: PointsService")
            self._points = PointsService(self._session, self._bot)
        return self._points

    # ===== LEVELS SERVICE =====

    @property
    def levels(self) -> LevelsService:
        """
        Servicio de gestión de niveles (gamificación).

        Proporciona:
        - Verificación y aplicación de level-ups
        - Consulta de información de niveles
        - Cálculo de progreso hacia siguiente nivel
        - Obtención de multiplicadores por nivel
        - Información de perks por nivel

        Returns:
            Instancia de LevelsService

        Example:
            >>> container = ServiceContainer(session, bot)
            >>> # Verificar level-up
            >>> should_up, old, new = await container.levels.check_level_up(
            ...     user_id=123,
            ...     current_points=150
            ... )
            >>> # Obtener información de progreso
            >>> info = await container.levels.get_user_level_info(123)
        """
        if self._levels is None:
            logger.debug("🔄 Lazy loading: LevelsService")
            self._levels = LevelsService(self._session, self._bot)
        return self._levels

    # ===== BADGES SERVICE =====

    @property
    def badges(self):
        """
        Servicio de gestión de insignias coleccionables.

        Proporciona:
        - Asignación de badges a usuarios
        - Consulta de colecciones personales
        - Catálogo completo de badges
        - Verificación de posesión
        - Operaciones administrativas

        Returns:
            Instancia de BadgesService

        Example:
            >>> container = ServiceContainer(session, bot)
            >>> # Asignar badge
            >>> badge = await container.badges.assign_badge(
            ...     user_id=123,
            ...     badge_id=1,
            ...     source="mission"
            ... )
            >>> # Obtener colección del usuario
            >>> user_badges = await container.badges.get_user_badges(123)
        """
        if self._badges is None:
            from bot.services.badges import BadgesService
            logger.debug("🔄 Lazy loading: BadgesService")
            self._badges = BadgesService(self._session, self)

        return self._badges

    # ===== REWARDS SERVICE =====

    @property
    def rewards(self):
        """
        Servicio de gestión de recompensas canjeables.

        Proporciona:
        - Obtener catálogo de recompensas disponibles
        - Validar si usuario puede canjear
        - Ejecutar canje (deducir puntos, entregar recompensa)
        - Consultar histórico de canjes
        - Operaciones administrativas

        Returns:
            Instancia de RewardsService

        Example:
            >>> container = ServiceContainer(session, bot)
            >>> # Obtener recompensas disponibles
            >>> rewards = await container.rewards.get_available_rewards(user_id=123)
            >>> # Canjear recompensa
            >>> success, msg, reward = await container.rewards.redeem_reward(
            ...     user_id=123,
            ...     reward_id=1
            ... )
        """
        if self._rewards is None:
            from bot.services.rewards import RewardsService
            logger.debug("🔄 Lazy loading: RewardsService")
            self._rewards = RewardsService(self._session, self)

        return self._rewards

    # ===== MISSIONS SERVICE =====

    @property
    def missions(self):
        """
        Servicio de gestión de misiones.

        Proporciona:
        - Obtener misiones disponibles para usuario
        - Tracking automático de progreso
        - Reset de misiones temporales (daily, weekly)
        - Verificación de completado
        - Entrega de recompensas

        Returns:
            Instancia de MissionsService

        Example:
            >>> container = ServiceContainer(session, bot)
            >>> # Obtener misiones activas
            >>> missions = await container.missions.get_active_missions(user_id=123)
            >>> # Actualizar progreso
            >>> updated = await container.missions.update_progress(
            ...     user_id=123,
            ...     objective_type=ObjectiveType.POINTS,
            ...     amount=10
            ... )
        """
        if self._missions is None:
            from bot.services.missions import MissionsService
            logger.debug("🔄 Lazy loading: MissionsService")
            self._missions = MissionsService(self._session, self)

        return self._missions

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
        if self._notification_service is not None:
            loaded.append("notifications")
        if self._gamification_service is not None:
            loaded.append("gamification")
        if self._reactions_service is not None:
            loaded.append("reactions")
        if self._points is not None:
            loaded.append("points")
        if self._levels is not None:
            loaded.append("levels")
        if self._badges is not None:
            loaded.append("badges")
        if self._rewards is not None:
            loaded.append("rewards")
        if self._missions is not None:
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
