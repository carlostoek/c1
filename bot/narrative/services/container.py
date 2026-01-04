"""
Contenedor de servicios de narrativa.

Implementa Dependency Injection con lazy loading para gestionar
el ciclo de vida de los servicios del módulo de narrativa.
"""
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from aiogram import Bot


class NarrativeContainer:
    """
    Contenedor de servicios con lazy loading.

    Servicios disponibles (lazy loaded):
    - chapter: ChapterService (CRUD capítulos)
    - fragment: FragmentService (CRUD fragmentos)
    - progress: ProgressService (avance usuario)
    - decision: DecisionService (procesar decisiones)
    - archetype: ArchetypeService (detección arquetipos)
    - requirements: RequirementsService (validar condiciones)
    """

    def __init__(self, session: AsyncSession, bot: Optional["Bot"] = None):
        """
        Inicializa container.

        Args:
            session: Sesión async de SQLAlchemy
            bot: Instancia del bot de Telegram (opcional, para integración)
        """
        self._session = session
        self._bot = bot

        # Servicios (lazy loaded)
        self._chapter_service = None
        self._fragment_service = None
        self._progress_service = None
        self._decision_service = None
        self._archetype_service = None
        self._requirements_service = None
        self._import_service = None
        self._validation_service = None

        # Servicios inmersivos (lazy loaded)
        self._engagement_service = None
        self._clue_service = None
        self._variant_service = None
        self._cooldown_service = None
        self._challenge_service = None
        self._journal_service = None
    # ========================================
    # PROPERTIES (LAZY LOADING)
    # ========================================

    @property
    def chapter(self):
        """Servicio de capítulos narrativos."""
        if self._chapter_service is None:
            from bot.narrative.services.chapter import ChapterService
            self._chapter_service = ChapterService(self._session)
        return self._chapter_service

    @property
    def fragment(self):
        """Servicio de fragmentos narrativos."""
        if self._fragment_service is None:
            from bot.narrative.services.fragment import FragmentService
            self._fragment_service = FragmentService(self._session)
        return self._fragment_service

    @property
    def progress(self):
        """Servicio de progreso del usuario."""
        if self._progress_service is None:
            from bot.narrative.services.progress import ProgressService
            self._progress_service = ProgressService(self._session)
        return self._progress_service

    @property
    def decision(self):
        """Servicio de procesamiento de decisiones."""
        if self._decision_service is None:
            from bot.narrative.services.decision import DecisionService
            self._decision_service = DecisionService(self._session)
        return self._decision_service

    @property
    def archetype(self):
        """Servicio de detección de arquetipos."""
        if self._archetype_service is None:
            from bot.narrative.services.archetype import ArchetypeService
            self._archetype_service = ArchetypeService(self._session)
        return self._archetype_service

    @property
    def requirements(self):
        """Servicio de validación de requisitos."""
        if self._requirements_service is None:
            from bot.narrative.services.requirements import RequirementsService
            # Este servicio necesita acceso a otros módulos para validaciones
            self._requirements_service = RequirementsService(
                self._session,
                bot=self._bot
            )
        return self._requirements_service

    @property
    def import_service(self):
        """Servicio de importación de JSON."""
        if self._import_service is None:
            from bot.narrative.services.import_service import JsonImportService
            self._import_service = JsonImportService(
                self._session,
                bot=self._bot
            )
        return self._import_service

    @property
    def validation(self):
        """Servicio de validación de integridad narrativa."""
        if self._validation_service is None:
            from bot.narrative.services.validation import NarrativeValidationService
            self._validation_service = NarrativeValidationService(self._session)
        return self._validation_service

    # ========================================
    # SERVICIOS INMERSIVOS (LAZY LOADING)
    # ========================================

    @property
    def engagement(self):
        """Servicio de tracking de engagement."""
        if self._engagement_service is None:
            from bot.narrative.services.engagement import EngagementService
            self._engagement_service = EngagementService(self._session)
        return self._engagement_service

    @property
    def clue(self):
        """Servicio de gestión de pistas."""
        if self._clue_service is None:
            from bot.narrative.services.clue import ClueService
            self._clue_service = ClueService(self._session)
        return self._clue_service

    @property
    def variant(self):
        """Servicio de variantes de fragmentos."""
        if self._variant_service is None:
            from bot.narrative.services.variant import VariantService
            self._variant_service = VariantService(self._session)
        return self._variant_service

    @property
    def cooldown(self):
        """Servicio de cooldowns narrativos."""
        if self._cooldown_service is None:
            from bot.narrative.services.cooldown import CooldownService
            self._cooldown_service = CooldownService(self._session)
        return self._cooldown_service

    @property
    def challenge(self):
        """Servicio de desafíos interactivos."""
        if self._challenge_service is None:
            from bot.narrative.services.challenge import ChallengeService
            self._challenge_service = ChallengeService(self._session)
        return self._challenge_service

    @property
    def journal(self):
        """Servicio del diario de viaje."""
        if self._journal_service is None:
            from bot.narrative.services.journal import JournalService
            self._journal_service = JournalService(self._session)
        return self._journal_service

    # ========================================
    # UTILIDADES
    # ========================================

    def get_loaded_services(self) -> List[str]:
        """
        Retorna servicios actualmente cargados.

        Returns:
            Lista de nombres de servicios cargados
        """
        loaded = []
        if self._chapter_service is not None:
            loaded.append('chapter')
        if self._fragment_service is not None:
            loaded.append('fragment')
        if self._progress_service is not None:
            loaded.append('progress')
        if self._decision_service is not None:
            loaded.append('decision')
        if self._archetype_service is not None:
            loaded.append('archetype')
        if self._requirements_service is not None:
            loaded.append('requirements')
        if self._import_service is not None:
            loaded.append('import')
        if self._validation_service is not None:
            loaded.append('validation')
        # Servicios inmersivos
        if self._engagement_service is not None:
            loaded.append('engagement')
        if self._clue_service is not None:
            loaded.append('clue')
        if self._variant_service is not None:
            loaded.append('variant')
        if self._cooldown_service is not None:
            loaded.append('cooldown')
        if self._challenge_service is not None:
            loaded.append('challenge')
        if self._journal_service is not None:
            loaded.append('journal')
        return loaded

    def clear_cache(self):
        """Limpia todos los servicios cargados."""
        self._chapter_service = None
        self._fragment_service = None
        self._progress_service = None
        self._decision_service = None
        self._archetype_service = None
        self._requirements_service = None
        self._import_service = None
        self._validation_service = None
        # Servicios inmersivos
        self._engagement_service = None
        self._clue_service = None
        self._variant_service = None
        self._cooldown_service = None
        self._challenge_service = None
        self._journal_service = None


# ========================================
# INSTANCIA GLOBAL (OPCIONAL)
# ========================================

_container_instance: Optional[NarrativeContainer] = None


def set_container(container: NarrativeContainer):
    """
    Establece container global para acceso desde servicios.

    Args:
        container: Instancia de NarrativeContainer
    """
    global _container_instance
    _container_instance = container


def get_container() -> NarrativeContainer:
    """
    Obtiene container global.

    Returns:
        NarrativeContainer instanciado

    Raises:
        RuntimeError: Si el container no ha sido inicializado
    """
    if _container_instance is None:
        raise RuntimeError(
            "NarrativeContainer not initialized. Call set_container() first."
        )
    return _container_instance


# Alias para conveniencia
class _ContainerProxy:
    """Proxy para acceso conveniente al container."""

    def __getattr__(self, name):
        return getattr(get_container(), name)


narrative_container = _ContainerProxy()
