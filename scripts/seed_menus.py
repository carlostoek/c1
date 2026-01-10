"""
Script de seed para menús dinámicos.

Popula la BD con menús iniciales para usuarios FREE y VIP.

Uso:
    python scripts/seed_menus.py
"""
import asyncio
import logging
import sys
from pathlib import Path

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.database import get_session
from bot.services.container import ServiceContainer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def seed_free_menu(container: ServiceContainer):
    """
    Crea menú inicial para usuarios FREE.

    Estructura:
    - Información de Contenido (submenu)
      - Sets (submenu)
        - Encanto Inicial + "Me interesa"
        - Sensualidad Revelada + "Me interesa"
        - Pasión Desbordante + "Me interesa"
        - Intimidad Explosiva + "Me interesa"
      - Personalizados + "Me interesa"
      - Volver
    - Mi Historia (BLOQUEADO si no onboarding)
    - Mi Perfil (BLOQUEADO si no onboarding)
    - Juegos (BLOQUEADO si no onboarding)
    - ¡Hazte VIP!
    """
    logger.info("🌱 Seeding menú FREE...")

    menu_items = [
        # ===== MENÚ PRINCIPAL FREE =====

        # Información de Contenido (submenu)
        {
            "item_key": "free_content",
            "button_text": "Información de Contenido",
            "button_emoji": "📢",
            "action_type": "submenu",
            "action_content": "free_content",  # Se ignora en submenus
            "target_role": "free",
            "display_order": 1,
            "row_number": 1,
            "requires_onboarding": False
        },

        # Mi Historia (acceso directo, validación al acceder)
        {
            "item_key": "free_historia",
            "button_text": "Mi Historia",
            "button_emoji": "📜",
            "action_type": "callback",
            "action_content": "narr:start",
            "target_role": "free",
            "display_order": 2,
            "row_number": 2,
            "requires_onboarding": False
        },

        # Mi Perfil (acceso directo, validación al acceder)
        {
            "item_key": "free_perfil",
            "button_text": "Mi Perfil",
            "button_emoji": "📊",
            "action_type": "callback",
            "action_content": "user:profile",
            "target_role": "free",
            "display_order": 3,
            "row_number": 3,
            "requires_onboarding": False
        },

        # Juegos (acceso directo, validación al acceder)
        {
            "item_key": "free_juegos",
            "button_text": "Juegos",
            "button_emoji": "🎮",
            "action_type": "callback",
            "action_content": "games:main",
            "target_role": "free",
            "display_order": 4,
            "row_number": 4,
            "requires_onboarding": False
        },

        # ¡Hazte VIP!
        {
            "item_key": "free_upgrade",
            "button_text": "¡Hazte VIP!",
            "button_emoji": "⭐",
            "action_type": "callback",
            "action_content": "user:vip_access",
            "target_role": "free",
            "display_order": 5,
            "row_number": 5,
            "requires_onboarding": False
        },

        # ===== SUBMENÚ: Información de Contenido =====

        # Sets (submenu)
        {
            "item_key": "free_sets",
            "button_text": "Sets",
            "button_emoji": "🌸",
            "action_type": "submenu",
            "action_content": "free_sets",
            "target_role": "free",
            "parent_key": "free_content",
            "display_order": 1,
            "row_number": 1,
            "requires_onboarding": False
        },

        # Personalizados
        {
            "item_key": "free_personalizado",
            "button_text": "Personalizados",
            "button_emoji": "✨",
            "action_type": "callback",
            "action_content": "interest:personalizado:consulta_general",
            "target_role": "free",
            "parent_key": "free_content",
            "display_order": 2,
            "row_number": 2,
            "requires_onboarding": False
        },

        # ===== SUBMENÚ: Sets =====

        # Encanto Inicial (muestra info → "Me interesa")
        {
            "item_key": "set_encanto",
            "button_text": "Encanto Inicial",
            "button_emoji": "🌸",
            "action_type": "callback",
            "action_content": "set_info:encanto_inicial",
            "target_role": "free",
            "parent_key": "free_sets",
            "display_order": 1,
            "row_number": 1,
            "requires_onboarding": False
        },

        # Sensualidad Revelada (muestra info → "Me interesa")
        {
            "item_key": "set_sensualidad",
            "button_text": "Sensualidad Revelada",
            "button_emoji": "💃",
            "action_type": "callback",
            "action_content": "set_info:sensualidad_revelada",
            "target_role": "free",
            "parent_key": "free_sets",
            "display_order": 2,
            "row_number": 2,
            "requires_onboarding": False
        },

        # Pasión Desbordante (muestra info → "Me interesa")
        {
            "item_key": "set_pasion",
            "button_text": "Pasión Desbordante",
            "button_emoji": "🔥",
            "action_type": "callback",
            "action_content": "set_info:pasion_desbordante",
            "target_role": "free",
            "parent_key": "free_sets",
            "display_order": 3,
            "row_number": 3,
            "requires_onboarding": False
        },

        # Intimidad Explosiva (muestra info → "Me interesa")
        {
            "item_key": "set_intimidad",
            "button_text": "Intimidad Explosiva",
            "button_emoji": "💥",
            "action_type": "callback",
            "action_content": "set_info:intimidad_explosiva",
            "target_role": "free",
            "parent_key": "free_sets",
            "display_order": 4,
            "row_number": 4,
            "requires_onboarding": False
        },
    ]

    created_count = 0
    for item_data in menu_items:
        try:
            item = await container.menu.create_menu_item(**item_data)
            logger.info(f"  ✅ Creado: {item.item_key}")
            created_count += 1
        except ValueError as e:
            # Item ya existe
            logger.debug(f"  ⏭️  Ya existe: {item_data['item_key']}")
        except Exception as e:
            logger.error(f"  ❌ Error creando {item_data['item_key']}: {e}")

    logger.info(f"✅ Menú FREE: {created_count} items creados")


async def seed_vip_menu(container: ServiceContainer):
    """
    Crea menú inicial para usuarios VIP.

    Estructura:
    - Mi Diván (placeholder)
    - Contenido Premium
    - Mapa del Deseo
    - Mi Historia
    - Mi Perfil
    """
    logger.info("🌱 Seeding menú VIP...")

    menu_items = [
        # Mi Diván (placeholder para implementación futura)
        {
            "item_key": "vip_divan",
            "button_text": "Mi Diván",
            "button_emoji": "🛋️",
            "action_type": "info",
            "action_content": "El Diván estará disponible pronto...",
            "target_role": "vip",
            "display_order": 1,
            "row_number": 1,
            "requires_onboarding": False
        },

        # Contenido Premium
        {
            "item_key": "vip_premium",
            "button_text": "Contenido Premium",
            "button_emoji": "💎",
            "action_type": "callback",
            "action_content": "content:premium",
            "target_role": "vip",
            "display_order": 2,
            "row_number": 2,
            "requires_onboarding": False
        },

        # Mapa del Deseo
        {
            "item_key": "vip_mapa",
            "button_text": "Mapa del Deseo",
            "button_emoji": "🗺️",
            "action_type": "callback",
            "action_content": "content:mapa_deseo",
            "target_role": "vip",
            "display_order": 3,
            "row_number": 3,
            "requires_onboarding": False
        },

        # Mi Historia (acceso completo)
        {
            "item_key": "vip_historia",
            "button_text": "Mi Historia",
            "button_emoji": "📜",
            "action_type": "callback",
            "action_content": "narr:start",
            "target_role": "vip",
            "display_order": 4,
            "row_number": 4,
            "requires_onboarding": False
        },

        # Mi Perfil (acceso completo)
        {
            "item_key": "vip_perfil",
            "button_text": "Mi Perfil",
            "button_emoji": "📊",
            "action_type": "callback",
            "action_content": "user:profile",
            "target_role": "vip",
            "display_order": 5,
            "row_number": 5,
            "requires_onboarding": False
        },
    ]

    created_count = 0
    for item_data in menu_items:
        try:
            item = await container.menu.create_menu_item(**item_data)
            logger.info(f"  ✅ Creado: {item.item_key}")
            created_count += 1
        except ValueError as e:
            logger.debug(f"  ⏭️  Ya existe: {item_data['item_key']}")
        except Exception as e:
            logger.error(f"  ❌ Error creando {item_data['item_key']}: {e}")

    logger.info(f"✅ Menú VIP: {created_count} items creados")


async def seed_menu_configs(container: ServiceContainer):
    """Crea configuraciones de menú por rol."""
    logger.info("🌱 Seeding configuraciones de menú...")

    configs = [
        {
            "role": "free",
            "welcome_message": "Bienvenido al Vestíbulo",
            "footer_message": None,
            "show_subscription_info": False
        },
        {
            "role": "vip",
            "welcome_message": "Bienvenido al Círculo Exclusivo",
            "footer_message": "Diana te espera en el Diván",
            "show_subscription_info": True
        },
    ]

    for config_data in configs:
        try:
            config = await container.menu.get_or_create_menu_config(**config_data)
            logger.info(f"  ✅ Config para role '{config.role}' lista")
        except Exception as e:
            logger.error(f"  ❌ Error creando config: {e}")

    logger.info("✅ Configuraciones de menú listas")


async def main():
    """Ejecuta el seed completo."""
    logger.info("🚀 Iniciando seed de menús...")

    # Inicializar BD primero
    from bot.database import init_db
    await init_db()

    async with get_session() as session:
        # Crear un bot mock (no se usa para seed)
        class MockBot:
            pass

        container = ServiceContainer(session, MockBot())

        try:
            # Seed menú FREE
            await seed_free_menu(container)

            # Seed menú VIP
            await seed_vip_menu(container)

            # Seed configuraciones
            await seed_menu_configs(container)

            # Commit final
            await session.commit()

            logger.info("✅ Seed completado exitosamente")

        except Exception as e:
            logger.error(f"❌ Error en seed: {e}", exc_info=True)
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
