#!/usr/bin/env python3
"""
Script de inicialización de datos para producción.

Verifica y carga todos los datos seed necesarios para que el bot
funcione correctamente en producción.

Uso:
    python scripts/init_production_data.py

El script es idempotente: puede ejecutarse múltiples veces sin duplicar datos.
"""

import asyncio
import sys
import subprocess
from pathlib import Path
from typing import Tuple

# Agregar directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import select, func
from bot.database.engine import get_session, init_db, close_db


# ============================================================
# DEFINICIÓN DE SEEDS Y SUS VERIFICACIONES
# ============================================================

SEEDS = [
    # (nombre, script, tabla_a_verificar, modelo, mínimo_esperado, descripción)
    {
        "name": "Protocol Levels",
        "script": "seed_protocol_levels.py",
        "check_table": "levels",
        "min_count": 7,
        "description": "Niveles del Protocolo de Acceso (Visitante → Guardián)",
    },
    {
        "name": "Reactions",
        "script": "seed_reactions.py",
        "check_table": "reactions",
        "min_count": 1,
        "description": "Reacciones predeterminadas para broadcasts",
    },
    {
        "name": "Cabinet Items",
        "script": "seed_cabinet_items.py",
        "check_table": "shop_items",
        "min_count": 10,
        "description": "Categorías e items del Gabinete",
    },
    {
        "name": "Level 1 - Bienvenida",
        "script": "seed_level_1.py",
        "check_slug": "l1-bienvenida",
        "description": "Contenido narrativo Nivel 1",
    },
    {
        "name": "Level 2 - Observación",
        "script": "seed_level_2.py",
        "check_slug": "l2-observacion",
        "description": "Contenido narrativo Nivel 2",
    },
    {
        "name": "Level 3 - Perfil de Deseo",
        "script": "seed_level_3.py",
        "check_slug": "l3-perfil-de-deseo",
        "description": "Contenido narrativo Nivel 3",
    },
    {
        "name": "Level 4 - Entrada al Diván",
        "script": "seed_level_4.py",
        "check_slug": "l4-entrada-divan",
        "description": "Contenido narrativo Nivel 4 (VIP)",
    },
    {
        "name": "Level 5 - Profundización",
        "script": "seed_level_5.py",
        "check_slug": "l5-profundizacion",
        "description": "Contenido narrativo Nivel 5 (VIP)",
    },
    {
        "name": "Level 6 - Culminación",
        "script": "seed_level_6.py",
        "check_slug": "l6-culminacion",
        "description": "Contenido narrativo Nivel 6 (VIP)",
    },
    {
        "name": "Easter Eggs",
        "script": "seed_easter_eggs.py",
        "check_slug": "easter-eggs",
        "description": "Fragmentos ocultos y especiales",
    },
]


async def check_table_count(session, table_name: str) -> int:
    """Cuenta registros en una tabla por nombre."""
    from sqlalchemy import text
    result = await session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
    return result.scalar() or 0


async def check_chapter_exists(session, slug: str) -> bool:
    """Verifica si un capítulo narrativo existe por slug."""
    from sqlalchemy import text
    result = await session.execute(
        text("SELECT COUNT(*) FROM narrative_chapters WHERE slug = :slug"),
        {"slug": slug}
    )
    return (result.scalar() or 0) > 0


async def check_seed_loaded(session, seed: dict) -> Tuple[bool, str]:
    """
    Verifica si un seed ya está cargado.

    Returns:
        (is_loaded, status_message)
    """
    try:
        if "check_table" in seed:
            count = await check_table_count(session, seed["check_table"])
            min_count = seed.get("min_count", 1)
            if count >= min_count:
                return True, f"✅ {count} registros"
            else:
                return False, f"⚠️  {count}/{min_count} registros"

        elif "check_slug" in seed:
            exists = await check_chapter_exists(session, seed["check_slug"])
            if exists:
                return True, "✅ Capítulo existe"
            else:
                return False, "❌ No encontrado"

        return False, "❓ Sin verificación"

    except Exception as e:
        # Tabla no existe aún
        return False, f"❌ Error: {e}"


def run_seed_script(script_name: str) -> Tuple[bool, str]:
    """
    Ejecuta un script de seed.

    Returns:
        (success, output)
    """
    script_path = ROOT_DIR / "scripts" / script_name

    if not script_path.exists():
        return False, f"Script no encontrado: {script_path}"

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
            timeout=120  # 2 minutos máximo por seed
        )

        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, f"Error: {result.stderr or result.stdout}"

    except subprocess.TimeoutExpired:
        return False, "Timeout: el script tardó más de 2 minutos"
    except Exception as e:
        return False, f"Error ejecutando script: {e}"


async def main():
    """Función principal."""
    print("=" * 70)
    print("🚀 INICIALIZACIÓN DE DATOS DE PRODUCCIÓN")
    print("=" * 70)
    print(f"\nDirectorio: {ROOT_DIR}")
    print(f"Seeds a verificar: {len(SEEDS)}\n")

    # Inicializar BD
    print("📦 Inicializando base de datos...")
    await init_db()

    seeds_to_run = []
    seeds_loaded = []

    # Fase 1: Verificar estado actual
    print("\n" + "-" * 70)
    print("📋 VERIFICANDO ESTADO ACTUAL")
    print("-" * 70 + "\n")

    async with get_session() as session:
        for seed in SEEDS:
            is_loaded, status = await check_seed_loaded(session, seed)

            icon = "✅" if is_loaded else "❌"
            print(f"  {icon} {seed['name']:30} {status}")

            if is_loaded:
                seeds_loaded.append(seed)
            else:
                seeds_to_run.append(seed)

    # Resumen
    print("\n" + "-" * 70)
    print(f"📊 RESUMEN: {len(seeds_loaded)} cargados, {len(seeds_to_run)} pendientes")
    print("-" * 70)

    if not seeds_to_run:
        print("\n✅ Todos los datos ya están cargados. ¡Listo para producción!")
        await close_db()
        return 0

    # Fase 2: Ejecutar seeds pendientes
    print("\n" + "=" * 70)
    print("🌱 EJECUTANDO SEEDS PENDIENTES")
    print("=" * 70 + "\n")

    success_count = 0
    error_count = 0

    for seed in seeds_to_run:
        print(f"\n▶️  {seed['name']}")
        print(f"   📄 {seed['script']}")
        print(f"   📝 {seed['description']}")

        success, output = run_seed_script(seed["script"])

        if success:
            print(f"   ✅ Completado")
            success_count += 1
        else:
            print(f"   ❌ Error: {output[:200]}...")
            error_count += 1

    # Fase 3: Verificación final
    print("\n" + "=" * 70)
    print("🔍 VERIFICACIÓN FINAL")
    print("=" * 70 + "\n")

    async with get_session() as session:
        all_ok = True
        for seed in SEEDS:
            is_loaded, status = await check_seed_loaded(session, seed)
            icon = "✅" if is_loaded else "❌"
            print(f"  {icon} {seed['name']:30} {status}")
            if not is_loaded:
                all_ok = False

    await close_db()

    # Resultado final
    print("\n" + "=" * 70)
    if all_ok:
        print("🎉 ¡INICIALIZACIÓN COMPLETADA EXITOSAMENTE!")
        print("   El bot está listo para producción.")
    else:
        print(f"⚠️  INICIALIZACIÓN PARCIAL")
        print(f"   {success_count} seeds ejecutados, {error_count} con errores")
        print("   Revisa los errores arriba y vuelve a ejecutar el script.")
    print("=" * 70 + "\n")

    return 0 if all_ok else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelado por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        sys.exit(1)
