"""
End-to-End Tests para ONDA 2.

Tests de integración para features de ONDA 2:
- Estadísticas (StatsService)
- Paginación
- Formatters
- Flujos integrados
"""
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import select

from bot.database import get_session
from bot.database.models import VIPSubscriber, InvitationToken, FreeChannelRequest
from bot.services.stats import StatsService, OverallStats, VIPStats, FreeStats, TokenStats
from bot.utils.pagination import Paginator
from bot.utils.formatters import (
    format_datetime,
    format_relative_time,
    format_currency,
    format_percentage,
    format_duration_minutes,
    status_emoji,
    days_remaining_emoji,
)


# ===== TESTS DE STATS SERVICE =====


@pytest.mark.asyncio
async def test_stats_overall():
    """Test de estadísticas generales."""
    print("\n🧪 Test 1: Estadísticas Generales")

    async with get_session() as session:
        stats_service = StatsService(session)
        overall = await stats_service.get_overall_stats()

        # Validar tipo y atributos
        assert isinstance(overall, OverallStats)
        assert isinstance(overall.total_vip_active, int)
        assert isinstance(overall.calculated_at, datetime)

        print(f"✅ Overall stats: {overall.total_vip_active} VIP, {overall.total_free_pending} Free")


@pytest.mark.asyncio
async def test_stats_vip():
    """Test de estadísticas VIP."""
    print("\n🧪 Test 2: Estadísticas VIP")

    async with get_session() as session:
        stats_service = StatsService(session)
        vip_stats = await stats_service.get_vip_stats()

        assert isinstance(vip_stats, VIPStats)
        assert vip_stats.total_active >= 0
        assert vip_stats.total_all_time >= vip_stats.total_active

        print(f"✅ VIP stats: {vip_stats.total_active} activos")


@pytest.mark.asyncio
async def test_stats_free():
    """Test de estadísticas Free."""
    print("\n🧪 Test 3: Estadísticas Free")

    async with get_session() as session:
        stats_service = StatsService(session)
        free_stats = await stats_service.get_free_stats()

        assert isinstance(free_stats, FreeStats)
        assert free_stats.total_pending >= 0
        assert free_stats.total_processed >= 0

        print(f"✅ Free stats: {free_stats.total_pending} pendientes")


@pytest.mark.asyncio
async def test_stats_tokens():
    """Test de estadísticas de Tokens."""
    print("\n🧪 Test 4: Estadísticas Tokens")

    async with get_session() as session:
        stats_service = StatsService(session)
        token_stats = await stats_service.get_token_stats()

        assert isinstance(token_stats, TokenStats)
        assert token_stats.total_generated >= 0
        assert token_stats.total_used >= 0
        assert token_stats.conversion_rate >= 0

        print(f"✅ Token stats: {token_stats.conversion_rate:.1f}% conversión")


@pytest.mark.asyncio
async def test_stats_cache():
    """Test de cache de estadísticas."""
    print("\n🧪 Test 5: Cache de Estadísticas")

    async with get_session() as session:
        stats_service = StatsService(session)

        # Primera llamada
        stats1 = await stats_service.get_overall_stats()
        timestamp1 = stats1.calculated_at

        # Segunda llamada (con cache)
        import asyncio
        await asyncio.sleep(0.1)
        stats2 = await stats_service.get_overall_stats()
        timestamp2 = stats2.calculated_at

        # Los timestamps deben ser iguales (cache hit)
        assert timestamp1 == timestamp2
        print("✅ Cache funciona (mismo timestamp)")

        # Force refresh
        await asyncio.sleep(0.1)
        stats3 = await stats_service.get_overall_stats(force_refresh=True)
        timestamp3 = stats3.calculated_at

        # El nuevo timestamp debe ser diferente
        assert timestamp3 > timestamp1
        print("✅ Force refresh funciona (nuevo timestamp)")


# ===== TESTS DE PAGINACIÓN =====


def test_pagination_basic():
    """Test básico de paginación."""
    print("\n🧪 Test 6: Paginación Básica")

    items = list(range(1, 26))
    paginator = Paginator(items=items, page_size=10)

    assert paginator.total_items == 25
    assert paginator.total_pages == 3

    page1 = paginator.get_page(1)
    assert page1.current_page == 1
    assert len(page1.items) == 10
    assert page1.has_previous == False
    assert page1.has_next == True

    page3 = paginator.get_page(3)
    assert len(page3.items) == 5
    assert page3.has_previous == True
    assert page3.has_next == False

    print(f"✅ Paginación: {paginator.total_pages} páginas")


def test_pagination_empty():
    """Test de paginación con lista vacía."""
    print("\n🧪 Test 7: Paginación Vacía")

    paginator = Paginator(items=[], page_size=10)

    assert paginator.total_items == 0
    assert paginator.total_pages == 1

    page = paginator.get_page(1)
    assert page.is_empty == True

    print("✅ Paginación vacía: 1 página, 0 items")


# ===== TESTS DE FORMATTERS =====


def test_formatters_dates():
    """Test de formateo de fechas."""
    print("\n🧪 Test 8: Formatters - Fechas")

    dt = datetime(2024, 12, 13, 14, 30, 45)

    result = format_datetime(dt)
    assert result == "2024-12-13 14:30"

    result = format_datetime(dt, include_time=False)
    assert result == "2024-12-13"

    print("✅ Formateo de fechas correcto")


def test_formatters_relative_time():
    """Test de tiempo relativo."""
    print("\n🧪 Test 9: Formatters - Tiempo Relativo")

    now = datetime.now(timezone.utc)

    past = now - timedelta(minutes=5)
    result = format_relative_time(past, reference=now)
    assert "hace 5 minutos" == result

    future = now + timedelta(hours=2)
    result = format_relative_time(future, reference=now)
    assert "en 2 horas" == result

    print("✅ Tiempo relativo correcto")


def test_formatters_numbers():
    """Test de formateo de números."""
    print("\n🧪 Test 10: Formatters - Números")

    result = format_currency(1234.56)
    assert result == "$1,234.56"

    result = format_percentage(85.5)
    assert result == "85.5%"

    result = format_duration_minutes(65)
    assert "1 hora" in result and "5 minutos" in result

    assert status_emoji("active") == "🟢"
    assert status_emoji("expired") == "⚪"
    assert days_remaining_emoji(45) == "🟢"
    assert days_remaining_emoji(2) == "🔴"

    print("✅ Formateo y emojis correctos")


# ===== TESTS INTEGRADOS =====


@pytest.mark.asyncio
async def test_vip_management_paginated():
    """Test de gestión VIP con paginación."""
    print("\n🧪 Test 11: Gestión VIP Paginada")

    async with get_session() as session:
        result = await session.execute(
            select(VIPSubscriber)
            .where(VIPSubscriber.status == "active")
            .order_by(VIPSubscriber.expiry_date.desc())
        )
        subscribers = result.scalars().all()

        paginator = Paginator(items=list(subscribers), page_size=10)
        page1 = paginator.get_page(1)

        assert isinstance(page1.items, list)
        print(f"✅ Gestión VIP: {len(page1.items)} activos en página 1")


@pytest.mark.asyncio
async def test_free_queue_paginated():
    """Test de cola Free con paginación."""
    print("\n🧪 Test 12: Cola Free Paginada")

    async with get_session() as session:
        result = await session.execute(
            select(FreeChannelRequest)
            .where(FreeChannelRequest.processed == False)
            .order_by(FreeChannelRequest.request_date.asc())
        )
        requests = result.scalars().all()

        paginator = Paginator(items=list(requests), page_size=10)
        page1 = paginator.get_page(1)

        assert isinstance(page1.items, list)
        print(f"✅ Cola Free: {len(page1.items)} pendientes en página 1")


# ===== MAIN =====


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🧪 EJECUTANDO TESTS E2E - ONDA 2")
    print("=" * 70)

    pytest.main([__file__, "-v", "-s"])
