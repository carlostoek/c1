"""
Tests para servicios de gamificación.

Prueba:
- PointsService: otorgar, gastar, regalo diario
- ReactionService: crear publicaciones, añadir reacciones
- StreakService: calcular rachas
"""
import pytest
from datetime import datetime, timedelta

from bot.database import get_session
from bot.services.container import ServiceContainer
from bot.database.gamification_models import (
    UserPoints, Publication, UserReaction,
    GamificationConfig, UserLevel
)
from bot.database.models import User
from bot.database.enums import TransactionType, ChannelType


@pytest.mark.asyncio
async def test_points_service_award_points(mock_bot):
    """Test: Otorgar puntos a un usuario."""
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Crear usuario
        user = User(
            user_id=999,
            first_name="Test",
            role="free"
        )
        session.add(user)
        await session.commit()

        # Otorgar puntos
        transaction = await container.points.award_points(
            user_id=999,
            amount=10,
            transaction_type=TransactionType.REACTION,
            description="Test reacción"
        )

        assert transaction is not None
        assert transaction.user_id == 999
        assert transaction.amount == 10
        assert transaction.transaction_type == TransactionType.REACTION

        # Verificar balance
        points = await container.points.get_balance(999)
        assert points is not None
        assert points.balance == 10
        assert points.total_earned == 10


@pytest.mark.asyncio
async def test_points_service_spend_points(mock_bot):
    """Test: Gastar puntos de un usuario."""
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Crear usuario y puntos
        user = User(user_id=998, first_name="Test", role="free")
        session.add(user)
        await session.commit()

        # Otorgar puntos iniciales
        await container.points.award_points(
            user_id=998,
            amount=50,
            transaction_type=TransactionType.ADMIN_GRANT,
            description="Puntos iniciales"
        )

        # Gastar puntos
        success, msg = await container.points.spend_points(
            user_id=998,
            amount=20,
            transaction_type=TransactionType.SHOP_PURCHASE,
            description="Compra de test"
        )

        assert success is True
        assert "20 puntos" in msg

        # Verificar balance
        points = await container.points.get_balance(998)
        assert points.balance == 30  # 50 - 20
        assert points.total_spent == 20


@pytest.mark.asyncio
async def test_points_service_insufficient_points(mock_bot):
    """Test: Intentar gastar más puntos de los disponibles."""
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Crear usuario con pocos puntos
        user = User(user_id=997, first_name="Test", role="free")
        session.add(user)
        await session.commit()

        await container.points.award_points(
            user_id=997,
            amount=5,
            transaction_type=TransactionType.ADMIN_GRANT,
            description="Puntos iniciales"
        )

        # Intentar gastar más de lo disponible
        success, msg = await container.points.spend_points(
            user_id=997,
            amount=10,
            transaction_type=TransactionType.SHOP_PURCHASE,
            description="Compra excesiva"
        )

        assert success is False
        assert "insuficientes" in msg.lower()

        # Balance no debe cambiar
        points = await container.points.get_balance(997)
        assert points.balance == 5


@pytest.mark.asyncio
async def test_points_service_daily_gift(mock_bot):
    """Test: Reclamar regalo diario."""
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Crear usuario
        user = User(user_id=996, first_name="Test", role="free")
        session.add(user)
        await session.commit()

        # Primer reclamo
        success1, points1, msg1 = await container.points.claim_daily_gift(996)
        assert success1 is True
        assert points1 > 0

        # Segundo reclamo inmediato (debe fallar)
        success2, points2, msg2 = await container.points.claim_daily_gift(996)
        assert success2 is False
        assert points2 == 0
        assert "esperar" in msg2.lower()


@pytest.mark.asyncio
async def test_points_service_leaderboard(mock_bot):
    """Test: Obtener leaderboard de usuarios."""
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Crear múltiples usuarios con IDs únicos para este test
        test_user_ids = [800, 801, 802, 803]
        for i, (user_id, points) in enumerate(zip(test_user_ids, [100, 50, 150, 75])):
            user = User(user_id=user_id, first_name=f"Leaderboard{i}", role="free")
            session.add(user)
            await session.commit()

            await container.points.award_points(
                user_id=user_id,
                amount=points,
                transaction_type=TransactionType.ADMIN_GRANT,
                description=f"Puntos iniciales {i}"
            )

        # Obtener leaderboard
        leaderboard = await container.points.get_leaderboard(limit=10)

        # Debe haber al menos 4 usuarios (nuestros usuarios de test)
        assert len(leaderboard) >= 4

        # Buscar al usuario con 150 puntos en el leaderboard
        user_150 = None
        for pos, points_obj in leaderboard:
            if points_obj.balance == 150:
                user_150 = (pos, points_obj)
                break

        assert user_150 is not None
        # Debe estar en los primeros puestos
        assert user_150[0] >= 1 and user_150[0] <= 3


@pytest.mark.asyncio
async def test_reaction_service_create_publication(mock_bot):
    """Test: Crear publicación con botones de reacción."""
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Crear publicación
        publication = await container.reactions.create_publication(
            channel_id="-100123456789",
            message_id=9999,
            channel_type=ChannelType.VIP,
            emojis=["👍", "❤️", "🔥"]
        )

        assert publication is not None
        assert publication.channel_id == "-100123456789"
        assert publication.message_id == 9999
        assert publication.channel_type == ChannelType.VIP
        assert publication.reaction_buttons == ["👍", "❤️", "🔥"]
        assert publication.active is True


@pytest.mark.asyncio
async def test_reaction_service_add_reaction(mock_bot):
    """Test: Añadir reacción de usuario a publicación."""
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Crear usuario y publicación
        user = User(user_id=995, first_name="Test", role="free")
        session.add(user)
        await session.commit()

        publication = await container.reactions.create_publication(
            channel_id="-100123456789",
            message_id=9998,
            channel_type=ChannelType.FREE,
            emojis=["👍", "❤️"]
        )

        # Añadir reacción
        success, msg, reaction = await container.reactions.add_reaction(
            user_id=995,
            publication_id=publication.id,
            emoji="👍",
            points_awarded=1
        )

        assert success is True
        assert reaction is not None
        assert reaction.user_id == 995
        assert reaction.emoji == "👍"
        assert reaction.points_awarded == 1


@pytest.mark.asyncio
async def test_reaction_service_duplicate_reaction(mock_bot):
    """Test: Evitar reacción duplicada del mismo usuario."""
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Crear usuario y publicación
        user = User(user_id=994, first_name="Test", role="free")
        session.add(user)
        await session.commit()

        publication = await container.reactions.create_publication(
            channel_id="-100123456789",
            message_id=9997,
            channel_type=ChannelType.FREE,
            emojis=["👍"]
        )

        # Primera reacción
        success1, _, reaction1 = await container.reactions.add_reaction(
            user_id=994,
            publication_id=publication.id,
            emoji="👍",
            points_awarded=1
        )
        assert success1 is True

        # Segunda reacción (debe fallar)
        success2, msg2, reaction2 = await container.reactions.add_reaction(
            user_id=994,
            publication_id=publication.id,
            emoji="👍",
            points_awarded=1
        )
        assert success2 is False
        assert "ya has reaccionado" in msg2.lower()
        assert reaction2 == reaction1  # Mismo objeto


@pytest.mark.asyncio
async def test_reaction_service_get_reaction_counts(mock_bot):
    """Test: Obtener conteos de reacciones por emoji."""
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Crear usuarios y publicación
        publication = await container.reactions.create_publication(
            channel_id="-100123456789",
            message_id=9996,
            channel_type=ChannelType.FREE,
            emojis=["👍", "❤️", "🔥"]
        )

        for i in range(3):
            user = User(user_id=990+i, first_name=f"Test{i}", role="free")
            session.add(user)
            await session.commit()

            await container.reactions.add_reaction(
                user_id=990+i,
                publication_id=publication.id,
                emoji=["👍", "❤️", "🔥"][i % 3],
                points_awarded=1
            )

        # Obtener conteos
        counts = await container.reactions.get_reaction_counts(publication.id)

        # Debe haber 1 reacción de cada emoji
        assert counts["👍"] == 1
        assert counts["❤️"] == 1
        assert counts["🔥"] == 1


@pytest.mark.asyncio
async def test_reaction_service_generate_keyboard(mock_bot):
    """Test: Generar keyboard inline con conteos."""
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        publication = await container.reactions.create_publication(
            channel_id="-100123456789",
            message_id=9995,
            channel_type=ChannelType.FREE,
            emojis=["👍", "❤️", "🔥"]
        )

        # Simular algunas reacciones
        counts = {"👍": 5, "❤️": 3, "🔥": 0}

        keyboard = container.reactions.generate_reaction_keyboard(
            publication_id=publication.id,
            emojis=publication.reaction_buttons,
            counts=counts
        )

        assert keyboard is not None
        assert len(keyboard.inline_keyboard) == 1  # 1 fila

        # Verificar botones
        buttons = keyboard.inline_keyboard[0]
        assert len(buttons) == 3

        # Callback data formato correcto
        assert buttons[0].callback_data == f"react:{publication.id}:0"
        assert buttons[1].callback_data == f"react:{publication.id}:1"
        assert buttons[2].callback_data == f"react:{publication.id}:2"


@pytest.mark.asyncio
async def test_streak_service_calculate_streak(mock_bot):
    """Test: Calcular racha de usuario en canal."""
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Crear 5 publicaciones
        publication_ids = []
        for i in range(5):
            pub = await container.reactions.create_publication(
                channel_id="-100123456789",
                message_id=9950+i,
                channel_type=ChannelType.VIP,
                emojis=["👍"]
            )
            publication_ids.append(pub.id)

        # Crear usuario
        user = User(user_id=985, first_name="Test", role="free")
        session.add(user)
        await session.commit()

        # Usuario reacciona a las últimas 3 publicaciones (P3, P4, P5)
        for i in [2, 3, 4]:  # Índices 2, 3, 4
            await container.reactions.add_reaction(
                user_id=985,
                publication_id=publication_ids[i],
                emoji="👍",
                points_awarded=1
            )

        # Calcular racha
        streak = await container.streak.calculate_streak(
            user_id=985,
            channel_id="-100123456789"
        )

        # Racha debe ser 3 (las últimas 3 consecutivas)
        assert streak == 3


@pytest.mark.asyncio
async def test_streak_service_broken_streak(mock_bot):
    """Test: Racha se rompe si falta una reacción."""
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Crear 5 publicaciones
        publication_ids = []
        for i in range(5):
            pub = await container.reactions.create_publication(
                channel_id="-100123456789",
                message_id=9940+i,
                channel_type=ChannelType.VIP,
                emojis=["👍"]
            )
            publication_ids.append(pub.id)

        # Crear usuario
        user = User(user_id=984, first_name="Test", role="free")
        session.add(user)
        await session.commit()

        # Usuario reacciona solo a P5 y P3 (no consecutivos desde el más reciente)
        # P5 sí, P4 no → racha rompe
        await container.reactions.add_reaction(
            user_id=984,
            publication_id=publication_ids[4],  # P5
            emoji="👍",
            points_awarded=1
        )
        await container.reactions.add_reaction(
            user_id=984,
            publication_id=publication_ids[2],  # P3
            emoji="👍",
            points_awarded=1
        )

        # Calcular racha
        streak = await container.streak.calculate_streak(
            user_id=984,
            channel_id="-100123456789"
        )

        # Racha debe ser 1 (solo P5, P4 rompe)
        assert streak == 1


@pytest.mark.asyncio
async def test_streak_service_update_streak(mock_bot):
    """Test: Actualizar racha después de reacción."""
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Crear publicaciones
        pub = await container.reactions.create_publication(
            channel_id="-100123456789",
            message_id=9930,
            channel_type=ChannelType.VIP,
            emojis=["👍"]
        )

        # Crear usuario
        user = User(user_id=983, first_name="Test", role="free")
        session.add(user)
        await session.commit()

        # Reaccionar
        await container.reactions.add_reaction(
            user_id=983,
            publication_id=pub.id,
            emoji="👍",
            points_awarded=1
        )

        # Actualizar racha
        new_streak, is_record = await container.streak.update_streak_after_reaction(
            user_id=983,
            channel_id="-100123456789"
        )

        assert new_streak == 1
        assert is_record is True  # Primer récord


@pytest.mark.asyncio
async def test_streak_service_multiplier(mock_bot):
    """Test: Obtener multiplicador según racha."""
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Probar diferentes niveles de racha
        multiplier_0 = await container.streak.get_streak_multiplier(0)
        assert multiplier_0 == 1.0

        multiplier_5 = await container.streak.get_streak_multiplier(5)
        assert multiplier_5 == 1.5

        multiplier_10 = await container.streak.get_streak_multiplier(10)
        assert multiplier_10 == 2.0

        multiplier_20 = await container.streak.get_streak_multiplier(20)
        assert multiplier_20 == 2.5

        multiplier_30 = await container.streak.get_streak_multiplier(30)
        assert multiplier_30 == 3.0


@pytest.mark.asyncio
async def test_gamification_config_singleton(mock_bot):
    """Test: GamificationConfig es singleton."""
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        # Obtener config (debe crear por defecto)
        config1 = await container.points._get_config()
        assert config1 is not None
        assert config1.id == 1
        assert config1.points_per_reaction == 1
        assert config1.daily_gift_points == 5
        assert config1.streak_multiplier == 1.5

        # Obtener nuevamente (mismo objeto)
        config2 = await container.points._get_config()
        assert config2.id == config1.id
