#!/usr/bin/env python3
"""Script de seed para los 7 Niveles del Protocolo de Acceso.

Crea los niveles narrativos definidos en EconomyConfig.LEVELS.

Uso:
    python scripts/seed_levels.py [--force]

Opciones:
    --force: Elimina niveles existentes antes de crear nuevos (peligroso)
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Agregar directorio raíz al path para imports
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from bot.database.engine import get_session, init_db
from bot.gamification.database.models import Level
from bot.gamification.config.economy import EconomyConfig


async def seed_levels(force: bool = False):
    """Crea los 7 niveles del Protocolo de Acceso en la base de datos.

    Args:
        force: Si True, elimina niveles existentes antes de crear nuevos
    """
    print("🌱 Iniciando seed de niveles del Protocolo de Acceso...")

    # Inicializar base de datos
    await init_db()

    async with get_session() as session:
        # Opción force: eliminar niveles existentes
        if force:
            print("⚠️  Modo FORCE activado - eliminando niveles existentes...")
            result = await session.execute(select(Level))
            existing_levels = result.scalars().all()

            for level in existing_levels:
                await session.delete(level)

            await session.commit()
            print(f"   ✅ Eliminados {len(existing_levels)} niveles existentes")

        # Obtener niveles existentes
        result = await session.execute(select(Level).order_by(Level.order))
        existing_levels = result.scalars().all()
        existing_dict = {lvl.order: lvl for lvl in existing_levels}

        print(f"   📊 Niveles existentes: {len(existing_levels)}")

        # Crear o actualizar niveles desde EconomyConfig
        created_count = 0
        updated_count = 0

        for level_num, level_info in EconomyConfig.LEVELS.items():
            level_order = level_num  # El order coincide con el número de nivel

            if level_order in existing_dict:
                # Actualizar nivel existente
                level = existing_dict[level_order]
                level.name = level_info["name"]
                level.min_besitos = level_info["threshold"]
                level.order = level_order
                level.benefits = str({"description": level_info["description"]})
                level.active = True

                print(f"   🔄 Actualizado: Nivel {level_num} - {level_info['name']} ({level_info['threshold']} besitos)")
                updated_count += 1
            else:
                # Crear nuevo nivel
                level = Level(
                    name=level_info["name"],
                    min_besitos=level_info["threshold"],
                    order=level_order,
                    benefits=str({"description": level_info["description"]}),
                    active=True
                )
                session.add(level)

                print(f"   ✨ Creado: Nivel {level_num} - {level_info['name']} ({level_info['threshold']} besitos)")
                created_count += 1

        try:
            await session.commit()
            print(f"\n🎉 Seed completado:")
            print(f"   ✅ Creados: {created_count} niveles")
            print(f"   🔄 Actualizados: {updated_count} niveles")
            print(f"\n📋 Niveles del Protocolo de Acceso:")
            for level_num, level_info in EconomyConfig.LEVELS.items():
                print(f"   {level_num}. {level_info['name']} ({level_info['threshold']}+ besitos)")

        except IntegrityError as e:
            print(f"\n❌ Error de integridad: {e}")
            print("   💡 Sugerencia: Usa --force para eliminar niveles existentes primero")
            await session.rollback()
            sys.exit(1)


async def show_levels():
    """Muestra los niveles actualmente en la base de datos."""
    print("📋 Niveles en la base de datos:")

    await init_db()

    async with get_session() as session:
        result = await session.execute(select(Level).order_by(Level.order))
        levels = result.scalars().all()

        if not levels:
            print("   ⚠️  No hay niveles en la base de datos")
            print("   💡 Ejecuta: python scripts/seed_levels.py")
            return

        for level in levels:
            benefits = eval(level.benefits) if level.benefits else {}
            description = benefits.get("description", "Sin descripción")
            print(f"   {level.order}. {level.name}")
            print(f"      Besitos mínimos: {level.min_besitos}")
            print(f"      Descripción: {description}")
            print(f"      Activo: {'Sí' if level.active else 'No'}")
            print()


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description="Seed de niveles del Protocolo de Acceso"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Elimina niveles existentes antes de crear nuevos (peligroso)"
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Muestra los niveles actuales sin modificar nada"
    )

    args = parser.parse_args()

    if args.show:
        asyncio.run(show_levels())
    else:
        asyncio.run(seed_levels(force=args.force))


if __name__ == "__main__":
    main()
