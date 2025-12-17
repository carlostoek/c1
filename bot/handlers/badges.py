"""
Handlers de badges - Colección personal de insignias.

Proporciona endpoints para que los usuarios visualicen:
- Su colección personal de badges
- Catálogo completo de badges disponibles
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from bot.database import get_session
from bot.services.container import ServiceContainer
from bot.database.models import BadgeRarity

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("mis_badges"))
async def show_user_badges(message: Message):
    """
    Muestra la colección personal de badges del usuario.

    Display:
    - Recuento total de badges
    - Conteo por rareza
    - Lista de badges adquiridos ordenados por rareza y fecha
    """
    async with get_session() as session:
        container = ServiceContainer(session, message.bot)

        try:
            user_badges = await container.badges.get_user_badges(
                message.from_user.id
            )

            if not user_badges:
                await message.answer(
                    "🏆 <b>Tu Colección de Badges</b>\n\n"
                    "Aún no tienes badges.\n"
                    "Completa misiones y canjea recompensas para conseguirlos.",
                    parse_mode="HTML"
                )
                return

            # Agrupar por rareza
            by_rarity = {
                BadgeRarity.LEGENDARY: [],
                BadgeRarity.EPIC: [],
                BadgeRarity.RARE: [],
                BadgeRarity.COMMON: []
            }

            for ub in user_badges:
                by_rarity[ub.badge.rarity].append(ub)

            # Construir mensaje
            text = "🏆 <b>Tu Colección de Badges</b>\n\n"

            # Conteo total
            total = len(user_badges)
            legendary = len(by_rarity[BadgeRarity.LEGENDARY])
            epic = len(by_rarity[BadgeRarity.EPIC])
            rare = len(by_rarity[BadgeRarity.RARE])
            common = len(by_rarity[BadgeRarity.COMMON])

            text += f"📊 <b>Total: {total} badges</b>\n"
            if legendary > 0:
                text += f"💎 Legendarios: {legendary}\n"
            if epic > 0:
                text += f"🥇 Épicos: {epic}\n"
            if rare > 0:
                text += f"🥈 Raros: {rare}\n"
            if common > 0:
                text += f"🥉 Comunes: {common}\n"

            text += "\n━━━━━━━━━━━━━━━━━━━━\n\n"

            # Listar badges por rareza
            rarity_names = {
                BadgeRarity.LEGENDARY: "💎 LEGENDARIOS",
                BadgeRarity.EPIC: "🥇 ÉPICOS",
                BadgeRarity.RARE: "🥈 RAROS",
                BadgeRarity.COMMON: "🥉 COMUNES"
            }

            for rarity in [BadgeRarity.LEGENDARY, BadgeRarity.EPIC,
                           BadgeRarity.RARE, BadgeRarity.COMMON]:
                badges_list = by_rarity[rarity]

                if not badges_list:
                    continue

                text += f"<b>{rarity_names[rarity]}</b>\n"

                for ub in badges_list:
                    date_str = ub.earned_at.strftime("%d/%m/%Y")
                    text += f"• {ub.badge.display_name}\n"
                    text += f"  <i>{ub.badge.description}</i>\n"
                    text += f"  📅 {date_str}\n\n"

            await message.answer(text, parse_mode="HTML")

        except Exception as e:
            logger.error(f"Error showing user badges: {e}", exc_info=True)
            await message.answer(
                "❌ Hubo un error al obtener tus badges."
            )


@router.message(Command("catalogo_badges"))
async def show_badges_catalog(message: Message):
    """
    Muestra el catálogo completo de badges disponibles.

    Display:
    - Todos los badges agrupados por rareza
    - Marca si ya los posee el usuario (✅ adquirido, 🔒 bloqueado)
    - Descripción completa de cada badge
    """
    async with get_session() as session:
        container = ServiceContainer(session, message.bot)

        try:
            # Obtener todos los badges disponibles (sin secretos)
            all_badges = await container.badges.get_all_badges(
                include_secret=False
            )

            if not all_badges:
                await message.answer("No hay badges disponibles.")
                return

            # Obtener badges del usuario
            user_badges = await container.badges.get_user_badges(
                message.from_user.id
            )
            user_badge_ids = {ub.badge_id for ub in user_badges}

            text = "📖 <b>Catálogo de Badges</b>\n\n"

            # Agrupar por rareza
            by_rarity = {
                BadgeRarity.LEGENDARY: [],
                BadgeRarity.EPIC: [],
                BadgeRarity.RARE: [],
                BadgeRarity.COMMON: []
            }

            for badge in all_badges:
                by_rarity[badge.rarity].append(badge)

            # Mostrar por rareza
            for rarity in [BadgeRarity.LEGENDARY, BadgeRarity.EPIC,
                           BadgeRarity.RARE, BadgeRarity.COMMON]:
                badges_list = by_rarity[rarity]

                if not badges_list:
                    continue

                text += f"<b>{badges_list[0].rarity_icon} {rarity.value.upper()}</b>\n"

                for badge in badges_list:
                    has_it = badge.id in user_badge_ids
                    status = "✅" if has_it else "🔒"

                    text += f"{status} {badge.display_name}\n"
                    text += f"   <i>{badge.description}</i>\n\n"

            await message.answer(text, parse_mode="HTML")

        except Exception as e:
            logger.error(f"Error showing badges catalog: {e}", exc_info=True)
            await message.answer(
                "❌ Hubo un error al obtener el catálogo de badges."
            )
