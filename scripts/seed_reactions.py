#!/usr/bin/env python3
"""Script de seed para reacciones predeterminadas.

Crea las reacciones base para el sistema de custom reactions en broadcasting.

Uso:
    python scripts/seed_reactions.py [--force]

Opciones:
    --force: Elimina reacciones existentes antes de crear nuevas (peligroso)
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
from bot.gamification.database.models import Reaction


# Reacciones predeterminadas del sistema
DEFAULT_REACTIONS = [
    {
        "emoji": "👍",
        "button_label": "Me Gusta",
        "besitos_value": 10,
        "sort_order": 1,
        "active": True
    },
    {
        "emoji": "❤️",
        "button_label": "Me Encanta",
        "besitos_value": 15,
        "sort_order": 2,
        "active": True
    },
    {
        "emoji": "🔥",
        "button_label": "Increíble",
        "besitos_value": 20,
        "sort_order": 3,
        "active": True
    },
    {
        "emoji": "😂",
        "button_label": "Divertido",
        "besitos_value": 10,
        "sort_order": 4,
        "active": True
    },
    {
        "emoji": "😮",
        "button_label": "Sorprendente",
        "besitos_value": 15,
        "sort_order": 5,
        "active": True
    }
]


async def seed_reactions(force: bool = False):
    """Crea reacciones predeterminadas en la base de datos.

    Args:
        force: Si True, elimina reacciones existentes antes de crear nuevas
    """
    print("🌱 Iniciando seed de reacciones...")

    # Inicializar base de datos
    await init_db()

    async with get_session() as session:
        if force:
            print("⚠️  Modo FORCE: Eliminando reacciones existentes...")
            # Obtener todas las reacciones
            stmt = select(Reaction)
            result = await session.execute(stmt)
            existing_reactions = result.scalars().all()

            for reaction in existing_reactions:
                await session.delete(reaction)

            await session.commit()
            print(f"🗑️  Eliminadas {len(existing_reactions)} reacciones existentes")

        # Crear reacciones predeterminadas
        created_count = 0
        skipped_count = 0

        for reaction_data in DEFAULT_REACTIONS:
            # Verificar si ya existe
            stmt = select(Reaction).where(Reaction.emoji == reaction_data["emoji"])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing and not force:
                print(f"⏭️  Reacción '{reaction_data['emoji']}' ya existe, omitiendo...")
                skipped_count += 1
                continue

            # Crear nueva reacción
            # Nota: button_emoji, button_label y sort_order se agregarán cuando
            # la migración 005 se aplique correctamente
            reaction = Reaction(
                emoji=reaction_data["emoji"],
                besitos_value=reaction_data["besitos_value"],
                active=reaction_data["active"]
            )

            # Intentar agregar campos opcionales (si existen en la BD)
            try:
                reaction.button_emoji = reaction_data["emoji"]
                reaction.button_label = reaction_data["button_label"]
                reaction.sort_order = reaction_data["sort_order"]
            except AttributeError:
                # Los campos no existen aún en la BD, skip
                pass

            session.add(reaction)

            try:
                await session.commit()
                print(
                    f"✅ Creada reacción: {reaction_data['emoji']} "
                    f"{reaction_data['button_label']} ({reaction_data['besitos_value']} besitos)"
                )
                created_count += 1
            except IntegrityError as e:
                await session.rollback()
                print(f"❌ Error al crear reacción '{reaction_data['emoji']}': {e}")
                skipped_count += 1

        # Resumen
        print("\n" + "="*50)
        print(f"✨ Seed completado:")
        print(f"   - Creadas: {created_count}")
        print(f"   - Omitidas: {skipped_count}")
        print(f"   - Total: {created_count + skipped_count}/{len(DEFAULT_REACTIONS)}")
        print("="*50)


async def show_existing_reactions():
    """Muestra las reacciones existentes en la base de datos."""
    print("\n📋 Reacciones existentes en la base de datos:\n")

    # Inicializar base de datos
    await init_db()

    async with get_session() as session:
        # Intentar ordenar por sort_order, o por id si no existe
        try:
            stmt = select(Reaction).order_by(Reaction.sort_order)
        except AttributeError:
            stmt = select(Reaction).order_by(Reaction.id)

        result = await session.execute(stmt)
        reactions = result.scalars().all()

        if not reactions:
            print("   (No hay reacciones registradas)")
            return

        for reaction in reactions:
            status = "✅ Activa" if reaction.active else "❌ Inactiva"
            # Intentar obtener button_label si existe
            label = getattr(reaction, 'button_label', None) or '(sin label)'
            print(
                f"   {reaction.emoji} {label} "
                f"- {reaction.besitos_value} besitos - {status}"
            )

        print(f"\n   Total: {len(reactions)} reacciones")


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description="Seed de reacciones predeterminadas para el sistema de broadcasting"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Elimina reacciones existentes antes de crear nuevas (PELIGROSO)"
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Muestra las reacciones existentes sin crear nuevas"
    )

    args = parser.parse_args()

    # Mostrar advertencia si se usa --force
    if args.force:
        print("\n⚠️  ADVERTENCIA: Modo --force activado")
        print("   Esto eliminará TODAS las reacciones existentes.")
        confirmation = input("   ¿Estás seguro? (escribe 'si' para continuar): ")

        if confirmation.lower() != "si":
            print("❌ Operación cancelada")
            sys.exit(0)

    # Ejecutar operación
    try:
        if args.show:
            asyncio.run(show_existing_reactions())
        else:
            asyncio.run(seed_reactions(force=args.force))

            # Mostrar reacciones finales
            asyncio.run(show_existing_reactions())

    except KeyboardInterrupt:
        print("\n\n⚠️  Operación interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error durante el seed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
