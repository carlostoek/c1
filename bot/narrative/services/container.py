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
        return loaded

    def clear_cache(self):
        """Limpia todos los servicios cargados."""
        self._chapter_service = None
        self._fragment_service = None
        self._progress_service = None
        self._decision_service = None
        self._archetype_service = None
        self._requirements_service = None


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
