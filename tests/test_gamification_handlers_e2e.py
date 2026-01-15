"""
Tests E2E para handlers de gamificación (SPRINT 2).

Prueba flujos completos:
- Callback de reacción en publicación
- Menú de perfil de usuario
- Configuración de gamificación (admin)
- Publicación con reacciones (admin)
"""
import pytest
from unittest.mock import AsyncMock, Mock
from aiogram.types import (
    CallbackQuery, Message, User, Chat,
    InlineKeyboardMarkup
)

from bot.database import get_session
from bot.services.container import ServiceContainer
from bot.database.models import User
from bot.database.enums import UserRole, ChannelType


@pytest.mark.asyncio
async def test_e2e_reaction_callback(mock_bot):
    """Test E2E: Flujo completo de reacción del usuario."""
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # 1. Crear usuario
        user = User(user_id=700, first_name="TestUser", role="free")
        session.add(user)
        await session.commit()

        # 2. Crear publicación
        publication = await container.reactions.create_publication(
            channel_id="-100123456789",
            message_id=5000,
            channel_type=ChannelType.VIP,
            emojis=["👍", "❤️", "🔥"]
        )

        # 3. Crear callback mock
        callback_query = Mock(spec=CallbackQuery)
        callback_query.from_user = Mock(spec=User)
        callback_query.from_user.id = 700
        callback_query.data = f"react:{publication.id}:0"  # Emoji 👍
        callback_query.message = Mock()
        callback_query.message.edit_reply_markup = AsyncMock()
        callback_query.answer = AsyncMock()

        # 4. Simular handler (sin ejecutar router, solo lógica)
        success, msg, reaction = await container.reactions.add_reaction(
            user_id=700,
            publication_id=publication.id,
            emoji="👍",
            points_awarded=1
        )

        assert success is True
        assert reaction is not None
        assert reaction.emoji == "👍"
        assert reaction.points_awarded == 1

        # 5. Verificar que se puede reaccionar solo una vez
        success2, msg2, reaction2 = await container.reactions.add_reaction(
            user_id=700,
            publication_id=publication.id,
            emoji="❤️",
            points_awarded=1
        )

        assert success2 is False
        assert "ya has reaccionado" in msg2.lower()
        assert reaction2 == reaction  # Mismo objeto


@pytest.mark.asyncio
async def test_e2e_profile_menu(mock_bot):
    """Test E2E: Menú de perfil muestra datos correctos."""
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # 1. Crear usuario con puntos
        user = User(user_id=701, first_name="ProfileUser", role="free")
        session.add(user)
        await session.commit()

        # Otorgar puntos
        await container.points.award_points(
            user_id=701,
            amount=100,
            transaction_type="admin_grant",
            description="Puntos iniciales"
        )

        # 2. Verificar balance
        points = await container.points.get_balance(701)
        assert points is not None
        assert points.balance == 100


@pytest.mark.asyncio
async def test_e2e_daily_gift_cooldown(mock_bot):
    """Test E2E: Regalo diario tiene cooldown de 24h."""
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Crear usuario
        user = User(user_id=702, first_name="GiftUser", role="free")
        session.add(user)
        await session.commit()

        # Primer reclamo - debe funcionar
        success1, points1, msg1 = await container.points.claim_daily_gift(702)
        assert success1 is True
        assert points1 > 0

        # Segundo reclamo inmediato - debe fallar
        success2, points2, msg2 = await container.points.claim_daily_gift(702)
        assert success2 is False
        assert points2 == 0
        assert "esperar" in msg2.lower()


@pytest.mark.asyncio
async def test_e2e_streak_calculation(mock_bot):
    """Test E2E: Cálculo de racha funciona correctamente."""
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Crear usuario
        user = User(user_id=703, first_name="StreakUser", role="free")
        session.add(user)
        await session.commit()

        # Crear 5 publicaciones
        channel_id = "-100123456789"
        publication_ids = []

        for i in range(5):
            pub = await container.reactions.create_publication(
                channel_id=channel_id,
                message_id=6000 + i,
                channel_type=ChannelType.VIP,
                emojis=["👍"]
            )
            publication_ids.append(pub.id)

        # Usuario reacciona a las últimas 3 publicaciones (índices 2, 3, 4)
        for i in [2, 3, 4]:
            await container.reactions.add_reaction(
                user_id=703,
                publication_id=publication_ids[i],
                emoji="👍",
                points_awarded=1
            )

        # Calcular racha
        streak = await container.streak.calculate_streak(703, channel_id)

        # Debe ser 3 (las últimas 3 consecutivas)
        assert streak == 3


@pytest.mark.asyncio
async def test_e2e_gamification_config(mock_bot):
    """Test E2E: Configuración de gamificación se actualiza."""
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Obtener config actual
        config = await container.points._get_config()
        original_points = config.points_per_reaction

        # Modificar puntos por reacción
        config.points_per_reaction = 5
        await session.commit()

        # Verificar que se guardó
        config2 = await container.points._get_config()
        assert config2.points_per_reaction == 5
        assert config2.points_per_reaction != original_points


@pytest.mark.asyncio
async def test_e2e_default_emojis_config(mock_bot):
    """Test E2E: Emojis predeterminados se configuran correctamente."""
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Configurar emojis predeterminados
        new_emojis = ["⭐", "💯", "🎉"]

        await container.reactions.set_default_emojis(new_emojis)

        # Verificar que se guardaron
        saved_emojis = await container.reactions.get_default_emojis()
        assert saved_emojis == new_emojis


@pytest.mark.asyncio
async def test_e2e_publication_creation(mock_bot):
    """Test E2E: Publicación se crea con keyboard correcto."""
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Crear publicación
        publication = await container.reactions.create_publication(
            channel_id="-100123456789",
            message_id=7000,
            channel_type=ChannelType.FREE,
            emojis=["👍", "❤️", "🔥", "🎉"]
        )

        # Verificar publicación
        assert publication is not None
        assert publication.channel_id == "-100123456789"
        assert publication.message_id == 7000
        assert publication.channel_type == ChannelType.FREE
        assert publication.reaction_buttons == ["👍", "❤️", "🔥", "🎉"]
        assert publication.active is True

        # Generar keyboard
        keyboard = container.reactions.generate_reaction_keyboard(
            publication_id=publication.id,
            emojis=publication.reaction_buttons,
            counts={}
        )

        assert keyboard is not None
        assert len(keyboard.inline_keyboard) == 1  # 1 fila
        assert len(keyboard.inline_keyboard[0]) == 4  # 4 botones

        # Verificar formato de callback_data
        button_0 = keyboard.inline_keyboard[0][0]
        assert button_0.callback_data == f"react:{publication.id}:0"


@pytest.mark.asyncio
async def test_e2e_reaction_counts(mock_bot):
    """Test E2E: Conteos de reacciones se calculan correctamente."""
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Crear publicación
        publication = await container.reactions.create_publication(
            channel_id="-100123456789",
            message_id=7001,
            channel_type=ChannelType.VIP,
            emojis=["👍", "❤️"]
        )

        # Crear usuarios y añadir reacciones
        users = [704, 705, 706, 707]

        for i, user_id in enumerate(users):
            user = User(user_id=user_id, first_name=f"User{i}", role="free")
            session.add(user)
            await session.commit()

            # 3 usuarios reaccionan con 👍, 1 con ❤️
            emoji = "👍" if i < 3 else "❤️"
            await container.reactions.add_reaction(
                user_id=user_id,
                publication_id=publication.id,
                emoji=emoji,
                points_awarded=1
            )

        # Obtener conteos
        counts = await container.reactions.get_reaction_counts(publication.id)

        assert counts["👍"] == 3
        assert counts["❤️"] == 1
        assert await container.reactions.get_total_reactions(publication.id) == 4


@pytest.mark.asyncio
async def test_e2e_leaderboard_integration(mock_bot):
    """Test E2E: Leaderboard funciona con múltiples usuarios."""
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Crear usuarios con diferentes puntos
        test_data = [
            (750, 200),
            (751, 150),
            (752, 300),
            (753, 100),
            (754, 250)
        ]

        for user_id, points in test_data:
            user = User(user_id=user_id, first_name=f"Leader{user_id}", role="free")
            session.add(user)
            await session.commit()

            await container.points.award_points(
                user_id=user_id,
                amount=points,
                transaction_type="admin_grant",
                description="Puntos test"
            )

        # Obtener leaderboard
        leaderboard = await container.points.get_leaderboard(limit=5)

        # Debe haber 5 usuarios
        assert len(leaderboard) == 5

        # Primer lugar debe tener 300 puntos
        assert leaderboard[0][1].balance == 300

        # Último lugar debe tener 100 puntos
        assert leaderboard[-1][1].balance == 100


@pytest.mark.asyncio
async def test_e2e_user_points_tracking(mock_bot):
    """Test E2E: Seguimiento de puntos del usuario es correcto."""
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Crear usuario
        user = User(user_id=760, first_name="TrackerUser", role="free")
        session.add(user)
        await session.commit()

        # Otorgar puntos múltiples veces
        await container.points.award_points(
            user_id=760,
            amount=50,
            transaction_type="admin_grant",
            description="Primera ganancia"
        )

        await container.points.award_points(
            user_id=760,
            amount=30,
            transaction_type="admin_grant",
            description="Segunda ganancia"
        )

        # Gastar puntos
        success, msg = await container.points.spend_points(
            user_id=760,
            amount=20,
            transaction_type="shop_purchase",
            description="Compra de prueba"
        )

        assert success is True

        # Verificar balance final
        points = await container.points.get_balance(760)
        assert points.balance == 60  # 50 + 30 - 20
        assert points.total_earned == 80  # 50 + 30
        assert points.total_spent == 20


@pytest.mark.asyncio
async def test_e2e_services_integration(mock_bot):
    """Test E2E: Integración entre servicios de gamificación."""
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # 1. Crear usuario
        user = User(user_id=770, first_name="IntegrationUser", role="free")
        session.add(user)
        await session.commit()

        # 2. Configurar emojis predeterminados
        test_emojis = ["👏", "🎉"]
        await container.reactions.set_default_emojis(test_emojis)

        # 3. Publicar con esos emojis
        publication = await container.reactions.create_publication(
            channel_id="-100123456789",
            message_id=8000,
            channel_type=ChannelType.VIP,
            emojis=test_emojis  # Debe usar los predeterminados
        )

        assert publication.reaction_buttons == test_emojis

        # 4. Usuario reacciona
        success, msg, reaction = await container.reactions.add_reaction(
            user_id=770,
            publication_id=publication.id,
            emoji="👏",
            points_awarded=1
        )

        assert success is True

        # 5. Verificar racha calculada
        streak = await container.streak.calculate_streak(
            user_id=770,
            channel_id="-100123456789"
        )

        assert streak == 1  # Primera reacción

        # 6. Verificar que usuario tiene puntos
        points = await container.points.get_balance(770)
        assert points.balance == 1
        assert points.current_streak == 1
