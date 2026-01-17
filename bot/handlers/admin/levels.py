"""
Levels Admin Handler - Gestión de niveles de gamificación.

Handlers:
- Menú de gestión de niveles
- Crear nuevo nivel (FSM)
- Ver lista de niveles
- Activar/desactivar niveles
"""
import logging
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.admin.main import admin_router
from bot.states.admin import LevelManagementStates
from bot.services.container import ServiceContainer
from bot.utils.keyboards import create_inline_keyboard

logger = logging.getLogger(__name__)


def create_levels_menu_keyboard() -> InlineKeyboardMarkup:
    """Crea keyboard del menú de gestión de niveles."""
    builder = InlineKeyboardBuilder()

    # Gestión
    builder.row(
        InlineKeyboardButton(text="➕ Crear Nivel", callback_data="admin:levels:create"),
        InlineKeyboardButton(text="📋 Ver Niveles", callback_data="admin:levels:list")
    )

    # Volver
    builder.row(
        InlineKeyboardButton(text="🔙 Volver a Gamificación", callback_data="admin:gamification")
    )

    return builder.as_markup()


@admin_router.callback_query(F.data == "admin:gamification:levels")
async def callback_levels_menu(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Muestra el menú de gestión de niveles.

    Opciones:
    - Crear nuevo nivel
    - Ver lista de niveles existentes
    """
    logger.debug("🏆 Admin abriendo menú de niveles")

    container = ServiceContainer(session, callback.bot)

    # Obtener niveles activos
    levels = await container.levels.get_all_levels()
    active_count = len(levels)

    text = (
        f"🏆 <b>Gestión de Niveles</b>\n\n"
        f"Niveles activos: {active_count}\n\n"
        f"Selecciona una opción:"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=create_levels_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.callback_query(F.data == "admin:levels:create")
async def callback_create_level_start(
    callback: CallbackQuery,
    state: FSMContext
):
    """Inicia el flujo para crear un nivel."""
    await state.set_state(LevelManagementStates.waiting_for_name)

    text = (
        "➕ <b>Crear Nuevo Nivel</b>\n\n"
        "Envía el <b>nombre</b> del nivel (máx. 100 caracteres).\n\n"
        "<b>Ejemplo:</b> <code>Nivel 1 - Principiante</code>"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard([
            [{"text": "❌ Cancelar", "callback_data": "admin:levels"}]
        ]),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.message(LevelManagementStates.waiting_for_name)
async def process_level_name(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa el nombre del nivel."""
    name = message.text.strip()

    if len(name) > 100:
        await message.answer(
            "❌ <b>Nombre muy largo</b>\n\n"
            "Máximo 100 caracteres. Intenta nuevamente.",
            parse_mode="HTML"
        )
        return

    # Guardar nombre y pedir puntos mínimos
    await state.update_data({"level_name": name})
    await state.set_state(LevelManagementStates.waiting_for_min_points)

    text = (
        f"✅ Nombre: <code>{name}</code>\n\n"
        "Envía los <b>puntos mínimos</b> requeridos para este nivel.\n\n"
        "<b>Ejemplo:</b> <code>100</code>\n\n"
        "<i>Los usuarios alcanzarán este nivel cuando acumulen "
        "esta cantidad de puntos o más.</i>"
    )

    await message.answer(
        text=text,
        reply_markup=create_inline_keyboard([
            [{"text": "❌ Cancelar", "callback_data": "admin:levels"}]
        ]),
        parse_mode="HTML"
    )


@admin_router.message(LevelManagementStates.waiting_for_min_points)
async def process_level_min_points(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa los puntos mínimos y pide color."""
    points_str = message.text.strip()

    # Validar que sea un número
    try:
        min_points = int(points_str)
    except ValueError:
        await message.answer(
            "❌ <b>Valor inválido</b>\n\n"
            "Debes enviar un número entero. Intenta nuevamente.",
            parse_mode="HTML"
        )
        return

    # Validar rango
    if min_points < 0:
        await message.answer(
            "❌ <b>Valor inválido</b>\n\n"
            "Los puntos mínimos deben ser >= 0. Intenta nuevamente.",
            parse_mode="HTML"
        )
        return

    if min_points > 1000000:
        await message.answer(
            "❌ <b>Valor muy alto</b>\n\n"
            "Máximo 1,000,000 de puntos. Intenta nuevamente.",
            parse_mode="HTML"
        )
        return

    # Guardar puntos y pedir color
    await state.update_data({"min_points": min_points})
    await state.set_state(LevelManagementStates.waiting_for_color)

    data = await state.get_data()

    text = (
        f"✅ Nombre: <code>{data['level_name']}</code>\n"
        f"✅ Puntos mínimos: {min_points:,}\n\n"
        "Envía el <b>color</b> del nivel (formato HEX).\n\n"
        "<b>Ejemplos:</b>\n"
        "<code>#FF5733</code> (rojo)\n"
        "<code>#33FF57</code> (verde)\n"
        "<code>#3357FF</code> (azul)\n\n"
        "<i>O envía cualquier texto para usar el color por defecto.</i>"
    )

    await message.answer(
        text=text,
        reply_markup=create_inline_keyboard([
            [{"text": "🎨 Usar color por defecto", "callback_data": "admin:levels:color:default"}],
            [{"text": "❌ Cancelar", "callback_data": "admin:levels"}]
        ]),
        parse_mode="HTML"
    )


@admin_router.message(LevelManagementStates.waiting_for_color)
async def process_level_color(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa el color y crea el nivel."""
    color = message.text.strip()

    # Validar formato HEX (básico)
    if color.startswith("#") and len(color) == 7:
        # Usar color proporcionado
        pass
    else:
        # Usar color por defecto
        color = "#00BCD4"  # Cyan

    # Continuar con creación
    await _create_level_from_fsm(state, session, message, message.from_user.id, color)


@admin_router.callback_query(F.data == "admin:levels:color:default")
async def process_level_color_default(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Usa color por defecto y crea el nivel."""
    default_color = "#00BCD4"  # Cyan
    await _create_level_from_fsm(state, session, callback, callback.from_user.id, default_color)


async def _create_level_from_fsm(
    state: FSMContext,
    session: AsyncSession,
    source: CallbackQuery or Message,
    admin_id: int,
    color: str
):
    """Helper para crear nivel desde datos del FSM."""
    # Obtener datos del FSM
    data = await state.get_data()

    # Verificar si ya existe un nivel con esos puntos mínimos
    container = ServiceContainer(session, source.bot if hasattr(source, 'bot') else source.message.bot)
    all_levels = await container.levels.get_all_levels()

    for level in all_levels:
        if level.min_points_required == data["min_points"]:
            if hasattr(source, 'answer'):
                await source.answer(
                    f"⚠️ Ya existe un nivel con {data['min_points']} puntos mínimos",
                    show_alert=True
                )
            else:
                await source.message.edit_text(
                    text=f"⚠️ Ya existe un nivel con {data['min_points']} puntos mínimos",
                    reply_markup=create_levels_menu_keyboard()
                )
            return

    # Crear nivel
    from bot.database.gamification_models import UserLevel
    from datetime import datetime

    level = UserLevel(
        name=data["level_name"],
        min_points_required=data["min_points"],
        color=color,
        active=True,
        created_at=datetime.utcnow(),
        created_by=admin_id
    )

    session.add(level)
    await session.commit()

    logger.info(
        f"🏆 Nivel creado: {level.name} ({level.min_points_required:,} pts, color: {level.color}, "
        f"by: {admin_id})"
    )

    if hasattr(source, 'answer'):
        await source.answer(
            f"✅ Nivel creado exitosamente",
            show_alert=True
        )

    text = (
        f"✅ <b>Nivel Creado</b>\n\n"
        f"🏆 <b>{level.name}</b>\n"
        f"📊 Puntos mínimos: {level.min_points_required:,}\n"
        f"🎨 Color: {level.color}\n\n"
        f"Los usuarios alcanzarán este nivel automáticamente "
        f"cuando acumulen {level.min_points_required:,} puntos o más."
    )

    if hasattr(source, 'message'):
        await source.message.edit_text(
            text=text,
            reply_markup=create_levels_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        await source.edit_text(
            text=text,
            reply_markup=create_levels_menu_keyboard(),
            parse_mode="HTML"
        )

    await state.clear()


@admin_router.callback_query(F.data == "admin:levels:list")
async def callback_list_levels(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Muestra lista de niveles existentes."""
    container = ServiceContainer(session, callback.bot)

    # Obtener todos los niveles (ordenados por puntos)
    levels = await container.levels.get_all_levels()

    if not levels:
        await callback.answer(
            "No hay niveles creados",
            show_alert=True
        )
        return

    # Crear keyboard con niveles
    keyboard_buttons = []

    for level in levels:
        status = "✅" if level.active else "❌"
        keyboard_buttons.append([{
            "text": f"{status} {level.name} ({level.min_points_required:,} pts)",
            "callback_data": f"admin:levels:view:{level.id}"
        }])

    keyboard_buttons.append([{
        "text": "🔙 Volver a Niveles",
        "callback_data": "admin:levels"
    }])

    text = (
        f"📋 <b>Niveles Existentes</b>\n\n"
        f"Total: {len(levels)} niveles (ordenados por puntos)\n"
        f"Selecciona un nivel para gestionarlo:"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(keyboard_buttons),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith("admin:levels:view:"))
async def callback_view_level(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Muestra detalles de un nivel y permite activar/desactivar."""
    level_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    level = await container.levels.get_level(level_id)

    if level is None:
        await callback.answer("Nivel no encontrado", show_alert=True)
        return

    status_text = "✅ Activo" if level.active else "❌ Inactivo"
    action = "Desactivar" if level.active else "Activar"

    text = (
        f"🏆 <b>{level.name}</b>\n\n"
        f"📊 Puntos mínimos: {level.min_points_required:,}\n"
        f"🎨 Color: {level.color}\n"
        f"📊 Estado: {status_text}\n"
        f"👤 Creado por: {level.created_by}\n"
        f"📅 Fecha: {level.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        f"Los usuarios alcanzan este nivel automáticamente al acumular "
        f"{level.min_points_required:,} puntos o más.\n\n"
        f"¿Qué deseas hacer?"
    )

    keyboard = create_inline_keyboard([
        [{
            "text": f"🔄 {action}",
            "callback_data": f"admin:levels:toggle:{level.id}"
        }],
        [{
            "text": "🔙 Volver a la Lista",
            "callback_data": "admin:levels:list"
        }],
        [{
            "text": "🔙 Volver al Menú",
            "callback_data": "admin:levels"
        }]
    ])

    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith("admin:levels:toggle:"))
async def callback_toggle_level(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Activa/desactiva un nivel."""
    level_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    level = await container.levels.get_level(level_id)

    if level is None:
        await callback.answer("Nivel no encontrado", show_alert=True)
        return

    # Toggle estado
    level.active = not level.active
    await session.commit()

    new_status = "activado" if level.active else "desactivado"

    logger.info(
        f"🏆 Nivel {new_status}: {level.name} "
        f"(by: {callback.from_user.id})"
    )

    await callback.answer(
        f"✅ Nivel {new_status}",
        show_alert=True
    )
