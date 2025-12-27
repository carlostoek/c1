#!/usr/bin/env python3
"""
Script de migración para agregar sistema de configuración de menús dinámicos.

Este script:
1. Crea las tablas menu_items y menu_configs
2. Verifica que se hayan creado correctamente

Uso:
    python scripts/migrate_add_menu_config.py
"""
import asyncio
import logging
import sys
from sqlalchemy import text

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def migrate_add_menu_config():
    """Ejecuta la migración para agregar sistema de configuración de menús."""

    try:
        # Importar después de logging configurado
        from bot.database.engine import get_engine
        from bot.database import init_db, close_db

        logger.info("🚀 Iniciando migración: agregar sistema de configuración de menús")

        # Inicializar BD (esto crea todas las tablas desde los modelos)
        await init_db()

        logger.info("✅ Migración completada exitosamente")
        logger.info("✅ Las tablas se actualizaron desde los modelos SQLAlchemy")

        # Verificar que las tablas existan
        engine = get_engine()

        async with engine.begin() as conn:
            # Verificar tabla menu_items
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='menu_items'")
            )
            exists = result.scalar() is not None

            if exists:
                logger.info("✅ Tabla 'menu_items' creada correctamente")
            else:
                logger.error("❌ Tabla 'menu_items' no encontrada")
                return False

            # Verificar tabla menu_configs
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='menu_configs'")
            )
            exists = result.scalar() is not None

            if exists:
                logger.info("✅ Tabla 'menu_configs' creada correctamente")
            else:
                logger.error("❌ Tabla 'menu_configs' no encontrada")
                return False

            # Verificar índices de menu_items
            result = await conn.execute(
                text("PRAGMA index_list(menu_items)")
            )
            indexes = result.fetchall()
            index_names = [idx[1] for idx in indexes]

            expected_indexes = ['ix_menu_items_role_active', 'ix_menu_items_order']
            for idx_name in expected_indexes:
                if idx_name in index_names or any(idx_name in name for name in index_names):
                    logger.info(f"✅ Índice '{idx_name}' creado correctamente")
                else:
                    logger.warning(f"⚠️ Índice '{idx_name}' no encontrado (puede haberse creado con nombre auto-generado)")

        await close_db()

        logger.info("\n" + "="*60)
        logger.info("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
        logger.info("="*60)
        logger.info("\nSistema de configuración de menús dinámicos instalado.")
        logger.info("\nPróximos pasos:")
        logger.info("1. Reiniciar el bot")
        logger.info("2. Ir a /admin → Configurar Menús")
        logger.info("3. Crear botones personalizados para VIP y FREE")

        return True

    except Exception as e:
        logger.error(f"❌ Error en migración: {e}", exc_info=True)
        return False


async def main():
    """Punto de entrada."""
    try:
        success = await migrate_add_menu_config()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
