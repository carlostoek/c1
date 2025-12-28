#!/usr/bin/env python3
"""
Script de migración para agregar sistema de onboarding narrativo.

Este script:
1. Crea las tablas user_onboarding_progress y onboarding_fragments
2. Verifica que se hayan creado correctamente
3. Pobla los fragmentos de onboarding iniciales

Uso:
    python scripts/migrate_add_onboarding.py
"""
import asyncio
import json
import logging
import sys
from datetime import datetime
from sqlalchemy import text

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Fragmentos iniciales del onboarding
ONBOARDING_FRAGMENTS = [
    {
        "step": 1,
        "speaker": "diana",
        "title": "Bienvenida al Mundo Narrativo",
        "content": """🌟 <b>Bienvenido al Mundo de Diana y Lucien</b>

Hola, soy Diana. Este es un lugar donde tus decisiones moldean la historia.

Cada elección que hagas tendrá consecuencias. Algunas te costarán besitos 💋, nuestra moneda especial.

Acabas de recibir <b>30 besitos de bienvenida</b>. ✨

¿Cómo te gusta enfrentar las historias?""",
        "decisions": json.dumps([
            {"text": "Me gusta actuar rápido y seguir mi instinto", "archetype_hint": "IMPULSIVE"},
            {"text": "Prefiero analizar antes de decidir", "archetype_hint": "CONTEMPLATIVE"}
        ])
    },
    {
        "step": 2,
        "speaker": "diana",
        "title": "Primera Decisión Tutorial",
        "content": """Perfecto. Ahora déjame mostrarte cómo funciona.

Imagina que encuentras una puerta misteriosa en un bosque oscuro.

¿Qué harías?""",
        "decisions": json.dumps([
            {"text": "Abrir la puerta inmediatamente", "archetype_hint": "IMPULSIVE"},
            {"text": "Examinar la puerta primero", "archetype_hint": "CONTEMPLATIVE"},
            {"text": "Observar desde lejos", "archetype_hint": "SILENT"}
        ])
    },
    {
        "step": 3,
        "speaker": "lucien",
        "title": "Explicación de Mecánicas",
        "content": """💋 <b>Sobre los Besitos</b>

Los besitos son la moneda de este mundo. Los usarás para:
• Desbloquear decisiones especiales
• Acceder a capítulos exclusivos
• Obtener pistas en desafíos

Puedes ganar más completando misiones y avanzando en la historia.

Recuerda, algunas decisiones tienen costo... ¡pero las mejores recompensas requieren inversión!""",
        "decisions": json.dumps([
            {"text": "Entendido, continuemos"}
        ])
    },
    {
        "step": 4,
        "speaker": "diana",
        "title": "Detección de Arquetipo",
        "content": """He estado observando tus elecciones...

Tu forma de tomar decisiones me dice mucho sobre ti.

Este conocimiento me ayudará a adaptar la historia a tu estilo.

¿Listo para descubrir qué tipo de viajero eres?""",
        "decisions": json.dumps([
            {"text": "Sí, quiero saber"},
            {"text": "Sigamos adelante"}
        ])
    },
    {
        "step": 5,
        "speaker": "diana",
        "title": "Entrada a Historia Completa",
        "content": """¡Listo! Ya conoces los fundamentos.

La historia completa te espera. ¿Estás preparado para sumergirte en el mundo de Diana y Lucien?

<i>Recuerda: cada decisión cuenta, cada camino es único.</i>""",
        "decisions": json.dumps([
            {"text": "📖 Comenzar la Historia", "callback": "narr:start"},
            {"text": "📚 Ver mi Diario de Viaje", "callback": "journal:view"}
        ])
    }
]


async def migrate_add_onboarding():
    """Ejecuta la migración para agregar sistema de onboarding."""

    try:
        # Importar después de logging configurado
        from bot.database.engine import get_engine
        from bot.database import init_db, close_db

        logger.info("🚀 Iniciando migración: agregar sistema de onboarding narrativo")

        # Inicializar BD (esto crea todas las tablas desde los modelos)
        await init_db()

        logger.info("✅ Tablas creadas desde modelos SQLAlchemy")

        # Verificar que las tablas existan
        engine = get_engine()

        async with engine.begin() as conn:
            # Verificar tabla user_onboarding_progress
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='user_onboarding_progress'")
            )
            exists = result.scalar() is not None

            if exists:
                logger.info("✅ Tabla 'user_onboarding_progress' creada correctamente")
            else:
                logger.error("❌ Tabla 'user_onboarding_progress' no encontrada")
                return False

            # Verificar tabla onboarding_fragments
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='onboarding_fragments'")
            )
            exists = result.scalar() is not None

            if exists:
                logger.info("✅ Tabla 'onboarding_fragments' creada correctamente")
            else:
                logger.error("❌ Tabla 'onboarding_fragments' no encontrada")
                return False

            # Poblar fragmentos de onboarding
            logger.info("📝 Poblando fragmentos de onboarding...")

            for fragment in ONBOARDING_FRAGMENTS:
                # Verificar si ya existe
                result = await conn.execute(
                    text("SELECT id FROM onboarding_fragments WHERE step = :step"),
                    {"step": fragment["step"]}
                )
                existing = result.scalar()

                if existing:
                    logger.info(f"  ⏭️ Paso {fragment['step']} ya existe, saltando...")
                    continue

                # Insertar fragmento
                now = datetime.utcnow().isoformat()
                await conn.execute(
                    text("""
                        INSERT INTO onboarding_fragments
                        (step, speaker, title, content, decisions, is_active, created_at, updated_at)
                        VALUES (:step, :speaker, :title, :content, :decisions, 1, :now, :now)
                    """),
                    {
                        "step": fragment["step"],
                        "speaker": fragment["speaker"],
                        "title": fragment["title"],
                        "content": fragment["content"],
                        "decisions": fragment["decisions"],
                        "now": now
                    }
                )
                logger.info(f"  ✅ Paso {fragment['step']}: {fragment['title']}")

        await close_db()

        logger.info("\n" + "="*60)
        logger.info("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
        logger.info("="*60)
        logger.info("\nSistema de onboarding narrativo instalado.")
        logger.info("\n5 fragmentos de onboarding creados:")
        for f in ONBOARDING_FRAGMENTS:
            logger.info(f"  - Paso {f['step']}: {f['title']}")
        logger.info("\nPróximos pasos:")
        logger.info("1. Reiniciar el bot")
        logger.info("2. Probar el flujo de aprobación Free")
        logger.info("3. El onboarding iniciará automáticamente")

        return True

    except Exception as e:
        logger.error(f"❌ Error en migración: {e}", exc_info=True)
        return False


async def main():
    """Punto de entrada."""
    try:
        success = await migrate_add_onboarding()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
