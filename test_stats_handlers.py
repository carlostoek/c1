"""
Test script for Stats Handlers (T19).

Validates:
- Handler imports
- Keyboard structure
- Message formatting
- Integration with StatsService
"""
import asyncio
import logging
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from bot.database import init_db, close_db, get_session
from bot.services.container import ServiceContainer
from bot.database.models import BotConfig, VIPSubscriber, InvitationToken, FreeChannelRequest
from bot.handlers.admin.stats import (
    callback_stats_general,
    callback_stats_refresh,
    callback_stats_vip,
    callback_stats_free,
    callback_stats_tokens,
    format_currency,
    format_percentage,
    _format_overall_stats_message,
    _format_vip_stats_message,
    _format_free_stats_message,
    _format_token_stats_message,
)
from bot.utils.keyboards import stats_menu_keyboard, admin_main_menu_keyboard


async def test_stats_handlers():
    """Test suite completo para Stats Handlers."""
    print("\n" + "="*70)
    print("🧪 TEST SUITE: Stats Handlers (T19)")
    print("="*70)

    try:
        await init_db()

        # Setup test data
        print("\n📝 Creando datos de prueba...")

        async with get_session() as session:
            from sqlalchemy import delete
            await session.execute(delete(FreeChannelRequest))
            await session.execute(delete(VIPSubscriber))
            await session.execute(delete(InvitationToken))
            await session.commit()

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

        # ===== TEST 1: Keyboard Imports =====
        print("\n" + "-"*70)
        print("🧪 TEST 1: Keyboard imports")
        print("-"*70)

        stats_kbd = stats_menu_keyboard()
        admin_main_kbd = admin_main_menu_keyboard()

        assert stats_kbd is not None, "stats_menu_keyboard debe retornar keyboard"
        assert admin_main_kbd is not None, "admin_main_menu_keyboard debe retornar keyboard"
        assert len(stats_kbd.inline_keyboard) == 5, f"Stats keyboard debe tener 5 filas, got {len(stats_kbd.inline_keyboard)}"
        assert len(admin_main_kbd.inline_keyboard) == 4, f"Admin main debe tener 4 botones, got {len(admin_main_kbd.inline_keyboard)}"

        # Verificar que existe botón de Estadísticas en admin main
        admin_buttons_text = [btn.text for row in admin_main_kbd.inline_keyboard for btn in row]
        assert "📊 Estadísticas" in admin_buttons_text, "Falta botón Estadísticas en admin main"

        print("✅ Keyboards válidos:")
        print(f"   - stats_menu_keyboard: 5 botones")
        print(f"   - admin_main_menu_keyboard: 4 botones (incluye Estadísticas)")

        # ===== TEST 2: Format Functions =====
        print("\n" + "-"*70)
        print("🧪 TEST 2: Format functions")
        print("-"*70)

        assert format_currency(1234.56) == "$1,234.56", "Currency format incorrecto"
        assert format_currency(0) == "$0.00", "Currency format para 0 incorrecto"
        assert format_percentage(85.5) == "85.5%", "Percentage format incorrecto"
        assert format_percentage(0) == "0.0%", "Percentage format para 0 incorrecto"

        print("✅ Format functions válidos:")
        print(f"   - format_currency: '$1,234.56'")
        print(f"   - format_percentage: '85.5%'")

        # ===== TEST 3: Overall Stats Message =====
        print("\n" + "-"*70)
        print("🧪 TEST 3: Overall stats message formatting")
        print("-"*70)

        async with get_session() as session:
            mock_bot = AsyncMock()
            container = ServiceContainer(session, mock_bot)
            overall_stats = await container.stats.get_overall_stats()

            message = _format_overall_stats_message(overall_stats)

            assert isinstance(message, str), "Message debe ser string"
            assert len(message) > 0, "Message no puede estar vacío"
            assert "Dashboard de Estadísticas" in message, "Falta título"
            assert "📺 CANAL VIP" in message, "Falta sección VIP"
            assert "📺 CANAL FREE" in message, "Falta sección Free"
            assert "🎟️ TOKENS" in message, "Falta sección Tokens"
            assert "📈 ACTIVIDAD RECIENTE" in message, "Falta sección Actividad"
            assert "💰 PROYECCIÓN DE INGRESOS" in message, "Falta sección Ingresos"
            assert str(overall_stats.total_vip_active) in message, "Falta número VIP activos"
            assert "UTC" in message, "Falta timestamp"

            # Verificar que no supera límite Telegram (4096 chars)
            assert len(message) <= 4096, f"Message demasiado largo: {len(message)} > 4096"

            print(f"✅ Overall stats message válido:")
            print(f"   - Longitud: {len(message)} caracteres")
            print(f"   - Todas las secciones presentes")
            print(f"   - Dentro del límite Telegram (4096)")

        # ===== TEST 4: VIP Stats Message =====
        print("\n" + "-"*70)
        print("🧪 TEST 4: VIP stats message formatting")
        print("-"*70)

        async with get_session() as session:
            mock_bot = AsyncMock()
            container = ServiceContainer(session, mock_bot)
            vip_stats = await container.stats.get_vip_stats()

            message = _format_vip_stats_message(vip_stats)

            assert isinstance(message, str), "Message debe ser string"
            assert "Estadísticas VIP Detalladas" in message, "Falta título"
            assert "TOTALES" in message, "Falta sección totales"
            assert "PRÓXIMAS A EXPIRAR" in message, "Falta sección próximas"
            assert "ACTIVIDAD RECIENTE" in message, "Falta sección actividad"
            assert "retención" in message.lower(), "Falta tasa de retención"
            assert len(message) <= 4096, f"Message demasiado largo: {len(message)}"

            print(f"✅ VIP stats message válido:")
            print(f"   - Longitud: {len(message)} caracteres")
            print(f"   - Todas las secciones presentes")

        # ===== TEST 5: Free Stats Message =====
        print("\n" + "-"*70)
        print("🧪 TEST 5: Free stats message formatting")
        print("-"*70)

        async with get_session() as session:
            mock_bot = AsyncMock()
            container = ServiceContainer(session, mock_bot)
            free_stats = await container.stats.get_free_stats()

            message = _format_free_stats_message(free_stats)

            assert isinstance(message, str), "Message debe ser string"
            assert "Estadísticas Free Detalladas" in message, "Falta título"
            assert "TOTALES" in message, "Falta sección totales"
            assert "ESTADO DE COLA" in message, "Falta sección cola"
            assert "ACTIVIDAD RECIENTE" in message, "Falta sección actividad"
            assert "procesamiento" in message.lower(), "Falta tasa de procesamiento"
            assert len(message) <= 4096, f"Message demasiado largo: {len(message)}"

            print(f"✅ Free stats message válido:")
            print(f"   - Longitud: {len(message)} caracteres")
            print(f"   - Todas las secciones presentes")

        # ===== TEST 6: Token Stats Message =====
        print("\n" + "-"*70)
        print("🧪 TEST 6: Token stats message formatting")
        print("-"*70)

        async with get_session() as session:
            mock_bot = AsyncMock()
            container = ServiceContainer(session, mock_bot)
            token_stats = await container.stats.get_token_stats()

            message = _format_token_stats_message(token_stats)

            assert isinstance(message, str), "Message debe ser string"
            assert "Estadísticas de Tokens Detalladas" in message, "Falta título"
            assert "TOTALES" in message, "Falta sección totales"
            assert "GENERADOS POR PERÍODO" in message, "Falta sección generados"
            assert "USADOS POR PERÍODO" in message, "Falta sección usados"
            assert "conversión" in message.lower(), "Falta tasa de conversión"
            assert "ANÁLISIS" in message, "Falta sección análisis"
            assert len(message) <= 4096, f"Message demasiado largo: {len(message)}"

            print(f"✅ Token stats message válido:")
            print(f"   - Longitud: {len(message)} caracteres")
            print(f"   - Todas las secciones presentes")

        # ===== TEST 7: Handler Mock Test =====
        print("\n" + "-"*70)
        print("🧪 TEST 7: Handler function signatures")
        print("-"*70)

        # Verificar que las funciones son async
        import inspect
        assert inspect.iscoroutinefunction(callback_stats_general), "callback_stats_general debe ser async"
        assert inspect.iscoroutinefunction(callback_stats_refresh), "callback_stats_refresh debe ser async"
        assert inspect.iscoroutinefunction(callback_stats_vip), "callback_stats_vip debe ser async"
        assert inspect.iscoroutinefunction(callback_stats_free), "callback_stats_free debe ser async"
        assert inspect.iscoroutinefunction(callback_stats_tokens), "callback_stats_tokens debe ser async"

        print("✅ Handler functions son async:")
        print(f"   - callback_stats_general: async ✓")
        print(f"   - callback_stats_refresh: async ✓")
        print(f"   - callback_stats_vip: async ✓")
        print(f"   - callback_stats_free: async ✓")
        print(f"   - callback_stats_tokens: async ✓")

        # ===== TEST 8: Admin Router Check =====
        print("\n" + "-"*70)
        print("🧪 TEST 8: Admin router imports")
        print("-"*70)

        from bot.handlers.admin.main import admin_router
        from bot.handlers.admin import stats as stats_module

        assert admin_router is not None, "admin_router debe existir"
        assert stats_module is not None, "stats module debe ser importable"

        print("✅ Router imports válidos:")
        print(f"   - admin_router importado correctamente")
        print(f"   - stats module importado correctamente")

        # ===== RESUMEN =====
        print("\n" + "="*70)
        print("✅✅✅ TODOS LOS TESTS PASARON (8/8)")
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
    success = asyncio.run(test_stats_handlers())
    exit(0 if success else 1)
