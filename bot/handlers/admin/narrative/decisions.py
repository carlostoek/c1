"""
Handler de administración de decisiones narrativas.

CRUD completo:
- Listar por fragmento
- Crear (wizard 4 pasos)
- Ver detalle
- Editar campos
- Toggle activo
- Eliminar
"""

import logging
from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.admin.narrative import narrative_admin_router
from bot.narrative.services.container import NarrativeContainer
from bot.states.admin import NarrativeAdminStates
from bot.utils.keyboards import create_inline_keyboard

logger = logging.getLogger(__name__)


# ========================================
# LISTAR DECISIONES
# ========================================

@narrative_admin_router.callback_query(F.data.startswith("narrative:decisions:"))
async def callback_decisions_list(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Lista decisiones de un fragmento."""
    await callback.answer()

    fragment_key = callback.data.replace("narrative:decisions:", "")
    await _show_decisions(callback.message, session, fragment_key, edit=True)


async def _show_decisions(
    message: Message,
    session: AsyncSession,
    fragment_key: str,
    edit: bool = True
):
    """Muestra decisiones de un fragmento."""
    narrative = NarrativeContainer(session)

    fragment = await narrative.fragment.get_fragment(fragment_key)
    if not fragment:
        await message.edit_text("❌ Fragmento no encontrado.")
        return

    decisions = await narrative.decision.get_decisions_by_fragment(
        fragment.id,
        active_only=False
    )

    # Header
    text = (
        f"📋 <b>Decisiones de: {fragment.title}</b>\n\n"
        f"Total: {len(decisions)} decisiones\n\n"
    )

    if not decisions:
        text += "<i>No hay decisiones en este fragmento.</i>\n"
    else:
        for dec in decisions:
            status = "✅" if dec.is_active else "❌"
            cost_text = f" 💰{dec.besitos_cost}" if dec.besitos_cost > 0 else ""
            grant_text = f" 💝+{dec.grants_besitos}" if dec.grants_besitos > 0 else ""
            text += f"{status} <b>{dec.button_text[:30]}</b>{cost_text}{grant_text}\n"
            text += f"   └ → <code>{dec.target_fragment_key}</code>\n"

    # Botones de decisiones
    buttons = []
    for dec in decisions:
        emoji = dec.button_emoji if dec.button_emoji else "📌"
        buttons.append([{
            "text": f"{emoji} {dec.button_text[:25]}",
            "callback_data": f"narrative:decision:view:{dec.id}"
        }])

    # Acciones
    buttons.append([{
        "text": "➕ Crear Decisión",
        "callback_data": f"narrative:decision:create:{fragment_key}"
    }])
    buttons.append([{
        "text": "🔙 Volver al Fragmento",
        "callback_data": f"narrative:fragment:view:{fragment_key}"
    }])

    keyboard = create_inline_keyboard(buttons)

    if edit:
        await message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


# ========================================
# VER DETALLE DE DECISIÓN
# ========================================

@narrative_admin_router.callback_query(F.data.regexp(r"narrative:decision:view:\d+"))
async def callback_decision_view(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Muestra detalle de una decisión."""
    await callback.answer()

    decision_id = int(callback.data.split(":")[-1])
    narrative = NarrativeContainer(session)
    decision = await narrative.decision.get_decision_by_id(decision_id)

    if not decision:
        await callback.message.edit_text(
            "❌ Decisión no encontrada.",
            reply_markup=create_inline_keyboard([[{
                "text": "🔙 Volver",
                "callback_data": "narrative:chapters"
            }]])
        )
        return

    # Obtener fragmento padre para navegación
    fragment = await narrative.fragment.get_fragment_by_id(decision.fragment_id) if hasattr(narrative.fragment, 'get_fragment_by_id') else None

    # Buscar fragmento padre por ID
    from sqlalchemy import select
    from bot.narrative.database import NarrativeFragment
    stmt = select(NarrativeFragment).where(NarrativeFragment.id == decision.fragment_id)
    result = await session.execute(stmt)
    fragment = result.scalar_one_or_none()

    fragment_key = fragment.fragment_key if fragment else "unknown"

    status = "✅ Activa" if decision.is_active else "❌ Inactiva"
    emoji = decision.button_emoji if decision.button_emoji else "📌"

    text = (
        f"{emoji} <b>{decision.button_text}</b>\n\n"
        f"<b>Estado:</b> {status}\n"
        f"<b>Destino:</b> <code>{decision.target_fragment_key}</code>\n"
        f"<b>Orden:</b> {decision.order}\n"
    )

    if decision.besitos_cost > 0:
        text += f"<b>Costo:</b> 💰 {decision.besitos_cost} besitos\n"

    if decision.grants_besitos > 0:
        text += f"<b>Otorga:</b> 💝 {decision.grants_besitos} besitos\n"

    if decision.affects_archetype:
        text += f"<b>Arquetipo:</b> {decision.affects_archetype}\n"

    toggle_text = "❌ Desactivar" if decision.is_active else "✅ Activar"

    keyboard = create_inline_keyboard([
        [
            {"text": "✏️ Editar", "callback_data": f"narrative:decision:edit:{decision_id}"},
            {"text": toggle_text, "callback_data": f"narrative:decision:toggle:{decision_id}"}
        ],
        [{
            "text": "🗑️ Eliminar",
            "callback_data": f"narrative:decision:delete:{decision_id}"
        }],
        [{
            "text": "🔙 Volver",
            "callback_data": f"narrative:decisions:{fragment_key}"
        }]
    ])

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)


# ========================================
# CREAR DECISIÓN (WIZARD 4 PASOS)
# ========================================

@narrative_admin_router.callback_query(F.data.startswith("narrative:decision:create:"))
async def callback_decision_create_start(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Inicia wizard de creación de decisión."""
    await callback.answer()

    fragment_key = callback.data.replace("narrative:decision:create:", "")

    # Obtener fragment_id
    narrative = NarrativeContainer(session)
    fragment = await narrative.fragment.get_fragment(fragment_key)

    if not fragment:
        await callback.message.edit_text("❌ Fragmento no encontrado.")
        return

    await state.update_data(
        decision_fragment_id=fragment.id,
        decision_fragment_key=fragment_key
    )
    await state.set_state(NarrativeAdminStates.waiting_for_decision_text)

    keyboard = create_inline_keyboard([[{
        "text": "❌ Cancelar",
        "callback_data": f"narrative:decisions:{fragment_key}"
    }]])

    await callback.message.edit_text(
        "📋 <b>Crear Decisión - Paso 1/4</b>\n\n"
        f"Fragmento: <code>{fragment_key}</code>\n\n"
        "Envía el <b>texto del botón</b>.\n\n"
        "<i>Ejemplo: Aceptar la propuesta</i>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@narrative_admin_router.message(NarrativeAdminStates.waiting_for_decision_text)
async def process_decision_text(
    message: Message,
    state: FSMContext
):
    """Procesa texto del botón."""
    button_text = message.text.strip()

    if len(button_text) < 2 or len(button_text) > 100:
        await message.answer(
            "❌ El texto debe tener entre 2 y 100 caracteres.\n"
            "Intenta de nuevo:"
        )
        return

    await state.update_data(decision_button_text=button_text)
    await state.set_state(NarrativeAdminStates.waiting_for_decision_target)

    data = await state.get_data()

    keyboard = create_inline_keyboard([[{
        "text": "❌ Cancelar",
        "callback_data": f"narrative:decisions:{data['decision_fragment_key']}"
    }]])

    await message.answer(
        "📋 <b>Crear Decisión - Paso 2/4</b>\n\n"
        f"Texto: <b>{button_text}</b>\n\n"
        "Envía el <b>fragment_key</b> destino.\n\n"
        "<i>El fragmento al que se navegará al elegir esta opción.\n"
        "Ejemplo: scene_02</i>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@narrative_admin_router.message(NarrativeAdminStates.waiting_for_decision_target)
async def process_decision_target(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa fragmento destino."""
    target_key = message.text.strip().lower().replace(" ", "_")

    if len(target_key) < 2 or len(target_key) > 50:
        await message.answer(
            "❌ El key debe tener entre 2 y 50 caracteres.\n"
            "Intenta de nuevo:"
        )
        return

    # Verificar que el fragmento destino existe
    narrative = NarrativeContainer(session)
    target_fragment = await narrative.fragment.get_fragment(target_key)

    if not target_fragment:
        await message.answer(
            f"⚠️ El fragmento '<code>{target_key}</code>' no existe todavía.\n\n"
            "Puedes continuar de todas formas (se creará después).\n"
            "Envía el mismo key para confirmar, o envía otro:",
            parse_mode="HTML"
        )
        # Guardar key para segunda confirmación
        data = await state.get_data()
        if data.get("pending_target") == target_key:
            # Segunda vez, confirmar
            pass
        else:
            await state.update_data(pending_target=target_key)
            return

    await state.update_data(decision_target=target_key)
    await state.set_state(NarrativeAdminStates.waiting_for_decision_cost)

    data = await state.get_data()

    keyboard = create_inline_keyboard([
        [{"text": "⏭️ Sin costo (0)", "callback_data": "narrative:decision:cost:0"}],
        [{"text": "❌ Cancelar", "callback_data": f"narrative:decisions:{data['decision_fragment_key']}"}]
    ])

    await message.answer(
        "📋 <b>Crear Decisión - Paso 3/4</b>\n\n"
        f"Texto: <b>{data['decision_button_text']}</b>\n"
        f"Destino: <code>{target_key}</code>\n\n"
        "Envía el <b>costo en besitos</b> (0 = gratis).\n\n"
        "<i>Cuántos besitos debe pagar el usuario para elegir esta opción.</i>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@narrative_admin_router.callback_query(
    NarrativeAdminStates.waiting_for_decision_cost,
    F.data == "narrative:decision:cost:0"
)
async def process_decision_cost_zero(
    callback: CallbackQuery,
    state: FSMContext
):
    """Atajo para costo 0."""
    await callback.answer()
    await _process_cost(callback.message, state, 0, edit=True)


@narrative_admin_router.message(NarrativeAdminStates.waiting_for_decision_cost)
async def process_decision_cost(
    message: Message,
    state: FSMContext
):
    """Procesa costo en besitos."""
    try:
        cost = int(message.text.strip())
        if cost < 0:
            raise ValueError()
    except ValueError:
        await message.answer(
            "❌ Envía un número entero >= 0.\n"
            "Intenta de nuevo:"
        )
        return

    await _process_cost(message, state, cost, edit=False)


async def _process_cost(message: Message, state: FSMContext, cost: int, edit: bool):
    """Procesa costo y pasa a grants."""
    await state.update_data(decision_cost=cost)
    await state.set_state(NarrativeAdminStates.waiting_for_decision_grants)

    data = await state.get_data()

    keyboard = create_inline_keyboard([
        [{"text": "⏭️ Sin recompensa (0)", "callback_data": "narrative:decision:grants:0"}],
        [{"text": "❌ Cancelar", "callback_data": f"narrative:decisions:{data['decision_fragment_key']}"}]
    ])

    text = (
        "📋 <b>Crear Decisión - Paso 4/4</b>\n\n"
        f"Texto: <b>{data['decision_button_text']}</b>\n"
        f"Destino: <code>{data['decision_target']}</code>\n"
        f"Costo: {cost} besitos\n\n"
        "Envía los <b>besitos a otorgar</b> (0 = ninguno).\n\n"
        "<i>Cuántos besitos recibe el usuario al elegir esta opción.</i>"
    )

    if edit:
        await message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


@narrative_admin_router.callback_query(
    NarrativeAdminStates.waiting_for_decision_grants,
    F.data == "narrative:decision:grants:0"
)
async def process_decision_grants_zero(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Atajo para grants 0."""
    await callback.answer()
    await _create_decision(callback.message, state, session, 0, edit=True)


@narrative_admin_router.message(NarrativeAdminStates.waiting_for_decision_grants)
async def process_decision_grants(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa besitos a otorgar."""
    try:
        grants = int(message.text.strip())
        if grants < 0:
            raise ValueError()
    except ValueError:
        await message.answer(
            "❌ Envía un número entero >= 0.\n"
            "Intenta de nuevo:"
        )
        return

    await _create_decision(message, state, session, grants, edit=False)


async def _create_decision(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    grants: int,
    edit: bool
):
    """Crea la decisión con los datos del FSM."""
    data = await state.get_data()
    await state.clear()

    narrative = NarrativeContainer(session)

    try:
        decision = await narrative.decision.create_decision(
            fragment_id=data["decision_fragment_id"],
            button_text=data["decision_button_text"],
            target_fragment_key=data["decision_target"],
            besitos_cost=data["decision_cost"],
            grants_besitos=grants
        )

        text = (
            "✅ <b>Decisión Creada</b>\n\n"
            f"<b>Texto:</b> {decision.button_text}\n"
            f"<b>Destino:</b> <code>{decision.target_fragment_key}</code>\n"
        )

        if decision.besitos_cost > 0:
            text += f"<b>Costo:</b> 💰 {decision.besitos_cost}\n"

        if grants > 0:
            text += f"<b>Otorga:</b> 💝 {grants}\n"

        keyboard = create_inline_keyboard([
            [{"text": "➕ Crear otra", "callback_data": f"narrative:decision:create:{data['decision_fragment_key']}"}],
            [{"text": "🔙 Ver Decisiones", "callback_data": f"narrative:decisions:{data['decision_fragment_key']}"}]
        ])

        if edit:
            await message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        else:
            await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Error creando decisión: {e}")
        await message.answer(f"❌ Error: {e}")


# ========================================
# EDITAR DECISIÓN
# ========================================

@narrative_admin_router.callback_query(F.data.regexp(r"narrative:decision:edit:\d+$"))
async def callback_decision_edit_menu(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Muestra menú de edición de la decisión."""
    await callback.answer()

    decision_id = int(callback.data.split(":")[-1])
    narrative = NarrativeContainer(session)
    decision = await narrative.decision.get_decision_by_id(decision_id)

    if not decision:
        await callback.message.edit_text("❌ Decisión no encontrada.")
        return

    text = (
        f"✏️ <b>Editar: {decision.button_text}</b>\n\n"
        "Selecciona el campo a editar:"
    )

    keyboard = create_inline_keyboard([
        [{"text": "📝 Texto", "callback_data": f"narrative:decision:edit:text:{decision_id}"}],
        [{"text": "🎯 Destino", "callback_data": f"narrative:decision:edit:target:{decision_id}"}],
        [{"text": "💰 Costo", "callback_data": f"narrative:decision:edit:cost:{decision_id}"}],
        [{"text": "🔙 Volver", "callback_data": f"narrative:decision:view:{decision_id}"}]
    ])

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)


@narrative_admin_router.callback_query(F.data.regexp(r"narrative:decision:edit:text:\d+"))
async def callback_edit_decision_text_start(
    callback: CallbackQuery,
    state: FSMContext
):
    """Inicia edición de texto."""
    await callback.answer()

    decision_id = int(callback.data.split(":")[-1])
    await state.update_data(editing_decision_id=decision_id)
    await state.set_state(NarrativeAdminStates.editing_decision_text)

    keyboard = create_inline_keyboard([[{
        "text": "❌ Cancelar",
        "callback_data": f"narrative:decision:view:{decision_id}"
    }]])

    await callback.message.edit_text(
        "📝 <b>Editar Texto</b>\n\n"
        "Envía el nuevo texto del botón:",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@narrative_admin_router.message(NarrativeAdminStates.editing_decision_text)
async def process_edit_decision_text(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa nuevo texto."""
    new_text = message.text.strip()

    if len(new_text) < 2 or len(new_text) > 100:
        await message.answer("❌ El texto debe tener entre 2 y 100 caracteres.")
        return

    data = await state.get_data()
    decision_id = data["editing_decision_id"]
    await state.clear()

    narrative = NarrativeContainer(session)
    await narrative.decision.update_decision(decision_id, button_text=new_text)

    keyboard = create_inline_keyboard([[{
        "text": "🔙 Volver a la decisión",
        "callback_data": f"narrative:decision:view:{decision_id}"
    }]])

    await message.answer(
        f"✅ Texto actualizado a: <b>{new_text}</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@narrative_admin_router.callback_query(F.data.regexp(r"narrative:decision:edit:target:\d+"))
async def callback_edit_decision_target_start(
    callback: CallbackQuery,
    state: FSMContext
):
    """Inicia edición de destino."""
    await callback.answer()

    decision_id = int(callback.data.split(":")[-1])
    await state.update_data(editing_decision_id=decision_id)
    await state.set_state(NarrativeAdminStates.editing_decision_target)

    keyboard = create_inline_keyboard([[{
        "text": "❌ Cancelar",
        "callback_data": f"narrative:decision:view:{decision_id}"
    }]])

    await callback.message.edit_text(
        "🎯 <b>Editar Destino</b>\n\n"
        "Envía el nuevo fragment_key destino:",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@narrative_admin_router.message(NarrativeAdminStates.editing_decision_target)
async def process_edit_decision_target(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa nuevo destino."""
    new_target = message.text.strip().lower().replace(" ", "_")

    if len(new_target) < 2 or len(new_target) > 50:
        await message.answer("❌ El key debe tener entre 2 y 50 caracteres.")
        return

    data = await state.get_data()
    decision_id = data["editing_decision_id"]
    await state.clear()

    narrative = NarrativeContainer(session)
    await narrative.decision.update_decision(decision_id, target_fragment_key=new_target)

    keyboard = create_inline_keyboard([[{
        "text": "🔙 Volver a la decisión",
        "callback_data": f"narrative:decision:view:{decision_id}"
    }]])

    await message.answer(
        f"✅ Destino actualizado a: <code>{new_target}</code>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@narrative_admin_router.callback_query(F.data.regexp(r"narrative:decision:edit:cost:\d+"))
async def callback_edit_decision_cost_start(
    callback: CallbackQuery,
    state: FSMContext
):
    """Inicia edición de costo."""
    await callback.answer()

    decision_id = int(callback.data.split(":")[-1])
    await state.update_data(editing_decision_id=decision_id)
    await state.set_state(NarrativeAdminStates.editing_decision_cost)

    keyboard = create_inline_keyboard([[{
        "text": "❌ Cancelar",
        "callback_data": f"narrative:decision:view:{decision_id}"
    }]])

    await callback.message.edit_text(
        "💰 <b>Editar Costo</b>\n\n"
        "Envía el nuevo costo en besitos (0 = gratis):",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@narrative_admin_router.message(NarrativeAdminStates.editing_decision_cost)
async def process_edit_decision_cost(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa nuevo costo."""
    try:
        new_cost = int(message.text.strip())
        if new_cost < 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ Envía un número entero >= 0.")
        return

    data = await state.get_data()
    decision_id = data["editing_decision_id"]
    await state.clear()

    narrative = NarrativeContainer(session)
    await narrative.decision.update_decision(decision_id, besitos_cost=new_cost)

    keyboard = create_inline_keyboard([[{
        "text": "🔙 Volver a la decisión",
        "callback_data": f"narrative:decision:view:{decision_id}"
    }]])

    await message.answer(
        f"✅ Costo actualizado a: <b>{new_cost}</b> besitos",
        parse_mode="HTML",
        reply_markup=keyboard
    )


# ========================================
# TOGGLE ACTIVO
# ========================================

@narrative_admin_router.callback_query(F.data.regexp(r"narrative:decision:toggle:\d+"))
async def callback_decision_toggle(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Toggle estado activo de la decisión."""
    decision_id = int(callback.data.split(":")[-1])

    narrative = NarrativeContainer(session)
    decision = await narrative.decision.get_decision_by_id(decision_id)

    if not decision:
        await callback.answer("❌ Decisión no encontrada", show_alert=True)
        return

    new_status = not decision.is_active
    await narrative.decision.update_decision(decision_id, is_active=new_status)

    status_text = "activada" if new_status else "desactivada"
    await callback.answer(f"✅ Decisión {status_text}", show_alert=True)

    # Recargar vista
    decision = await narrative.decision.get_decision_by_id(decision_id)

    # Obtener fragment_key
    from sqlalchemy import select
    from bot.narrative.database import NarrativeFragment
    stmt = select(NarrativeFragment).where(NarrativeFragment.id == decision.fragment_id)
    result = await session.execute(stmt)
    fragment = result.scalar_one_or_none()
    fragment_key = fragment.fragment_key if fragment else "unknown"

    status = "✅ Activa" if decision.is_active else "❌ Inactiva"
    emoji = decision.button_emoji if decision.button_emoji else "📌"

    text = (
        f"{emoji} <b>{decision.button_text}</b>\n\n"
        f"<b>Estado:</b> {status}\n"
        f"<b>Destino:</b> <code>{decision.target_fragment_key}</code>\n"
        f"<b>Orden:</b> {decision.order}\n"
    )

    if decision.besitos_cost > 0:
        text += f"<b>Costo:</b> 💰 {decision.besitos_cost} besitos\n"

    if decision.grants_besitos > 0:
        text += f"<b>Otorga:</b> 💝 {decision.grants_besitos} besitos\n"

    toggle_text = "❌ Desactivar" if decision.is_active else "✅ Activar"

    keyboard = create_inline_keyboard([
        [
            {"text": "✏️ Editar", "callback_data": f"narrative:decision:edit:{decision_id}"},
            {"text": toggle_text, "callback_data": f"narrative:decision:toggle:{decision_id}"}
        ],
        [{"text": "🗑️ Eliminar", "callback_data": f"narrative:decision:delete:{decision_id}"}],
        [{"text": "🔙 Volver", "callback_data": f"narrative:decisions:{fragment_key}"}]
    ])

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)


# ========================================
# ELIMINAR DECISIÓN
# ========================================

@narrative_admin_router.callback_query(F.data.regexp(r"narrative:decision:delete:\d+"))
async def callback_decision_delete(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Confirma eliminación de decisión."""
    await callback.answer()

    decision_id = int(callback.data.split(":")[-1])
    narrative = NarrativeContainer(session)
    decision = await narrative.decision.get_decision_by_id(decision_id)

    if not decision:
        await callback.message.edit_text("❌ Decisión no encontrada.")
        return

    # Obtener fragment_key
    from sqlalchemy import select
    from bot.narrative.database import NarrativeFragment
    stmt = select(NarrativeFragment).where(NarrativeFragment.id == decision.fragment_id)
    result = await session.execute(stmt)
    fragment = result.scalar_one_or_none()
    fragment_key = fragment.fragment_key if fragment else "unknown"

    text = (
        f"⚠️ <b>¿Eliminar decisión?</b>\n\n"
        f"<b>{decision.button_text}</b>\n"
        f"→ {decision.target_fragment_key}\n\n"
        "<i>Esta acción desactivará la decisión (soft delete).</i>"
    )

    keyboard = create_inline_keyboard([
        [
            {"text": "🗑️ Sí, eliminar", "callback_data": f"narrative:decision:confirm_delete:{decision_id}"},
            {"text": "❌ Cancelar", "callback_data": f"narrative:decision:view:{decision_id}"}
        ]
    ])

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)


@narrative_admin_router.callback_query(F.data.regexp(r"narrative:decision:confirm_delete:\d+"))
async def callback_decision_confirm_delete(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Ejecuta eliminación de la decisión."""
    decision_id = int(callback.data.split(":")[-1])

    narrative = NarrativeContainer(session)
    decision = await narrative.decision.get_decision_by_id(decision_id)

    if not decision:
        await callback.answer("❌ Decisión no encontrada", show_alert=True)
        return

    # Obtener fragment_key antes de eliminar
    from sqlalchemy import select
    from bot.narrative.database import NarrativeFragment
    stmt = select(NarrativeFragment).where(NarrativeFragment.id == decision.fragment_id)
    result = await session.execute(stmt)
    fragment = result.scalar_one_or_none()
    fragment_key = fragment.fragment_key if fragment else "unknown"

    await narrative.decision.delete_decision(decision_id)

    await callback.answer("🗑️ Decisión eliminada", show_alert=True)
    await _show_decisions(callback.message, session, fragment_key, edit=True)
