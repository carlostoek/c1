"""Handler de configuración de gamificación para administradores.

Responsabilidades:
- Menú principal de configuración de gamificación
- CRUD de reacciones (catálogo)
- Configuración global del sistema
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares import DatabaseMiddleware
from bot.filters.admin import IsAdmin
from bot.gamification.services.container import GamificationContainer
from bot.gamification.states.admin import ReactionConfigStates
from bot.utils.keyboards import create_inline_keyboard

logger = logging.getLogger(__name__)

# Router para configuración de gamificación
router = Router(name="gamification_config")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())
router.message.middleware(DatabaseMiddleware())
router.callback_query.middleware(DatabaseMiddleware())


# ========================================
# MENÚ PRINCIPAL DE CONFIGURACIÓN
# ========================================

@router.callback_query(F.data == "gamif:admin:config")
async def show_config_menu(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Muestra menú principal de configuración de gamificación.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    logger.info(f"⚙️ Usuario {callback.from_user.id} abriendo configuración de gamificación")

    container = GamificationContainer(session, callback.bot)

    # Obtener estadísticas básicas
    all_reactions = await container.reaction.get_all_reactions()
    active_reactions = [r for r in all_reactions if r.active]

    # Obtener configuración de regalo diario
    from bot.gamification.database.models import GamificationConfig as DBConfig
    config = await session.get(DBConfig, 1)
    if config:
        daily_gift_status = "✅ Activado" if config.daily_gift_enabled else "❌ Desactivado"
        daily_gift_besitos = config.daily_gift_besitos
    else:
        daily_gift_status = "❓ No configurado"
        daily_gift_besitos = 10

    text = f"""⚙️ <b>Configuración de Gamificación</b>

📊 <b>Estado del Sistema:</b>
• Reacciones configuradas: {len(all_reactions)}
• Reacciones activas: {len(active_reactions)}
• Regalo diario: {daily_gift_status} ({daily_gift_besitos} besitos)

<b>Opciones disponibles:</b>"""

    keyboard = [
        [{"text": "🎁 Configurar Regalo Diario", "callback_data": "gamif:config:daily_gift"}],
        [{"text": "🎮 Gestionar Reacciones", "callback_data": "gamif:config:reactions"}],
        [{"text": "🔙 Volver al Menú", "callback_data": "gamif:menu"}]
    ]

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(keyboard),
        parse_mode="HTML"
    )
    await callback.answer()


# ========================================
# GESTIÓN DE REACCIONES
# ========================================

@router.callback_query(F.data == "gamif:config:reactions")
async def show_reactions_list(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Muestra lista de reacciones configuradas con opciones CRUD.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    logger.info(f"📋 Usuario {callback.from_user.id} viendo lista de reacciones")

    container = GamificationContainer(session, callback.bot)
    reactions = await container.reaction.get_all_reactions()

    if not reactions:
        text = """🎮 <b>Gestión de Reacciones</b>

⚠️ No hay reacciones configuradas.

Las reacciones son los emojis que aparecen como botones en los mensajes de broadcast y otorgan besitos a los usuarios.

<b>Ejemplo:</b>
❤️ → 10 besitos
🔥 → 15 besitos
👍 → 5 besitos"""
    else:
        text = "🎮 <b>Gestión de Reacciones</b>\n\n"
        text += "<b>Reacciones Configuradas:</b>\n\n"

        for reaction in reactions:
            status = "✅" if reaction.active else "❌"
            btn_emoji = reaction.button_emoji or reaction.emoji
            btn_label = reaction.button_label or f"{reaction.besitos_value} besitos"
            text += f"{status} {reaction.emoji} → {reaction.besitos_value} besitos\n"
            text += f"   Botón: {btn_emoji} {btn_label}\n\n"

    keyboard = []

    # Botones de reacciones individuales
    for reaction in reactions:
        status_emoji = "✅" if reaction.active else "❌"
        keyboard.append([{
            "text": f"{status_emoji} {reaction.emoji} ({reaction.besitos_value} besitos)",
            "callback_data": f"gamif:reaction:edit:{reaction.id}"
        }])

    # Botones de acciones
    keyboard.append([{"text": "➕ Crear Nueva Reacción", "callback_data": "gamif:reaction:create"}])
    keyboard.append([{"text": "🔙 Volver", "callback_data": "gamif:admin:config"}])

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(keyboard),
        parse_mode="HTML"
    )
    await callback.answer()


# ========================================
# CREAR NUEVA REACCIÓN
# ========================================

@router.callback_query(F.data == "gamif:reaction:create")
async def start_create_reaction(
    callback: CallbackQuery,
    state: FSMContext
):
    """Inicia wizard de creación de reacción.

    Args:
        callback: Callback query
        state: FSM context
    """
    logger.info(f"➕ Usuario {callback.from_user.id} creando nueva reacción")

    await state.set_state(ReactionConfigStates.waiting_for_emoji)

    text = """➕ <b>Crear Nueva Reacción</b>

<b>Paso 1/3:</b> Envía el emoji que quieres usar como reacción.

<b>Ejemplo:</b> ❤️ 🔥 👍 ⭐ 💯

⚠️ Solo se acepta UN emoji por reacción."""

    keyboard = [[{"text": "❌ Cancelar", "callback_data": "gamif:reaction:cancel"}]]

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(keyboard),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(StateFilter(ReactionConfigStates.waiting_for_emoji))
async def process_emoji_input(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa el emoji ingresado y pide valor de besitos.

    Args:
        message: Mensaje del usuario
        state: FSM context
        session: Sesión de BD
    """
    emoji = message.text.strip()

    # Validar que sea un emoji válido
    if len(emoji) > 10 or len(emoji) == 0:
        await message.answer(
            "❌ Por favor envía un emoji válido.\n\n"
            "Ejemplo: ❤️ 🔥 👍",
            parse_mode="HTML"
        )
        return

    # Verificar que no exista ya
    container = GamificationContainer(session, message.bot)
    existing = await container.reaction.get_reaction_by_emoji(emoji)

    if existing:
        await message.answer(
            f"⚠️ El emoji {emoji} ya está configurado.\n\n"
            f"Valor actual: {existing.besitos_value} besitos\n"
            f"Estado: {'Activo' if existing.active else 'Inactivo'}\n\n"
            "Usa el menú para editar la reacción existente.",
            parse_mode="HTML"
        )
        return

    # Guardar emoji y pedir besitos
    await state.update_data(emoji=emoji)
    await state.set_state(ReactionConfigStates.waiting_for_besitos)

    text = f"""➕ <b>Crear Nueva Reacción</b>

<b>Paso 2/3:</b> ¿Cuántos besitos otorgará {emoji}?

Envía un número entre 1 y 100.

<b>Sugerencias:</b>
• 5-10 besitos: Reacciones comunes
• 15-25 besitos: Reacciones especiales
• 50-100 besitos: Reacciones premium"""

    keyboard = [[{"text": "❌ Cancelar", "callback_data": "gamif:reaction:cancel"}]]

    await message.answer(
        text=text,
        reply_markup=create_inline_keyboard(keyboard),
        parse_mode="HTML"
    )


@router.message(StateFilter(ReactionConfigStates.waiting_for_besitos))
async def process_besitos_input(
    message: Message,
    state: FSMContext
):
    """Procesa el valor de besitos y muestra confirmación.

    Args:
        message: Mensaje del usuario
        state: FSM context
    """
    try:
        besitos = int(message.text.strip())
        if besitos < 1 or besitos > 100:
            raise ValueError("Fuera de rango")
    except ValueError:
        await message.answer(
            "❌ Por favor envía un número válido entre 1 y 100.",
            parse_mode="HTML"
        )
        return

    # Guardar valor y mostrar confirmación
    data = await state.get_data()
    emoji = data["emoji"]

    await state.update_data(besitos_value=besitos)
    await state.set_state(ReactionConfigStates.confirm_create)

    text = f"""➕ <b>Crear Nueva Reacción</b>

<b>Paso 3/3:</b> Confirma los datos de la nueva reacción:

🎯 <b>Emoji:</b> {emoji}
💰 <b>Besitos:</b> {besitos}
📊 <b>Estado:</b> Activa

¿Deseas crear esta reacción?"""

    keyboard = [
        [
            {"text": "✅ Confirmar", "callback_data": "gamif:reaction:confirm_create"},
            {"text": "❌ Cancelar", "callback_data": "gamif:reaction:cancel"}
        ]
    ]

    await message.answer(
        text=text,
        reply_markup=create_inline_keyboard(keyboard),
        parse_mode="HTML"
    )


@router.callback_query(
    StateFilter(ReactionConfigStates.confirm_create),
    F.data == "gamif:reaction:confirm_create"
)
async def confirm_create_reaction(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Crea la reacción en BD y muestra confirmación.

    Args:
        callback: Callback query
        state: FSM context
        session: Sesión de BD
    """
    data = await state.get_data()
    emoji = data["emoji"]
    besitos_value = data["besitos_value"]

    container = GamificationContainer(session, callback.bot)

    try:
        reaction = await container.reaction.create_reaction(
            emoji=emoji,
            besitos_value=besitos_value
        )

        logger.info(
            f"✅ Reacción creada: {emoji} → {besitos_value} besitos "
            f"(ID: {reaction.id}) por usuario {callback.from_user.id}"
        )

        text = f"""✅ <b>Reacción Creada Exitosamente</b>

🎯 {emoji} → {besitos_value} besitos

La reacción ya está disponible para usar en broadcasts.

Los usuarios ganarán <b>{besitos_value} besitos</b> cada vez que presionen el botón {emoji}."""

        keyboard = [
            [{"text": "➕ Crear Otra", "callback_data": "gamif:reaction:create"}],
            [{"text": "📋 Ver Todas", "callback_data": "gamif:config:reactions"}],
            [{"text": "🔙 Menú Config", "callback_data": "gamif:admin:config"}]
        ]

        await callback.message.edit_text(
            text=text,
            reply_markup=create_inline_keyboard(keyboard),
            parse_mode="HTML"
        )
        await callback.answer("✅ Reacción creada")

    except Exception as e:
        logger.error(f"Error creando reacción: {e}", exc_info=True)
        await callback.answer(
            "❌ Error al crear la reacción. Intenta nuevamente.",
            show_alert=True
        )

    finally:
        await state.clear()


# ========================================
# EDITAR REACCIÓN
# ========================================

@router.callback_query(F.data.startswith("gamif:reaction:edit:"))
async def show_reaction_edit_menu(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Muestra menú de edición de una reacción específica.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    reaction_id = int(callback.data.split(":")[-1])

    logger.info(f"✏️ Usuario {callback.from_user.id} editando reacción {reaction_id}")

    container = GamificationContainer(session, callback.bot)
    reaction = await container.reaction.get_reaction_by_id(reaction_id)

    if not reaction:
        await callback.answer("❌ Reacción no encontrada", show_alert=True)
        return

    status_text = "✅ Activa" if reaction.active else "❌ Inactiva"
    btn_emoji = reaction.button_emoji or reaction.emoji
    btn_label = reaction.button_label or f"{reaction.besitos_value} besitos"

    text = f"""✏️ <b>Editar Reacción</b>

🎯 <b>Emoji:</b> {reaction.emoji}
💰 <b>Besitos:</b> {reaction.besitos_value}
📊 <b>Estado:</b> {status_text}

<b>Configuración de Botón:</b>
🔹 Emoji del botón: {btn_emoji}
🔹 Etiqueta: {btn_label}

<b>¿Qué deseas hacer?</b>"""

    keyboard = []

    # Opciones de edición
    keyboard.append([{"text": "💰 Cambiar Besitos", "callback_data": f"gamif:reaction:edit_besitos:{reaction_id}"}])
    keyboard.append([{"text": "🎨 Cambiar Emoji Botón", "callback_data": f"gamif:reaction:edit_btn_emoji:{reaction_id}"}])
    keyboard.append([{"text": "🏷️ Cambiar Etiqueta", "callback_data": f"gamif:reaction:edit_btn_label:{reaction_id}"}])

    # Toggle activo/inactivo
    if reaction.active:
        keyboard.append([{"text": "🔴 Desactivar", "callback_data": f"gamif:reaction:deactivate:{reaction_id}"}])
    else:
        keyboard.append([{"text": "🟢 Activar", "callback_data": f"gamif:reaction:activate:{reaction_id}"}])

    # Eliminar
    keyboard.append([{"text": "🗑️ Eliminar", "callback_data": f"gamif:reaction:delete_confirm:{reaction_id}"}])

    # Volver
    keyboard.append([{"text": "🔙 Volver", "callback_data": "gamif:config:reactions"}])

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(keyboard),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:reaction:edit_besitos:"))
async def start_edit_besitos(
    callback: CallbackQuery,
    state: FSMContext
):
    """Inicia wizard para cambiar besitos de una reacción.

    Args:
        callback: Callback query
        state: FSM context
    """
    reaction_id = int(callback.data.split(":")[-1])

    await state.update_data(editing_reaction_id=reaction_id)
    await state.set_state(ReactionConfigStates.waiting_for_edit_besitos)

    text = """💰 <b>Cambiar Valor de Besitos</b>

Envía el nuevo valor de besitos (1-100).

<b>Sugerencias:</b>
• 5-10: Reacciones comunes
• 15-25: Reacciones especiales
• 50-100: Reacciones premium"""

    keyboard = [[{"text": "❌ Cancelar", "callback_data": "gamif:reaction:cancel"}]]

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(keyboard),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(StateFilter(ReactionConfigStates.waiting_for_edit_besitos))
async def process_edit_besitos(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa el nuevo valor de besitos y actualiza la reacción.

    Args:
        message: Mensaje del usuario
        state: FSM context
        session: Sesión de BD
    """
    try:
        new_besitos = int(message.text.strip())
        if new_besitos < 1 or new_besitos > 100:
            raise ValueError("Fuera de rango")
    except ValueError:
        await message.answer(
            "❌ Por favor envía un número válido entre 1 y 100.",
            parse_mode="HTML"
        )
        return

    data = await state.get_data()
    reaction_id = data["editing_reaction_id"]

    container = GamificationContainer(session, message.bot)

    try:
        reaction = await container.reaction.update_reaction(
            reaction_id=reaction_id,
            besitos_value=new_besitos
        )

        if reaction:
            logger.info(
                f"✅ Reacción {reaction_id} actualizada: {reaction.emoji} → "
                f"{new_besitos} besitos por usuario {message.from_user.id}"
            )

            text = f"""✅ <b>Reacción Actualizada</b>

🎯 {reaction.emoji}
💰 Nuevo valor: <b>{new_besitos} besitos</b>

Los cambios se aplicarán en los próximos broadcasts."""

            keyboard = [
                [{"text": "📋 Ver Todas", "callback_data": "gamif:config:reactions"}],
                [{"text": "🔙 Menú Config", "callback_data": "gamif:admin:config"}]
            ]

            await message.answer(
                text=text,
                reply_markup=create_inline_keyboard(keyboard),
                parse_mode="HTML"
            )
        else:
            await message.answer("❌ Error: Reacción no encontrada")

    except Exception as e:
        logger.error(f"Error actualizando reacción: {e}", exc_info=True)
        await message.answer("❌ Error al actualizar la reacción")

    finally:
        await state.clear()


# ========================================
# ACTIVAR/DESACTIVAR REACCIÓN
# ========================================

@router.callback_query(F.data.startswith("gamif:reaction:activate:"))
async def activate_reaction(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Activa una reacción desactivada.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    reaction_id = int(callback.data.split(":")[-1])

    container = GamificationContainer(session, callback.bot)
    reaction = await container.reaction.update_reaction(
        reaction_id=reaction_id,
        active=True
    )

    if reaction:
        logger.info(f"✅ Reacción {reaction_id} activada por usuario {callback.from_user.id}")
        await callback.answer(f"✅ {reaction.emoji} activada")

        # Volver a mostrar menú de edición
        await show_reaction_edit_menu(callback, session)
    else:
        await callback.answer("❌ Error al activar", show_alert=True)


@router.callback_query(F.data.startswith("gamif:reaction:deactivate:"))
async def deactivate_reaction(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Desactiva una reacción activa.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    reaction_id = int(callback.data.split(":")[-1])

    container = GamificationContainer(session, callback.bot)
    reaction = await container.reaction.update_reaction(
        reaction_id=reaction_id,
        active=False
    )

    if reaction:
        logger.info(f"🔴 Reacción {reaction_id} desactivada por usuario {callback.from_user.id}")
        await callback.answer(f"🔴 {reaction.emoji} desactivada")

        # Volver a mostrar menú de edición
        await show_reaction_edit_menu(callback, session)
    else:
        await callback.answer("❌ Error al desactivar", show_alert=True)


# ========================================
# ELIMINAR REACCIÓN
# ========================================

@router.callback_query(F.data.startswith("gamif:reaction:delete_confirm:"))
async def confirm_delete_reaction(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Muestra confirmación antes de eliminar una reacción.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    reaction_id = int(callback.data.split(":")[-1])

    container = GamificationContainer(session, callback.bot)
    reaction = await container.reaction.get_reaction_by_id(reaction_id)

    if not reaction:
        await callback.answer("❌ Reacción no encontrada", show_alert=True)
        return

    text = f"""⚠️ <b>Confirmar Eliminación</b>

¿Estás seguro de eliminar la reacción {reaction.emoji}?

<b>Valor:</b> {reaction.besitos_value} besitos

⚠️ <b>Advertencia:</b> Esta acción no se puede deshacer.
Los datos históricos de reacciones se mantendrán, pero esta reacción
no estará disponible para nuevos broadcasts."""

    keyboard = [
        [
            {"text": "✅ Sí, Eliminar", "callback_data": f"gamif:reaction:delete:{reaction_id}"},
            {"text": "❌ Cancelar", "callback_data": f"gamif:reaction:edit:{reaction_id}"}
        ]
    ]

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(keyboard),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:reaction:delete:"))
async def delete_reaction(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Elimina la reacción de la base de datos.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    reaction_id = int(callback.data.split(":")[-1])

    container = GamificationContainer(session, callback.bot)
    success = await container.reaction.delete_reaction(reaction_id)

    if success:
        logger.info(f"🗑️ Reacción {reaction_id} eliminada por usuario {callback.from_user.id}")

        text = """✅ <b>Reacción Eliminada</b>

La reacción ha sido eliminada del catálogo.

Ya no estará disponible para nuevos broadcasts."""

        keyboard = [
            [{"text": "📋 Ver Todas", "callback_data": "gamif:config:reactions"}],
            [{"text": "🔙 Menú Config", "callback_data": "gamif:admin:config"}]
        ]

        await callback.message.edit_text(
            text=text,
            reply_markup=create_inline_keyboard(keyboard),
            parse_mode="HTML"
        )
        await callback.answer("✅ Reacción eliminada")
    else:
        await callback.answer("❌ Error al eliminar", show_alert=True)


# ========================================
# CANCELAR WIZARD
# ========================================

@router.callback_query(F.data == "gamif:reaction:cancel")
async def cancel_reaction_wizard(
    callback: CallbackQuery,
    state: FSMContext
):
    """Cancela el wizard de reacción y vuelve al menú.

    Args:
        callback: Callback query
        state: FSM context
    """
    await state.clear()

    text = "❌ Operación cancelada."

    keyboard = [
        [{"text": "📋 Ver Reacciones", "callback_data": "gamif:config:reactions"}],
        [{"text": "🔙 Menú Config", "callback_data": "gamif:admin:config"}]
    ]

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(keyboard),
        parse_mode="HTML"
    )
    await callback.answer()


# ========================================
# CONFIGURACIÓN DE REGALO DIARIO
# ========================================

# (El código se agregará en los siguientes pasos)
