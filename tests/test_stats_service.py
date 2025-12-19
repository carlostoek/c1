"""
Test script para validar StatsService (T18).

Pruebas de:
- Cálculo de estadísticas
- Funcionamiento del cache
- Force refresh
- Serialización de dataclasses
- Queries optimizadas
"""
import asyncio
import logging
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from bot.database import init_db, close_db, get_session
from bot.services.stats import StatsService, OverallStats, VIPStats, FreeStats, TokenStats
from bot.database.models import BotConfig, VIPSubscriber, InvitationToken, FreeChannelRequest


async def test_stats_service():
    """Test suite completo para StatsService."""
    print("\n" + "="*70)
    print("🧪 TEST SUITE: StatsService (T18)")
    print("="*70)

    try:
        await init_db()

        # ===== SETUP: Poblar BD con datos de prueba =====
        print("\n📝 Creando datos de prueba...")

        async with get_session() as session:
            # Limpiar datos de pruebas anteriores
            from sqlalchemy import delete
            await session.execute(delete(FreeChannelRequest))
            await session.execute(delete(VIPSubscriber))
            await session.execute(delete(InvitationToken))
            await session.commit()

            # Crear BotConfig
            config = await session.get(BotConfig, 1)
            if config:
                config.wait_time_minutes = 5
                config.subscription_fees = {"monthly": 10, "yearly": 100}
            else:
                config = BotConfig(
                    id=1,
                    wait_time_minutes=5,
                    subscription_fees={"monthly": 10, "yearly": 100}
                )
                session.add(config)

            # Crear tokens con valores únicos
            import secrets
            token1_str = secrets.token_hex(8).upper()
            token2_str = secrets.token_hex(8).upper()

            token1 = InvitationToken(
                token=token1_str,
                generated_by=999,
                created_at=datetime.utcnow(),
                duration_hours=24,
                used=True,
                used_by=111,
                used_at=datetime.utcnow()
            )
            token2 = InvitationToken(
                token=token2_str,
                generated_by=999,
                created_at=datetime.utcnow(),
                duration_hours=24,
                used=False,
                used_by=None,
                used_at=None
            )
            session.add(token1)
            session.add(token2)
            await session.flush()

            # Crear VIP activos
            vip_active1 = VIPSubscriber(
                user_id=111,
                join_date=datetime.utcnow() - timedelta(days=5),
                expiry_date=datetime.utcnow() + timedelta(days=15),
                status="active",
                token_id=token1.id
            )
            vip_active2 = VIPSubscriber(
                user_id=112,
                join_date=datetime.utcnow() - timedelta(days=20),
                expiry_date=datetime.utcnow() + timedelta(days=8),
                status="active",
                token_id=token1.id
            )

            # Crear VIP expirado
            vip_expired = VIPSubscriber(
                user_id=222,
                join_date=datetime.utcnow() - timedelta(days=40),
                expiry_date=datetime.utcnow() - timedelta(days=1),
                status="expired",
                token_id=token1.id
            )

            session.add(vip_active1)
            session.add(vip_active2)
            session.add(vip_expired)
            await session.flush()

            # Crear solicitudes Free
            free_pending = FreeChannelRequest(
                user_id=333,
                request_date=datetime.utcnow() - timedelta(minutes=2),
                processed=False
            )
            free_ready = FreeChannelRequest(
                user_id=334,
                request_date=datetime.utcnow() - timedelta(minutes=10),
                processed=False
            )
            free_processed = FreeChannelRequest(
                user_id=335,
                request_date=datetime.utcnow() - timedelta(days=1),
                processed=True,
                processed_at=datetime.utcnow() - timedelta(minutes=60)
            )

            session.add(free_pending)
            session.add(free_ready)
            session.add(free_processed)

            await session.commit()

        print("✅ Datos de prueba creados")

        # ===== TEST 1: Overall Stats =====
        print("\n" + "-"*70)
        print("🧪 TEST 1: get_overall_stats()")
        print("-"*70)

        async with get_session() as session:
            service = StatsService(session)
            overall = await service.get_overall_stats()

            assert isinstance(overall, OverallStats), "Debe retornar OverallStats"
            assert overall.total_vip_active >= 2, f"Expected >= 2 VIP activos, got {overall.total_vip_active}"
            assert overall.total_vip_expired >= 1, f"Expected >= 1 VIP expirado, got {overall.total_vip_expired}"
            assert overall.total_free_pending >= 2, f"Expected >= 2 Free pendientes, got {overall.total_free_pending}"
            assert overall.total_tokens_generated >= 2, f"Expected >= 2 tokens, got {overall.total_tokens_generated}"
            assert overall.total_tokens_used >= 1, f"Expected >= 1 token usado, got {overall.total_tokens_used}"
            assert isinstance(overall.calculated_at, datetime), "calculated_at debe ser datetime"

            print(f"✅ Overall Stats válido:")
            print(f"   - VIP activos: {overall.total_vip_active}")
            print(f"   - VIP expirados: {overall.total_vip_expired}")
            print(f"   - Free pendientes: {overall.total_free_pending}")
            print(f"   - Tokens generados: {overall.total_tokens_generated}")
            print(f"   - Tokens usados: {overall.total_tokens_used}")
            print(f"   - Ingreso proyectado: ${overall.projected_monthly_revenue}/mes")

        # ===== TEST 2: Cache Funcionando =====
        print("\n" + "-"*70)
        print("🧪 TEST 2: Cache funciona (no recalcula)")
        print("-"*70)

        async with get_session() as session:
            service = StatsService(session)

            # Primera llamada
            overall1 = await service.get_overall_stats()
            timestamp1 = overall1.calculated_at

            # Segunda llamada (debe usar cache)
            await asyncio.sleep(0.1)
            overall2 = await service.get_overall_stats()
            timestamp2 = overall2.calculated_at

            assert timestamp1 == timestamp2, "Cache no funcionó: timestamps diferentes"
            print(f"✅ Cache funciona correctamente (timestamp idéntico)")

        # ===== TEST 3: Force Refresh =====
        print("\n" + "-"*70)
        print("🧪 TEST 3: force_refresh=True ignora cache")
        print("-"*70)

        async with get_session() as session:
            service = StatsService(session)

            # Primera llamada
            overall1 = await service.get_overall_stats()
            timestamp1 = overall1.calculated_at

            # Esperar y forzar recálculo
            await asyncio.sleep(0.2)
            overall3 = await service.get_overall_stats(force_refresh=True)
            timestamp3 = overall3.calculated_at

            assert timestamp3 > timestamp1, "Force refresh no funcionó: timestamp no avanzó"
            print(f"✅ Force refresh funciona (nuevo timestamp: {timestamp3 > timestamp1})")

        # ===== TEST 4: VIP Stats =====
        print("\n" + "-"*70)
        print("🧪 TEST 4: get_vip_stats()")
        print("-"*70)

        async with get_session() as session:
            service = StatsService(session)
            vip_stats = await service.get_vip_stats()

            assert isinstance(vip_stats, VIPStats), "Debe retornar VIPStats"
            assert vip_stats.total_active >= 2, f"Expected >= 2 VIP activos, got {vip_stats.total_active}"
            assert vip_stats.total_expired >= 1, f"Expected >= 1 VIP expirado, got {vip_stats.total_expired}"
            assert isinstance(vip_stats.top_subscribers, list), "top_subscribers debe ser list"

            print(f"✅ VIP Stats válido:")
            print(f"   - Total activos: {vip_stats.total_active}")
            print(f"   - Total expirados: {vip_stats.total_expired}")
            print(f"   - Total histórico: {vip_stats.total_all_time}")
            print(f"   - Expirando esta semana: {vip_stats.expiring_this_week}")
            print(f"   - Top subscribers: {len(vip_stats.top_subscribers)} items")

        # ===== TEST 5: Free Stats =====
        print("\n" + "-"*70)
        print("🧪 TEST 5: get_free_stats()")
        print("-"*70)

        async with get_session() as session:
            service = StatsService(session)
            free_stats = await service.get_free_stats()

            assert isinstance(free_stats, FreeStats), "Debe retornar FreeStats"
            assert free_stats.total_pending >= 2, f"Expected >= 2 Free pendientes, got {free_stats.total_pending}"
            assert free_stats.ready_to_process >= 1, f"Expected >= 1 listo para procesar, got {free_stats.ready_to_process}"
            assert isinstance(free_stats.next_to_process, list), "next_to_process debe ser list"

            print(f"✅ Free Stats válido:")
            print(f"   - Total pendientes: {free_stats.total_pending}")
            print(f"   - Total procesados: {free_stats.total_processed}")
            print(f"   - Listos para procesar: {free_stats.ready_to_process}")
            print(f"   - Aún esperando: {free_stats.still_waiting}")
            print(f"   - Promedio espera: {free_stats.avg_wait_time_minutes} minutos")

        # ===== TEST 6: Token Stats =====
        print("\n" + "-"*70)
        print("🧪 TEST 6: get_token_stats()")
        print("-"*70)

        async with get_session() as session:
            service = StatsService(session)
            token_stats = await service.get_token_stats()

            assert isinstance(token_stats, TokenStats), "Debe retornar TokenStats"
            assert token_stats.total_generated >= 2, f"Expected >= 2 tokens, got {token_stats.total_generated}"
            assert token_stats.total_used >= 1, f"Expected >= 1 token usado, got {token_stats.total_used}"
            assert 0 <= token_stats.conversion_rate <= 100, f"Conversion rate fuera de rango: {token_stats.conversion_rate}"

            print(f"✅ Token Stats válido:")
            print(f"   - Total generados: {token_stats.total_generated}")
            print(f"   - Total usados: {token_stats.total_used}")
            print(f"   - Total expirados: {token_stats.total_expired}")
            print(f"   - Disponibles: {token_stats.total_available}")
            print(f"   - Tasa conversión: {token_stats.conversion_rate}%")

        # ===== TEST 7: Serialización =====
        print("\n" + "-"*70)
        print("🧪 TEST 7: Serialización con to_dict()")
        print("-"*70)

        async with get_session() as session:
            service = StatsService(session)
            overall = await service.get_overall_stats(force_refresh=True)

            overall_dict = overall.to_dict()
            assert isinstance(overall_dict, dict), "to_dict() debe retornar dict"
            assert "total_vip_active" in overall_dict, "Falta total_vip_active en dict"
            assert "calculated_at" in overall_dict, "Falta calculated_at en dict"
            assert isinstance(overall_dict["calculated_at"], str), "calculated_at debe ser ISO string"

            print(f"✅ Serialización funciona:")
            print(f"   - Dict keys: {len(overall_dict)} items")
            print(f"   - calculated_at format: {overall_dict['calculated_at']}")

        # ===== TEST 8: Cache TTL =====
        print("\n" + "-"*70)
        print("🧪 TEST 8: Cache TTL (5 minutos)")
        print("-"*70)

        async with get_session() as session:
            service = StatsService(session)

            # Cache debe ser fresh inicialmente
            assert service._is_cache_fresh("overall_stats") == False, "Cache no debe existir"

            # Obtener y cachear
            await service.get_overall_stats()
            assert service._is_cache_fresh("overall_stats") == True, "Cache debe ser fresh"

            # Verificar TTL
            cached_value, cached_time = service._cache["overall_stats"]
            age = (datetime.utcnow() - cached_time).total_seconds()
            assert age < StatsService.CACHE_TTL, f"Cache age {age}s >= TTL {StatsService.CACHE_TTL}s"

            print(f"✅ Cache TTL funciona:")
            print(f"   - TTL configurado: {StatsService.CACHE_TTL} segundos")
            print(f"   - Age actual: {age:.2f} segundos")

        # ===== TEST 9: Clear Cache =====
        print("\n" + "-"*70)
        print("🧪 TEST 9: clear_cache()")
        print("-"*70)

        async with get_session() as session:
            service = StatsService(session)

            # Llenar cache
            await service.get_overall_stats()
            assert len(service._cache) > 0, "Cache debe tener datos"

            # Limpiar cache
            service.clear_cache()
            assert len(service._cache) == 0, "Cache debe estar vacío"

            print(f"✅ clear_cache() funciona correctamente")

        # ===== TEST 10: Lazy Loading en Container =====
        print("\n" + "-"*70)
        print("🧪 TEST 10: StatsService lazy loading en container")
        print("-"*70)

        from bot.services.container import ServiceContainer
        from aiogram import Bot

        async with get_session() as session:
            # Mock bot (no hacer llamadas reales)
            from unittest.mock import AsyncMock
            mock_bot = AsyncMock(spec=Bot)

            container = ServiceContainer(session, mock_bot)

            # Stats no debe estar cargado
            assert container._stats_service is None, "Stats no debe estar precargado"

            # Acceder a stats (lazy load)
            stats_service = container.stats
            assert container._stats_service is not None, "Stats debe estar cargado tras acceso"
            assert isinstance(stats_service, StatsService), "Debe retornar StatsService"

            # Segunda llamada debe reutilizar la instancia
            stats_service2 = container.stats
            assert stats_service is stats_service2, "Debe reutilizar la misma instancia"

            # get_loaded_services debe incluir 'stats'
            loaded = container.get_loaded_services()
            assert "stats" in loaded, "stats debe estar en loaded services"

            print(f"✅ Lazy loading funciona:")
            print(f"   - Stats cargado bajo demanda: ✓")
            print(f"   - Instancia reutilizada: ✓")
            print(f"   - get_loaded_services(): {loaded}")

        # ===== RESUMEN =====
        print("\n" + "="*70)
        print("✅✅✅ TODOS LOS TESTS PASARON (10/10)")
        print("="*70)

        return True

    except AssertionError as e:
        print(f"\n❌ ASSERTION FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await close_db()


if __name__ == "__main__":
    success = asyncio.run(test_stats_service())
    exit(0 if success else 1)
