"""
Reactions Handlers - Procesa reacciones de usuarios en publicaciones.

Handlers:
- callback_react_to_publication: Procesa click en botón de reacción
"""
import logging
from aiogram import F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.user.main import user_router
from bot.services.container import ServiceContainer

logger = logging.getLogger(__name__)


@user_router.callback_query(F.data.startswith("react:"))
async def callback_react_to_publication(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
):
    """
    Procesa el click de un usuario en un botón de reacción.

    Formato callback: react:{publication_id}:{emoji_index}

    Flujo:
    1. Extraer publication_id y emoji del callback data
    2. Verificar si el usuario ya reaccionó (evitar duplicado)
    3. Si no reaccionó:
       - Otorgar puntos con multiplicador de racha
       - Actualizar racha del usuario
       - Crear registro de reacción
    4. Actualizar botones con nuevos conteos
    5. Responder con puntos ganados + info de racha

    Args:
        callback: Callback query del click
        session: Sesión de BD
        state: FSM context
    """
    user_id = callback.from_user.id
    callback_data = callback.data

    logger.debug(f"👆 User {user_id} clickeó en reacción: {callback_data}")

    try:
        container = ServiceContainer(session, callback.bot)

        # Extraer datos del callback
        # Formato: react:{publication_id}:{emoji_index}
        parts = callback_data.split(":")
        if len(parts) != 3 or parts[0] != "react":
            await callback.answer("❌ Formato inválido", show_alert=True)
            return

        publication_id = int(parts[1])
        emoji_index = int(parts[2])

        # Obtener publicación
        publication = await container.reactions.get_publication_by_id(publication_id)
        if publication is None:
            await callback.answer("❌ Publicación no encontrada", show_alert=True)
            return

        if not publication.active:
            await callback.answer("❌ Esta publicación ya no acepta reacciones", show_alert=True)
            return

        # Obtener emoji del índice
        emojis = publication.reaction_buttons
        if emoji_index >= len(emojis):
            await callback.answer("❌ Índice de emoji inválido", show_alert=True)
            return

        emoji = emojis[emoji_index]

        # Verificar si ya reaccionó
        already_reacted = await container.reactions.has_reacted(user_id, publication_id)

        if already_reacted:
            # Ya reaccionó - informar al usuario
            await callback.answer(
                f"⚠️ Ya has reaccionado a esta publicación con {emoji}",
                show_alert=True
            )
            return

        # Obtener configuración para calcular puntos
        config = await container.points._get_config()
        base_points = config.points_per_reaction

        # Calcular racha actual para multiplicador
        streak = await container.streak.calculate_streak(user_id, publication.channel_id)
        multiplier = await container.streak.get_streak_multiplier(streak)

        # Calcular puntos otorgados
        points_awarded = int(base_points * multiplier)

        # Añadir reacción
        success, msg, reaction = await container.reactions.add_reaction(
            user_id=user_id,
            publication_id=publication_id,
            emoji=emoji,
            points_awarded=points_awarded
        )

        if not success:
            await callback.answer(f"❌ {msg}", show_alert=True)
            return

        # Actualizar racha después de la reacción
        new_streak, is_record = await container.streak.update_streak_after_reaction(
            user_id=user_id,
            channel_id=publication.channel_id
        )

        # Obtener nuevos conteos para actualizar keyboard
        counts = await container.reactions.get_reaction_counts(publication_id)
        new_keyboard = container.reactions.generate_reaction_keyboard(
            publication_id=publication_id,
            emojis=emojis,
            counts=counts
        )

        # Actualizar mensaje con nuevos conteos
        try:
            await callback.message.edit_reply_markup(reply_markup=new_keyboard)
        except Exception as e:
            logger.warning(f"⚠️ No se pudo actualizar keyboard: {e}")

        # Respuesta al usuario
        if multiplier > 1.0:
            streak_info = f" | 🔥 Racha: {new_streak} (x{multiplier})"
        else:
            streak_info = f" | 🔥 Racha: {new_streak}"

        if is_record:
            record_msg = " | 🏆 ¡NUEVO RÉCORD!"
        else:
            record_msg = ""

        await callback.answer(
            f"✅ +{points_awarded} puntos{streak_info}{record_msg}",
            show_alert=False  # Solo toast, no alerta
        )

        logger.info(
            f"✅ User {user_id} reaccionó con {emoji}: "
            f"+{points_awarded} pts, racha={new_streak}"
        )

        # Verificar si completó alguna misión
        # TODO: Implementar en SPRINT 4
        # await container.missions.update_progress(
        #     user_id=user_id,
        #     mission_type=MissionType.REACT_N_TIMES,
        #     increment=1
        # )

    except ValueError as e:
        logger.error(f"❌ Error procesando reacción: {e}")
        await callback.answer("❌ Error al procesar reacción", show_alert=True)

    except Exception as e:
        logger.error(f"❌ Error inesperado en reacción: {e}", exc_info=True)
        await callback.answer("❌ Error inesperado", show_alert=True)
