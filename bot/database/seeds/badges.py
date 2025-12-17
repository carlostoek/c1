"""
Seeds de insignias para el sistema de gamificación.

Inserta insignias predefinidas en la base de datos durante la inicialización.
"""

from bot.database.models import Badge, BadgeRarity


BADGE_SEEDS = [
    {
        "name": "Novato",
        "emoji": "🌱",
        "description": "Primera vez en el sistema",
        "rarity": BadgeRarity.COMMON,
        "is_active": True,
        "is_secret": False,
        "badge_metadata": {"unlock_condition": "user_started"}
    },
    {
        "name": "Centena",
        "emoji": "💯",
        "description": "Alcanzaste 100 besitos",
        "rarity": BadgeRarity.RARE,
        "is_active": True,
        "is_secret": False,
        "badge_metadata": {"unlock_condition": "besitos_100"}
    },
    {
        "name": "Experto",
        "emoji": "🌟",
        "description": "Llegaste a nivel 5",
        "rarity": BadgeRarity.EPIC,
        "is_active": True,
        "is_secret": False,
        "badge_metadata": {"unlock_condition": "level_5"}
    },
    {
        "name": "Leyenda",
        "emoji": "🏆",
        "description": "Alcanzaste nivel máximo",
        "rarity": BadgeRarity.LEGENDARY,
        "is_active": True,
        "is_secret": False,
        "badge_metadata": {"unlock_condition": "level_max"}
    },
    {
        "name": "Constante",
        "emoji": "🔥",
        "description": "7 días de login consecutivos",
        "rarity": BadgeRarity.RARE,
        "is_active": True,
        "is_secret": False,
        "badge_metadata": {"unlock_condition": "streak_7"}
    },
    {
        "name": "Dedicado",
        "emoji": "💪",
        "description": "30 días de login consecutivos",
        "rarity": BadgeRarity.EPIC,
        "is_active": True,
        "is_secret": False,
        "badge_metadata": {"unlock_condition": "streak_30"}
    },
    {
        "name": "Reactor",
        "emoji": "❤️",
        "description": "100 reacciones totales",
        "rarity": BadgeRarity.RARE,
        "is_active": True,
        "is_secret": False,
        "badge_metadata": {"unlock_condition": "reactions_100"}
    },
    {
        "name": "VIP Puro",
        "emoji": "⭐",
        "description": "Suscripción VIP activa",
        "rarity": BadgeRarity.EPIC,
        "is_active": True,
        "is_secret": False,
        "badge_metadata": {"unlock_condition": "vip_active"}
    },
    {
        "name": "Coleccionista",
        "emoji": "💋",
        "description": "1000 Besitos acumulados",
        "rarity": BadgeRarity.LEGENDARY,
        "is_active": True,
        "is_secret": False,
        "badge_metadata": {"unlock_condition": "besitos_1000"}
    },
]


async def seed_badges(session) -> int:
    """
    Inserta insignias predefinidas en la base de datos.

    Args:
        session: AsyncSession para operaciones de BD

    Returns:
        Cantidad de insignias insertadas
    """
    from sqlalchemy import select

    count = 0
    for badge_data in BADGE_SEEDS:
        # Verificar si ya existe la insignia
        stmt = select(Badge).where(Badge.name == badge_data["name"])
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            # Crear nueva insignia
            badge = Badge(**badge_data)
            session.add(badge)
            count += 1

    if count > 0:
        await session.commit()

    return count
