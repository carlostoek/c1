"""
Tests E2E simplificados para FASE N6: Sistema de Arquetipos.

Valida:
- Detección de arquetipos por tiempo de respuesta
- Cálculo de confianza
- Clasificación de tiempos
"""

import pytest
from bot.database.engine import get_session, init_db
from bot.narrative.services.archetype import ArchetypeService
from bot.narrative.services.progress import ProgressService
from bot.narrative.database import (
    UserDecisionHistory,
    UserNarrativeProgress,
    ArchetypeType,
)


@pytest.fixture(scope="function", autouse=True)
async def setup_db():
    """Inicializar base de datos antes de cada test."""
    await init_db()


@pytest.mark.asyncio
async def test_classify_response_time_impulsive():
    """Test: Clasificación de tiempo IMPULSIVE (< 5s)."""
    async with get_session() as session:
        archetype_service = ArchetypeService(session)

        # Tiempos impulsivos (< 5s)
        assert archetype_service.classify_response_time(2.0) == ArchetypeType.IMPULSIVE
        assert archetype_service.classify_response_time(4.5) == ArchetypeType.IMPULSIVE


@pytest.mark.asyncio
async def test_classify_response_time_contemplative():
    """Test: Clasificación de tiempo CONTEMPLATIVE (> 30s)."""
    async with get_session() as session:
        archetype_service = ArchetypeService(session)

        # Tiempos contemplativos (> 30s)
        assert archetype_service.classify_response_time(35.0) == ArchetypeType.CONTEMPLATIVE
        assert archetype_service.classify_response_time(60.0) == ArchetypeType.CONTEMPLATIVE


@pytest.mark.asyncio
async def test_classify_response_time_silent():
    """Test: Clasificación de tiempo SILENT (> 120s)."""
    async with get_session() as session:
        archetype_service = ArchetypeService(session)

        # Tiempos silenciosos (> 120s timeout)
        assert archetype_service.classify_response_time(130.0) == ArchetypeType.SILENT
        assert archetype_service.classify_response_time(200.0) == ArchetypeType.SILENT


@pytest.mark.asyncio
async def test_calculate_confidence_increases():
    """Test: Confianza aumenta con más decisiones."""
    async with get_session() as session:
        archetype_service = ArchetypeService(session)

        # Con 2 decisiones (baja confianza)
        conf_2 = archetype_service.calculate_confidence(
            total_decisions=2,
            avg_time=3.0,
            archetype=ArchetypeType.IMPULSIVE
        )

        # Con 10 decisiones (alta confianza)
        conf_10 = archetype_service.calculate_confidence(
            total_decisions=10,
            avg_time=3.0,
            archetype=ArchetypeType.IMPULSIVE
        )

        # Validar que confianza aumentó
        assert conf_10 > conf_2
        assert conf_10 >= 0.75  # Alta confianza con 10 decisiones


@pytest.mark.asyncio
async def test_archetype_detection_flow():
    """Test: Flujo completo de detección de arquetipo."""
    user_id = 999999

    async with get_session() as session:
        archetype_service = ArchetypeService(session)
        progress_service = ProgressService(session)

        # Crear decisiones simuladas con tiempos impulsivos
        for i in range(5):
            history = UserDecisionHistory(
                user_id=user_id,
                fragment_key="test_fragment",
                decision_id=1,  # ID ficticio
                response_time_seconds=3  # 3 segundos (impulsivo)
            )
            session.add(history)
        await session.commit()

        # Analizar y detectar arquetipo
        archetype, confidence = await archetype_service.analyze_and_update(
            user_id=user_id
        )

        # Validar detección
        assert archetype == ArchetypeType.IMPULSIVE
        assert confidence > 0.6  # Confianza media-alta con 5 decisiones

        # Verificar que se actualizó en progreso
        progress = await progress_service.get_progress(user_id)
        assert progress is not None
        assert progress.detected_archetype == ArchetypeType.IMPULSIVE
        assert progress.archetype_confidence > 0


@pytest.mark.asyncio
async def test_archetype_stats():
    """Test: Estadísticas de tiempos de respuesta."""
    user_id = 888888

    async with get_session() as session:
        archetype_service = ArchetypeService(session)

        # Crear decisiones con tiempos variados
        times = [2, 3, 5, 10, 15]  # Promedio: 7 segundos
        for time_val in times:
            history = UserDecisionHistory(
                user_id=user_id,
                fragment_key="test_fragment",
                decision_id=1,
                response_time_seconds=time_val
            )
            session.add(history)
        await session.commit()

        # Obtener estadísticas
        stats = await archetype_service.get_response_time_stats(user_id)

        # Validar estadísticas
        assert stats['total_decisions'] == 5
        assert stats['decisions_with_time'] == 5
        assert stats['avg_response_time'] == 7.0
        assert stats['min_response_time'] == 2.0
        assert stats['max_response_time'] == 15.0


@pytest.mark.asyncio
async def test_get_archetype_current():
    """Test: Obtener arquetipo actual del usuario."""
    user_id = 777777

    async with get_session() as session:
        archetype_service = ArchetypeService(session)

        # Usuario sin progreso
        archetype, confidence = await archetype_service.get_archetype(user_id)
        assert archetype == ArchetypeType.UNKNOWN
        assert confidence == 0.0

        # Crear progreso
        progress = UserNarrativeProgress(
            user_id=user_id,
            detected_archetype=ArchetypeType.CONTEMPLATIVE,
            archetype_confidence=0.75
        )
        session.add(progress)
        await session.commit()

        # Verificar arquetipo
        archetype, confidence = await archetype_service.get_archetype(user_id)
        assert archetype == ArchetypeType.CONTEMPLATIVE
        assert confidence == 0.75


@pytest.mark.asyncio
async def test_archetype_distribution():
    """Test: Distribución de arquetipos entre usuarios."""
    async with get_session() as session:
        archetype_service = ArchetypeService(session)

        # Crear usuarios con diferentes arquetipos
        users = [
            (100001, ArchetypeType.IMPULSIVE),
            (100002, ArchetypeType.IMPULSIVE),
            (100003, ArchetypeType.CONTEMPLATIVE),
            (100004, ArchetypeType.SILENT),
        ]

        for user_id, archetype in users:
            progress = UserNarrativeProgress(
                user_id=user_id,
                detected_archetype=archetype,
                archetype_confidence=0.8
            )
            session.add(progress)
        await session.commit()

        # Obtener distribución
        distribution = await archetype_service.get_archetype_distribution()

        # Validar distribución (al menos los que agregamos)
        assert distribution['impulsive'] >= 2
        assert distribution['contemplative'] >= 1
        assert distribution['silent'] >= 1
