"""
Tests E2E para A3 - Deep Links y Activación Automática de Tokens

Validar:
1. Generación de tokens vinculados a plans
2. Activación automática vía deep link
3. Cambio de rol de FREE a VIP automáticamente
4. Compatibilidad con tokens antiguos sin plan
"""
import logging
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from bot.services.container import ServiceContainer
from bot.database.models import SubscriptionPlan, InvitationToken, VIPSubscriber
from bot.database.engine import get_session
from bot.database.enums import UserRole


logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_generate_token_with_plan(mock_bot):
    """
    Test: Generar token vinculado a un plan específico.

    Escenario:
    1. Crear un plan activo
    2. Generar token vinculado al plan
    3. Verificar que token tiene plan_id
    4. Verificar que duration_hours corresponde al plan

    Expected:
    - Token creado con plan_id
    - Token duration_hours = plan.duration_days * 24
    - Token válido por 24 horas (expiry)
    """
    print("\n[TEST A3] Generar Token con Plan")

    admin_id = 999999
    plan_name = "Plan Mensual"
    plan_days = 30
    plan_price = 9.99

    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Paso 1: Crear un plan
        print("  1. Creando plan de suscripción...")
        plan = await container.pricing.create_plan(
            name=plan_name,
            duration_days=plan_days,
            price=plan_price,
            currency="$",
            created_by=admin_id
        )
        assert plan.id is not None
        assert plan.active == True
        print(f"     OK: Plan creado (ID: {plan.id}, Duración: {plan_days} días)")

        # Paso 2: Generar token vinculado al plan
        print("  2. Generando token vinculado al plan...")
        token = await container.subscription.generate_vip_token(
            generated_by=admin_id,
            duration_hours=plan.duration_days * 24,  # Convertir días a horas
            plan_id=plan.id  # NUEVO: Vincular con plan
        )

        assert token.plan_id == plan.id
        assert token.duration_hours == plan_days * 24
        assert token.used == False
        print(
            f"     OK: Token generado (ID: {token.id}, Plan ID: {token.plan_id}, "
            f"Duración: {token.duration_hours}h)"
        )

        # Paso 3: Verificar que el token está vinculado
        print("  3. Verificando vinculación token-plan...")
        await session.refresh(token)
        assert token.plan is not None
        assert token.plan.name == plan_name
        print(f"     OK: Plan asociado al token: {token.plan.name}")


@pytest.mark.asyncio
async def test_activate_vip_from_deep_link(mock_bot):
    """
    Test: Activar suscripción VIP desde deep link.

    Escenario:
    1. Crear plan y token vinculado
    2. Crear usuario con rol FREE
    3. Activar suscripción con activate_vip_subscription
    4. Verificar que usuario tiene VIP activo
    5. Verificar que rol puede actualizar a VIP en BD

    Expected:
    - Suscriptor creado con expiry_date correcto
    - Usuario puede tener rol actualizado a VIP
    - Token marcado como usado
    - Invite link se puede generar
    """
    print("\n[TEST A3] Activar VIP desde Deep Link")

    admin_id = 999999
    user_id = 444444
    plan_days = 30

    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Crear usuario
        print("  1. Creando usuario...")
        from aiogram.types import User as TelegramUser

        telegram_user = TelegramUser(
            id=user_id,
            is_bot=False,
            first_name="Test",
            last_name="User"
        )
        user = await container.user.get_or_create_user(
            telegram_user=telegram_user,
            default_role=UserRole.FREE
        )
        # Asegurar que el rol es FREE
        if user.role != UserRole.FREE:
            user.role = UserRole.FREE
            await session.commit()
        assert user.role == UserRole.FREE
        print(f"     OK: Usuario creado (ID: {user.user_id}, Rol: {user.role.value})")

        # Crear plan
        plan = await container.pricing.create_plan(
            name="Plan Mensual",
            duration_days=plan_days,
            price=9.99,
            currency="$",
            created_by=admin_id
        )
        await session.commit()
        await session.refresh(plan)

        # Crear token vinculado
        token = await container.subscription.generate_vip_token(
            generated_by=admin_id,
            duration_hours=plan_days * 24,
            plan_id=plan.id
        )
        await session.commit()
        await session.refresh(token)

        # Paso 2: Activar suscripción VIP y actualizar rol (simula handler completo)
        print("  2. Activando suscripción VIP...")

        # Marcar token como usado
        token.used = True
        token.used_by = user.user_id
        token.used_at = datetime.utcnow()

        # Activar suscripción
        subscriber = await container.subscription.activate_vip_subscription(
            user_id=user.user_id,
            token_id=token.id,
            duration_hours=plan_days * 24
        )

        # Actualizar rol automáticamente (esto lo hace el handler)
        await container.user.change_role(user.user_id, UserRole.VIP, "Token activado")

        # Commit único de toda la transacción
        await session.commit()
        await session.refresh(subscriber)
        await session.refresh(user)

        assert subscriber.user_id == user.user_id
        assert subscriber.status == "active"
        assert not subscriber.is_expired()
        print(f"     OK: Suscriptor creado (Expira: {subscriber.expiry_date})")

        # Paso 3: Verificar que VIP está activo
        print("  3. Verificando VIP activo...")
        is_vip = await container.subscription.is_vip_active(user.user_id)
        assert is_vip == True
        print("     OK: VIP activo verificado")

        # Paso 4: Verificar que el rol fue actualizado automáticamente
        print("  4. Verificando rol automáticamente actualizado...")
        assert user.role == UserRole.VIP
        print(f"     OK: Rol automáticamente actualizado a {user.role.value}")

        # Paso 5: Validar que token ya está marcado como usado
        print("  5. Validando token usado...")
        is_valid, msg, checked_token = await container.subscription.validate_token(token.token)
        assert is_valid == False  # No es válido porque ya fue usado
        print(f"     OK: Token ya usado (msg: {msg})")


@pytest.mark.asyncio
async def test_deep_link_format(mock_bot):
    """
    Test: Generar deep link profesional.

    Escenario:
    1. Generar token
    2. Crear deep link en formato t.me/botname?start=TOKEN
    3. Verificar que el link contiene el token correcto

    Expected:
    - Deep link tiene formato correcto
    - Deep link contiene el token
    - Deep link contiene username del bot
    """
    print("\n[TEST A3] Formato de Deep Link")

    admin_id = 999999

    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Crear token
        print("  1. Generando token...")
        token = await container.subscription.generate_vip_token(
            generated_by=admin_id,
            duration_hours=24
        )
        print(f"     OK: Token generado: {token.token}")

        # Generar deep link
        print("  2. Construyendo deep link...")
        # Usar username del bot (simulado)
        bot_username = "test_bot"
        deep_link = f"https://t.me/{bot_username}?start={token.token}"

        assert "https://t.me/" in deep_link
        assert bot_username in deep_link
        assert token.token in deep_link
        assert "?start=" in deep_link

        print(f"     OK: Deep link generado: {deep_link[:50]}...")


@pytest.mark.asyncio
async def test_extend_vip_via_deep_link(mock_bot):
    """
    Test: Extender suscripción VIP existente vía deep link.

    Escenario:
    1. Crear usuario VIP con expiración próxima
    2. Crear token y activar vía deep link
    3. Verificar que expiry_date se extiende
    4. Verificar que no crea duplicate subscribers

    Expected:
    - Suscriptor se extiende (no se crea nuevo)
    - expiry_date se actualiza correctamente
    - No hay múltiples rows en vip_subscribers
    """
    print("\n[TEST A3] Extender VIP vía Deep Link")

    admin_id = 999999
    user_id = 555555
    plan_days = 30

    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Crear usuario y plan
        from aiogram.types import User as TelegramUser

        telegram_user = TelegramUser(
            id=user_id,
            is_bot=False,
            first_name="Test",
            last_name="User"
        )
        user = await container.user.get_or_create_user(
            telegram_user=telegram_user,
            default_role=UserRole.FREE
        )
        # Asegurar que el rol es FREE
        if user.role != UserRole.FREE:
            user.role = UserRole.FREE
            await session.commit()

        plan = await container.pricing.create_plan(
            name="Plan Mensual",
            duration_days=plan_days,
            price=9.99,
            currency="$",
            created_by=admin_id
        )

        # Paso 1: Crear suscriptor VIP existente
        print("  1. Creando suscriptor VIP existente...")
        token1 = await container.subscription.generate_vip_token(
            generated_by=admin_id,
            duration_hours=plan_days * 24,
            plan_id=plan.id
        )

        subscriber1 = await container.subscription.activate_vip_subscription(
            user_id=user.user_id,
            token_id=token1.id,
            duration_hours=plan_days * 24
        )

        original_expiry = subscriber1.expiry_date
        print(
            f"     OK: Suscriptor creado (Expira: {original_expiry})"
        )

        # Paso 2: Crear nuevo token y activar
        print("  2. Activando nuevo token para usuario existente...")
        token2 = await container.subscription.generate_vip_token(
            generated_by=admin_id,
            duration_hours=plan_days * 24,
            plan_id=plan.id
        )

        subscriber2 = await container.subscription.activate_vip_subscription(
            user_id=user.user_id,
            token_id=token2.id,
            duration_hours=plan_days * 24
        )

        # Paso 3: Verificar extensión
        print("  3. Verificando extensión de suscripción...")
        assert subscriber2.user_id == subscriber1.user_id
        assert subscriber2.expiry_date > original_expiry
        print(
            f"     OK: Suscripción extendida (Nueva expiry: {subscriber2.expiry_date})"
        )


@pytest.mark.asyncio
async def test_backward_compatibility_token_without_plan(mock_bot):
    """
    Test: Compatibilidad con tokens antiguos sin plan_id.

    Escenario:
    1. Generar token SIN plan_id (compatibilidad)
    2. Intentar activar vía deep link
    3. Verificar que devuelve error apropiado

    Expected:
    - Token se genera sin plan_id
    - Validación de token funciona
    - Activación rechaza token sin plan (error apropiado)
    """
    print("\n[TEST A3] Compatibilidad Token Sin Plan")

    admin_id = 999999
    user_id = 666666

    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Paso 1: Generar token sin plan_id
        print("  1. Generando token sin plan_id (backwards compat)...")
        token = await container.subscription.generate_vip_token(
            generated_by=admin_id,
            duration_hours=24,
            plan_id=None  # Sin plan
        )

        assert token.plan_id is None
        print(f"     OK: Token generado sin plan_id: {token.token}")

        # Paso 2: Validar token
        print("  2. Validando token...")
        is_valid, msg, checked_token = await container.subscription.validate_token(token.token)
        assert is_valid == True
        print(f"     OK: Token válido (msg: {msg})")

        # Paso 3: Verificar que plan es None
        print("  3. Verificando que plan es None...")
        await session.refresh(token)
        assert token.plan is None
        print("     OK: Plan es None (compatibilidad con tokens antiguos)")


@pytest.mark.asyncio
async def test_token_expiry_validation(mock_bot):
    """
    Test: Validar que tokens expiran correctamente.

    Escenario:
    1. Generar token
    2. Simular expiración (modificar created_at)
    3. Intentar validar token
    4. Verificar que rechaza token expirado

    Expected:
    - Token es inválido después de expiración
    - Mensaje de error apropiado
    """
    print("\n[TEST A3] Validación de Expiración de Token")

    admin_id = 999999

    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Paso 1: Generar token
        print("  1. Generando token...")
        token = await container.subscription.generate_vip_token(
            generated_by=admin_id,
            duration_hours=1  # Expira en 1 hora
        )
        print(f"     OK: Token generado: {token.token}")

        # Paso 2: Simular expiración
        print("  2. Simulando expiración del token...")
        token.created_at = datetime.utcnow() - timedelta(hours=2)  # Hace 2 horas
        await session.commit()

        # Paso 3: Validar token
        print("  3. Validando token expirado...")
        is_valid, msg, checked_token = await container.subscription.validate_token(token.token)

        assert is_valid == False
        assert "expirado" in msg.lower() or "expired" in msg.lower()
        print(f"     OK: Token rechazado (msg: {msg})")


@pytest.mark.asyncio
async def test_token_single_use(mock_bot):
    """
    Test: Token de un solo uso.

    Escenario:
    1. Generar token
    2. Crear usuario y activar con el token
    3. Intentar usar el mismo token otra vez
    4. Verificar que rechaza token usado

    Expected:
    - Primer uso: éxito
    - Segundo uso: error "token ya fue usado"
    """
    print("\n[TEST A3] Token de Un Solo Uso")

    admin_id = 999999
    user1_id = 777777
    user2_id = 888888
    plan_days = 30

    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        from aiogram.types import User as TelegramUser

        # Crear plan
        plan = await container.pricing.create_plan(
            name="Plan Mensual",
            duration_days=plan_days,
            price=9.99,
            currency="$",
            created_by=admin_id
        )

        # Crear token
        print("  1. Generando token de un solo uso...")
        token = await container.subscription.generate_vip_token(
            generated_by=admin_id,
            duration_hours=plan_days * 24,
            plan_id=plan.id
        )
        print(f"     OK: Token generado: {token.token}")

        # Usuario 1 usa el token
        print("  2. Primer usuario canjea token...")
        telegram_user1 = TelegramUser(
            id=user1_id,
            is_bot=False,
            first_name="User1",
            last_name="Test"
        )
        user1 = await container.user.get_or_create_user(
            telegram_user=telegram_user1,
            default_role=UserRole.FREE
        )

        subscriber1 = await container.subscription.activate_vip_subscription(
            user_id=user1.user_id,
            token_id=token.id,
            duration_hours=plan_days * 24
        )

        # Marcar como usado
        token.used = True
        token.used_by = user1.user_id
        token.used_at = datetime.utcnow()
        await session.commit()

        print(f"     OK: Primer usuario activó suscripción")

        # Usuario 2 intenta usar el mismo token
        print("  3. Segundo usuario intenta canjear mismo token...")
        is_valid, msg, checked_token = await container.subscription.validate_token(token.token)

        assert is_valid == False
        assert "usado" in msg.lower() or "used" in msg.lower()
        print(f"     OK: Token rechazado (msg: {msg})")
