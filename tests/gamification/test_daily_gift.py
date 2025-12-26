"""Tests E2E para el sistema de regalo diario.

Tests incluidos:
- Reclamación exitosa de regalo diario
- Prevención de reclamaciones duplicadas
- Cálculo de rachas consecutivas
- Reinicio de racha después de perder días
- Sistema habilitado/desactivado
- Configuración de cantidad de besitos
"""

import pytest
from datetime import datetime, timedelta, UTC
from sqlalchemy import select

from bot.gamification.services.daily_gift import DailyGiftService
from bot.gamification.services.besito import BesitoService
from bot.gamification.database.models import (
    DailyGiftClaim,
    GamificationConfig,
    UserGamification,
    BesitoTransaction
)
from bot.gamification.database.enums import TransactionType


@pytest.mark.asyncio
async def test_first_daily_gift_claim(db_session):
    """Test: Primera reclamación de regalo diario.

    Verifica:
    - Usuario puede reclamar regalo por primera vez
    - Se crea registro de reclamación
    - Racha inicial es 1
    - Se otorgan besitos correctamente
    """
    user_id = 12345
    service = DailyGiftService(db_session)

    # Configurar sistema (besitos por defecto = 10)
    config = GamificationConfig(id=1, daily_gift_enabled=True, daily_gift_besitos=15)
    db_session.add(config)
    await db_session.commit()

    # Reclamar regalo por primera vez
    success, message, details = await service.claim_daily_gift(user_id)

    assert success is True
    assert details['besitos_earned'] == 15
    assert details['current_streak'] == 1
    assert details['total_claims'] == 1

    # Verificar registro en BD
    claim = await db_session.get(DailyGiftClaim, user_id)
    assert claim is not None
    assert claim.current_streak == 1
    assert claim.total_claims == 1


@pytest.mark.asyncio
async def test_daily_gift_cannot_claim_twice_same_day(db_session):
    """Test: No se puede reclamar dos veces el mismo día.

    Verifica:
    - Primera reclamación es exitosa
    - Segunda reclamación es rechazada
    - Mensaje indica cuándo puede reclamar nuevamente
    """
    user_id = 12346
    service = DailyGiftService(db_session)

    # Configurar sistema
    config = GamificationConfig(id=1, daily_gift_enabled=True, daily_gift_besitos=10)
    db_session.add(config)
    await db_session.commit()

    # Primera reclamación
    success1, msg1, details1 = await service.claim_daily_gift(user_id)
    assert success1 is True

    # Segunda reclamación (mismo día)
    success2, msg2, details2 = await service.claim_daily_gift(user_id)
    assert success2 is False
    assert "Ya reclamaste" in msg2 or "Próximo regalo" in msg2


@pytest.mark.asyncio
async def test_daily_gift_streak_consecutive_days(db_session):
    """Test: Racha se incrementa en días consecutivos.

    Verifica:
    - Día 1: racha = 1
    - Día 2 (consecutivo): racha = 2
    - Día 3 (consecutivo): racha = 3
    """
    user_id = 12347
    service = DailyGiftService(db_session)

    # Configurar sistema
    config = GamificationConfig(id=1, daily_gift_enabled=True, daily_gift_besitos=10)
    db_session.add(config)
    await db_session.commit()

    # Día 1
    success, msg, details = await service.claim_daily_gift(user_id)
    assert success is True
    assert details['current_streak'] == 1

    # Simular día siguiente (modificar last_claim_date manualmente)
    claim = await db_session.get(DailyGiftClaim, user_id)
    yesterday = datetime.now(UTC) - timedelta(days=1)
    claim.last_claim_date = yesterday
    await db_session.commit()

    # Día 2 (consecutivo)
    success, msg, details = await service.claim_daily_gift(user_id)
    assert success is True
    assert details['current_streak'] == 2

    # Simular día siguiente
    claim = await db_session.get(DailyGiftClaim, user_id)
    yesterday = datetime.now(UTC) - timedelta(days=1)
    claim.last_claim_date = yesterday
    await db_session.commit()

    # Día 3 (consecutivo)
    success, msg, details = await service.claim_daily_gift(user_id)
    assert success is True
    assert details['current_streak'] == 3


@pytest.mark.asyncio
async def test_daily_gift_streak_reset_after_skip(db_session):
    """Test: Racha se reinicia si se pierde un día.

    Verifica:
    - Racha inicial = 2
    - Después de perder 2 días, racha = 1
    """
    user_id = 12348
    service = DailyGiftService(db_session)

    # Configurar sistema
    config = GamificationConfig(id=1, daily_gift_enabled=True, daily_gift_besitos=10)
    db_session.add(config)
    await db_session.commit()

    # Crear racha de 2 días
    claim = DailyGiftClaim(
        user_id=user_id,
        last_claim_date=datetime.now(UTC) - timedelta(days=1),
        current_streak=2,
        total_claims=2
    )
    db_session.add(claim)
    await db_session.commit()

    # Simular 3 días de ausencia (se perdió la racha)
    claim.last_claim_date = datetime.now(UTC) - timedelta(days=3)
    await db_session.commit()

    # Reclamar hoy (racha se debe reiniciar a 1)
    success, msg, details = await service.claim_daily_gift(user_id)
    assert success is True
    assert details['current_streak'] == 1  # Racha reiniciada


@pytest.mark.asyncio
async def test_daily_gift_system_disabled(db_session):
    """Test: Sistema desactivado rechaza reclamaciones.

    Verifica:
    - Cuando daily_gift_enabled = False
    - Reclamación es rechazada
    - Mensaje indica que el sistema está desactivado
    """
    user_id = 12349
    service = DailyGiftService(db_session)

    # Configurar sistema DESACTIVADO
    config = GamificationConfig(id=1, daily_gift_enabled=False, daily_gift_besitos=10)
    db_session.add(config)
    await db_session.commit()

    # Intentar reclamar
    success, msg, details = await service.claim_daily_gift(user_id)
    assert success is False
    assert "desactivado" in msg.lower()


@pytest.mark.asyncio
async def test_daily_gift_besitos_transaction(db_session):
    """Test: Transacción de besitos se registra correctamente.

    Verifica:
    - Se crea transacción con tipo DAILY_GIFT
    - Balance se actualiza correctamente
    - Transaction incluye descripción adecuada
    """
    user_id = 12350
    service = DailyGiftService(db_session)

    # Configurar sistema
    config = GamificationConfig(id=1, daily_gift_enabled=True, daily_gift_besitos=20)
    db_session.add(config)
    await db_session.commit()

    # Reclamar regalo
    success, msg, details = await service.claim_daily_gift(user_id)
    assert success is True
    assert details['besitos_earned'] == 20

    # Verificar transacción en BD
    stmt = select(BesitoTransaction).where(
        BesitoTransaction.user_id == user_id,
        BesitoTransaction.transaction_type == TransactionType.DAILY_GIFT.value
    )
    result = await db_session.execute(stmt)
    transaction = result.scalar_one_or_none()

    assert transaction is not None
    assert transaction.amount == 20
    assert "Regalo diario" in transaction.description

    # Verificar balance del usuario
    user_gamif = await db_session.get(UserGamification, user_id)
    assert user_gamif.total_besitos == 20


@pytest.mark.asyncio
async def test_daily_gift_status(db_session):
    """Test: get_daily_gift_status retorna información correcta.

    Verifica:
    - Antes de reclamar: can_claim = True
    - Después de reclamar: can_claim = False
    - Información de racha es correcta
    """
    user_id = 12351
    service = DailyGiftService(db_session)

    # Configurar sistema
    config = GamificationConfig(id=1, daily_gift_enabled=True, daily_gift_besitos=10)
    db_session.add(config)
    await db_session.commit()

    # Estado antes de reclamar
    status = await service.get_daily_gift_status(user_id)
    assert status['can_claim'] is True
    assert status['current_streak'] == 0
    assert status['total_claims'] == 0

    # Reclamar
    await service.claim_daily_gift(user_id)

    # Estado después de reclamar
    status = await service.get_daily_gift_status(user_id)
    assert status['can_claim'] is False
    assert status['current_streak'] == 1
    assert status['total_claims'] == 1


@pytest.mark.asyncio
async def test_daily_gift_reset_user_streak(db_session):
    """Test: Admin puede resetear racha de un usuario.

    Verifica:
    - Racha se reinicia a 0
    - Total de reclamaciones se mantiene
    """
    user_id = 12352
    service = DailyGiftService(db_session)

    # Crear racha de 5 días
    claim = DailyGiftClaim(
        user_id=user_id,
        current_streak=5,
        longest_streak=5,
        total_claims=10
    )
    db_session.add(claim)
    await db_session.commit()

    # Resetear racha (función admin)
    success = await service.reset_user_streak(user_id)
    assert success is True

    # Verificar que racha = 0
    claim = await db_session.get(DailyGiftClaim, user_id)
    assert claim.current_streak == 0
    assert claim.total_claims == 10  # Se mantiene
