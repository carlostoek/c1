"""
Menu Configuration Handlers - Gestión de menús desde interfaz admin.

Permite a administradores:
- Ver/listar botones configurados
- Crear nuevos botones
- Editar botones existentes
- Activar/desactivar botones
- Configurar mensajes del menú
"""
import logging
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.container import ServiceContainer
from bot.states.admin import MenuConfigStates
from bot.utils.keyboards import create_inline_keyboard
from bot.middlewares import AdminAuthMiddleware, DatabaseMiddleware

logger = logging.getLogger(__name__)

menu_config_router = Router(name="menu_config")

# Aplicar middlewares (orden correcto: Database primero, AdminAuth después)
menu_config_router.message.middleware(DatabaseMiddleware())
menu_config_router.message.middleware(AdminAuthMiddleware())
menu_config_router.callback_query.middleware(DatabaseMiddleware())
menu_config_router.callback_query.middleware(AdminAuthMiddleware())


# ═══════════════════════════════════════════════════════════════
# KEYBOARDS PARA CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════

def menu_management_keyboard():
    """Keyboard principal de gestión de menús."""
    return create_inline_keyboard([
        [{"text": "📋 Ver Botones VIP", "callback_data": "menuconfig:list:vip"}],
        [{"text": "📋 Ver Botones FREE", "callback_data": "menuconfig:list:free"}],
        [{"text": "➕ Crear Nuevo Botón", "callback_data": "menuconfig:create"}],
        [{"text": "⚙️ Configurar Mensaje VIP", "callback_data": "menuconfig:msg:vip"}],
        [{"text": "⚙️ Configurar Mensaje FREE", "callback_data": "menuconfig:msg:free"}],
        [{"text": "🔙 Volver", "callback_data": "admin:main"}]
    ])


def button_actions_keyboard(item_key: str, is_active: bool):
    """Keyboard de acciones para un botón específico."""
    toggle_text = "🔴 Desactivar" if is_active else "🟢 Activar"
    return create_inline_keyboard([
        [{"text": "✏️ Editar Texto", "callback_data": f"menuconfig:edit:text:{item_key}"}],
        [{"text": "📝 Editar Contenido", "callback_data": f"menuconfig:edit:content:{item_key}"}],
        [{"text": toggle_text, "callback_data": f"menuconfig:toggle:{item_key}"}],
        [{"text": "🗑️ Eliminar", "callback_data": f"menuconfig:delete:{item_key}"}],
        [{"text": "🔙 Volver", "callback_data": "menuconfig:main"}]
    ])


def role_selection_keyboard():
    """Keyboard para seleccionar rol target."""
    return create_inline_keyboard([
        [{"text": "⭐ Solo VIP", "callback_data": "menuconfig:role:vip"}],
        [{"text": "🆓 Solo FREE", "callback_data": "menuconfig:role:free"}],
        [{"text": "👥 Ambos", "callback_data": "menuconfig:role:all"}],
        [{"text": "❌ Cancelar", "callback_data": "menuconfig:cancel"}]
    ])


def action_type_keyboard():
    """Keyboard para seleccionar tipo de acción."""
    return create_inline_keyboard([
        [{"text": "ℹ️ Información", "callback_data": "menuconfig:actiontype:info"}],
        [{"text": "🔗 URL Externa", "callback_data": "menuconfig:actiontype:url"}],
        [{"text": "📞 Contacto", "callback_data": "menuconfig:actiontype:contact"}],
        [{"text": "❌ Cancelar", "callback_data": "menuconfig:cancel"}]
    ])


# ═══════════════════════════════════════════════════════════════
# HANDLER PRINCIPAL
# ═══════════════════════════════════════════════════════════════

@menu_config_router.callback_query(F.data == "admin:menu_config")
async def callback_menu_config_main(callback: CallbackQuery, session: AsyncSession):
    """Muestra el menú principal de configuración de menús."""
    logger.debug(f"📋 Admin {callback.from_user.id} abrió config de menús")

    await callback.message.edit_text(
        "📋 <b>Configuración de Menús</b>\n\n"
        "Desde aquí puedes configurar los botones que verán\n"
        "los usuarios VIP y FREE.\n\n"
        "Selecciona una opción:",
        reply_markup=menu_management_keyboard(),
        parse_mode="HTML"
    )


# ═══════════════════════════════════════════════════════════════
# LISTAR BOTONES
# ═══════════════════════════════════════════════════════════════

@menu_config_router.callback_query(F.data.startswith("menuconfig:list:"))
async def callback_list_buttons(callback: CallbackQuery, session: AsyncSession):
    """Lista los botones configurados para un rol."""
    role = callback.data.split(":")[-1]

    container = ServiceContainer(session, callback.bot)
    items = await container.menu.get_menu_items_for_role(role, only_active=False)

    if not items:
        text = f"📋 <b>Botones {role.upper()}</b>\n\n"
        text += "No hay botones configurados para este rol.\n\n"
        text += "Usa 'Crear Nuevo Botón' para agregar uno."
    else:
        text = f"📋 <b>Botones {role.upper()}</b>\n\n"
        for i, item in enumerate(items, 1):
            status = "✅" if item.is_active else "❌"
            emoji = item.button_emoji or ""
            text += f"{i}. {status} {emoji} <b>{item.button_text}</b>\n"
            text += f"   └ Key: <code>{item.item_key}</code>\n"
            text += f"   └ Tipo: {item.action_type}\n\n"

    # Crear keyboard con botones para cada item
    buttons = []
    for item in items:
        emoji = "✅" if item.is_active else "❌"
        buttons.append([{
            "text": f"{emoji} {item.button_text}",
            "callback_data": f"menuconfig:item:{item.item_key}"
        }])

    buttons.append([{"text": "🔙 Volver", "callback_data": "admin:menu_config"}])

    await callback.message.edit_text(
        text,
        reply_markup=create_inline_keyboard(buttons),
        parse_mode="HTML"
    )


# ═══════════════════════════════════════════════════════════════
# VER/EDITAR BOTÓN INDIVIDUAL
# ═══════════════════════════════════════════════════════════════

@menu_config_router.callback_query(F.data.startswith("menuconfig:item:"))
async def callback_view_button(callback: CallbackQuery, session: AsyncSession):
    """Muestra detalles y acciones para un botón específico."""
    item_key = callback.data.split(":")[-1]

    container = ServiceContainer(session, callback.bot)
    item = await container.menu.get_menu_item(item_key)

    if not item:
        await callback.answer("❌ Botón no encontrado", show_alert=True)
        return

    status = "✅ Activo" if item.is_active else "❌ Inactivo"
    emoji = item.button_emoji or "(sin emoji)"

    text = (
        f"🔘 <b>Detalles del Botón</b>\n\n"
        f"<b>Key:</b> <code>{item.item_key}</code>\n"
        f"<b>Texto:</b> {item.button_text}\n"
        f"<b>Emoji:</b> {emoji}\n"
        f"<b>Rol:</b> {item.target_role.upper()}\n"
        f"<b>Tipo:</b> {item.action_type}\n"
        f"<b>Estado:</b> {status}\n\n"
    )

    if len(item.action_content) > 200:
        text += f"<b>Contenido:</b>\n<pre>{item.action_content[:200]}...</pre>"
    else:
        text += f"<b>Contenido:</b>\n<pre>{item.action_content}</pre>"

    await callback.message.edit_text(
        text,
        reply_markup=button_actions_keyboard(item_key, item.is_active),
        parse_mode="HTML"
    )


# ═══════════════════════════════════════════════════════════════
# CREAR NUEVO BOTÓN - FLUJO FSM
# ═══════════════════════════════════════════════════════════════

@menu_config_router.callback_query(F.data == "menuconfig:create")
async def callback_create_button_start(
    callback: CallbackQuery,
    state: FSMContext
):
    """Inicia el flujo de creación de botón."""
    await state.clear()
    await state.set_state(MenuConfigStates.waiting_for_button_text)

    await callback.message.edit_text(
        "➕ <b>Crear Nuevo Botón</b>\n\n"
        "Paso 1/5: Escribe el texto que verá el usuario en el botón.\n\n"
        "Ejemplo: <code>Información de Contacto</code>\n\n"
        "Envía /cancel para cancelar.",
        parse_mode="HTML"
    )


@menu_config_router.message(MenuConfigStates.waiting_for_button_text)
async def process_button_text(message: Message, state: FSMContext):
    """Procesa el texto del botón."""
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Creación cancelada.")
        return

    button_text = message.text.strip()
    if len(button_text) > 100:
        await message.answer("❌ El texto es muy largo (máx 100 caracteres). Intenta de nuevo.")
        return

    await state.update_data(button_text=button_text)
    await state.set_state(MenuConfigStates.waiting_for_button_emoji)

    await message.answer(
        "➕ <b>Crear Nuevo Botón</b>\n\n"
        "Paso 2/5: Envía un emoji para el botón (opcional).\n\n"
        "Ejemplo: 📞 o ℹ️\n\n"
        "Envía <code>-</code> para omitir el emoji.",
        parse_mode="HTML"
    )


@menu_config_router.message(MenuConfigStates.waiting_for_button_emoji)
async def process_button_emoji(message: Message, state: FSMContext):
    """Procesa el emoji del botón."""
    emoji = message.text.strip()

    if emoji == "-" or emoji == "/cancel":
        emoji = None
    elif len(emoji) > 10:
        await message.answer("❌ Envía solo un emoji. Intenta de nuevo.")
        return

    await state.update_data(button_emoji=emoji)
    await state.set_state(MenuConfigStates.waiting_for_action_type)

    await message.answer(
        "➕ <b>Crear Nuevo Botón</b>\n\n"
        "Paso 3/5: Selecciona el tipo de acción:",
        reply_markup=action_type_keyboard(),
        parse_mode="HTML"
    )


@menu_config_router.callback_query(
    F.data.startswith("menuconfig:actiontype:"),
    MenuConfigStates.waiting_for_action_type
)
async def process_action_type(callback: CallbackQuery, state: FSMContext):
    """Procesa el tipo de acción."""
    action_type = callback.data.split(":")[-1]

    await state.update_data(action_type=action_type)
    await state.set_state(MenuConfigStates.waiting_for_action_content)

    if action_type == "info":
        prompt = (
            "➕ <b>Crear Nuevo Botón</b>\n\n"
            "Paso 4/5: Escribe el texto informativo que verá el usuario\n"
            "cuando presione este botón.\n\n"
            "Puedes usar formato HTML básico:\n"
            "• <code>&lt;b&gt;negrita&lt;/b&gt;</code>\n"
            "• <code>&lt;i&gt;itálica&lt;/i&gt;</code>\n"
            "• <code>&lt;code&gt;código&lt;/code&gt;</code>"
        )
    elif action_type == "url":
        prompt = (
            "➕ <b>Crear Nuevo Botón</b>\n\n"
            "Paso 4/5: Envía la URL a la que llevará el botón.\n\n"
            "Ejemplo: <code>https://ejemplo.com/contacto</code>"
        )
    else:  # contact
        prompt = (
            "➕ <b>Crear Nuevo Botón</b>\n\n"
            "Paso 4/5: Escribe la información de contacto.\n\n"
            "Ejemplo:\n"
            "<code>📧 Email: soporte@ejemplo.com\n"
            "📱 WhatsApp: +1234567890</code>"
        )

    await callback.message.edit_text(prompt, parse_mode="HTML")


@menu_config_router.message(MenuConfigStates.waiting_for_action_content)
async def process_action_content(message: Message, state: FSMContext):
    """Procesa el contenido de la acción."""
    content = message.text.strip()

    data = await state.get_data()
    action_type = data.get("action_type")

    # Validar URL si es tipo url
    if action_type == "url" and not content.startswith(("http://", "https://")):
        await message.answer("❌ La URL debe comenzar con http:// o https://")
        return

    await state.update_data(action_content=content)
    await state.set_state(MenuConfigStates.waiting_for_target_role)

    await message.answer(
        "➕ <b>Crear Nuevo Botón</b>\n\n"
        "Paso 5/5: ¿Para qué usuarios será visible este botón?",
        reply_markup=role_selection_keyboard(),
        parse_mode="HTML"
    )


@menu_config_router.callback_query(
    F.data.startswith("menuconfig:role:"),
    MenuConfigStates.waiting_for_target_role
)
async def process_target_role(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa el rol target y crea el botón."""
    target_role = callback.data.split(":")[-1]

    data = await state.get_data()

    # Generar item_key único
    import secrets
    item_key = f"{target_role}_{secrets.token_hex(4)}"

    container = ServiceContainer(session, callback.bot)

    # Obtener orden (último + 1)
    existing = await container.menu.get_menu_items_for_role(target_role, only_active=False)
    display_order = len(existing)
    row_number = display_order  # Cada botón en su propia fila por defecto

    # Crear el botón
    item = await container.menu.create_menu_item(
        item_key=item_key,
        button_text=data["button_text"],
        button_emoji=data.get("button_emoji"),
        action_type=data["action_type"],
        action_content=data["action_content"],
        target_role=target_role,
        display_order=display_order,
        row_number=row_number,
        created_by=callback.from_user.id
    )

    await state.clear()

    await callback.message.edit_text(
        f"✅ <b>Botón Creado Exitosamente</b>\n\n"
        f"<b>Key:</b> <code>{item.item_key}</code>\n"
        f"<b>Texto:</b> {item.button_text}\n"
        f"<b>Rol:</b> {item.target_role.upper()}\n"
        f"<b>Tipo:</b> {item.action_type}\n\n"
        f"El botón ya está activo y visible para los usuarios.",
        reply_markup=create_inline_keyboard([
            [{"text": "📋 Ver Todos los Botones", "callback_data": f"menuconfig:list:{target_role}"}],
            [{"text": "➕ Crear Otro", "callback_data": "menuconfig:create"}],
            [{"text": "🔙 Volver", "callback_data": "admin:menu_config"}]
        ]),
        parse_mode="HTML"
    )


# ═══════════════════════════════════════════════════════════════
# EDITAR BOTÓN
# ═══════════════════════════════════════════════════════════════

@menu_config_router.callback_query(F.data.startswith("menuconfig:edit:text:"))
async def callback_edit_button_text(
    callback: CallbackQuery,
    state: FSMContext
):
    """Inicia edición del texto del botón."""
    item_key = callback.data.split(":")[-1]

    await state.set_state(MenuConfigStates.editing_button_text)
    await state.update_data(editing_item_key=item_key)

    await callback.message.edit_text(
        "✏️ <b>Editar Texto del Botón</b>\n\n"
        "Envía el nuevo texto para el botón.\n\n"
        "Envía /cancel para cancelar.",
        parse_mode="HTML"
    )


@menu_config_router.message(MenuConfigStates.editing_button_text)
async def process_edit_button_text(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa la edición del texto."""
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Edición cancelada.")
        return

    new_text = message.text.strip()
    if len(new_text) > 100:
        await message.answer("❌ Texto muy largo (máx 100 caracteres).")
        return

    data = await state.get_data()
    item_key = data.get("editing_item_key")

    container = ServiceContainer(session, message.bot)
    item = await container.menu.update_menu_item(item_key, button_text=new_text)

    await state.clear()

    if item:
        await message.answer(
            f"✅ Texto actualizado: <b>{new_text}</b>",
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Error al actualizar.")


# ═══════════════════════════════════════════════════════════════
# TOGGLE Y DELETE
# ═══════════════════════════════════════════════════════════════

@menu_config_router.callback_query(F.data.startswith("menuconfig:toggle:"))
async def callback_toggle_button(callback: CallbackQuery, session: AsyncSession):
    """Activa/desactiva un botón."""
    item_key = callback.data.split(":")[-1]

    container = ServiceContainer(session, callback.bot)
    new_state = await container.menu.toggle_menu_item(item_key)

    if new_state is not None:
        status = "activado ✅" if new_state else "desactivado ❌"
        await callback.answer(f"Botón {status}", show_alert=True)

        # Refrescar vista
        item = await container.menu.get_menu_item(item_key)
        if item:
            await callback.message.edit_reply_markup(
                reply_markup=button_actions_keyboard(item_key, item.is_active)
            )
    else:
        await callback.answer("❌ Botón no encontrado", show_alert=True)


@menu_config_router.callback_query(F.data.startswith("menuconfig:delete:"))
async def callback_delete_button(callback: CallbackQuery, session: AsyncSession):
    """Elimina un botón (con confirmación)."""
    item_key = callback.data.split(":")[-1]

    # Mostrar confirmación
    await callback.message.edit_text(
        f"⚠️ <b>¿Eliminar botón?</b>\n\n"
        f"Key: <code>{item_key}</code>\n\n"
        f"Esta acción no se puede deshacer.",
        reply_markup=create_inline_keyboard([
            [
                {"text": "✅ Sí, eliminar", "callback_data": f"menuconfig:confirm_delete:{item_key}"},
                {"text": "❌ Cancelar", "callback_data": f"menuconfig:item:{item_key}"}
            ]
        ]),
        parse_mode="HTML"
    )


@menu_config_router.callback_query(F.data.startswith("menuconfig:confirm_delete:"))
async def callback_confirm_delete(callback: CallbackQuery, session: AsyncSession):
    """Confirma y ejecuta la eliminación."""
    item_key = callback.data.split(":")[-1]

    container = ServiceContainer(session, callback.bot)
    deleted = await container.menu.delete_menu_item(item_key)

    if deleted:
        await callback.message.edit_text(
            "✅ Botón eliminado correctamente.",
            reply_markup=create_inline_keyboard([
                [{"text": "🔙 Volver", "callback_data": "admin:menu_config"}]
            ])
        )
    else:
        await callback.answer("❌ Error al eliminar", show_alert=True)


# ═══════════════════════════════════════════════════════════════
# VOLVER AL MENÚ Y CANCELAR
# ═══════════════════════════════════════════════════════════════

@menu_config_router.callback_query(F.data == "menuconfig:main")
async def callback_menu_config_back(callback: CallbackQuery, session: AsyncSession):
    """Vuelve al menú principal de configuración de menús."""
    await callback_menu_config_main(callback, session)


@menu_config_router.callback_query(F.data == "menuconfig:cancel")
async def callback_cancel(callback: CallbackQuery, state: FSMContext):
    """Cancela cualquier operación en curso."""
    await state.clear()
    await callback.message.edit_text(
        "❌ Operación cancelada.",
        reply_markup=create_inline_keyboard([
            [{"text": "🔙 Volver", "callback_data": "admin:menu_config"}]
        ])
    )
