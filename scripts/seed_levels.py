import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from bot.gamification.database.models import Base, Level
from bot.gamification.services.level import LevelService
import os

# Database URL from environment or default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bot.db")

# Define the levels as per FASE 2 document
LEVEL_DEFINITIONS = {
    1: {"name": "Visitante", "threshold": 0,
        "description": "Recién llegado, bajo observación de Lucien"},
    2: {"name": "Observado", "threshold": 5,
        "description": "Lucien ha notado su presencia"},
    3: {"name": "Evaluado", "threshold": 15,
        "description": "Ha pasado las primeras pruebas"},
    4: {"name": "Reconocido", "threshold": 35,
        "description": "Diana sabe que existe"},
    5: {"name": "Admitido", "threshold": 70,
        "description": "Tiene derecho a estar en el Diván"},
    6: {"name": "Confidente", "threshold": 120,
        "description": "Lucien comparte información privilegiada"},
    7: {"name": "Guardián de Secretos", "threshold": 200,
        "description": "El círculo más íntimo"}
}

async def seed_levels():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    async with async_session() as session:
        level_service = LevelService(session)

        print("Seeding levels...")
        for order, info in LEVEL_DEFINITIONS.items():
            try:
                # Check if level already exists by order or min_besitos
                # Note: calculate_level_for_besitos finds level based on besitos,
                # we need to find by name or order for robust upsert logic.
                # For now, a simpler approach: try to create, if it fails due to unique constraint, update.
                # A more robust check would involve fetching all levels and then comparing.
                
                # Try to get level by name, order, or min_besitos
                existing_levels = await level_service.get_all_levels(active_only=False)
                found_level = next((lvl for lvl in existing_levels if lvl.order == order or lvl.name == info["name"] or lvl.min_besitos == info["threshold"]), None)

                if found_level:
                    print(f"Level {info['name']} (order {order}) already exists. Updating if necessary.")
                    await level_service.update_level(
                        level_id=found_level.id,
                        name=info["name"],
                        min_besitos=info["threshold"],
                        order=order,
                        benefits={"description": info["description"]}
                    )
                else:
                    print(f"Creating level: {info['name']} (order {order})")
                    await level_service.create_level(
                        name=info["name"],
                        min_besitos=info["threshold"],
                        order=order,
                        benefits={"description": info["description"]}
                    )
                print(f"Successfully processed level: {info['name']}")
            except ValueError as e:
                print(f"Error processing level {info['name']}: {e}")
            except Exception as e:
                print(f"An unexpected error occurred for level {info['name']}: {e}")
        
        await session.commit()
        print("Level seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed_levels())
