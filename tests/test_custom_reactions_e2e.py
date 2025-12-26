"""
End-to-End Tests - Sistema de Reacciones Personalizadas.

Tests que validan escenarios reales del sistema de reacciones
personalizadas para mensajes de broadcasting:
- Flujo completo broadcast con reacciones
- Usuario reacciona y gana besitos
- Prevención de reacciones duplicadas
- Estadísticas de reacciones precisas
- Backward compatibility (broadcast sin reacciones)
"""
import pytest
from datetime import datetime, UTC

from bot.database import get_session
from bot.database.models import BroadcastMessage, User
from bot.gamification.database.models import CustomReaction, Reaction
from bot.gamification.services.container import GamificationContainer
from sqlalchemy import select


@pytest.mark.asyncio
async def test_broadcast_with_reactions_full_flow(mock_bot):
    """
    Test E2E: Flujo completo de broadcast con reacciones.

    Escenario:
    1. Admin crea un BroadcastMessage con gamificación habilitada
    2. Sistema registra el mensaje con configuración de reacciones
    3. Verificar datos en BD

    Expected:
    - BroadcastMessage creado con gamification_enabled=True
    - reaction_buttons contiene configuración de 3 reacciones
    - Stats iniciales en 0
    """
    print("\n[TEST] Flujo Completo Broadcast con Reacciones")

    admin_id = 999111
    channel_id = -1001234567890
    message_id = 99912345

    async with get_session() as session:
        # Paso 1: Crear usuario admin
        print("  1. Creando usuario admin...")
        admin = User(
            user_id=admin_id,
            username="admin_user",
            first_name="Admin",
            role="ADMIN"
        )
        session.add(admin)
        await session.commit()
        print("     OK: Admin creado")

        # Paso 2: Crear reacciones disponibles
        print("  2. Creando tipos de reacciones...")
        reactions = [
            Reaction(
                emoji="👍_test1",
                button_label="Me Gusta",
                besitos_value=10,
                sort_order=1,
                active=True
            ),
            Reaction(
                emoji="❤️_test1",
                button_label="Me Encanta",
                besitos_value=15,
                sort_order=2,
                active=True
            ),
            Reaction(
                emoji="🔥_test1",
                button_label="Increíble",
                besitos_value=20,
                sort_order=3,
                active=True
            ),
        ]
        for reaction in reactions:
            session.add(reaction)
        await session.commit()
        print("     OK: 3 tipos de reacciones creados")

        # Paso 3: Crear BroadcastMessage con gamificación
        print("  3. Creando broadcast message con gamificación...")
        broadcast_msg = BroadcastMessage(
            message_id=message_id,
            chat_id=channel_id,
            content_type="text",
            content_text="¡Nuevo contenido exclusivo! 🎉",
            sent_by=admin_id,
            gamification_enabled=True,
            reaction_buttons=[
                {"emoji": "👍_test1", "label": "Me Gusta", "reaction_type_id": reactions[0].id, "besitos": 10},
                {"emoji": "❤️_test1", "label": "Me Encanta", "reaction_type_id": reactions[1].id, "besitos": 15},
                {"emoji": "🔥_test1", "label": "Increíble", "reaction_type_id": reactions[2].id, "besitos": 20},
            ],
            content_protected=False,
            total_reactions=0,
            unique_reactors=0
        )
        session.add(broadcast_msg)
        await session.commit()
        print(f"     OK: Broadcast message creado (ID: {broadcast_msg.id})")

        # Paso 4: Verificar creación correcta
        print("  4. Verificando datos...")
        result = await session.execute(
            select(BroadcastMessage).where(BroadcastMessage.id == broadcast_msg.id)
        )
        saved_msg = result.scalar_one()

        assert saved_msg.gamification_enabled == True
        assert len(saved_msg.reaction_buttons) == 3
        assert saved_msg.total_reactions == 0
        assert saved_msg.unique_reactors == 0
        print("     OK: Datos verificados")

    print("  [PASSED] Flujo Completo Broadcast con Reacciones\n")


@pytest.mark.asyncio
async def test_user_reacts_and_earns_besitos(mock_bot):
    """
    Test E2E: Usuario reacciona y gana besitos.

    Escenario:
    1. Existe un BroadcastMessage con gamificación
    2. Usuario reacciona con "👍"
    3. Usuario gana 10 besitos
    4. CustomReaction creado en BD

    Expected:
    - CustomReaction creado
    - Besitos otorgados correctamente
    - Stats del mensaje actualizadas
    """
    print("\n[TEST] Usuario Reacciona y Gana Besitos")

    admin_id = 999222
    user_id = 999333
    channel_id = -1001234567891
    message_id = 99912346

    async with get_session() as session:
        container = GamificationContainer(session, mock_bot)

        # Paso 1: Crear admin y usuario
        print("  1. Creando usuarios...")
        admin = User(user_id=admin_id, username="admin", first_name="Admin", role="ADMIN")
        user = User(user_id=user_id, username="testuser", first_name="Test User", role="FREE")
        session.add_all([admin, user])
        await session.commit()
        print("     OK: Usuarios creados")

        # Paso 2: Crear reacción tipo
        print("  2. Creando tipo de reacción...")
        reaction_type = Reaction(
            emoji="👍_test2",
            button_label="Me Gusta",
            besitos_value=10,
            sort_order=1,
            active=True
        )
        session.add(reaction_type)
        await session.commit()
        print("     OK: Tipo de reacción creado")

        # Paso 3: Crear BroadcastMessage
        print("  3. Creando broadcast message...")
        broadcast_msg = BroadcastMessage(
            message_id=message_id,
            chat_id=channel_id,
            content_type="text",
            content_text="Test message",
            sent_by=admin_id,
            gamification_enabled=True,
            reaction_buttons=[
                {"emoji": "👍_test2", "label": "Me Gusta", "reaction_type_id": reaction_type.id, "besitos": 10}
            ]
        )
        session.add(broadcast_msg)
        await session.commit()
        print(f"     OK: Broadcast message creado (ID: {broadcast_msg.id})")

        # Paso 4: Usuario reacciona
        print("  4. Usuario reacciona con 👍...")
        result = await container.custom_reaction.register_custom_reaction(
            broadcast_message_id=broadcast_msg.id,
            user_id=user_id,
            reaction_type_id=reaction_type.id,
            emoji="👍_test2"
        )

        assert result["success"] == True
        assert result["besitos_earned"] == 10
        assert result["already_reacted"] == False
        print(f"     OK: Usuario ganó {result['besitos_earned']} besitos")

        # Paso 5: Verificar CustomReaction en BD
        print("  5. Verificando CustomReaction en BD...")
        stmt = select(CustomReaction).where(
            CustomReaction.broadcast_message_id == broadcast_msg.id,
            CustomReaction.user_id == user_id
        )
        db_result = await session.execute(stmt)
        custom_reaction = db_result.scalar_one()

        assert custom_reaction.emoji == "👍_test2"
        assert custom_reaction.besitos_earned == 10
        print("     OK: CustomReaction creado correctamente")

        # Paso 6: Verificar stats actualizadas
        print("  6. Verificando stats del mensaje...")
        await session.refresh(broadcast_msg)
        assert broadcast_msg.total_reactions == 1
        assert broadcast_msg.unique_reactors == 1
        print("     OK: Stats actualizadas (1 reacción, 1 usuario único)")

    print("  [PASSED] Usuario Reacciona y Gana Besitos\n")


@pytest.mark.asyncio
async def test_prevent_duplicate_reactions(mock_bot):
    """
    Test E2E: Prevención de reacciones duplicadas.

    Escenario:
    1. Usuario reacciona con "❤️"
    2. Usuario intenta reaccionar de nuevo con "❤️"
    3. Segunda reacción es rechazada

    Expected:
    - Primera reacción: success=True
    - Segunda reacción: success=False, already_reacted=True
    - No se otorgan besitos duplicados
    """
    print("\n[TEST] Prevención de Reacciones Duplicadas")

    admin_id = 999444
    user_id = 999555
    channel_id = -1001234567892
    message_id = 99912347

    async with get_session() as session:
        container = GamificationContainer(session, mock_bot)

        # Setup: Crear usuarios, reacción tipo, y broadcast
        admin = User(user_id=admin_id, username="admin", first_name="Admin", role="ADMIN")
        user = User(user_id=user_id, username="testuser", first_name="Test", role="FREE")
        session.add_all([admin, user])

        reaction_type = Reaction(
            emoji="❤️_test3",
            button_label="Me Encanta",
            besitos_value=15,
            sort_order=2,
            active=True
        )
        session.add(reaction_type)

        broadcast_msg = BroadcastMessage(
            message_id=message_id,
            chat_id=channel_id,
            content_type="text",
            content_text="Test",
            sent_by=admin_id,
            gamification_enabled=True,
            reaction_buttons=[
                {"emoji": "❤️_test3", "label": "Me Encanta", "reaction_type_id": reaction_type.id, "besitos": 15}
            ]
        )
        session.add(broadcast_msg)
        await session.commit()

        # Paso 1: Primera reacción
        print("  1. Usuario reacciona con ❤️ (primera vez)...")
        result1 = await container.custom_reaction.register_custom_reaction(
            broadcast_message_id=broadcast_msg.id,
            user_id=user_id,
            reaction_type_id=reaction_type.id,
            emoji="❤️_test3"
        )

        assert result1["success"] == True
        assert result1["besitos_earned"] == 15
        assert result1["already_reacted"] == False
        first_total = result1["total_besitos"]
        print(f"     OK: Primera reacción exitosa (15 besitos ganados)")

        # Paso 2: Segunda reacción (duplicada)
        print("  2. Usuario intenta reaccionar con ❤️ (segunda vez)...")
        result2 = await container.custom_reaction.register_custom_reaction(
            broadcast_message_id=broadcast_msg.id,
            user_id=user_id,
            reaction_type_id=reaction_type.id,
            emoji="❤️_test3"
        )

        assert result2["success"] == False
        assert result2["already_reacted"] == True
        assert result2["besitos_earned"] == 0
        print("     OK: Segunda reacción rechazada")

        # Paso 3: Verificar que no se duplicó en BD
        print("  3. Verificando que no hay duplicados en BD...")
        stmt = select(CustomReaction).where(
            CustomReaction.broadcast_message_id == broadcast_msg.id,
            CustomReaction.user_id == user_id,
            CustomReaction.reaction_type_id == reaction_type.id
        )
        db_result = await session.execute(stmt)
        all_reactions = db_result.all()

        assert len(all_reactions) == 1
        print("     OK: Solo 1 reacción en BD (no duplicados)")

        # Paso 4: Verificar besitos no cambiaron
        print("  4. Verificando besitos del usuario...")
        balance = await container.besito.get_balance(user_id)
        assert balance == first_total  # No cambió después de rechazo
        print(f"     OK: Balance sin cambios ({balance} besitos)")

    print("  [PASSED] Prevención de Reacciones Duplicadas\n")


@pytest.mark.asyncio
async def test_reaction_stats_accurate(mock_bot):
    """
    Test E2E: Estadísticas de reacciones precisas.

    Escenario:
    1. 3 usuarios reaccionan con diferentes emojis
    2. Verificar contadores precisos por emoji
    3. Verificar stats del mensaje (total y únicos)

    Expected:
    - Stats por emoji correctos
    - total_reactions = 3
    - unique_reactors = 3
    """
    print("\n[TEST] Estadísticas de Reacciones Precisas")

    admin_id = 999666
    user1_id = 999777
    user2_id = 999888
    user3_id = 999999
    channel_id = -1001234567893
    message_id = 99912348

    async with get_session() as session:
        container = GamificationContainer(session, mock_bot)

        # Setup: Usuarios
        print("  1. Creando 4 usuarios (1 admin + 3 users)...")
        users = [
            User(user_id=admin_id, username="admin", first_name="Admin", role="ADMIN"),
            User(user_id=user1_id, username="user1", first_name="User 1", role="FREE"),
            User(user_id=user2_id, username="user2", first_name="User 2", role="FREE"),
            User(user_id=user3_id, username="user3", first_name="User 3", role="VIP"),
        ]
        session.add_all(users)

        # Setup: Reacciones tipo
        reactions = [
            Reaction(emoji="👍_test4", button_label="Me Gusta", besitos_value=10, sort_order=1, active=True),
            Reaction(emoji="❤️_test4", button_label="Me Encanta", besitos_value=15, sort_order=2, active=True),
            Reaction(emoji="🔥_test4", button_label="Increíble", besitos_value=20, sort_order=3, active=True),
        ]
        session.add_all(reactions)
        await session.flush()  # Para obtener los IDs

        # Setup: Broadcast
        broadcast_msg = BroadcastMessage(
            message_id=message_id,
            chat_id=channel_id,
            content_type="text",
            content_text="Test stats",
            sent_by=admin_id,
            gamification_enabled=True,
            reaction_buttons=[
                {"emoji": "👍_test4", "label": "Me Gusta", "reaction_type_id": reactions[0].id, "besitos": 10},
                {"emoji": "❤️_test4", "label": "Me Encanta", "reaction_type_id": reactions[1].id, "besitos": 15},
                {"emoji": "🔥_test4", "label": "Increíble", "reaction_type_id": reactions[2].id, "besitos": 20},
            ]
        )
        session.add(broadcast_msg)
        await session.commit()
        print("     OK: Setup completo")

        # Paso 2: User1 reacciona con 👍
        print("  2. User1 reacciona con 👍...")
        await container.custom_reaction.register_custom_reaction(
            broadcast_message_id=broadcast_msg.id,
            user_id=user1_id,
            reaction_type_id=reactions[0].id,
            emoji="👍_test4"
        )

        # Paso 3: User2 reacciona con ❤️
        print("  3. User2 reacciona con ❤️...")
        await container.custom_reaction.register_custom_reaction(
            broadcast_message_id=broadcast_msg.id,
            user_id=user2_id,
            reaction_type_id=reactions[1].id,
            emoji="❤️_test4"
        )

        # Paso 4: User3 reacciona con 🔥
        print("  4. User3 reacciona con 🔥...")
        await container.custom_reaction.register_custom_reaction(
            broadcast_message_id=broadcast_msg.id,
            user_id=user3_id,
            reaction_type_id=reactions[2].id,
            emoji="🔥_test4"
        )
        print("     OK: 3 usuarios reaccionaron")

        # Paso 5: Verificar stats por emoji
        print("  5. Verificando stats por emoji...")
        stats = await container.custom_reaction.get_message_reaction_stats(
            broadcast_msg.id
        )

        assert stats["👍_test4"] == 1
        assert stats["❤️_test4"] == 1
        assert stats["🔥_test4"] == 1
        print(f"     OK: Stats por emoji: {stats}")

        # Paso 6: Verificar stats del mensaje
        print("  6. Verificando stats del mensaje...")
        await session.refresh(broadcast_msg)
        assert broadcast_msg.total_reactions == 3
        assert broadcast_msg.unique_reactors == 3
        print(f"     OK: total_reactions={broadcast_msg.total_reactions}, unique_reactors={broadcast_msg.unique_reactors}")

    print("  [PASSED] Estadísticas de Reacciones Precisas\n")


@pytest.mark.asyncio
async def test_broadcast_without_reactions(mock_bot):
    """
    Test E2E: Backward compatibility - Broadcast sin reacciones.

    Escenario:
    1. Crear BroadcastMessage con gamification_enabled=False
    2. Verificar que no tiene reaction_buttons
    3. Sistema no requiere reacciones para funcionar

    Expected:
    - BroadcastMessage creado exitosamente
    - gamification_enabled=False
    - reaction_buttons vacío
    - Sistema backward compatible
    """
    print("\n[TEST] Backward Compatibility - Broadcast sin Reacciones")

    admin_id = 998111
    channel_id = -1001234567894
    message_id = 99812349

    async with get_session() as session:
        # Paso 1: Crear admin
        print("  1. Creando admin...")
        admin = User(user_id=admin_id, username="admin", first_name="Admin", role="ADMIN")
        session.add(admin)
        await session.commit()

        # Paso 2: Crear broadcast SIN gamificación
        print("  2. Creando broadcast SIN gamificación...")
        broadcast_msg = BroadcastMessage(
            message_id=message_id,
            chat_id=channel_id,
            content_type="text",
            content_text="Mensaje simple sin reacciones",
            sent_by=admin_id,
            gamification_enabled=False,  # ← Sin gamificación
            reaction_buttons=[],  # ← Sin botones
            content_protected=False
        )
        session.add(broadcast_msg)
        await session.commit()
        print(f"     OK: Broadcast creado (ID: {broadcast_msg.id})")

        # Paso 3: Verificar datos
        print("  3. Verificando datos...")
        result = await session.execute(
            select(BroadcastMessage).where(BroadcastMessage.id == broadcast_msg.id)
        )
        saved_msg = result.scalar_one()

        assert saved_msg.gamification_enabled == False
        assert len(saved_msg.reaction_buttons) == 0
        assert saved_msg.total_reactions == 0
        print("     OK: Broadcast sin gamificación funciona correctamente")

        # Paso 4: Verificar que no hay reacciones asociadas
        print("  4. Verificando que no hay reacciones...")
        stmt = select(CustomReaction).where(
            CustomReaction.broadcast_message_id == broadcast_msg.id
        )
        db_result = await session.execute(stmt)
        reactions = db_result.all()

        assert len(reactions) == 0
        print("     OK: No hay reacciones (como se esperaba)")

    print("  [PASSED] Backward Compatibility - Broadcast sin Reacciones\n")
