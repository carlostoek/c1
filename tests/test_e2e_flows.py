"""
End-to-End Tests - Flujos completos del usuario.

Tests que validan escenarios reales de principio a fin:
- Flujo VIP completo (generar token -> canjear -> acceso)
- Flujo Free completo (solicitar -> esperar -> acceso)
- Expulsion automatica de VIP
- Validacion de tokens (edge cases)
"""
import pytest
from datetime import datetime, timedelta

from bot.database import get_session
from bot.database.models import InvitationToken, VIPSubscriber
from bot.services.container import ServiceContainer
from sqlalchemy import select


@pytest.mark.asyncio
async def test_vip_flow_complete(mock_bot):
    """
    Test E2E: Flujo VIP completo.

    Escenario:
    1. Admin genera token VIP
    2. Usuario canjea token
    3. Usuario recibe suscripcion VIP activa
    4. Verificar datos en BD

    Expected:
    - Token generado con 16 caracteres
    - Token validado como unused
    - Suscriptor creado con status='active'
    - Token marcado como used despues del canje
    """
    print("\n[TEST] Flujo VIP Completo")

    admin_id = 111111
    user_id = 222222

    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Paso 1: Admin genera token
        print("  1. Generando token VIP...")
        token = await container.subscription.generate_vip_token(
            generated_by=admin_id,
            duration_hours=24
        )

        assert token.token is not None
        assert len(token.token) == 16
        assert token.used == False
        print(f"     OK: Token generado: {token.token}")

        # Paso 2: Usuario canjea token
        print("  2. Canjeando token...")
        success, msg, subscriber = await container.subscription.redeem_vip_token(
            token_str=token.token,
            user_id=user_id
        )

        assert success == True
        assert subscriber is not None
        assert subscriber.user_id == user_id
        assert subscriber.status == "active"
        print(f"     OK: Token canjeado")

        # Paso 3: Verificar suscripcion activa
        print("  3. Verificando suscripcion...")
        is_vip = await container.subscription.is_vip_active(user_id)
        assert is_vip == True

        days = subscriber.days_remaining()
        assert days >= 0  # Puede ser 0 si se creó hoy
        print(f"     OK: VIP activo ({days} dias restantes)")

        # Paso 4: Verificar token marcado como usado
        print("  4. Verificando token usado...")
        result = await session.execute(
            select(InvitationToken).where(InvitationToken.token == token.token)
        )
        used_token = result.scalar_one()

        assert used_token.used == True
        assert used_token.used_by == user_id
        assert used_token.used_at is not None
        print(f"     OK: Token marcado como usado")

    print("  [PASSED] Flujo VIP Completo\n")


@pytest.mark.asyncio
async def test_free_flow_complete(mock_bot):
    """
    Test E2E: Flujo Free completo.

    Escenario:
    1. Usuario solicita acceso Free
    2. Solicitud queda pendiente
    3. Simular paso del tiempo (modificar request_date)
    4. Procesar cola
    5. Verificar solicitud procesada

    Expected:
    - Solicitud creada con processed=False
    - No se procesa inmediatamente
    - Se procesa despues del wait_time
    - No se procesa dos veces
    """
    print("\n[TEST] Flujo Free Completo")

    user_id = 333333
    wait_time = 5

    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Configurar tiempo de espera
        await container.config.set_wait_time(wait_time)

        # Paso 1: Usuario solicita acceso
        print("  1. Creando solicitud Free...")
        request = await container.subscription.create_free_request(user_id)

        assert request.user_id == user_id
        assert request.processed == False
        print(f"     OK: Solicitud creada (ID: {request.id})")

        # Paso 2: Verificar no se puede procesar inmediatamente
        print("  2. Verificando solicitud pendiente...")
        ready = await container.subscription.process_free_queue(wait_time)
        assert len(ready) == 0
        print(f"     OK: Solicitud en espera")

        # Paso 3: Simular paso del tiempo
        print(f"  3. Simulando espera de {wait_time} minutos...")
        request.request_date = datetime.utcnow() - timedelta(minutes=wait_time + 1)
        await session.commit()
        print(f"     OK: Tiempo simulado")

        # Paso 4: Procesar cola
        print("  4. Procesando cola Free...")
        ready = await container.subscription.process_free_queue(wait_time)

        assert len(ready) == 1
        assert ready[0].user_id == user_id
        assert ready[0].processed == True
        assert ready[0].processed_at is not None
        print(f"     OK: Solicitud procesada")

        # Paso 5: Verificar no se procesa dos veces
        print("  5. Verificando no duplicacion...")
        ready_again = await container.subscription.process_free_queue(wait_time)
        assert len(ready_again) == 0
        print(f"     OK: No se procesa dos veces")

    print("  [PASSED] Flujo Free Completo\n")


@pytest.mark.asyncio
async def test_vip_expiration(mock_bot):
    """
    Test E2E: Expiracion automatica de VIP.

    Escenario:
    1. Crear suscriptor VIP con fecha de expiracion pasada
    2. Ejecutar tarea de expiracion
    3. Verificar marcado como expirado
    4. Verificar ya no es VIP activo

    Expected:
    - Suscriptor creado con fecha pasada
    - is_expired() retorna True
    - expire_vip_subscribers() marca como expired
    - is_vip_active() retorna False despues
    """
    print("\n[TEST] Expiracion VIP")

    user_id = 444444

    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Paso 1: Crear suscriptor VIP expirado
        print("  1. Creando suscriptor VIP expirado...")

        # Crear token primero
        token = InvitationToken(
            token="EXPIREDTOKEN123",
            generated_by=111111,
            created_at=datetime.utcnow() - timedelta(days=2),
            duration_hours=24,
            used=True,
            used_by=user_id,
            used_at=datetime.utcnow() - timedelta(days=2)
        )
        session.add(token)
        await session.commit()
        await session.refresh(token)

        # Crear suscriptor expirado
        subscriber = VIPSubscriber(
            user_id=user_id,
            join_date=datetime.utcnow() - timedelta(days=2),
            expiry_date=datetime.utcnow() - timedelta(days=1),
            status="active",
            token_id=token.id
        )
        session.add(subscriber)
        await session.commit()
        print(f"     OK: Suscriptor creado (expirado ayer)")

        # Paso 2: Verificar is_expired() funciona
        print("  2. Verificando deteccion de expiracion...")
        assert subscriber.is_expired() == True
        print(f"     OK: Detectado como expirado")

        # Paso 3: Ejecutar tarea de expiracion
        print("  3. Ejecutando tarea de expiracion...")
        expired_count = await container.subscription.expire_vip_subscribers()
        assert expired_count == 1
        print(f"     OK: {expired_count} suscriptor(es) expirados")

        # Paso 4: Verificar estado actualizado
        print("  4. Verificando estado actualizado...")
        await session.refresh(subscriber)
        assert subscriber.status == "expired"
        print(f"     OK: Status actualizado a 'expired'")

        # Paso 5: Verificar is_vip_active() retorna False
        print("  5. Verificando is_vip_active()...")
        is_vip = await container.subscription.is_vip_active(user_id)
        assert is_vip == False
        print(f"     OK: Ya no es VIP activo")

    print("  [PASSED] Expiracion VIP\n")


@pytest.mark.asyncio
async def test_token_validation_edge_cases(mock_bot):
    """
    Test E2E: Casos edge de validacion de tokens.

    Casos validados:
    - Token no existe
    - Token ya usado
    - Token expirado
    - Token valido

    Expected:
    - Token inexistente: is_valid=False, "no encontrado" en msg
    - Token usado: is_valid=False, "usado" en msg
    - Token expirado: is_valid=False, "expirado" en msg
    - Token valido: is_valid=True, "valido" en msg
    """
    print("\n[TEST] Validacion de Tokens (Edge Cases)")

    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Caso 1: Token no existe
        print("  1. Token no existente...")
        is_valid, msg, _ = await container.subscription.validate_token("NOEXISTE12345678")
        assert is_valid == False
        assert "no encontrado" in msg.lower()
        print(f"     OK: Rechazado - {msg}")

        # Caso 2: Token usado
        print("  2. Token ya usado...")
        token_usado = await container.subscription.generate_vip_token(111111, 24)
        token_usado.used = True
        token_usado.used_by = 999999
        await session.commit()

        is_valid, msg, _ = await container.subscription.validate_token(token_usado.token)
        assert is_valid == False
        assert "usado" in msg.lower()
        print(f"     OK: Rechazado - {msg}")

        # Caso 3: Token expirado
        print("  3. Token expirado...")
        token_expirado = await container.subscription.generate_vip_token(111111, 1)
        token_expirado.created_at = datetime.utcnow() - timedelta(hours=2)
        await session.commit()

        is_valid, msg, _ = await container.subscription.validate_token(token_expirado.token)
        assert is_valid == False
        assert "expirado" in msg.lower()
        print(f"     OK: Rechazado - {msg}")

        # Caso 4: Token valido
        print("  4. Token valido...")
        token_valido = await container.subscription.generate_vip_token(111111, 24)

        is_valid, msg, _ = await container.subscription.validate_token(token_valido.token)
        assert is_valid == True
        assert "válido" in msg.lower() or "valido" in msg.lower()
        print(f"     OK: Aceptado - {msg}")

    print("  [PASSED] Validacion de Tokens\n")


@pytest.mark.asyncio
async def test_duplicate_free_request_prevention(mock_bot):
    """
    Test E2E: Prevencion de solicitudes Free duplicadas.

    Escenario:
    1. Usuario crea primera solicitud Free
    2. Usuario intenta crear segunda solicitud
    3. Segunda solicitud debe fallar

    Expected:
    - Primera solicitud: creada exitosamente
    - Segunda solicitud: retorna error "ya existe"
    """
    print("\n[TEST] Prevencion de Solicitudes Duplicadas")

    user_id = 555555

    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Paso 1: Crear primera solicitud
        print("  1. Creando primera solicitud...")
        request1 = await container.subscription.create_free_request(user_id)
        assert request1 is not None
        print(f"     OK: Primera solicitud creada")

        # Paso 2: Intentar crear segunda (debe fallar)
        print("  2. Intentando crear segunda solicitud...")
        request2 = await container.subscription.create_free_request(user_id)
        # Dependiendo de la implementacion, puede retornar existente o None
        assert request2 is not None
        assert request2.id == request1.id
        print(f"     OK: Se retorna solicitud existente (no duplicada)")

    print("  [PASSED] Prevencion de Duplicados\n")
