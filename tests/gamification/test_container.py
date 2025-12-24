"""
Tests para GamificationContainer - Dependency Injection.

Valida lazy loading, singleton pattern, instancia global.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.gamification.services import (
    GamificationContainer,
    set_container,
    get_container,
    gamification_container,
)
from bot.gamification.services.reaction import ReactionService
from bot.gamification.services.besito import BesitoService
from bot.gamification.services.level import LevelService
from bot.gamification.services.mission import MissionService
from bot.gamification.services.reward import RewardService
from bot.gamification.services.user_gamification import UserGamificationService


@pytest.mark.asyncio
async def test_container_initialization(db_session: AsyncSession):
    """Test 1: Container se inicializa correctamente."""
    container = GamificationContainer(db_session)

    # Servicios no deben estar cargados inicialmente
    loaded = container.get_loaded_services()
    assert loaded == [], f"Servicios no deberían estar cargados: {loaded}"


@pytest.mark.asyncio
async def test_lazy_loading_reaction_service(db_session: AsyncSession):
    """Test 2: ReactionService se carga solo al accederlo."""
    container = GamificationContainer(db_session)

    # Antes de acceder
    assert container.get_loaded_services() == []

    # Acceder al servicio
    reaction = container.reaction
    assert isinstance(reaction, ReactionService)

    # Ahora debe estar cargado
    assert 'reaction' in container.get_loaded_services()


@pytest.mark.asyncio
async def test_lazy_loading_all_services(db_session: AsyncSession):
    """Test 3: Todos los servicios se cargan correctamente con lazy loading."""
    container = GamificationContainer(db_session)

    # Acceder a cada servicio
    reaction = container.reaction
    besito = container.besito
    level = container.level
    mission = container.mission
    reward = container.reward
    user_gamif = container.user_gamification

    # Validar tipos
    assert isinstance(reaction, ReactionService)
    assert isinstance(besito, BesitoService)
    assert isinstance(level, LevelService)
    assert isinstance(mission, MissionService)
    assert isinstance(reward, RewardService)
    assert isinstance(user_gamif, UserGamificationService)

    # Todos deben estar cargados
    loaded = container.get_loaded_services()
    expected = ['reaction', 'besito', 'level', 'mission', 'reward', 'user_gamification']
    assert set(loaded) == set(expected)


@pytest.mark.asyncio
async def test_singleton_per_session(db_session: AsyncSession):
    """Test 4: Servicios se reutilizan dentro de la misma sesión (singleton)."""
    container = GamificationContainer(db_session)

    # Acceder dos veces al mismo servicio
    reaction1 = container.reaction
    reaction2 = container.reaction

    # Deben ser la misma instancia
    assert reaction1 is reaction2


@pytest.mark.asyncio
async def test_clear_cache(db_session: AsyncSession):
    """Test 5: clear_cache() limpia todos los servicios cargados."""
    container = GamificationContainer(db_session)

    # Cargar algunos servicios
    _ = container.reaction
    _ = container.besito
    assert len(container.get_loaded_services()) == 2

    # Limpiar cache
    container.clear_cache()

    # Servicios deben estar descargados
    assert container.get_loaded_services() == []

    # Acceder nuevamente crea nuevas instancias
    reaction_new = container.reaction
    assert isinstance(reaction_new, ReactionService)
    assert 'reaction' in container.get_loaded_services()


@pytest.mark.asyncio
async def test_global_instance_set_and_get(db_session: AsyncSession):
    """Test 6: set_container() y get_container() funcionan correctamente."""
    container = GamificationContainer(db_session)

    # Establecer como global
    set_container(container)

    # Obtener instancia global
    global_container = get_container()

    # Debe ser la misma instancia
    assert global_container is container


@pytest.mark.asyncio
async def test_global_instance_error_without_set(db_session: AsyncSession):
    """Test 7: get_container() lanza error si no se inicializó."""
    # Resetear instancia global
    from bot.gamification.services import container as container_module
    container_module._container_instance = None

    # Intentar obtener sin establecer
    with pytest.raises(RuntimeError, match="GamificationContainer not initialized"):
        get_container()


@pytest.mark.asyncio
async def test_gamification_container_proxy(db_session: AsyncSession):
    """Test 8: gamification_container proxy funciona correctamente."""
    container = GamificationContainer(db_session)
    set_container(container)

    # Acceder via proxy
    reaction = gamification_container.reaction
    assert isinstance(reaction, ReactionService)

    # get_loaded_services via proxy
    loaded = gamification_container.get_loaded_services()
    assert 'reaction' in loaded


@pytest.mark.asyncio
async def test_middleware_integration(db_session: AsyncSession):
    """Test 9: Simula integración con middleware."""
    # Simular data del middleware
    data = {}

    # Middleware crea container
    gamif_container = GamificationContainer(db_session)
    set_container(gamif_container)
    data["gamification"] = gamif_container

    # Handler accede al container
    container_from_data = data["gamification"]

    # Usar servicios
    reaction = container_from_data.reaction
    assert isinstance(reaction, ReactionService)

    # También puede acceder via global
    global_reaction = gamification_container.reaction
    assert global_reaction is reaction  # Misma instancia
