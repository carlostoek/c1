"""
Tests E2E para el sistema de onboarding narrativo.

Verifica:
1. Mensaje de bienvenida después de aprobación Free
2. Flujo completo de 5 pasos de onboarding
3. Bloqueo de acceso a historia sin completar onboarding
4. Onboarding solo se ejecuta una vez
5. Detección de arquetipo durante onboarding
6. Progresión de fragmentos en orden correcto
"""
import pytest
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

from bot.database import get_session
from bot.narrative.services.container import NarrativeContainer
from bot.narrative.database.onboarding_models import (
    UserOnboardingProgress,
    OnboardingFragment,
)
from bot.narrative.database.enums import ArchetypeType


class TestOnboardingWelcome:
    """Tests para mensaje de bienvenida post-aprobación."""

    @pytest.mark.asyncio
    async def test_onboarding_welcome_after_free_approval(self, mock_bot):
        """
        Test 1: Verificar envío de mensaje onboarding después de aprobar solicitud Free.

        Verifica:
        - Se otorgan 30 besitos
        - Se envía mensaje con botón "Comenzar Tutorial"
        """
        async with get_session() as session:
            user_id = 111111

            # Mock del bot send_message
            mock_bot.send_message = AsyncMock(return_value=Mock())

            # Importar y ejecutar función de onboarding welcome
            from bot.handlers.user.narrative.onboarding import send_onboarding_welcome

            result = await send_onboarding_welcome(
                bot=mock_bot,
                user_id=user_id,
                session=session
            )

            # Verificar que se envió mensaje
            assert result is True
            mock_bot.send_message.assert_called_once()

            # Verificar contenido del mensaje
            call_args = mock_bot.send_message.call_args
            assert call_args.kwargs["chat_id"] == user_id
            assert "Bienvenido" in call_args.kwargs["text"]
            assert "30 besitos" in call_args.kwargs["text"]

            # Verificar que se creó progreso de onboarding
            narrative = NarrativeContainer(session)
            progress = await narrative.onboarding.get_or_create_progress(user_id)
            assert progress.besitos_granted == 30

            await session.commit()


class TestOnboardingCompleteFlow:
    """Tests para flujo completo de onboarding."""

    @pytest.mark.asyncio
    async def test_onboarding_complete_flow(self):
        """
        Test 2: Flujo completo de 5 pasos de onboarding.

        Verifica:
        - Iniciar onboarding marca started=True
        - Avanzar por los 5 pasos
        - Completar marca completed=True
        """
        async with get_session() as session:
            user_id = 222222
            narrative = NarrativeContainer(session)

            # Iniciar onboarding
            progress = await narrative.onboarding.mark_onboarding_started(user_id)
            assert progress.started is True
            assert progress.current_step == 1

            # Simular decisiones en cada paso
            for step in range(1, 6):
                await narrative.onboarding.update_step(user_id, step)
                await narrative.onboarding.record_decision(
                    user_id=user_id,
                    step=step,
                    choice_index=0,
                    archetype_hint="IMPULSIVE" if step < 3 else "CONTEMPLATIVE"
                )

            # Completar onboarding
            progress = await narrative.onboarding.mark_onboarding_completed(user_id)
            assert progress.completed is True
            assert progress.current_step == 5

            # Verificar arquetipo detectado
            archetype = await narrative.onboarding.get_detected_archetype(user_id)
            assert archetype is not None

            await session.commit()


class TestOnboardingBlocksStoryAccess:
    """Tests para bloqueo de acceso a historia."""

    @pytest.mark.asyncio
    async def test_onboarding_prevents_story_access(self):
        """
        Test 3: Sin completar onboarding, no se puede acceder a historia.

        Verifica:
        - has_completed_onboarding() retorna False para usuario nuevo
        - Después de completar, retorna True
        """
        async with get_session() as session:
            user_id = 333333
            narrative = NarrativeContainer(session)

            # Usuario nuevo no ha completado
            has_completed = await narrative.onboarding.has_completed_onboarding(user_id)
            assert has_completed is False

            # Simular completación
            await narrative.onboarding.mark_onboarding_started(user_id)
            await narrative.onboarding.mark_onboarding_completed(user_id)

            # Ahora sí ha completado
            has_completed = await narrative.onboarding.has_completed_onboarding(user_id)
            assert has_completed is True

            await session.commit()


class TestOnboardingOnlyOnce:
    """Tests para idempotencia del onboarding."""

    @pytest.mark.asyncio
    async def test_onboarding_only_once(self, mock_bot):
        """
        Test 4: Onboarding solo se ejecuta una vez por usuario.

        Verifica:
        - Segundo intento de welcome no otorga besitos adicionales
        - has_completed_onboarding evita re-ejecución
        """
        async with get_session() as session:
            user_id = 444444
            narrative = NarrativeContainer(session)

            # Primera ejecución
            besitos1 = await narrative.onboarding.grant_welcome_besitos(user_id, 30)
            assert besitos1 == 30

            # Segunda ejecución - no debe otorgar más
            besitos2 = await narrative.onboarding.grant_welcome_besitos(user_id, 30)
            assert besitos2 == 0

            # Verificar total otorgado
            progress = await narrative.onboarding.get_or_create_progress(user_id)
            assert progress.besitos_granted == 30

            await session.commit()


class TestArchetypeDetection:
    """Tests para detección de arquetipo durante onboarding."""

    @pytest.mark.asyncio
    async def test_archetype_detection_impulsive(self):
        """
        Test 5a: Detectar arquetipo IMPULSIVE con decisiones apropiadas.
        """
        async with get_session() as session:
            user_id = 555551
            narrative = NarrativeContainer(session)

            # Registrar 3 decisiones IMPULSIVE
            await narrative.onboarding.mark_onboarding_started(user_id)
            for step in range(1, 4):
                await narrative.onboarding.record_decision(
                    user_id=user_id,
                    step=step,
                    choice_index=0,
                    archetype_hint="IMPULSIVE"
                )

            # Verificar detección
            archetype = await narrative.onboarding.get_detected_archetype(user_id)
            assert archetype == ArchetypeType.IMPULSIVE

            await session.commit()

    @pytest.mark.asyncio
    async def test_archetype_detection_contemplative(self):
        """
        Test 5b: Detectar arquetipo CONTEMPLATIVE con decisiones apropiadas.
        """
        async with get_session() as session:
            user_id = 555552
            narrative = NarrativeContainer(session)

            # Registrar 3 decisiones CONTEMPLATIVE
            await narrative.onboarding.mark_onboarding_started(user_id)
            for step in range(1, 4):
                await narrative.onboarding.record_decision(
                    user_id=user_id,
                    step=step,
                    choice_index=1,
                    archetype_hint="CONTEMPLATIVE"
                )

            # Verificar detección
            archetype = await narrative.onboarding.get_detected_archetype(user_id)
            assert archetype == ArchetypeType.CONTEMPLATIVE

            await session.commit()


class TestFragmentProgression:
    """Tests para progresión de fragmentos de onboarding."""

    @pytest.mark.asyncio
    async def test_onboarding_fragment_progression(self):
        """
        Test 6: Verificar que fragmentos se muestran en orden correcto.

        Verifica:
        - Existen 5 fragmentos de onboarding
        - Están ordenados por step
        - Cada uno tiene contenido y decisiones
        """
        async with get_session() as session:
            narrative = NarrativeContainer(session)

            # Obtener todos los fragmentos
            fragments = await narrative.onboarding.get_all_fragments()

            # Verificar que hay 5 fragmentos
            assert len(fragments) >= 5

            # Verificar orden y contenido
            for i, fragment in enumerate(fragments[:5], start=1):
                assert fragment.step == i
                assert fragment.content is not None
                assert len(fragment.content) > 10  # Contenido mínimo

                # Verificar que tiene decisiones (excepto quizás el paso 3)
                decisions = narrative.onboarding.parse_decisions(fragment)
                assert decisions is not None

            await session.commit()

    @pytest.mark.asyncio
    async def test_get_fragment_by_step(self):
        """
        Test 6b: Verificar obtención de fragmento por paso específico.
        """
        async with get_session() as session:
            narrative = NarrativeContainer(session)

            # Obtener fragmento del paso 1
            fragment = await narrative.onboarding.get_fragment(step=1)
            assert fragment is not None
            assert fragment.step == 1
            assert "Bienvenido" in fragment.title or "Diana" in fragment.content

            # Obtener fragmento del paso 5 (último)
            fragment = await narrative.onboarding.get_fragment(step=5)
            assert fragment is not None
            assert fragment.step == 5

            await session.commit()


class TestOnboardingSummary:
    """Tests para resumen de estado de onboarding."""

    @pytest.mark.asyncio
    async def test_onboarding_summary(self):
        """
        Test adicional: Verificar resumen de estado de onboarding.
        """
        async with get_session() as session:
            user_id = 666666
            narrative = NarrativeContainer(session)

            # Iniciar onboarding
            await narrative.onboarding.mark_onboarding_started(user_id)
            await narrative.onboarding.grant_welcome_besitos(user_id, 30)

            # Avanzar algunos pasos
            for step in range(1, 4):
                await narrative.onboarding.update_step(user_id, step)
                await narrative.onboarding.record_decision(
                    user_id=user_id,
                    step=step,
                    choice_index=0,
                    archetype_hint="IMPULSIVE"
                )

            # Obtener resumen
            summary = await narrative.onboarding.get_onboarding_summary(user_id)

            assert summary["user_id"] == user_id
            assert summary["started"] is True
            assert summary["completed"] is False
            assert summary["current_step"] == 3
            assert summary["besitos_granted"] == 30
            assert summary["decisions_count"] == 3

            await session.commit()
