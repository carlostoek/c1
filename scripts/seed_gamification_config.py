#!/usr/bin/env python3
"""
Seed de configuración de gamificación.

Migra datos hardcoded de GamificationConfig a las tablas de BD.
Ejecutar una sola vez después de crear las tablas.

Idempotente: Puede correrse múltiples veces sin duplicar datos.

Usage:
    python scripts/seed_gamification_config.py
"""
import asyncio
import sys
import logging
from datetime import datetime
from pathlib import Path

# Agregar root al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from bot.database.engine import get_session_factory, init_db, close_db
from bot.database.models import (
    ActionConfig,
    LevelConfig,
    BadgeConfig,
    RewardConfig,
    MissionConfig,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# DATOS A MIGRAR (tomados de GamificationConfig actual)
# ═══════════════════════════════════════════════════════════════

ACTION_CONFIGS = [
    # (action_key, display_name, description, points_amount)
    ("user_started", "Bienvenida", "Bienvenida al bot", 10),
    ("joined_free_channel", "Canal Free", "Ingreso al canal Free", 25),
    ("joined_vip", "Activación VIP", "Activación VIP", 100),
    ("message_reacted", "Reacción", "Reacción a mensaje", 5),
    ("first_reaction_of_day", "Primera Reacción", "Primera reacción del día (bonus)", 10),
    ("daily_login_base", "Login Diario", "Regalo diario base", 20),
    ("daily_login_streak_bonus", "Bonus Racha", "Bonus por racha (5 por día consecutivo)", 5),
    ("referral_success", "Referido", "Referido exitoso", 50),
    ("minigame_win", "Victoria Minijuego", "Victoria en minijuego", 15),
]

LEVEL_CONFIGS = [
    # (name, min_points, max_points, multiplier, icon, color, order)
    ("Novato", 0, 499, 1.0, "🌱", "#95a5a6", 1),
    ("Bronce", 500, 1999, 1.1, "🥉", "#cd7f32", 2),
    ("Plata", 2000, 4999, 1.2, "🥈", "#c0c0c0", 3),
    ("Oro", 5000, 9999, 1.3, "🥇", "#ffd700", 4),
    ("Platino", 10000, 19999, 1.5, "💎", "#e5e4e2", 5),
    ("Diamante", 20000, 49999, 1.7, "💠", "#b9f2ff", 6),
    ("Leyenda", 50000, None, 2.0, "👑", "#ff69b4", 7),
]

BADGE_CONFIGS = [
    # (badge_key, name, icon, requirement_type, requirement_value, description)
    ("streak_7", "Constante", "🔥", "daily_streak", 7, "7 días consecutivos de login"),
    ("streak_30", "Dedicado", "💪", "daily_streak", 30, "30 días consecutivos de login"),
    ("reactions_100", "Reactor", "❤️", "total_reactions", 100, "100 reacciones totales"),
    ("vip_member", "VIP", "⭐", "vip_active", 1, "Suscripción VIP activa"),
    ("besitos_1000", "Coleccionista", "💋", "total_besitos", 1000, "1000 Besitos acumulados"),
]


async def seed_action_configs(session) -> int:
    """Seed action_configs table."""
    count = 0
    for action_key, display_name, description, points_amount in ACTION_CONFIGS:
        # Verificar si ya existe
        existing = await session.execute(
            select(ActionConfig).where(ActionConfig.action_key == action_key)
        )
        if existing.scalar_one_or_none():
            print(f"  ⏭️  ActionConfig '{action_key}' ya existe, saltando...")
            continue

        config = ActionConfig(
            action_key=action_key,
            display_name=display_name,
            description=description,
            points_amount=points_amount,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(config)
        count += 1
        print(f"  ✅ ActionConfig '{action_key}' creado ({points_amount} pts)")

    return count


async def seed_level_configs(session) -> int:
    """Seed level_configs table."""
    count = 0
    for name, min_points, max_points, multiplier, icon, color, order in LEVEL_CONFIGS:
        # Verificar si ya existe
        existing = await session.execute(
            select(LevelConfig).where(LevelConfig.name == name)
        )
        if existing.scalar_one_or_none():
            print(f"  ⏭️  LevelConfig '{name}' ya existe, saltando...")
            continue

        max_display = str(max_points) if max_points else "∞"
        config = LevelConfig(
            name=name,
            min_points=min_points,
            max_points=max_points,
            multiplier=multiplier,
            icon=icon,
            color=color,
            order=order,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(config)
        count += 1
        print(
            f"  ✅ LevelConfig '{name}' creado ({min_points}-{max_display} pts, "
            f"x{multiplier}, {icon})"
        )

    return count


async def seed_badge_configs(session) -> int:
    """Seed badge_configs table."""
    count = 0
    for badge_key, name, icon, req_type, req_value, description in BADGE_CONFIGS:
        # Verificar si ya existe
        existing = await session.execute(
            select(BadgeConfig).where(BadgeConfig.badge_key == badge_key)
        )
        if existing.scalar_one_or_none():
            print(f"  ⏭️  BadgeConfig '{badge_key}' ya existe, saltando...")
            continue

        config = BadgeConfig(
            badge_key=badge_key,
            name=name,
            icon=icon,
            description=description,
            requirement_type=req_type,
            requirement_value=req_value,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(config)
        count += 1
        print(
            f"  ✅ BadgeConfig '{badge_key}' creado ({icon} {req_type}={req_value})"
        )

    return count


async def main():
    """Ejecuta el seed completo."""
    print("═" * 70)
    print("🌱 SEED DE CONFIGURACIÓN DE GAMIFICACIÓN")
    print("═" * 70)

    # Inicializar BD
    try:
        await init_db()
        session_factory = get_session_factory()

        async with session_factory() as session:
            try:
                print("\n📋 Seeding ActionConfigs (9 acciones)...")
                actions_count = await seed_action_configs(session)

                print("\n📈 Seeding LevelConfigs (7 niveles)...")
                levels_count = await seed_level_configs(session)

                print("\n🏆 Seeding BadgeConfigs (5 badges)...")
                badges_count = await seed_badge_configs(session)

                # Commit
                await session.commit()

                print("\n" + "═" * 70)
                print("✅ SEED COMPLETADO EXITOSAMENTE")
                print("═" * 70)
                print(f"  ActionConfigs creados: {actions_count}")
                print(f"  LevelConfigs creados:  {levels_count}")
                print(f"  BadgeConfigs creados:  {badges_count}")
                print(f"  Total: {actions_count + levels_count + badges_count}")
                print("═" * 70)

            except Exception as e:
                await session.rollback()
                print(f"\n❌ ERROR durante seed: {e}")
                raise

    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
