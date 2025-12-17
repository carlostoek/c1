"""
Configuration Wizard - Flujo conversacional para admin.

Permite configurar misiones completas con recompensas/badges
en un solo flujo sin salir del contexto.

FILOSOFÍA: FSM simple con estados mínimos necesarios.
"""
import logging
from aiogram import F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.admin.main import admin_router
from bot.services.container import ServiceContainer
from bot.services.configuration import ConfigurationError
from bot.utils.keyboards import create_inline_keyboard
from bot.database.models import MissionType, ObjectiveType

logger = logging.getLogger(__name__)


# ===== ESTADOS DEL WIZARD =====

class MissionWizard(StatesGroup):
    """
    Estados para configurar misión completa.

    Flujo simple:
    1. Nombre
    2. Descripción
    3. Tipo (diaria/semanal/permanente)
    4. Objetivo (puntos/reacciones/etc)
    5. Valor objetivo
    6. ¿Recompensa? (sí/no)
    7. [Si sí] Badge (nuevo/existente/ninguno)
    8. [Si nuevo] Nombre y emoji de badge
    9. [Opcional] Puntos extra
    10. Preview
    11. Confirmar
    """
    name = State()
    description = State()
    mission_type = State()
    objective_type = State()
    objective_value = State()

    # Recompensa
    wants_reward = State()
    badge_choice = State()        # nuevo/existente/ninguno
    badge_name = State()          # Si nuevo
    badge_emoji = State()         # Si nuevo
    reward_points = State()       # Puntos extra opcionales

    # Final
    preview = State()
    confirm = State()


# ===== INICIO DEL WIZARD =====

@admin_router.callback_query(F.data == "config:mission_create")
async def start_mission_wizard(callback: CallbackQuery, state: FSMContext):
    """
    Inicia wizard de configuración de misión.

    Callback: config:mission_create
    Solo para admins.

    Args:
        callback: Callback query
        state: FSM context
    """
    await state.clear()
    await state.set_state(MissionWizard.name)

    text = (
        "🎯 <b>Configuración de Misión</b>\n\n"
        "Vamos a crear una misión paso a paso.\n"
        "Puedes cancelar en cualquier momento con /cancelar\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "1️⃣ <b>Nombre de la misión:</b>\n"
        "<i>Ejemplo: Primera Centena</i>"
    )

    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@admin_router.message(F.command("cancelar"), StateFilter("*"))
async def cancel_wizard(message: Message, state: FSMContext):
    """
    Cancela wizard en cualquier momento.

    Comando: /cancelar

    Args:
        message: Message
        state: FSM context
    """
    current_state = await state.get_state()
    if current_state and current_state.startswith("MissionWizard"):
        await state.clear()
        await message.answer(
            "❌ Configuración cancelada.\n"
            "Ningún cambio fue guardado."
        )
    else:
        await message.answer("No hay wizard activo en este momento.")


# ===== PASOS DEL WIZARD =====

@admin_router.message(MissionWizard.name)
async def process_mission_name(message: Message, state: FSMContext):
    """Paso 1: Nombre de misión."""
    if not message.text or len(message.text.strip()) < 1:
        await message.answer("⚠️ Por favor ingresa un nombre válido")
        return

    await state.update_data(mission_name=message.text)
    await state.set_state(MissionWizard.description)

    await message.answer(
        "✅ <b>Nombre guardado</b>\n\n"
        "2️⃣ <b>Descripción de la misión:</b>\n"
        "<i>Ejemplo: Alcanza 100 besitos acumulados</i>",
        parse_mode="HTML"
    )


@admin_router.message(MissionWizard.description)
async def process_mission_description(message: Message, state: FSMContext):
    """Paso 2: Descripción."""
    if not message.text or len(message.text.strip()) < 1:
        await message.answer("⚠️ Por favor ingresa una descripción válida")
        return

    await state.update_data(mission_description=message.text)
    await state.set_state(MissionWizard.mission_type)

    buttons = [
        [{"text": "📅 Diaria", "callback_data": "type:daily"}],
        [{"text": "📆 Semanal", "callback_data": "type:weekly"}],
        [{"text": "♾️ Permanente", "callback_data": "type:permanent"}]
    ]

    await message.answer(
        "✅ <b>Descripción guardada</b>\n\n"
        "3️⃣ <b>Tipo de misión:</b>",
        reply_markup=create_inline_keyboard(buttons),
        parse_mode="HTML"
    )


@admin_router.callback_query(F.data.startswith("type:"), MissionWizard.mission_type)
async def process_mission_type(callback: CallbackQuery, state: FSMContext):
    """Paso 3: Tipo de misión."""
    mission_type = callback.data.split(":")[1]
    await state.update_data(mission_type=mission_type)
    await state.set_state(MissionWizard.objective_type)

    type_names = {
        "daily": "Diaria",
        "weekly": "Semanal",
        "permanent": "Permanente"
    }

    buttons = [
        [{"text": "💰 Acumular puntos", "callback_data": "obj:points"}],
        [{"text": "❤️ Número de reacciones", "callback_data": "obj:reactions"}],
        [{"text": "📊 Alcanzar nivel", "callback_data": "obj:level"}]
    ]

    await callback.message.edit_text(
        f"✅ <b>Tipo: {type_names[mission_type]}</b>\n\n"
        "4️⃣ <b>Objetivo de la misión:</b>",
        reply_markup=create_inline_keyboard(buttons),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith("obj:"), MissionWizard.objective_type)
async def process_objective_type(callback: CallbackQuery, state: FSMContext):
    """Paso 4: Tipo de objetivo."""
    obj_type = callback.data.split(":")[1]
    await state.update_data(objective_type=obj_type)
    await state.set_state(MissionWizard.objective_value)

    obj_names = {
        "points": "Acumular puntos",
        "reactions": "Número de reacciones",
        "level": "Alcanzar nivel"
    }

    examples = {
        "points": "Ejemplo: 100",
        "reactions": "Ejemplo: 50",
        "level": "Ejemplo: 5"
    }

    await callback.message.edit_text(
        f"✅ <b>Objetivo: {obj_names[obj_type]}</b>\n\n"
        "5️⃣ <b>¿Cuánto?</b>\n"
        f"<i>{examples[obj_type]}</i>",
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.message(MissionWizard.objective_value)
async def process_objective_value(message: Message, state: FSMContext):
    """Paso 5: Valor del objetivo."""
    try:
        value = int(message.text)
        if value <= 0:
            raise ValueError("Debe ser positivo")
    except ValueError:
        await message.answer("⚠️ Por favor envía un número válido mayor a 0")
        return

    await state.update_data(objective_value=value)
    await state.set_state(MissionWizard.wants_reward)

    buttons = [
        [{"text": "✅ Sí, agregar recompensa", "callback_data": "reward:yes"}],
        [{"text": "❌ No, sin recompensa", "callback_data": "reward:no"}]
    ]

    await message.answer(
        "✅ <b>Objetivo guardado</b>\n\n"
        "6️⃣ <b>¿Agregar recompensa al completar?</b>",
        reply_markup=create_inline_keyboard(buttons),
        parse_mode="HTML"
    )


@admin_router.callback_query(F.data.startswith("reward:"), MissionWizard.wants_reward)
async def process_wants_reward(callback: CallbackQuery, state: FSMContext):
    """Paso 6: ¿Quiere recompensa?"""
    wants = callback.data.split(":")[1] == "yes"

    if not wants:
        # Ir directo a preview
        await state.update_data(has_reward=False)
        await show_preview(callback.message, state)
        await callback.answer()
        return

    await state.update_data(has_reward=True)
    await state.set_state(MissionWizard.badge_choice)

    buttons = [
        [{"text": "🆕 Crear badge nuevo", "callback_data": "badge:new"}],
        [{"text": "⏭️ Sin badge", "callback_data": "badge:none"}]
    ]

    await callback.message.edit_text(
        "✅ <b>Recompensa activada</b>\n\n"
        "7️⃣ <b>Badge para la recompensa:</b>",
        reply_markup=create_inline_keyboard(buttons),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith("badge:"), MissionWizard.badge_choice)
async def process_badge_choice(callback: CallbackQuery, state: FSMContext):
    """Paso 7: Elección de badge."""
    choice = callback.data.split(":")[1]

    if choice == "none":
        # Sin badge, ir a puntos extra
        await state.update_data(badge_choice="none")
        await state.set_state(MissionWizard.reward_points)
        await callback.message.edit_text(
            "✅ <b>Sin badge</b>\n\n"
            "8️⃣ <b>Puntos extra al completar (opcional):</b>\n"
            "<i>Envía 0 si no quieres dar puntos extra</i>",
            parse_mode="HTML"
        )
        await callback.answer()
        return

    # choice == "new"
    await state.update_data(badge_choice="new")
    await state.set_state(MissionWizard.badge_name)
    await callback.message.edit_text(
        "🆕 <b>Nuevo Badge</b>\n\n"
        "Nombre del badge:\n"
        "<i>Ejemplo: Oro</i>",
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.message(MissionWizard.badge_name)
async def process_badge_name(message: Message, state: FSMContext):
    """Paso 8a: Nombre de badge nuevo."""
    if not message.text or len(message.text.strip()) < 1:
        await message.answer("⚠️ Por favor ingresa un nombre válido")
        return

    await state.update_data(badge_name=message.text)
    await state.set_state(MissionWizard.badge_emoji)

    await message.answer(
        "✅ <b>Nombre guardado</b>\n\n"
        "Emoji del badge:\n"
        "<i>Ejemplo: 🏆</i>",
        parse_mode="HTML"
    )


@admin_router.message(MissionWizard.badge_emoji)
async def process_badge_emoji(message: Message, state: FSMContext):
    """Paso 8b: Emoji de badge nuevo."""
    if not message.text or len(message.text.strip()) < 1:
        await message.answer("⚠️ Por favor envía un emoji válido")
        return

    await state.update_data(badge_emoji=message.text)
    await state.set_state(MissionWizard.reward_points)

    await message.answer(
        "✅ <b>Badge configurado</b>\n\n"
        "9️⃣ <b>Puntos extra al completar (opcional):</b>\n"
        "<i>Envía 0 si no quieres dar puntos extra</i>",
        parse_mode="HTML"
    )


@admin_router.message(MissionWizard.reward_points)
async def process_reward_points(message: Message, state: FSMContext):
    """Paso 9: Puntos extra."""
    try:
        points = int(message.text)
        if points < 0:
            raise ValueError("No puede ser negativo")
    except ValueError:
        await message.answer("⚠️ Por favor envía un número válido (0 o mayor)")
        return

    await state.update_data(reward_points=points)

    # Ir a preview
    await show_preview(message, state)


# ===== PREVIEW Y CONFIRMACIÓN =====

async def show_preview(message: Message, state: FSMContext):
    """
    Muestra preview completo de la configuración.

    Args:
        message: Message object
        state: FSM context
    """
    data = await state.get_data()
    await state.set_state(MissionWizard.preview)

    # Construir preview
    preview = "📋 <b>PREVIEW DE CONFIGURACIÓN</b>\n"
    preview += "━━━━━━━━━━━━━━━━━━━━━━\n\n"

    # Misión
    preview += f"🎯 <b>Misión:</b> {data['mission_name']}\n"
    preview += f"📝 {data['mission_description']}\n"

    type_names = {"daily": "Diaria", "weekly": "Semanal", "permanent": "Permanente"}
    preview += f"🔄 Tipo: {type_names.get(data['mission_type'], 'N/A')}\n"

    obj_names = {
        "points": "Acumular puntos",
        "reactions": "Reacciones",
        "level": "Alcanzar nivel"
    }
    preview += (
        f"🎯 Objetivo: {obj_names.get(data['objective_type'], 'N/A')} "
        f"({data['objective_value']})\n\n"
    )

    # Recompensa
    if data.get('has_reward'):
        preview += "🎁 <b>Recompensa:</b>\n"

        if data.get('badge_choice') == 'new':
            preview += (
                f"   🏆 Badge: {data.get('badge_emoji', '❓')} "
                f"{data.get('badge_name', 'N/A')} <i>(nuevo)</i>\n"
            )
        elif data.get('badge_choice') == 'none':
            preview += "   🏆 Sin badge\n"

        points = data.get('reward_points', 0)
        if points > 0:
            preview += f"   💰 Puntos extra: +{points} 💋\n"
    else:
        preview += "🎁 Sin recompensa\n"

    preview += "\n━━━━━━━━━━━━━━━━━━━━━━\n"
    preview += "<b>¿Todo correcto?</b>"

    buttons = [
        [
            {"text": "✅ Confirmar", "callback_data": "confirm:yes"},
            {"text": "❌ Cancelar", "callback_data": "confirm:no"}
        ]
    ]

    await message.answer(
        preview,
        reply_markup=create_inline_keyboard(buttons),
        parse_mode="HTML"
    )


@admin_router.callback_query(F.data.startswith("confirm:"), MissionWizard.preview)
async def process_confirmation(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """
    Confirma y crea todo en una transacción.

    Args:
        callback: Callback query
        state: FSM context
        session: DB session
    """
    choice = callback.data.split(":")[1]

    if choice == "no":
        await state.clear()
        await callback.message.edit_text("❌ Configuración cancelada.")
        await callback.answer()
        return

    # Confirmar - Crear todo
    data = await state.get_data()

    try:
        container = ServiceContainer(session, callback.bot)

        # Preparar datos para ConfigurationService
        mission_data = {
            "name": data["mission_name"],
            "description": data["mission_description"],
            "icon": "🎯",
            "mission_type": data["mission_type"],
            "objective_type": data["objective_type"],
            "objective_value": data["objective_value"]
        }

        reward_data = None
        badge_data = None

        if data.get('has_reward'):
            reward_data = {
                "name": f"Recompensa: {data['mission_name']}",
                "description": f"Recompensa por completar: {data['mission_name']}",
                "icon": "🎁",
                "reward_type": "badge" if data.get('badge_choice') == 'new' else "points",
                "cost": 0,
                "limit_type": "once",
                "points_amount": data.get('reward_points', 0)
            }

            if data.get('badge_choice') == 'new':
                badge_data = {
                    "name": data.get('badge_name'),
                    "emoji": data.get('badge_emoji'),
                    "description": f"Badge de {data['mission_name']}",
                    "rarity": "rare"
                }

        # CREAR TODO
        result = await container.configuration.create_mission_complete(
            mission_data=mission_data,
            reward_data=reward_data,
            badge_data=badge_data
        )

        # Mensaje de éxito
        success = "✅ <b>¡Configuración Completada!</b>\n\n"
        success += f"🎯 Misión creada: {result['mission'].name}\n"

        if 'reward' in result:
            success += f"🎁 Recompensa creada\n"

        if 'badge' in result:
            success += f"🏆 Badge creado: {result['badge'].display_name}\n"

        success += "\n✨ Todo vinculado correctamente"

        await callback.message.edit_text(success, parse_mode="HTML")
        await state.clear()
        logger.info(
            f"✅ Misión '{result['mission'].name}' creada "
            f"por admin {callback.from_user.id}"
        )

    except ConfigurationError as e:
        await callback.answer(
            f"❌ Error: {str(e)}",
            show_alert=True
        )
        logger.error(f"ConfigurationError: {e}")

    except Exception as e:
        await callback.message.edit_text(
            f"❌ <b>Error inesperado</b>\n\n"
            f"<code>{str(e)}</code>\n\n"
            f"Por favor intenta de nuevo.",
            parse_mode="HTML"
        )
        logger.error(f"Error en process_confirmation: {e}", exc_info=True)

    finally:
        await callback.answer()
