"""
Tests para la integración cross-module (Fases 4 y 5).

Fase 4: Wizard Unificado
Fase 5: Panel de Configuración Central
"""

import pytest
import pytest_asyncio
from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from bot.gamification.database.models import (
    Base as GamificationBase,
    UserGamification, Mission, Reward, Level
)
from bot.gamification.database.enums import MissionType, RewardType


# ========================================
# FIXTURES
# ========================================

@pytest_asyncio.fixture
async def db_engine():
    """Crea engine de SQLite en memoria para tests cross-module."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        # Crear tablas de gamificación
        await conn.run_sync(GamificationBase.metadata.create_all)

        # Intentar crear tablas de shop y narrative si existen
        try:
            from bot.shop.database.models import Base as ShopBase
            await conn.run_sync(ShopBase.metadata.create_all)
        except ImportError:
            pass

        try:
            from bot.narrative.database import Base as NarrativeBase
            await conn.run_sync(NarrativeBase.metadata.create_all)
        except ImportError:
            pass

    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Sesión de BD en memoria para tests."""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def gamification_container(db_session):
    """Container de gamificación para tests."""
    from bot.gamification.services.container import GamificationContainer
    return GamificationContainer(db_session)


@pytest_asyncio.fixture
async def sample_data(db_session):
    """Crea datos de prueba en todos los módulos."""
    # Gamificación: Misión
    mission = Mission(
        name="Misión de Prueba",
        description="Descripción de prueba",
        mission_type=MissionType.ONE_TIME.value,
        criteria='{"type": "one_time", "count": 10}',
        besitos_reward=100,
        active=True,
        created_by=999
    )
    db_session.add(mission)

    # Gamificación: Recompensa
    reward = Reward(
        name="Recompensa de Prueba",
        description="Descripción de prueba",
        reward_type=RewardType.BADGE.value,
        active=True,
        created_by=999
    )
    db_session.add(reward)

    # Gamificación: Nivel
    level = Level(
        name="Nivel Prueba",
        min_besitos=0,
        order=1,
        active=True
    )
    db_session.add(level)

    # Gamificación: Usuario
    user = UserGamification(
        user_id=12345,
        total_besitos=500
    )
    db_session.add(user)

    await db_session.commit()

    return {
        "mission": mission,
        "reward": reward,
        "level": level,
        "user": user
    }


# ========================================
# TESTS FASE 4: WIZARD UNIFICADO
# ========================================

class TestUnifiedWizardStates:
    """Tests para los estados del wizard unificado."""

    def test_unified_wizard_states_exist(self):
        """Verifica que UnifiedWizardStates existe y tiene los estados correctos."""
        from bot.gamification.states.admin import UnifiedWizardStates

        # Verificar estados principales
        assert hasattr(UnifiedWizardStates, 'main_menu')
        assert hasattr(UnifiedWizardStates, 'creating_mission')
        assert hasattr(UnifiedWizardStates, 'creating_reward')
        assert hasattr(UnifiedWizardStates, 'creating_shop_item')
        assert hasattr(UnifiedWizardStates, 'creating_chapter')

    def test_shop_item_states_exist(self):
        """Verifica que los estados de creación de item de tienda existen."""
        from bot.gamification.states.admin import UnifiedWizardStates

        assert hasattr(UnifiedWizardStates, 'shop_select_category')
        assert hasattr(UnifiedWizardStates, 'shop_enter_name')
        assert hasattr(UnifiedWizardStates, 'shop_enter_description')
        assert hasattr(UnifiedWizardStates, 'shop_enter_price')
        assert hasattr(UnifiedWizardStates, 'shop_select_type')
        assert hasattr(UnifiedWizardStates, 'shop_select_rarity')
        assert hasattr(UnifiedWizardStates, 'shop_enter_icon')
        assert hasattr(UnifiedWizardStates, 'shop_confirm')

    def test_chapter_states_exist(self):
        """Verifica que los estados de creación de capítulo existen."""
        from bot.gamification.states.admin import UnifiedWizardStates

        assert hasattr(UnifiedWizardStates, 'chapter_enter_name')
        assert hasattr(UnifiedWizardStates, 'chapter_enter_slug')
        assert hasattr(UnifiedWizardStates, 'chapter_enter_description')
        assert hasattr(UnifiedWizardStates, 'chapter_select_type')
        assert hasattr(UnifiedWizardStates, 'chapter_enter_order')
        assert hasattr(UnifiedWizardStates, 'chapter_confirm')


class TestConfigPanelStates:
    """Tests para los estados del panel de configuración."""

    def test_config_panel_states_exist(self):
        """Verifica que ConfigPanelStates existe y tiene los estados correctos."""
        from bot.gamification.states.admin import ConfigPanelStates

        assert hasattr(ConfigPanelStates, 'main_dashboard')
        assert hasattr(ConfigPanelStates, 'filter_by_module')
        assert hasattr(ConfigPanelStates, 'search_objects')
        assert hasattr(ConfigPanelStates, 'toggle_active')
        assert hasattr(ConfigPanelStates, 'quick_edit')


# ========================================
# TESTS FASE 5: CONFIGURATION PANEL SERVICE
# ========================================

class TestConfigurationPanelService:
    """Tests para el servicio de panel de configuración."""

    @pytest.mark.asyncio
    async def test_get_gamification_stats(self, gamification_container, sample_data):
        """Verifica estadísticas de gamificación."""
        stats = await gamification_container.config_panel.get_gamification_stats()

        assert stats['status'] == 'ok'
        assert stats['module'] == 'gamification'
        assert stats['missions_active'] >= 1
        assert stats['rewards_active'] >= 1
        assert stats['levels_count'] >= 1
        assert stats['users_with_profile'] >= 1

    @pytest.mark.asyncio
    async def test_get_global_summary(self, gamification_container, sample_data):
        """Verifica resumen global de todos los módulos."""
        summary = await gamification_container.config_panel.get_global_summary()

        assert 'timestamp' in summary
        assert 'health' in summary
        assert 'modules_status' in summary
        assert 'gamification' in summary
        assert 'totals' in summary

        # Verificar que gamificación está ok
        assert summary['modules_status']['gamification'] == 'ok'

    @pytest.mark.asyncio
    async def test_list_all_missions(self, gamification_container, sample_data):
        """Verifica listado de misiones."""
        missions = await gamification_container.config_panel.get_all_missions()

        assert len(missions) >= 1
        assert missions[0]['name'] == 'Misión de Prueba'
        assert missions[0]['module'] == 'gamification'

    @pytest.mark.asyncio
    async def test_list_all_rewards(self, gamification_container, sample_data):
        """Verifica listado de recompensas."""
        rewards = await gamification_container.config_panel.get_all_rewards()

        assert len(rewards) >= 1
        assert rewards[0]['name'] == 'Recompensa de Prueba'
        assert rewards[0]['module'] == 'gamification'

    @pytest.mark.asyncio
    async def test_toggle_mission_active(self, gamification_container, sample_data, db_session):
        """Verifica toggle de estado activo de misión."""
        mission_id = sample_data['mission'].id

        # Verificar estado inicial (activo)
        missions = await gamification_container.config_panel.get_all_missions(active_only=False)
        initial_state = next(m for m in missions if m['id'] == mission_id)['is_active']
        assert initial_state is True

        # Toggle
        success = await gamification_container.config_panel.toggle_mission_active(mission_id)
        assert success is True

        # Verificar cambio
        missions = await gamification_container.config_panel.get_all_missions(active_only=False)
        new_state = next(m for m in missions if m['id'] == mission_id)['is_active']
        assert new_state is False

    @pytest.mark.asyncio
    async def test_toggle_reward_active(self, gamification_container, sample_data, db_session):
        """Verifica toggle de estado activo de recompensa."""
        reward_id = sample_data['reward'].id

        # Toggle
        success = await gamification_container.config_panel.toggle_reward_active(reward_id)
        assert success is True

        # Verificar cambio
        rewards = await gamification_container.config_panel.get_all_rewards(active_only=False)
        new_state = next(r for r in rewards if r['id'] == reward_id)['is_active']
        assert new_state is False

    @pytest.mark.asyncio
    async def test_dashboard_text_generation(self, gamification_container, sample_data):
        """Verifica generación de texto del dashboard."""
        text = await gamification_container.config_panel.get_dashboard_text()

        assert 'Panel de Configuración Central' in text
        assert 'GAMIFICACIÓN' in text
        assert 'TIENDA' in text
        assert 'NARRATIVA' in text
        assert 'Misiones activas:' in text

    @pytest.mark.asyncio
    async def test_pagination_missions(self, gamification_container, db_session):
        """Verifica paginación de misiones."""
        # Crear múltiples misiones
        for i in range(7):
            mission = Mission(
                name=f"Misión {i+1}",
                description="Descripción",
                mission_type=MissionType.ONE_TIME.value,
                criteria='{}',
                besitos_reward=10,
                active=True,
                created_by=999
            )
            db_session.add(mission)
        await db_session.commit()

        # Obtener primera página
        page1 = await gamification_container.config_panel.get_all_missions(
            limit=5, offset=0
        )
        assert len(page1) == 5

        # Obtener segunda página
        page2 = await gamification_container.config_panel.get_all_missions(
            limit=5, offset=5
        )
        assert len(page2) >= 2

    @pytest.mark.asyncio
    async def test_toggle_nonexistent_mission(self, gamification_container):
        """Verifica toggle de misión inexistente."""
        success = await gamification_container.config_panel.toggle_mission_active(99999)
        assert success is False


# ========================================
# TESTS DE INTEGRACIÓN CONTAINER
# ========================================

class TestContainerIntegration:
    """Tests de integración del container con el nuevo servicio."""

    @pytest.mark.asyncio
    async def test_config_panel_lazy_loading(self, db_session):
        """Verifica que config_panel se carga de forma lazy."""
        from bot.gamification.services.container import GamificationContainer

        container = GamificationContainer(db_session)

        # Inicialmente no debería estar cargado
        assert 'config_panel' not in container.get_loaded_services()

        # Acceder al servicio
        _ = container.config_panel

        # Ahora debería estar cargado
        assert 'config_panel' in container.get_loaded_services()

    @pytest.mark.asyncio
    async def test_container_clear_cache(self, db_session):
        """Verifica que clear_cache limpia config_panel."""
        from bot.gamification.services.container import GamificationContainer

        container = GamificationContainer(db_session)

        # Cargar servicio
        _ = container.config_panel
        assert 'config_panel' in container.get_loaded_services()

        # Limpiar cache
        container.clear_cache()
        assert 'config_panel' not in container.get_loaded_services()


# ========================================
# TESTS DE SLUGIFY
# ========================================

class TestSlugify:
    """Tests para la función slugify del wizard unificado."""

    def test_slugify_basic(self):
        """Verifica slugify básico."""
        from bot.gamification.handlers.admin.unified_wizard import slugify

        assert slugify("Hello World") == "hello-world"
        assert slugify("Los Kinkys") == "los-kinkys"
        # La función slugify preserva caracteres unicode (acentos)
        result = slugify("Capítulo 1")
        assert result == "capítulo-1"  # Los acentos se preservan con \w

    def test_slugify_special_chars(self):
        """Verifica slugify con caracteres especiales."""
        from bot.gamification.handlers.admin.unified_wizard import slugify

        assert slugify("Hello! World?") == "hello-world"
        assert slugify("Test @#$ Name") == "test-name"

    def test_slugify_spaces(self):
        """Verifica slugify con múltiples espacios."""
        from bot.gamification.handlers.admin.unified_wizard import slugify

        assert slugify("Hello    World") == "hello-world"
        assert slugify("  Spaces  ") == "spaces"
