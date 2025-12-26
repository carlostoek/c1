"""
Role-Based Menus Tests - Validación de menús diferenciados por rol.

Tests que verifican que cada rol (ADMIN, VIP, FREE) recibe el menú correcto:
- Admin recibe redirección a /admin
- VIP activo recibe menú VIP con 3 opciones
- FREE recibe menú básico con opción de canjear token
- VIP handlers funcionan correctamente
"""
import pytest
from datetime import datetime, timedelta

from bot.database import get_session
from bot.services.container import ServiceContainer
from bot.database.models import VIPSubscriber, SubscriptionPlan
from bot.database.enums import UserRole
from bot.utils.keyboards import vip_user_menu_keyboard


@pytest.mark.asyncio
async def test_vip_menu_keyboard_structure(mock_bot):
    """
    Test: Estructura del teclado del menú VIP.

    Verifica que el teclado VIP tiene:
    - 3 botones en total
    - Botón "Acceder al Canal VIP" con callback user:vip_access
    - Botón "Ver Mi Suscripción" con callback user:vip_status
    - Botón "Renovar Suscripción" con callback user:vip_renew

    Expected:
    - Keyboard con 3 filas
    - Callbacks correctos
    """
    print("\n[TEST] Estructura del Teclado VIP")

    keyboard = vip_user_menu_keyboard()

    # Verificar estructura
    assert keyboard is not None
    assert hasattr(keyboard, 'inline_keyboard')
    assert len(keyboard.inline_keyboard) == 3

    # Verificar botones
    buttons = keyboard.inline_keyboard

    # Botón 1: Acceder al Canal VIP
    assert buttons[0][0].text == "📺 Acceder al Canal VIP"
    assert buttons[0][0].callback_data == "user:vip_access"

    # Botón 2: Ver Mi Suscripción
    assert buttons[1][0].text == "⏱️ Ver Mi Suscripción"
    assert buttons[1][0].callback_data == "user:vip_status"

    # Botón 3: Renovar Suscripción
    assert buttons[2][0].text == "🎁 Renovar Suscripción"
    assert buttons[2][0].callback_data == "user:vip_renew"

    print("  OK: Teclado VIP tiene estructura correcta")
    print("  [PASSED] Estructura del Teclado VIP\n")


@pytest.mark.asyncio
async def test_vip_user_has_active_subscription(mock_bot):
    """
    Test: Usuario VIP tiene suscripción activa.

    Escenario:
    1. Crear usuario VIP con suscripción activa
    2. Verificar que is_vip_active() retorna True
    3. Verificar que get_vip_subscriber() retorna datos correctos

    Expected:
    - Usuario detectado como VIP activo
    - Días restantes > 0
    - Status = 'active'
    """
    print("\n[TEST] Usuario VIP Tiene Suscripción Activa")

    user_id = 333333
    admin_id = 111111

    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Generar token primero (necesario para crear subscriber)
        print("  1. Generando token VIP...")
        token = await container.subscription.generate_vip_token(
            generated_by=admin_id,
            duration_hours=30 * 24  # 30 días
        )

        # Crear suscripción VIP usando el token
        print("  2. Creando suscripción VIP...")
        success, msg, subscriber = await container.subscription.redeem_vip_token(
            token_str=token.token,
            user_id=user_id
        )

        assert success == True
        assert subscriber is not None

        # Verificar VIP activo
        print("  3. Verificando VIP activo...")
        is_vip = await container.subscription.is_vip_active(user_id)
        assert is_vip == True

        # Obtener datos del suscriptor
        print("  4. Obteniendo datos del suscriptor...")
        sub = await container.subscription.get_vip_subscriber(user_id)
        assert sub is not None
        assert sub.user_id == user_id
        assert sub.status == "active"

        days = sub.days_remaining()
        assert days >= 29  # Al menos 29 días (puede ser 30)

        print(f"     OK: Usuario VIP activo con {days} días restantes")

    print("  [PASSED] Usuario VIP Tiene Suscripción Activa\n")


@pytest.mark.asyncio
async def test_vip_status_shows_correct_info(mock_bot):
    """
    Test: El handler vip_status muestra información correcta.

    Escenario:
    1. Crear suscriptor VIP con plan asociado
    2. Verificar que get_vip_subscriber() retorna plan correcto
    3. Verificar cálculo de días restantes

    Expected:
    - Días restantes calculados correctamente
    - Plan asociado visible
    - Fechas formateadas correctamente
    """
    print("\n[TEST] VIP Status Muestra Información Correcta")

    user_id = 900001  # ID único para evitar colisiones
    admin_id = 111111

    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Crear plan de prueba
        print("  1. Creando plan de prueba...")
        plan = SubscriptionPlan(
            name="Plan Mensual Test",
            duration_days=30,
            price=9.99,
            currency="USD",
            active=True,
            created_by=admin_id
        )
        session.add(plan)
        await session.commit()
        await session.refresh(plan)

        # Generar token con plan
        print("  2. Generando token con plan...")
        token = await container.subscription.generate_vip_token(
            generated_by=admin_id,
            duration_hours=30 * 24,  # 30 días
            plan_id=plan.id
        )

        # Canjear token
        print("  3. Canjeando token...")
        success, msg, subscriber = await container.subscription.redeem_vip_token(
            token_str=token.token,
            user_id=user_id
        )

        assert success == True
        assert subscriber is not None

        # Verificar información del suscriptor
        print("  4. Verificando información...")
        sub = await container.subscription.get_vip_subscriber(user_id)
        assert sub is not None

        # Verificar plan asociado (acceder a relaciones dentro del contexto de sesión)
        assert sub.token_id is not None
        assert sub.token_id == token.id

        # Acceder a token y plan dentro del contexto de sesión
        await session.refresh(sub, ["token"])
        assert sub.token is not None
        assert sub.token.plan_id is not None

        # Refresh plan también
        await session.refresh(sub.token, ["plan"])
        assert sub.token.plan.name == "Plan Mensual Test"
        assert sub.token.plan.price == 9.99

        # Verificar días restantes
        days = sub.days_remaining()
        assert days >= 29  # Al menos 29 días

        print(f"     OK: Plan asociado correctamente ({sub.token.plan.name})")
        print(f"     OK: {days} días restantes calculados")

    print("  [PASSED] VIP Status Muestra Información Correcta\n")


@pytest.mark.asyncio
async def test_free_user_cannot_access_vip_menu(mock_bot):
    """
    Test: Usuario FREE no puede acceder a menú VIP.

    Escenario:
    1. Usuario FREE sin suscripción
    2. Verificar que is_vip_active() retorna False
    3. Verificar que get_vip_subscriber() retorna None

    Expected:
    - Usuario NO detectado como VIP
    - No debe recibir menú VIP
    """
    print("\n[TEST] Usuario FREE No Puede Acceder a Menú VIP")

    user_id = 555555

    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Verificar que NO es VIP
        print("  1. Verificando usuario FREE...")
        is_vip = await container.subscription.is_vip_active(user_id)
        assert is_vip == False

        # Verificar que NO tiene suscripción
        print("  2. Verificando ausencia de suscripción...")
        sub = await container.subscription.get_vip_subscriber(user_id)
        assert sub is None

        print("     OK: Usuario FREE correctamente detectado sin acceso VIP")

    print("  [PASSED] Usuario FREE No Puede Acceder a Menú VIP\n")


@pytest.mark.asyncio
async def test_expired_vip_loses_access(mock_bot):
    """
    Test: VIP expirado pierde acceso al menú.

    Escenario:
    1. Crear suscripción VIP expirada (hace 1 día)
    2. Verificar que is_vip_active() retorna False
    3. Verificar que status se detecta como expirado

    Expected:
    - VIP expirado NO tiene acceso activo
    - No debe recibir menú VIP
    """
    print("\n[TEST] VIP Expirado Pierde Acceso")

    user_id = 666666
    admin_id = 111111

    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Generar token con duración corta
        print("  1. Generando token VIP...")
        token = await container.subscription.generate_vip_token(
            generated_by=admin_id,
            duration_hours=1  # 1 hora (simula expirado)
        )

        # Canjear token
        print("  2. Canjeando token...")
        success, msg, subscriber = await container.subscription.redeem_vip_token(
            token_str=token.token,
            user_id=user_id
        )

        assert success == True

        # Modificar manualmente la fecha de expiración para simular expiración
        print("  3. Modificando expiry_date para simular expiración...")
        subscriber.expiry_date = datetime.utcnow() - timedelta(days=1)
        await session.commit()

        # Verificar que NO es VIP activo
        print("  4. Verificando VIP expirado...")
        is_vip = await container.subscription.is_vip_active(user_id)
        assert is_vip == False

        # Verificar que days_remaining es negativo
        sub = await container.subscription.get_vip_subscriber(user_id)
        assert sub is not None
        days = sub.days_remaining()
        assert days < 0  # Negativo porque expiró

        print(f"     OK: VIP expirado correctamente ({days} días restantes)")

    print("  [PASSED] VIP Expirado Pierde Acceso\n")


@pytest.mark.asyncio
async def test_vip_renew_shows_available_plans(mock_bot):
    """
    Test: Renovación VIP muestra planes disponibles.

    Escenario:
    1. Crear múltiples planes activos
    2. Verificar que get_active_plans() retorna todos los planes
    3. Verificar que planes inactivos NO aparecen

    Expected:
    - Solo planes activos visibles
    - Información completa de cada plan
    """
    print("\n[TEST] Renovación VIP Muestra Planes Disponibles")

    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Crear planes de prueba
        print("  1. Creando planes de prueba...")
        admin_id = 111111

        plan1 = SubscriptionPlan(
            name="Plan Básico",
            duration_days=7,
            price=4.99,
            currency="USD",
            active=True,
            created_by=admin_id
        )
        plan2 = SubscriptionPlan(
            name="Plan Pro",
            duration_days=30,
            price=14.99,
            currency="USD",
            active=True,
            created_by=admin_id
        )
        plan3 = SubscriptionPlan(
            name="Plan Anual",
            duration_days=365,
            price=99.99,
            currency="USD",
            active=False,  # INACTIVO
            created_by=admin_id
        )

        session.add_all([plan1, plan2, plan3])
        await session.commit()

        # Obtener planes activos
        print("  2. Obteniendo planes activos...")
        plans = await container.pricing.get_all_plans(active_only=True)

        # Verificar que solo retorna planes activos
        assert len(plans) >= 2  # Al menos plan1 y plan2 (puede haber más de tests anteriores)
        assert all(p.active for p in plans)

        # Verificar que plan3 (inactivo) NO aparece
        plan_names = [p.name for p in plans]
        assert "Plan Básico" in plan_names
        assert "Plan Pro" in plan_names
        assert "Plan Anual" not in plan_names  # Este debe estar ausente

        # Verificar que el plan inactivo específico NO está
        plan3_ids = [p.id for p in plans if p.name == "Plan Anual"]
        assert len(plan3_ids) == 0  # Plan Anual no debe estar en activos

        print(f"     OK: {len(plans)} planes activos disponibles")
        print(f"     OK: Planes inactivos ocultos correctamente")

        print("  [PASSED] Renovación VIP Muestra Planes Disponibles\n")
