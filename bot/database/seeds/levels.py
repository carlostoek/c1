"""
Seeds de niveles predefinidos para el sistema de gamificación.

Ejecutar después de crear la tabla levels mediante migraciones de Alembic.
Proporciona los 7 niveles base con sus configuraciones y beneficios.

Ejemplo de uso:
    python -m bot.database.seeds.levels
"""
import logging
from datetime import datetime, timezone

from sqlalchemy import select

logger = logging.getLogger(__name__)

# Definiciones de los 7 niveles
LEVEL_DEFINITIONS = [
    {
        "level": 1,
        "name": "Novato",
        "icon": "🌱",
        "min_points": 0,
        "max_points": 99,
        "multiplier": 1.0,
        "perks": [
            "Bienvenido al sistema de gamificación"
        ]
    },
    {
        "level": 2,
        "name": "Aprendiz",
        "icon": "📚",
        "min_points": 100,
        "max_points": 249,
        "multiplier": 1.1,
        "perks": [
            "Multiplicador de puntos x1.1",
            "Primer paso en tu progreso"
        ]
    },
    {
        "level": 3,
        "name": "Competente",
        "icon": "💪",
        "min_points": 250,
        "max_points": 499,
        "multiplier": 1.2,
        "perks": [
            "Multiplicador de puntos x1.2",
            "Desbloqueo de misiones especiales"
        ]
    },
    {
        "level": 4,
        "name": "Avanzado",
        "icon": "🎯",
        "min_points": 500,
        "max_points": 999,
        "multiplier": 1.3,
        "perks": [
            "Multiplicador de puntos x1.3",
            "Acceso a recompensas premium"
        ]
    },
    {
        "level": 5,
        "name": "Experto",
        "icon": "🌟",
        "min_points": 1000,
        "max_points": 2499,
        "multiplier": 1.5,
        "perks": [
            "Multiplicador de puntos x1.5",
            "Badge exclusivo de experto",
            "Prioridad en soporte"
        ]
    },
    {
        "level": 6,
        "name": "Maestro",
        "icon": "👑",
        "min_points": 2500,
        "max_points": 4999,
        "multiplier": 1.8,
        "perks": [
            "Multiplicador de puntos x1.8",
            "Badge dorado de maestro",
            "Acceso anticipado a nuevas funciones"
        ]
    },
    {
        "level": 7,
        "name": "Leyenda",
        "icon": "🏆",
        "min_points": 5000,
        "max_points": None,  # Sin límite
        "multiplier": 2.0,
        "perks": [
            "Multiplicador de puntos x2.0",
            "Badge legendario exclusivo",
            "Reconocimiento especial en la comunidad",
            "Todas las ventajas del sistema"
        ]
    }
]


async def seed_levels(session):
    """
    Crea los niveles predefinidos en la base de datos.

    Args:
        session: Sesión de base de datos async

    Raises:
        Exception: Si ocurre un error durante la creación de niveles
    """
    from bot.database.models import Level

    logger.info("🌱 Seeding niveles...")

    for level_data in LEVEL_DEFINITIONS:
        # Verificar si ya existe
        result = await session.execute(
            select(Level).where(Level.level == level_data["level"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            logger.info(f"  ⏭️  Nivel {level_data['level']} ya existe, saltando...")
            continue

        # Crear nivel
        level = Level(**level_data)
        session.add(level)
        max_pts = level.max_points or "∞"
        logger.info(
            f"  ✅ Creado: {level.display_name} "
            f"({level.min_points}-{max_pts} pts, {level.multiplier}x)"
        )

    await session.commit()
    logger.info("🎉 Niveles creados exitosamente!")


# Script ejecutable
if __name__ == "__main__":
    import asyncio
    import sys

    async def run_seed():
        """Ejecuta el seed de niveles."""
        try:
            from bot.database import get_session, init_db

            await init_db()
            async with get_session() as session:
                await seed_levels(session)
        except Exception as e:
            logger.error(f"❌ Error durante seed: {e}", exc_info=True)
            sys.exit(1)

    asyncio.run(run_seed())
