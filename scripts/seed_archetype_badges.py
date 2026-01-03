"""
Seed script para Badges de Arquetipos (FASE 3).

Crea los badges que se otorgan cuando se detecta el arquetipo de un usuario.

Usage:
    python scripts/seed_archetype_badges.py

Author: Sistema de Gamificación
Version: 1.0
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from bot.database.models import Base
from bot.gamification.database.models import Reward, Badge
from bot.gamification.database.enums import RewardType, BadgeRarity
from bot.config import settings


# Archetype badges configuration
ARCHETYPE_BADGES = [
    {
        "name": "El Explorador",
        "description": "Su curiosidad es insaciable. Revisa cada rincón, busca lo que otros ignoran.",
        "reward_type": RewardType.BADGE,
        "icon": "🔍",
        "rarity": BadgeRarity.RARE,
        "archetype": "EXPLORER",
        "unlock_condition": {
            "type": "archetype",
            "archetype": "explorer"
        }
    },
    {
        "name": "El Directo",
        "description": "No pierde tiempo en ceremonias. Sabe lo que quiere y va por ello.",
        "reward_type": RewardType.BADGE,
        "icon": "⚡",
        "rarity": BadgeRarity.RARE,
        "archetype": "DIRECT",
        "unlock_condition": {
            "type": "archetype",
            "archetype": "direct"
        }
    },
    {
        "name": "El Romántico",
        "description": "Busca conexión emocional genuina. Ve a Diana no solo como creadora, sino como persona.",
        "reward_type": RewardType.BADGE,
        "icon": "💝",
        "rarity": BadgeRarity.EPIC,
        "archetype": "ROMANTIC",
        "unlock_condition": {
            "type": "archetype",
            "archetype": "romantic"
        }
    },
    {
        "name": "El Analítico",
        "description": "Su mente funciona con precisión admirable. Analiza, cuestiona, estructura.",
        "reward_type": RewardType.BADGE,
        "icon": "🧠",
        "rarity": BadgeRarity.RARE,
        "archetype": "ANALYTICAL",
        "unlock_condition": {
            "type": "archetype",
            "archetype": "analytical"
        }
    },
    {
        "name": "El Persistente",
        "description": "Vuelve siempre. Donde otros abandonan, usted persiste. Donde otros se rinden, usted reintenta.",
        "reward_type": RewardType.BADGE,
        "icon": "🔄",
        "rarity": BadgeRarity.EPIC,
        "archetype": "PERSISTENT",
        "unlock_condition": {
            "type": "archetype",
            "archetype": "persistent"
        }
    },
    {
        "name": "El Paciente",
        "description": "Se toma su tiempo. Procesa. No se apresura por agradar ni presiona por resultados inmediatos.",
        "reward_type": RewardType.BADGE,
        "icon": "⏳",
        "rarity": BadgeRarity.EPIC,
        "archetype": "PATIENT",
        "unlock_condition": {
            "type": "archetype",
            "archetype": "patient"
        }
    },
]


async def seed_archetype_badges():
    """Create archetype badges in database."""
    # Create engine
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{settings.DATABASE_URL}",
        echo=False
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with AsyncSession(engine) as session:
        print("🎭 Creando Badges de Arquetipos...")

        created_count = 0
        updated_count = 0

        for badge_config in ARCHETYPE_BADGES:
            archetype = badge_config["archetype"]
            icon = badge_config["icon"]
            name = badge_config["name"]

            # Check if badge already exists
            stmt = select(Reward).join(Badge).where(
                Reward.name == name
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                print(f"  ✓ Badge '{name}' ({icon}) ya existe - Actualizando...")
                # Update
                existing.description = badge_config["description"]
                existing.unlock_conditions = str(badge_config["unlock_condition"])

                # Update badge fields
                existing.badges[0].icon = icon
                existing.badges[0].rarity = badge_config["rarity"].value

                updated_count += 1
            else:
                print(f"  + Creando badge '{name}' ({icon})...")

                # Create Reward
                reward = Reward(
                    name=name,
                    description=badge_config["description"],
                    reward_type=badge_config["reward_type"].value,
                    unlock_conditions=str(badge_config["unlock_condition"]),
                    active=True,
                    created_by=1,  # System
                )
                session.add(reward)
                await session.flush()  # To get reward.id

                # Create Badge
                badge = Badge(
                    id=reward.id,
                    icon=icon,
                    rarity=badge_config["rarity"].value,
                )
                session.add(badge)

                created_count += 1

        # Commit changes
        await session.commit()

        print(f"\n✅ Badges de arquetipos creados/actualizados:")
        print(f"   - Creados: {created_count}")
        print(f"   - Actualizados: {updated_count}")
        print(f"   - Total: {len(ARCHETYPE_BADGES)} badges")


if __name__ == "__main__":
    asyncio.run(seed_archetype_badges())
