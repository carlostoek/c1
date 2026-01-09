"""
Script de seed data para cargar contenido narrativo inicial.

Carga un capítulo de ejemplo con fragmentos y decisiones para
demostrar el sistema de narrativa funcionando.

Uso:
    python scripts/seed_narrative.py
"""
# Este es el motor básico. Para narrativa avanzada y su importación, consulte la documentación: `docs/DOBLE-MOTOR-NARRATIVA.md`

import asyncio
import sys
import os

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.database import init_db, close_db, get_session
from bot.narrative.database import ChapterType
from bot.narrative.services.chapter import ChapterService
from bot.narrative.services.fragment import FragmentService
from bot.narrative.database import FragmentDecision


async def seed_narrative_content():
    """Carga contenido narrativo inicial."""
    print("🌱 Iniciando seed de contenido narrativo...")

    # Inicializar BD
    await init_db()

    async with get_session() as session:
        chapter_service = ChapterService(session)
        fragment_service = FragmentService(session)

        # Verificar si ya existe contenido
        existing = await chapter_service.get_chapter_by_slug("los-kinkys-demo")
        if existing:
            print("⚠️  El capítulo 'Los Kinkys Demo' ya existe. Saltando seed.")
            return

        print("📚 Creando capítulo 'Los Kinkys Demo'...")

        # Crear capítulo FREE
        chapter = await chapter_service.create_chapter(
            name="Los Kinkys (Demo)",
            slug="los-kinkys-demo",
            chapter_type=ChapterType.FREE,
            description="Capítulo de demostración del sistema narrativo",
            order=0
        )

        print(f"✅ Capítulo creado: {chapter.name} (ID: {chapter.id})")

        # Fragmento 1: Bienvenida de Diana (Entry Point)
        print("📄 Creando fragmento 1: Bienvenida...")
        frag1 = await fragment_service.create_fragment(
            chapter_id=chapter.id,
            fragment_key="demo_welcome",
            title="Bienvenida de Diana",
            speaker="diana",
            content=(
                "🎭 <b>Diana:</b>\n\n"
                "Hola, bienvenido a mi mundo... o mejor dicho, a nuestro pequeño secreto. "
                "Soy Diana, y si estás aquí es porque algo te atrajo de este lugar.\n\n"
                "Este es solo el comienzo. ¿Estás listo para explorar?"
            ),
            is_entry_point=True,
            order=0
        )

        # Decisiones para fragmento 1
        decision1_a = FragmentDecision(
            fragment_id=frag1.id,
            button_text="🚪 Descubrir más",
            target_fragment_key="demo_decision_a",
            order=0,
            besitos_cost=0,
            grants_besitos=10,
            is_active=True
        )

        decision1_b = FragmentDecision(
            fragment_id=frag1.id,
            button_text="🤔 Ir con calma",
            target_fragment_key="demo_decision_b",
            order=1,
            besitos_cost=0,
            grants_besitos=5,
            affects_archetype="contemplative",
            is_active=True
        )

        session.add_all([decision1_a, decision1_b])
        await session.flush()

        print(f"✅ Fragmento 1 creado con 2 decisiones")

        # Fragmento 2A: Decisión impulsiva
        print("📄 Creando fragmento 2A: Decisión impulsiva...")
        frag2a = await fragment_service.create_fragment(
            chapter_id=chapter.id,
            fragment_key="demo_decision_a",
            title="Respuesta Impulsiva",
            speaker="diana",
            content=(
                "🎭 <b>Diana:</b>\n\n"
                "Veo que no tienes miedo de avanzar rápido. Me gusta eso. "
                "La vida es demasiado corta para dudar, ¿no crees?\n\n"
                "<i>Has ganado 10 besitos por tu valentía.</i>"
            ),
            order=1
        )

        # Fragmento 2B: Decisión contemplativa
        print("📄 Creando fragmento 2B: Decisión contemplativa...")
        frag2b = await fragment_service.create_fragment(
            chapter_id=chapter.id,
            fragment_key="demo_decision_b",
            title="Respuesta Contemplativa",
            speaker="diana",
            content=(
                "🎭 <b>Diana:</b>\n\n"
                "Interesante... Prefieres observar antes de actuar. "
                "Eso habla de alguien que piensa las cosas.\n\n"
                "<i>Has ganado 5 besitos.</i>"
            ),
            order=2
        )

        # Decisiones finales (ambos fragmentos llevan al mismo final)
        decision_final_a = FragmentDecision(
            fragment_id=frag2a.id,
            button_text="✨ Continuar",
            target_fragment_key="demo_ending",
            order=0,
            besitos_cost=0,
            is_active=True
        )

        decision_final_b = FragmentDecision(
            fragment_id=frag2b.id,
            button_text="✨ Continuar",
            target_fragment_key="demo_ending",
            order=0,
            besitos_cost=0,
            is_active=True
        )

        session.add_all([decision_final_a, decision_final_b])
        await session.flush()

        print(f"✅ Fragmentos 2A y 2B creados")

        # Fragmento 3: Final del demo
        print("📄 Creando fragmento 3: Final del demo...")
        frag3 = await fragment_service.create_fragment(
            chapter_id=chapter.id,
            fragment_key="demo_ending",
            title="Fin del Demo",
            speaker="diana",
            content=(
                "🎭 <b>Diana:</b>\n\n"
                "Esto es solo una pequeña muestra de lo que vendrá. "
                "Hay mucho más por descubrir, pero tendrás que esperar a que "
                "se cargue el contenido completo.\n\n"
                "Gracias por probar el sistema. 💋\n\n"
                "<i>Fin del capítulo de demostración</i>"
            ),
            is_ending=True,
            order=3
        )

        print(f"✅ Fragmento 3 creado (final)")

        await session.commit()

    await close_db()

    print("\n✅ Seed completado exitosamente!")
    print(f"   - 1 capítulo: 'Los Kinkys (Demo)'")
    print(f"   - 4 fragmentos narrativos")
    print(f"   - 4 decisiones interactivas")
    print("\n🎮 Ahora los usuarios pueden acceder a '📖 Historia' desde el menú principal.")


if __name__ == "__main__":
    asyncio.run(seed_narrative_content())
