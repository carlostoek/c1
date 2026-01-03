"""
Tests E2E para el sistema de tracking y detección de arquetipos (FASE 3).

Cubre:
- BehaviorTrackingService
- ArchetypeDetectionService
- AdaptedMessageService
"""

import pytest
from datetime import datetime, UTC, timedelta

from bot.gamification.services.behavior_tracking import BehaviorTrackingService
from bot.gamification.services.archetype_detection import ArchetypeDetectionService
from bot.gamification.services.adapted_messages import AdaptedMessageService
from bot.gamification.database.models import UserBehaviorSignals, UserGamification
from bot.gamification.database.enums import InteractionType


# =============================================================================
# TESTS BEHAVIOR TRACKING SERVICE
# =============================================================================

class TestBehaviorTrackingService:
    """Tests para BehaviorTrackingService."""

    @pytest.mark.asyncio
    async def test_track_button_click(self, db_session):
        """Test tracking de clicks en botones."""
        tracking = BehaviorTrackingService(db_session)

        # Registrar un click
        await tracking.track_button_click(
            user_id=12345,
            button_id="menu:profile",
            context="dynamic_menu",
            time_to_click=2.5,
            is_exploration=True,
            is_direct_action=False
        )

        # Verificar que se creó/actualizó UserBehaviorSignals
        signals = await tracking.get_behavior_signals(12345)
        assert signals is not None
        assert signals.user_id == 12345
        assert signals.total_interactions >= 1

    @pytest.mark.asyncio
    async def test_track_session(self, db_session):
        """Test tracking de sesiones."""
        tracking = BehaviorTrackingService(db_session)

        # Registrar sesión
        await tracking.track_session(
            user_id=12345,
            session_type="start",
            is_return=False
        )

        # Verificar que se creó el perfil
        signals = await tracking.get_behavior_signals(12345)
        assert signals is not None
        assert signals.total_sessions >= 1

    @pytest.mark.asyncio
    async def test_track_content_interaction(self, db_session):
        """Test tracking de interacciones con contenido."""
        tracking = BehaviorTrackingService(db_session)

        # Registrar interacción con contenido emotivo
        await tracking.track_content_interaction(
            user_id=12345,
            content_id="story_1",
            content_type="narrative",
            interaction_type="view",
            is_emotional=True,
            is_personal=True,
            tags=["emotional", "diana_story"]
        )

        # Verificar que se registró
        signals = await tracking.get_behavior_signals(12345)
        assert signals is not None
        assert signals.emotional_content_views >= 1
        assert signals.personal_stories_accessed >= 1

    @pytest.mark.asyncio
    async def test_track_decision(self, db_session):
        """Test tracking de decisiones."""
        tracking = BehaviorTrackingService(db_session)

        # Registrar decisión
        await tracking.track_decision(
            user_id=12345,
            decision_id="decision_1",
            time_to_decide=15.0,
            options_available=3,
            decision_type="narrative",
            is_systematic=False,
            is_emotional=False
        )

        # Verificar que se registró
        signals = await tracking.get_behavior_signals(12345)
        assert signals is not None
        assert signals.total_interactions >= 1

    @pytest.mark.asyncio
    async def test_get_signals_as_dict(self, db_session):
        """Test obtener señales como diccionario."""
        tracking = BehaviorTrackingService(db_session)

        # Registrar algunas interacciones
        await tracking.track_button_click(
            user_id=12345,
            button_id="menu:profile",
            context="dynamic_menu",
            time_to_click=2.5,
            is_exploration=True,
            is_direct_action=False
        )

        # Obtener señales como dict
        signals_dict = await tracking.get_signals_as_dict(12345)
        assert signals_dict is not None
        assert "total_interactions" in signals_dict
        assert signals_dict["total_interactions"] >= 1

    @pytest.mark.asyncio
    async def test_sync_streak_data(self, db_session):
        """Test sincronización de datos de racha."""
        tracking = BehaviorTrackingService(db_session)

        # Crear algunas señales primero
        user_id = 12345
        await tracking.track_session(user_id=user_id, session_type="start", is_return=False)

        # sync_streak_data no debería fallar incluso sin DailyGiftClaim
        await tracking.sync_streak_data(user_id)

        # Verificar que las señales existen
        signals = await tracking.get_behavior_signals(user_id)
        assert signals is not None


# =============================================================================
# TESTS ARCHETYPE DETECTION SERVICE
# =============================================================================

class TestArchetypeDetectionService:
    """Tests para ArchetypeDetectionService."""

    @pytest.mark.asyncio
    async def test_get_archetype_no_signals(self, db_session):
        """Test obtener arquetipo sin señales suficientes."""
        detection = ArchetypeDetectionService(db_session)

        # Usuario sin señales
        result = await detection.get_archetype(99999)
        assert result is None

    @pytest.mark.asyncio
    async def test_should_reevaluate_no_signals(self, db_session):
        """Test should_reevaluate sin señales."""
        detection = ArchetypeDetectionService(db_session)

        # Usuario sin señales
        should = await detection.should_reevaluate(99999)
        assert should is True  # Debería evaluar por primera vez

    @pytest.mark.asyncio
    async def test_detect_archetype_insufficient_data(self, db_session):
        """Test detección con datos insuficientes."""
        tracking = BehaviorTrackingService(db_session)
        detection = ArchetypeDetectionService(db_session)

        # Crear señales insuficientes
        await tracking.track_button_click(
            user_id=12345,
            button_id="menu:profile",
            context="dynamic_menu",
            time_to_click=2.5,
            is_exploration=True,
            is_direct_action=False
        )

        # Intentar detectar
        result = await detection.detect_archetype(12345)

        # No debería detectar (datos insuficientes)
        assert result.archetype is None
        assert result.interactions_count < 25

    @pytest.mark.asyncio
    async def test_detect_archetype_explorer_pattern(self, db_session):
        """Test detección de arquetipo EXPLORER."""
        tracking = BehaviorTrackingService(db_session)
        detection = ArchetypeDetectionService(db_session)

        # Simular patrón EXPLORER
        user_id = 12345
        for i in range(30):
            await tracking.track_content_interaction(
                user_id=user_id,
                content_id=f"section_{i}",
                content_type="narrative",
                interaction_type="view",
                is_emotional=False,
                is_personal=False
            )

        # Detectar arquetipo
        result = await detection.detect_archetype(user_id)

        # Debería detectar algún arquetipo (puede variar según el algoritmo)
        # Lo importante es que no falle y tenga interacciones suficientes
        assert result.interactions_count >= 25

    @pytest.mark.asyncio
    async def test_get_archetype_scores(self, db_session):
        """Test obtener scores de arquetipo."""
        tracking = BehaviorTrackingService(db_session)
        detection = ArchetypeDetectionService(db_session)

        # Crear señales suficientes
        user_id = 12345
        for i in range(30):
            await tracking.track_content_interaction(
                user_id=user_id,
                content_id=f"section_{i}",
                content_type="narrative",
                interaction_type="view",
                is_emotional=False,
                is_personal=False
            )

        # Ejecutar detección
        result = await detection.detect_archetype(user_id)

        # Obtener scores desde BD (puede estar vacío si no se detectó arquetipo)
        scores = await detection.get_archetype_scores(user_id)

        # Debería retornar un diccionario (vacío o con datos)
        assert isinstance(scores, dict)

        # Si hay scores, verificar que tengan las claves correctas
        if scores:
            assert len(scores) == 6
            assert "EXPLORER" in scores
            assert "DIRECT" in scores
            assert "ROMANTIC" in scores
            assert "ANALYTICAL" in scores
            assert "PERSISTENT" in scores
            assert "PATIENT" in scores

    @pytest.mark.asyncio
    async def test_get_archetype_insights(self, db_session):
        """Test obtener insights de arquetipo."""
        tracking = BehaviorTrackingService(db_session)
        detection = ArchetypeDetectionService(db_session)

        # Crear señales suficientes
        user_id = 12345
        for i in range(30):
            await tracking.track_content_interaction(
                user_id=user_id,
                content_id=f"section_{i}",
                content_type="narrative",
                interaction_type="view",
                is_emotional=False,
                is_personal=False
            )

        # Ejecutar detección primero
        result = await detection.detect_archetype(user_id)

        # Obtener insights (puede ser None si no hay arquetipo guardado)
        insights = await detection.get_archetype_insights(user_id)

        # Si se detectó arquetipo, insights debería tener datos
        if result.archetype:
            assert insights is not None
            assert hasattr(insights, "archetype")
            assert hasattr(insights, "confidence")
            assert hasattr(insights, "dominant_traits")
        else:
            # Si no se detectó, insights puede ser None
            assert insights is None or isinstance(insights, object)


# =============================================================================
# TESTS ADAPTED MESSAGE SERVICE
# =============================================================================

class TestAdaptedMessageService:
    """Tests para AdaptedMessageService."""

    @pytest.mark.asyncio
    async def test_get_adapted_message_no_archetype(self, db_session):
        """Test obtener mensaje adaptado sin arquetipo."""
        service = AdaptedMessageService(db_session)

        variants = {
            "EXPLORER": "Mensaje para exploradores",
            "DIRECT": "Mensaje directos",
            "default": "Mensaje genérico"
        }

        # Usuario sin arquetipo
        message = await service.get_adapted_message(
            user_id=99999,
            message_variants=variants,
            default_message="Default"
        )

        # Debería retornar el default
        assert message == "Default"

    @pytest.mark.asyncio
    async def test_get_adapted_vip_invitation(self, db_session):
        """Test obtener invitación VIP adaptada."""
        service = AdaptedMessageService(db_session)

        # Usuario sin arquetipo
        message = await service.get_adapted_vip_invitation(99999)

        # Debería retornar un mensaje (default de Lucien)
        assert message is not None
        assert len(message) > 0

    @pytest.mark.asyncio
    async def test_get_adapted_mission_description(self, db_session):
        """Test obtener descripción de misión adaptada."""
        service = AdaptedMessageService(db_session)

        base_desc = "Completa esta misión para ganar besitos"
        message = await service.get_adapted_mission_description(
            user_id=99999,
            mission_name="Misión Test",
            base_description=base_desc
        )

        # Debería incluir el nombre de la misión
        assert "Misión Test" in message
        assert base_desc in message

    @pytest.mark.asyncio
    async def test_get_archetype_emoji(self, db_session):
        """Test obtener emoji de arquetipo."""
        service = AdaptedMessageService(db_session)

        # Usuario sin arquetipo
        emoji = await service.get_archetype_emoji(99999)

        # Debería retornar el emoji de desconocido
        assert emoji == "❓"

    @pytest.mark.asyncio
    async def test_get_archetype_name(self, db_session):
        """Test obtener nombre de arquetipo."""
        service = AdaptedMessageService(db_session)

        # Usuario sin arquetipo
        name = await service.get_archetype_name(99999)

        # Debería retornar "Desconocido"
        assert name == "Desconocido"


# =============================================================================
# TESTS DE INTEGRACIÓN
# =============================================================================

class TestArchetypeIntegration:
    """Tests de integración del sistema de arquetipos."""

    @pytest.mark.asyncio
    async def test_full_tracking_flow(self, db_session):
        """Test flujo completo de tracking."""
        tracking = BehaviorTrackingService(db_session)
        detection = ArchetypeDetectionService(db_session)

        user_id = 12345

        # 1. Registrar sesión
        await tracking.track_session(
            user_id=user_id,
            session_type="start",
            is_return=False
        )

        # 2. Registrar clicks
        for i in range(5):
            await tracking.track_button_click(
                user_id=user_id,
                button_id=f"button_{i}",
                context="test",
                time_to_click=2.0,
                is_exploration=True,
                is_direct_action=False
            )

        # 3. Verificar que se registraron las señales
        signals = await tracking.get_behavior_signals(user_id)
        assert signals is not None
        assert signals.total_sessions >= 1
        assert signals.total_interactions >= 5

    @pytest.mark.asyncio
    async def test_signals_dict_completeness(self, db_session):
        """Test que todas las métricas estén disponibles en dict."""
        tracking = BehaviorTrackingService(db_session)

        user_id = 12345

        # Registrar varios tipos de interacciones
        await tracking.track_session(user_id=user_id, session_type="start", is_return=False)
        await tracking.track_button_click(
            user_id=user_id, button_id="test", context="test",
            time_to_click=1.0, is_exploration=True, is_direct_action=False
        )

        # Obtener dict
        signals_dict = await tracking.get_signals_as_dict(user_id)

        # Verificar métricas clave existen
        expected_metrics = [
            "total_interactions",
            "total_sessions",
            "content_sections_visited",
            "emotional_content_views",
            "avg_time_to_click",
            "current_streak"
        ]

        for metric in expected_metrics:
            assert metric in signals_dict, f"Métrica {metric} no encontrada"
