"""
Contenedor de servicios de gamificación.

Implementa Dependency Injection con lazy loading para gestionar
el ciclo de vida de los servicios del módulo.
"""

from typing import Optional, List, TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from aiogram import Bot


class GamificationContainer:
    """Contenedor de servicios con lazy loading."""

    def __init__(self, session: AsyncSession, bot: Optional["Bot"] = None):
        """
        Inicializa container.

        Args:
            session: Sesión async de SQLAlchemy
            bot: Instancia del bot de Telegram (opcional, requerido para notificaciones)
        """
        self._session = session
        self._bot = bot

        # Servicios (lazy loaded)
        self._reaction_service = None
        self._custom_reaction_service = None
        self._besito_service = None
        self._level_service = None
        self._mission_service = None
        self._reward_service = None
        self._user_gamification_service = None
        self._stats_service = None
        self._notification_service = None
        self._daily_gift_service = None
        self._unified_reward_service = None
        self._narrative_condition_service = None
        self._config_panel_service = None

        # Orchestrators (lazy loaded)
        self._mission_orchestrator = None
        self._reward_orchestrator = None
        self._configuration_orchestrator = None

    # ========================================
    # PROPERTIES (LAZY LOADING)
    # ========================================

    @property
    def reaction(self):
        """Servicio de reacciones."""
        if self._reaction_service is None:
            from bot.gamification.services.reaction import ReactionService
            self._reaction_service = ReactionService(self._session)
        return self._reaction_service

    @property
    def custom_reaction(self):
        """Servicio de reacciones personalizadas (broadcasting)."""
        if self._custom_reaction_service is None:
            from bot.gamification.services.custom_reaction import CustomReactionService
            self._custom_reaction_service = CustomReactionService(self._session)
        return self._custom_reaction_service

    @property
    def besito(self):
        """Servicio de besitos."""
        if self._besito_service is None:
            from bot.gamification.services.besito import BesitoService
            self._besito_service = BesitoService(self._session)
        return self._besito_service

    @property
    def level(self):
        """Servicio de niveles."""
        if self._level_service is None:
            from bot.gamification.services.level import LevelService
            self._level_service = LevelService(self._session)
        return self._level_service

    @property
    def mission(self):
        """Servicio de misiones."""
        if self._mission_service is None:
            from bot.gamification.services.mission import MissionService
            self._mission_service = MissionService(self._session)
        return self._mission_service

    @property
    def reward(self):
        """Servicio de recompensas."""
        if self._reward_service is None:
            from bot.gamification.services.reward import RewardService
            self._reward_service = RewardService(self._session)
        return self._reward_service

    @property
    def user_gamification(self):
        """Servicio de perfil de usuario."""
        if self._user_gamification_service is None:
            from bot.gamification.services.user_gamification import UserGamificationService
            self._user_gamification_service = UserGamificationService(self._session)
        return self._user_gamification_service

    @property
    def stats(self):
        """Servicio de estadísticas."""
        if self._stats_service is None:
            from bot.gamification.services.stats import StatsService
            self._stats_service = StatsService(self._session)
        return self._stats_service

    @property
    def notifications(self):
        """Servicio de notificaciones."""
        if self._notification_service is None:
            if self._bot is None:
                raise RuntimeError(
                    "NotificationService requires a Bot instance. "
                    "Initialize GamificationContainer with bot parameter."
                )
            from bot.gamification.services.notifications import NotificationService
            self._notification_service = NotificationService(self._bot, self._session)
        return self._notification_service

    @property
    def daily_gift(self):
        """Servicio de regalo diario."""
        if self._daily_gift_service is None:
            from bot.gamification.services.daily_gift import DailyGiftService
            self._daily_gift_service = DailyGiftService(self._session)
        return self._daily_gift_service

    @property
    def unified_reward(self):
        """Servicio unificado de recompensas cross-module."""
        if self._unified_reward_service is None:
            from bot.gamification.services.unified import UnifiedRewardService
            self._unified_reward_service = UnifiedRewardService(self._session)
        return self._unified_reward_service

    @property
    def narrative_condition(self):
        """Servicio de verificación de condiciones narrativas."""
        if self._narrative_condition_service is None:
            from bot.gamification.services.narrative_condition import NarrativeConditionService
            self._narrative_condition_service = NarrativeConditionService(self._session)
        return self._narrative_condition_service

    @property
    def config_panel(self):
        """Servicio de panel de configuración central (cross-module)."""
        if self._config_panel_service is None:
            from bot.gamification.services.config_panel import ConfigurationPanelService
            self._config_panel_service = ConfigurationPanelService(self._session)
        return self._config_panel_service

    @property
    def mission_orchestrator(self):
        """Orquestador de creación de misiones."""
        if self._mission_orchestrator is None:
            from bot.gamification.services.orchestrator.mission import MissionOrchestrator
            self._mission_orchestrator = MissionOrchestrator(self._session)
        return self._mission_orchestrator

    @property
    def reward_orchestrator(self):
        """Orquestador de creación de recompensas."""
        if self._reward_orchestrator is None:
            from bot.gamification.services.orchestrator.reward import RewardOrchestrator
            self._reward_orchestrator = RewardOrchestrator(self._session)
        return self._reward_orchestrator

    @property
    def configuration_orchestrator(self):
        """Orquestador maestro de configuración."""
        if self._configuration_orchestrator is None:
            from bot.gamification.services.orchestrator.configuration import ConfigurationOrchestrator
            self._configuration_orchestrator = ConfigurationOrchestrator(self._session)
        return self._configuration_orchestrator

    # ========================================
    # UTILIDADES
    # ========================================

    def get_loaded_services(self) -> List[str]:
        """Retorna servicios actualmente cargados."""
        loaded = []
        if self._reaction_service is not None:
            loaded.append('reaction')
        if self._custom_reaction_service is not None:
            loaded.append('custom_reaction')
        if self._besito_service is not None:
            loaded.append('besito')
        if self._level_service is not None:
            loaded.append('level')
        if self._mission_service is not None:
            loaded.append('mission')
        if self._reward_service is not None:
            loaded.append('reward')
        if self._user_gamification_service is not None:
            loaded.append('user_gamification')
        if self._stats_service is not None:
            loaded.append('stats')
        if self._notification_service is not None:
            loaded.append('notifications')
        if self._daily_gift_service is not None:
            loaded.append('daily_gift')
        if self._unified_reward_service is not None:
            loaded.append('unified_reward')
        if self._narrative_condition_service is not None:
            loaded.append('narrative_condition')
        if self._config_panel_service is not None:
            loaded.append('config_panel')
        if self._mission_orchestrator is not None:
            loaded.append('mission_orchestrator')
        if self._reward_orchestrator is not None:
            loaded.append('reward_orchestrator')
        if self._configuration_orchestrator is not None:
            loaded.append('configuration_orchestrator')
        return loaded

    def clear_cache(self):
        """Limpia todos los servicios cargados."""
        self._reaction_service = None
        self._custom_reaction_service = None
        self._besito_service = None
        self._level_service = None
        self._mission_service = None
        self._reward_service = None
        self._user_gamification_service = None
        self._stats_service = None
        self._notification_service = None
        self._daily_gift_service = None
        self._unified_reward_service = None
        self._narrative_condition_service = None
        self._config_panel_service = None
        self._mission_orchestrator = None
        self._reward_orchestrator = None
        self._configuration_orchestrator = None


# ========================================
# INSTANCIA GLOBAL
# ========================================

_container_instance: Optional[GamificationContainer] = None


def set_container(container: GamificationContainer):
    """Establece container global para acceso desde servicios."""
    global _container_instance
    _container_instance = container


def get_container() -> GamificationContainer:
    """Obtiene container global."""
    if _container_instance is None:
        raise RuntimeError("GamificationContainer not initialized. Call set_container() first.")
    return _container_instance


# Alias para conveniencia
class _ContainerProxy:
    """Proxy para acceso conveniente al container."""

    def __getattr__(self, name):
        return getattr(get_container(), name)


gamification_container = _ContainerProxy()
