#!/usr/bin/env python3
"""
Script para eliminar capítulos y fragmentos de la narrativa.

Elimina SOLO el contenido narrativo:
- Capítulos
- Fragmentos (escenas)
- Decisiones de fragmentos
- Requisitos de fragmentos
- Variantes de fragmentos
- Desafíos de fragmentos
- Ventanas de tiempo de fragmentos

NO elimina datos de usuarios (progreso, visitas, cooldowns, etc.)

⚠️  ADVERTENCIA: Esta operación NO es reversible.
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import delete, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.engine import get_session
from bot.narrative.database import (
    NarrativeChapter,
    NarrativeFragment,
    FragmentDecision,
    FragmentRequirement,
)
from bot.narrative.database.models_immersive import (
    FragmentVariant,
    FragmentChallenge,
    FragmentTimeWindow,
)


async def count_content(session: AsyncSession) -> dict:
    """Cuenta solo el contenido narrativo (capítulos y fragmentos)."""
    counts = {}

    for model, name in [
        (FragmentTimeWindow, "fragment_time_windows"),
        (FragmentChallenge, "fragment_challenges"),
        (FragmentVariant, "fragment_variants"),
        (FragmentRequirement, "fragment_requirements"),
        (FragmentDecision, "fragment_decisions"),
        (NarrativeFragment, "narrative_fragments"),
        (NarrativeChapter, "narrative_chapters"),
    ]:
        stmt = select(func.count()).select_from(model)
        result = await session.execute(stmt)
        counts[name] = result.scalar_one()

    return counts


async def reset_narrative(confirm: bool = False) -> None:
    """
    Elimina capítulos y fragmentos de la base de datos.

    Args:
        confirm: Si es False, muestra lo que se eliminará y pide confirmación
    """
    print("=" * 50)
    print("🗑️  ELIMINAR CAPÍTULOS Y FRAGMENTOS")
    print("=" * 50)

    # Inicializar base de datos primero
    from bot.database.engine import init_db
    await init_db()

    async with get_session() as session:
        # Contar registros antes de eliminar
        print("\n📊 Contando contenido narrativo...")
        counts_before = await count_content(session)

        total = sum(counts_before.values())
        print(f"\nTotal de registros a eliminar: {total:,}")

        if total == 0:
            print("\n✅ No hay capítulos ni fragmentos para eliminar.")
            return

        # Mostrar desglose
        print("\nDesglose:")
        for table, count in sorted(counts_before.items()):
            if count > 0:
                print(f"  • {table}: {count:,}")

        # Confirmación
        if not confirm:
            print("\n" + "⚠️ " * 20)
            print("ADVERTENCIA: Se eliminarán TODOS los capítulos y fragmentos.")
            print("Los datos de usuarios (progreso, visitas) se mantendrán.")
            print("⚠️ " * 20)

            response = input("\n¿Estás seguro? (escribe 'ELIMINAR' para confirmar): ")
            if response != "ELIMINAR":
                print("\n❌ Operación cancelada.")
                return

        print("\n🔄 Iniciando eliminación...")

        # Orden de eliminación (respetando foreign keys)
        steps = [
            # 1. Motor Inmersivo (asociado a fragmentos)
            ("fragment_time_windows", delete(FragmentTimeWindow)),
            ("fragment_challenges", delete(FragmentChallenge)),
            ("fragment_variants", delete(FragmentVariant)),

            # 2. Motor Básico - Contenido (en orden inverso de dependencia)
            ("fragment_requirements", delete(FragmentRequirement)),
            ("fragment_decisions", delete(FragmentDecision)),
            ("narrative_fragments", delete(NarrativeFragment)),
            ("narrative_chapters", delete(NarrativeChapter)),
        ]

        for table_name, stmt in steps:
            result = await session.execute(stmt)
            rows_affected = result.rowcount
            print(f"  ✓ {table_name}: {rows_affected:,} eliminados")

        # Commit de todos los cambios
        await session.commit()

        print("\n" + "=" * 50)
        print("✅ ELIMINACIÓN COMPLETADA")
        print("=" * 50)

        # Verificar que todo esté vacío
        counts_after = await count_content(session)
        remaining = sum(counts_after.values())

        if remaining > 0:
            print(f"\n⚠️  Quedaron {remaining:,} registros (datos huérfanos)")
        else:
            print("\n✨ Todos los capítulos y fragmentos han sido eliminados.")
            print("📊 Los datos de usuarios se mantienen intactos.")


def main():
    """Punto de entrada principal."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Resetear toda la narrativa de la base de datos"
    )
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Saltar confirmación (usar con precaución)"
    )

    args = parser.parse_args()

    try:
        asyncio.run(reset_narrative(confirm=args.yes))
    except KeyboardInterrupt:
        print("\n\n❌ Operación cancelada por el usuario.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
