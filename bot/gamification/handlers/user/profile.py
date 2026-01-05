"""
Handler para visualización de perfil de usuario con la voz de Lucien.

Muestra información de gamificación del usuario con el formato y tono de Lucien.
"""
import logging
from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram import F
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares import DatabaseMiddleware
from bot.gamification.services.container import GamificationContainer
from bot.utils.lucien_messages import Lucien
from bot.utils.menu_helpers import build_profile_menu

logger = logging.getLogger(__name__)
router = Router()

# Registrar middleware para inyectar session y gamification
router.message.middleware(DatabaseMiddleware())
router.callback_query.middleware(DatabaseMiddleware())


def _get_level_comment(level_order: int) -> str:
    """Retorna el comentario de Lucien basado en el número de nivel."""
    if level_order <= 2:
        return Lucien.PROFILE_LEVEL_LOW
    if level_order <= 4:
        return Lucien.PROFILE_LEVEL_MID
    if level_order <= 6:
        return Lucien.PROFILE_LEVEL_HIGH
    return Lucien.PROFILE_LEVEL_MAX


def _build_lucien_profile_text(profile_data: dict) -> str:
    """Construye el texto del perfil con la voz de Lucien."""
    level_info = profile_data.get('level', {})
    current_level = level_info.get('current')
    
    if not current_level:
        return Lucien.ERROR_GENERIC # No debería pasar si el usuario existe

    level_comment = _get_level_comment(current_level.order)
    
    progress_bar = Lucien.format_progress_bar(
        current=int(level_info.get('progress_percentage', 0)),
        total=100
    )

    besitos_total = profile_data.get('besitos', {}).get('total', 0)
    
    # TODO: Obtener arquetipo y distintivos cuando el servicio lo provea.
    # archetype_info = "Arquetipo: {archetype_name}\n\"{archetype_description}\""
    # badges_list = "Distintivos: {badges_list}"

    return (
        f"{level_comment}\n\n"
        f"📊 <b>Su Expediente</b>\n\n"
        f"Nivel: {current_level.name} ({current_level.order}/7)\n"
        f"{progress_bar} {int(level_info.get('progress_percentage', 0)) homers}\n"
        f"Besitos: {besitos_total}\n\n"
    )


async def _send_profile_view(
    user_id: int,
    bot: Bot,
    session: AsyncSession,
    gamification: GamificationContainer,
    message_to_edit: Message = None
):
    """Función unificada para obtener y enviar la vista de perfil."""
    try:
        # 1. Obtener datos crudos del perfil
        profile_data = await gamification.user_gamification.get_user_profile(user_id)

        # 2. Construir el texto del perfil con voz de Lucien
        profile_text = _build_lucien_profile_text(profile_data)

        # 3. Construir el menú usando el helper
        # El texto del menú de build_profile_menu es un summary que ignoramos ahora.
        _, keyboard = await build_profile_menu(session, bot, user_id)

        # 4. Enviar o editar el mensaje
        if message_to_edit:
            await message_to_edit.edit_text(profile_text, reply_markup=keyboard, parse_mode="HTML")
        else:
            # Esta lógica es para el comando /profile, donde no hay mensaje que editar.
            # Necesitamos obtener el objeto Message de alguna manera, lo cual no es ideal.
            # Por ahora, el comando /profile no está soportado en la nueva versión.
            # Se asume que el acceso es siempre vía callback.
            # Si se necesita, se debe pasar el `message` original aquí.
            logger.warning("El comando /profile directo no está implementado para enviar un nuevo mensaje.")

    except Exception as e:
        logger.error(f"Error al mostrar el perfil de Lucien: {e}", exc_info=True)
        if message_to_edit:
            await bot.send_message(user_id, Lucien.ERROR_GENERIC, parse_mode="HTML")


@router.callback_query(F.data == "user:profile")
async def show_profile_callback(callback: CallbackQuery, session: AsyncSession, gamification: GamificationContainer):
    """Muestra el perfil de gamificación (callback desde el menú principal)."""
    await _send_profile_view(
        user_id=callback.from_user.id,
        bot=callback.bot,
        session=session,
        gamification=gamification,
        message_to_edit=callback.message
    )
    await callback.answer()

# El comando /profile ya no es necesario si todo el flujo es por botones,
# pero se mantiene por si se usa directamente.
# Para que funcione, necesitaría una forma de obtener el objeto `message` para responder.
# Por simplicidad y siguiendo el flujo de UI, se prioriza el callback.
@router.message(Command("profile"))
@router.message(Command("perfil"))
async def show_profile_command(message: Message, session: AsyncSession, gamification: GamificationContainer):
    """Muestra el perfil de gamificación (comando directo)."""
    # Esta implementación es un hack para poder responder al comando.
    # Lo ideal sería tener una única función que maneje ambos casos de forma más elegante.
    temp_message = await message.answer("Cargando expediente...", parse_mode="HTML")
    await _send_profile_view(
        user_id=message.from_user.id,
        bot=message.bot,
        session=session,
        gamification=gamification,
        message_to_edit=temp_message
    )

