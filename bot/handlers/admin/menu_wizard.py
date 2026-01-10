"""
Menu Wizard - Wizard para crear/editar items de menú dinámico.

Permite a los administradores gestionar menús sin tocar código:
- Crear nuevos items de menú
- Editar items existentes
- Validación de datos
- Mensajes de Lucien

Wizard de 10 pasos:
1. Item Key (identificador único)
2. Button Text (texto del botón)
3. Button Emoji (opcional)
4. Action Type (callback/url/submenu/info/blocked)
5. Action Content (según tipo)
6. Target Role (vip/free/all/admin)
7. Parent Key (opcional, para submenús)
8. Display Order (número)
9. Row Number (número)
10. Requires Onboarding (Sí/No)
"""
import logging
from typing import Optional

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.admin.main import admin_router
from bot.states.admin import MenuWizardStates
from bot.services.container import ServiceContainer
from bot.services.lucien_voice import LucienVoiceService
from bot.utils.keyboards import (
    create_inline_keyboard,
    action_type_selection_keyboard,
    target_role_selection_keyboard,
    boolean_selection_keyboard,
    wizard_cancel_keyboard
)

logger = logging.getLogger(__name__)

# Router específico para el wizard de menús
menu_wizard_router = Router(name="menu_wizard")


# ========================================
# INICIO DEL WIZARD
# ========================================

@admin_router.callback_query(F.data == "admin:menu_create")
async def start_create_wizard(callback: CallbackQuery, state: FSMContext):
    """
    Inicia el wizard para crear nuevo item de menú.

    Comienza el flujo de 10 pasos para crear un nuevo item.
    """
    logger.info(f"🧙 Admin {callback.from_user.id} iniciando wizard de creación de menú")

    # Limpiar estado anterior y establecer nuevo estado
    await state.clear()
    await state.set_state(MenuWizardStates.entering_item_key)
    await state.update_data(mode="create")

    # Mensaje de bienvenida con Lucien
    lucien = LucienVoiceService()
    text = await lucien.get_wizard_message("menu_welcome")

    keyboard = wizard_cancel_keyboard()

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# ========================================
# PASO 1: ITEM KEY
# ========================================

@menu_wizard_router.message(MenuWizardStates.entering_item_key)
async def enter_item_key(message: Message, state: FSMContext):
    """
    Paso 1: Ingresar item_key (identificador único).

    Validaciones:
    - No vacío
    - Solo letras minúsculas, números y guiones bajos
    - Máximo 100 caracteres
    """
    item_key = message.text.strip()

    # Validación
    if not item_key:
        await message.answer("❌ El item_key no puede estar vacío.")
        return

    if len(item_key) > 100:
        await message.answer("❌ El item_key debe tener máximo 100 caracteres.")
        return

    # Validar formato: solo letras minúsculas, números y guiones bajos
    import re
    if not re.match(r'^[a-z0-9_]+$', item_key):
        await message.answer(
            "❌ Formato inválido. Use solo letras minúsculas, números y guiones bajos.\n"
            "<i>Ejemplo: 'mi_nuevo_item', 'vip_opcion'</i>",
            parse_mode="HTML"
        )
        return

    # Guardar en FSM data
    await state.update_data(item_key=item_key)
    logger.info(f"✅ Item key guardado: {item_key}")

    # Pasar al siguiente paso
    await state.set_state(MenuWizardStates.entering_button_text)

    lucien = LucienVoiceService()
    text = await lucien.get_wizard_message("menu_step_button_text")
    keyboard = wizard_cancel_keyboard()

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


# ========================================
# PASO 2: BUTTON TEXT
# ========================================

@menu_wizard_router.message(MenuWizardStates.entering_button_text)
async def enter_button_text(message: Message, state: FSMContext):
    """
    Paso 2: Ingresar texto del botón.

    Validaciones:
    - No vacío
    - Máximo 100 caracteres
    """
    button_text = message.text.strip()

    if not button_text:
        await message.answer("❌ El texto del botón no puede estar vacío.")
        return

    if len(button_text) > 100:
        await message.answer("❌ El texto debe tener máximo 100 caracteres.")
        return

    # Guardar en FSM data
    await state.update_data(button_text=button_text)
    logger.info(f"✅ Button text guardado: {button_text}")

    # Pasar al siguiente paso
    await state.set_state(MenuWizardStates.entering_button_emoji)

    lucien = LucienVoiceService()
    text = await lucien.get_wizard_message("menu_step_button_emoji")
    keyboard = wizard_cancel_keyboard()

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


# ========================================
# PASO 3: BUTTON EMOJI (OPCIONAL)
# ========================================

@menu_wizard_router.message(MenuWizardStates.entering_button_emoji)
async def enter_button_emoji(message: Message, state: FSMContext):
    """
    Paso 3: Ingresar emoji del botón (opcional).

    Validaciones:
    - Máximo 10 caracteres
    - Opcional (/skip para omitir)
    """
    button_emoji = message.text.strip()

    # Permitir omitir
    if button_emoji == "/skip":
        button_emoji = None
        logger.info("✅ Button emoji omitido")
    else:
        if len(button_emoji) > 10:
            await message.answer("❌ El emoji debe tener máximo 10 caracteres.")
            return

        # Guardar en FSM data
        await state.update_data(button_emoji=button_emoji)
        logger.info(f"✅ Button emoji guardado: {button_emoji}")

    # Pasar al siguiente paso
    await state.set_state(MenuWizardStates.selecting_action_type)

    text = (
        "📝 <b>Paso 4/10: Tipo de Acción</b>\n\n"
        "Seleccione el tipo de acción que ejecutará este botón:\n\n"
        "• <b>🔘 Callback:</b> Ejecuta un callback_data del bot\n"
        "• <b>🔗 URL:</b> Abre un enlace externo\n"
        "• <b>📁 Submenú:</b> Navega a un submenú\n"
        "• <b>ℹ️ Info:</b> Muestra un mensaje informativo\n"
        "• <b>🚫 Blocked:</b> Opción bloqueada (muestra mensaje de error)"
    )

    keyboard = action_type_selection_keyboard()

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


# ========================================
# PASO 4: ACTION TYPE
# ========================================

@menu_wizard_router.callback_query(MenuWizardStates.selecting_action_type, F.data.startswith("wizard:action:"))
async def select_action_type(callback: CallbackQuery, state: FSMContext):
    """
    Paso 4: Seleccionar tipo de acción.

    Opciones:
    - callback: Ejecuta callback_data
    - url: Abre enlace externo
    - submenu: Navega a submenú
    - info: Muestra mensaje
    - blocked: Opción bloqueada
    """
    action_type = callback.data.split(":")[-1]

    # Validar tipo
    valid_types = ["callback", "url", "submenu", "info", "blocked"]
    if action_type not in valid_types:
        await callback.answer("❌ Tipo de acción inválido", show_alert=True)
        return

    # Guardar en FSM data
    await state.update_data(action_type=action_type)
    logger.info(f"✅ Action type seleccionado: {action_type}")

    # Pasar al siguiente paso
    await state.set_state(MenuWizardStates.entering_action_content)

    lucien = LucienVoiceService()
    text = await lucien.get_wizard_message("menu_step_action_content")
    keyboard = wizard_cancel_keyboard()

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# ========================================
# PASO 5: ACTION CONTENT
# ========================================

@menu_wizard_router.message(MenuWizardStates.entering_action_content)
async def enter_action_content(message: Message, state: FSMContext):
    """
    Paso 5: Ingresar contenido de la acción.

    Validación según tipo:
    - URL: debe comenzar con http:// o https://
    - Otros: no vacío
    """
    action_content = message.text.strip()
    data = await state.get_data()
    action_type = data.get("action_type")

    # Validación según tipo
    if action_type == "url":
        if not action_content.startswith(("http://", "https://")):
            await message.answer(
                "❌ La URL debe comenzar con <code>http://</code> o <code>https://</code>",
                parse_mode="HTML"
            )
            return

    if not action_content:
        await message.answer("❌ El contenido no puede estar vacío.")
        return

    # Guardar en FSM data
    await state.update_data(action_content=action_content)
    logger.info(f"✅ Action content guardado: {action_content}")

    # Pasar al siguiente paso
    await state.set_state(MenuWizardStates.selecting_target_role)

    text = (
        "📝 <b>Paso 6/10: Rol Objetivo</b>\n\n"
        "Seleccione qué tipo de usuarios verán este botón:\n\n"
        "• <b>👥 FREE:</b> Solo usuarios gratuitos\n"
        "• <b>⭐ VIP:</b> Solo suscriptores VIP\n"
        "• <b>👑 Admin:</b> Solo administradores\n"
        "• <b>🌐 Todos:</b> Todos los usuarios"
    )

    keyboard = target_role_selection_keyboard()

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


# ========================================
# PASO 6: TARGET ROLE
# ========================================

@menu_wizard_router.callback_query(MenuWizardStates.selecting_target_role, F.data.startswith("wizard:role:"))
async def select_target_role(callback: CallbackQuery, state: FSMContext):
    """
    Paso 6: Seleccionar rol objetivo.

    Opciones:
    - free: Usuarios gratuitos
    - vip: Suscriptores VIP
    - admin: Administradores
    - all: Todos los usuarios
    """
    target_role = callback.data.split(":")[-1]

    # Validar rol
    valid_roles = ["free", "vip", "admin", "all"]
    if target_role not in valid_roles:
        await callback.answer("❌ Rol inválido", show_alert=True)
        return

    # Guardar en FSM data
    await state.update_data(target_role=target_role)
    logger.info(f"✅ Target role seleccionado: {target_role}")

    # Pasar al siguiente paso
    await state.set_state(MenuWizardStates.selecting_parent_key)

    lucien = LucienVoiceService()
    text = await lucien.get_wizard_message("menu_step_parent_key")

    keyboard = create_inline_keyboard([
        [{"text": "⬅️ Omitir (Menú Principal)", "callback_data": "wizard:parent:skip"}],
        [{"text": "❌ Cancelar", "callback_data": "wizard:cancel"}]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# ========================================
# PASO 7: PARENT KEY (OPCIONAL)
# ========================================

@menu_wizard_router.callback_query(MenuWizardStates.selecting_parent_key, F.data == "wizard:parent:skip")
async def skip_parent_key(callback: CallbackQuery, state: FSMContext):
    """
    Paso 7: Omitir parent_key (menú principal).
    """
    await state.update_data(parent_key=None)
    logger.info("✅ Parent key omitido (menú principal)")

    # Pasar al siguiente paso
    await _proceed_to_display_order(callback.message, state)


@menu_wizard_router.message(MenuWizardStates.selecting_parent_key)
async def enter_parent_key(message: Message, state: FSMContext, session: AsyncSession):
    """
    Paso 7: Ingresar parent_key (para submenús).

    Validaciones:
    - Debe existir en BD
    - No puede crear ciclos
    """
    parent_key = message.text.strip()

    if not parent_key:
        await message.answer("❌ El parent_key no puede estar vacío. Envíe un key válido o use el botón para omitir.")
        return

    # Verificar que el parent existe
    container = ServiceContainer(session, message.bot)
    parent = await container.menu.get_menu_item_by_key(parent_key)

    if not parent:
        await message.answer(f"❌ El item '{parent_key}' no existe. Use un item_key válido.")
        return

    # Guardar en FSM data
    await state.update_data(parent_key=parent_key)
    logger.info(f"✅ Parent key guardado: {parent_key}")

    # Pasar al siguiente paso
    await _proceed_to_display_order(message, state)


async def _proceed_to_display_order(message: Message, state: FSMContext):
    """Helper para pasar al paso 8."""
    await state.set_state(MenuWizardStates.entering_display_order)

    lucien = LucienVoiceService()
    text = await lucien.get_wizard_message("menu_step_display_order")
    keyboard = wizard_cancel_keyboard()

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


# ========================================
# PASO 8: DISPLAY ORDER
# ========================================

@menu_wizard_router.message(MenuWizardStates.entering_display_order)
async def enter_display_order(message: Message, state: FSMContext):
    """
    Paso 8: Ingresar orden de visualización.

    Validaciones:
    - Número entero positivo
    - Valor por defecto: 1
    """
    try:
        display_order = int(message.text.strip())
        if display_order < 0:
            raise ValueError("Debe ser positivo")
    except ValueError:
        await message.answer("❌ Debe ser un número positivo (ej: 1, 2, 3...)")
        return

    # Guardar en FSM data
    await state.update_data(display_order=display_order)
    logger.info(f"✅ Display order guardado: {display_order}")

    # Pasar al siguiente paso
    await state.set_state(MenuWizardStates.entering_row_number)

    lucien = LucienVoiceService()
    text = await lucien.get_wizard_message("menu_step_row_number")
    keyboard = wizard_cancel_keyboard()

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


# ========================================
# PASO 9: ROW NUMBER
# ========================================

@menu_wizard_router.message(MenuWizardStates.entering_row_number)
async def enter_row_number(message: Message, state: FSMContext):
    """
    Paso 9: Ingresar número de fila.

    Validaciones:
    - Número entero positivo
    - Valor por defecto: 1
    """
    try:
        row_number = int(message.text.strip())
        if row_number < 0:
            raise ValueError("Debe ser positivo")
    except ValueError:
        await message.answer("❌ Debe ser un número positivo (ej: 1, 2, 3...)")
        return

    # Guardar en FSM data
    await state.update_data(row_number=row_number)
    logger.info(f"✅ Row number guardado: {row_number}")

    # Pasar al siguiente paso
    await state.set_state(MenuWizardStates.entering_requires_onboarding)

    text = (
        "📝 <b>Paso 10/10: Requiere Onboarding</b>\n\n"
        "¿Este botón debe estar bloqueado hasta que el usuario complete el tutorial?\n\n"
        "• <b>Sí:</b> El usuario debe completar el onboarding primero\n"
        "• <b>No:</b> Cualquiera puede verlo desde el inicio"
    )

    keyboard = boolean_selection_keyboard()

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


# ========================================
# PASO 10: REQUIRES ONBOARDING
# ========================================

@menu_wizard_router.callback_query(MenuWizardStates.entering_requires_onboarding, F.data.startswith("wizard:bool:"))
async def enter_requires_onboarding(callback: CallbackQuery, state: FSMContext):
    """
    Paso 10: ¿Requiere onboarding?

    Opciones:
    - Sí (true)
    - No (false)
    """
    bool_value = callback.data.split(":")[-1]
    requires_onboarding = bool_value == "true"

    # Guardar en FSM data
    await state.update_data(requires_onboarding=requires_onboarding)
    logger.info(f"✅ Requires onboarding: {requires_onboarding}")

    # Pasar a confirmación
    await state.set_state(MenuWizardStates.confirming)
    await _show_confirmation(callback.message, state)


async def _show_confirmation(message: Message, state: FSMContext):
    """Muestra resumen y solicitud de confirmación."""
    data = await state.get_data()

    # Construir resumen
    summary = (
        "📋 <b>RESUMEN DEL NUEVO ITEM</b>\n\n"
        f"<b>🔑 Item Key:</b> <code>{data.get('item_key')}</code>\n"
        f"<b>📝 Texto:</b> {data.get('button_text')}\n"
        f"<b>🎨 Emoji:</b> {data.get('button_emoji', '(sin emoji)')}\n"
        f"<b>⚡ Tipo:</b> {data.get('action_type').upper()}\n"
        f"<b>📦 Contenido:</b> <code>{data.get('action_content')}</code>\n"
        f"<b>👥 Rol:</b> {data.get('target_role').upper()}\n"
        f"<b>📁 Padre:</b> {data.get('parent_key', '(Menú Principal)')}\n"
        f"<b>🔢 Orden:</b> {data.get('display_order')}\n"
        f"<b>📐 Fila:</b> {data.get('row_number')}\n"
        f"<b>🔒 Onboarding:</b> {'Sí' if data.get('requires_onboarding') else 'No'}\n\n"
        "<i>¿Desea crear este item de menú?</i>"
    )

    keyboard = create_inline_keyboard([
        [{"text": "✅ Confirmar y Crear", "callback_data": "wizard:menu:confirm"}],
        [{"text": "❌ Cancelar", "callback_data": "wizard:cancel"}]
    ])

    await message.answer(summary, reply_markup=keyboard, parse_mode="HTML")


# ========================================
# CONFIRMACIÓN Y GUARDADO
# ========================================

@menu_wizard_router.callback_query(F.data == "wizard:menu:confirm")
async def confirm_and_create(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Confirmación final: Crea el item de menú.

    Valida todos los datos y crea el item en BD.
    """
    data = await state.get_data()

    logger.info(f"🧙 Creando item de menú: {data.get('item_key')}")

    try:
        container = ServiceContainer(session, callback.bot)

        # Verificar que item_key no exista
        existing = await container.menu.get_menu_item_by_key(data["item_key"])
        if existing:
            await callback.message.edit_text(
                "❌ <b>Error:</b> El item_key ya existe.\n\n"
                f"Use otro key o edite el existente: <code>{data['item_key']}</code>",
                parse_mode="HTML"
            )
            await state.clear()
            await callback.answer()
            return

        # Crear el item
        item = await container.menu.create_menu_item(
            item_key=data["item_key"],
            button_text=data["button_text"],
            button_emoji=data.get("button_emoji"),
            action_type=data["action_type"],
            action_content=data["action_content"],
            target_role=data["target_role"],
            parent_key=data.get("parent_key"),
            display_order=data["display_order"],
            row_number=data["row_number"],
            requires_onboarding=data["requires_onboarding"],
            is_active=True,
            created_by=callback.from_user.id
        )

        # Commit
        await session.commit()

        logger.info(f"✅ Item creado exitosamente: {item.item_key}")

        # Mensaje de éxito con Lucien
        lucien = LucienVoiceService()
        text = await lucien.get_wizard_message("menu_success")

        keyboard = create_inline_keyboard([
            [{"text": "🔙 Volver al Panel", "callback_data": "admin:menus"}]
        ])

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await state.clear()
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Error creando item: {e}", exc_info=True)

        lucien = LucienVoiceService()
        text = await lucien.get_wizard_message("menu_error")

        keyboard = create_inline_keyboard([
            [{"text": "🔙 Volver al Panel", "callback_data": "admin:menus"}]
        ])

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await state.clear()
        await callback.answer()


# ========================================
# CANCELAR WIZARD
# ========================================

@menu_wizard_router.callback_query(F.data == "wizard:cancel")
async def cancel_wizard(callback: CallbackQuery, state: FSMContext):
    """Cancela el wizard y vuelve al panel."""
    logger.info("❌ Wizard cancelado por el usuario")

    await state.clear()

    lucien = LucienVoiceService()
    text = await lucien.get_wizard_message("menu_cancelled")

    keyboard = create_inline_keyboard([
        [{"text": "🔙 Volver al Panel", "callback_data": "admin:menus"}]
    ])

    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.debug(f"No se pudo editar mensaje: {e}")

    await callback.answer()


# ========================================
# VOLVER ATRÁS
# ========================================

@menu_wizard_router.callback_query(F.data == "wizard:back")
async def go_back(callback: CallbackQuery, state: FSMContext):
    """Vuelve al paso anterior del wizard."""
    # Implementación simple: cancelar por ahora
    # En una versión completa podría volver al estado anterior
    await cancel_wizard(callback, state)
