#!/usr/bin/env python3
"""
Script de migración manual para agregar sistema de tarifas/planes de suscripción.

Este script:
1. Crea la tabla subscription_plans
2. Agrega la columna plan_id a invitation_tokens
3. Inserta 3 planes por defecto (Mensual, Trimestral, Anual)

Uso:
    python scripts/migrate_add_pricing_plans.py
"""
import asyncio
import logging
import sys
from datetime import datetime
from sqlalchemy import text, inspect

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def migrate_add_pricing_plans():
    """Ejecuta la migración para agregar sistema de tarifas."""

    try:
        # Importar después de logging configurado
        from bot.database.engine import get_engine
        from bot.database import init_db, close_db

        logger.info("🚀 Iniciando migración: agregar sistema de tarifas")

        # Inicializar BD (esto crea todas las tablas desde los modelos)
        await init_db()

        logger.info("✅ Migración completada exitosamente")
        logger.info("✅ Las tablas se actualizaron desde los modelos SQLAlchemy")

        # Verificar que la tabla existe
        engine = get_engine()

        async with engine.begin() as conn:
            # Verificar tabla subscription_plans
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='subscription_plans'")
            )
            exists = result.scalar() is not None

            if exists:
                logger.info("✅ Tabla 'subscription_plans' creada correctamente")
            else:
                logger.error("❌ Tabla 'subscription_plans' no encontrada")
                return False

            # Verificar columna plan_id en invitation_tokens
            result = await conn.execute(
                text("""
                    PRAGMA table_info(invitation_tokens)
                """)
            )
            columns = result.fetchall()
            column_names = [col[1] for col in columns]

            if "plan_id" not in column_names:
                logger.info("📝 Agregando columna 'plan_id' a 'invitation_tokens'...")
                try:
                    await conn.execute(
                        text("""
                            ALTER TABLE invitation_tokens
                            ADD COLUMN plan_id INTEGER
                        """)
                    )
                    await conn.commit()
                    logger.info("✅ Columna 'plan_id' agregada a 'invitation_tokens'")
                except Exception as e:
                    if "already exists" in str(e):
                        logger.info("✅ Columna 'plan_id' ya existe en 'invitation_tokens'")
                    else:
                        logger.error(f"❌ Error agregando columna: {e}")
                        return False
            else:
                logger.info("✅ Columna 'plan_id' ya existe en 'invitation_tokens'")

        # Insertar planes por defecto si no existen
        logger.info("📋 Verificando planes por defecto...")

        from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
        from bot.database.models import SubscriptionPlan

        async_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        async with async_session_factory() as session:
            from sqlalchemy import select

            # Verificar si ya existen planes
            result = await session.execute(
                select(SubscriptionPlan)
            )
            existing_plans = result.scalars().all()

            if len(existing_plans) >= 3:
                logger.info(f"✅ Ya existen {len(existing_plans)} planes configurados")
            else:
                logger.info("📝 Insertando planes por defecto...")

                default_plans = [
                    SubscriptionPlan(
                        name="Plan Mensual",
                        duration_days=30,
                        price=9.99,
                        currency="$",
                        active=True,
                        created_at=datetime.utcnow(),
                        created_by=0  # Admin del sistema
                    ),
                    SubscriptionPlan(
                        name="Plan Trimestral",
                        duration_days=90,
                        price=24.99,
                        currency="$",
                        active=True,
                        created_at=datetime.utcnow(),
                        created_by=0
                    ),
                    SubscriptionPlan(
                        name="Plan Anual",
                        duration_days=365,
                        price=79.99,
                        currency="$",
                        active=True,
                        created_at=datetime.utcnow(),
                        created_by=0
                    )
                ]

                for plan in default_plans:
                    session.add(plan)

                await session.commit()
                logger.info(f"✅ {len(default_plans)} planes por defecto insertados")

        await close_db()

        return True

    except Exception as e:
        logger.error(f"❌ Error en migración: {e}", exc_info=True)
        return False


async def main():
    """Punto de entrada."""
    try:
        success = await migrate_add_pricing_plans()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
