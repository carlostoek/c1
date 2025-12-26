"""Handler CRUD completo de niveles de gamificación.

Responsabilidades:
- Listar niveles con distribución de usuarios
- Ver detalles de nivel individual + stats
- Editar campos inline (name, min_besitos, order, benefits)
- Activar/desactivar niveles
- Eliminar con validaciones (reasignar usuarios)
"""

import logging
import json
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.admin import IsAdmin
from bot.middlewares import DatabaseMiddleware
from bot.gamification.services.container import GamificationContainer
from bot.gamification.states.admin import LevelConfigStates
from bot.utils.keyboards import create_inline_keyboard

logger = logging.getLogger(__name__)

# Router para configuración de niveles
router = Router(name="level_config")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())
router.message.middleware(DatabaseMiddleware())
router.callback_query.middleware(DatabaseMiddleware())


# ========================================
# LISTA DE NIVELES
# ========================================

@router.callback_query(F.data == "gamif:admin:levels")
async def list_levels(callback: CallbackQuery, session: AsyncSession):
    """Muestra lista de niveles con distribución de usuarios.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    logger.info(f"📊 Usuario {callback.from_user.id} viendo lista de niveles")

    container = GamificationContainer(session, callback.bot)

    # Obtener niveles ordenados por order
    levels = await container.level.get_all_levels(active_only=False)

    # Obtener distribución de usuarios
    distribution = await container.level.get_level_distribution()

    if not levels:
        text = """📊 <b>Gestión de Niveles</b>

⚠️ No hay niveles configurados.

Los niveles definen la progresión de usuarios según besitos acumulados.

<b>Ejemplo de estructura:</b>
1. Novato (0-500 besitos)
2. Regular (500-2000 besitos)
3. Fanático (2000-5000 besitos)"""

        keyboard = [
            [{"text": "➕ Crear Primer Nivel", "callback_data": "gamif:wizard:level_prog"}],
            [{"text": "🔙 Volver", "callback_data": "gamif:menu"}]
        ]

        await callback.message.edit_text(
            text=text,
            reply_markup=create_inline_keyboard(keyboard),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    # Construir texto con niveles
    text = """📊 <b>NIVELES CONFIGURADOS</b>
━━━━━━━━━━━━━━━━

"""

    total_users = sum(distribution.values())

    for level in levels:
        status = "✅" if level.active else "❌"
        users_count = distribution.get(level.name, 0)
        percentage = (users_count / total_users * 100) if total_users > 0 else 0

        text += f"""{status} <b>{level.order}. {level.name}</b>
   └ {level.min_besitos:,} besitos mínimos
   └ {users_count} usuarios ({percentage:.1f}%)

"""

    text += f"\n<i>Total: {len(levels)} niveles | {total_users} usuarios distribuidos</i>"

    # Botones por nivel
    keyboard = []
    for level in levels:
        status_emoji = "✅" if level.active else "❌"
        users_count = distribution.get(level.name, 0)
        keyboard.append([{
            "text": f"{status_emoji} {level.order}. {level.name} ({users_count} usuarios)",
            "callback_data": f"gamif:level:view:{level.id}"
        }])

    # Botones de acciones
    keyboard.append([{"text": "➕ Crear Nivel", "callback_data": "gamif:wizard:level_prog"}])
    keyboard.append([{"text": "🔙 Volver", "callback_data": "gamif:menu"}])

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(keyboard),
        parse_mode="HTML"
    )
    await callback.answer()


# ========================================
# VISTA DETALLADA DE NIVEL
# ========================================

@router.callback_query(F.data.startswith("gamif:level:view:"))
async def view_level_details(callback: CallbackQuery, session: AsyncSession):
    """Muestra detalles completos de un nivel.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    level_id = int(callback.data.split(":")[-1])

    logger.info(f"👁️ Usuario {callback.from_user.id} viendo nivel {level_id}")

    container = GamificationContainer(session, callback.bot)
    level = await container.level.get_level_by_id(level_id)

    if not level:
        await callback.answer("❌ Nivel no encontrado", show_alert=True)
        return

    # Obtener usuarios en este nivel
    users_in_level = await container.level.get_users_in_level(level_id, limit=100)
    users_count = len(users_in_level)

    # Obtener nivel siguiente
    next_level = await container.level.get_next_level(level_id)

    # Construir texto
    status_text = "✅ Activo" if level.active else "❌ Inactivo"

    text = f"""📊 <b>Nivel: {level.name}</b>

<b>📋 INFORMACIÓN</b>
━━━━━━━━━━━━━━━━
• Orden: {level.order}
• Besitos mínimos: {level.min_besitos:,}
• Estado: {status_text}
"""

    if level.benefits:
        try:
            benefits = json.loads(level.benefits)
            if benefits:
                text += f"\n<b>🎁 Beneficios:</b>\n"
                for key, value in benefits.items():
                    text += f"  • {key}: {value}\n"
        except (json.JSONDecodeError, AttributeError):
            pass

    text += f"""
<b>👥 ESTADÍSTICAS</b>
━━━━━━━━━━━━━━━━
• Usuarios en este nivel: {users_count}
"""

    if next_level:
        text += f"• Siguiente nivel: {next_level.name} ({next_level.min_besitos:,} besitos)"
    else:
        text += "• <i>Nivel máximo alcanzado</i>"

    # Botones de acciones
    keyboard = []

    # Editar campos
    keyboard.append([
        {"text": "✏️ Editar Nombre", "callback_data": f"gamif:level:edit_field:{level_id}:name"},
        {"text": "💰 Editar Besitos", "callback_data": f"gamif:level:edit_field:{level_id}:min_besitos"}
    ])
    keyboard.append([
        {"text": "🔢 Editar Orden", "callback_data": f"gamif:level:edit_field:{level_id}:order"},
        {"text": "🎁 Editar Beneficios", "callback_data": f"gamif:level:edit_field:{level_id}:benefits"}
    ])

    # Activar/desactivar
    if level.active:
        keyboard.append([{"text": "🔴 Desactivar", "callback_data": f"gamif:level:toggle:{level_id}"}])
    else:
        keyboard.append([{"text": "🟢 Activar", "callback_data": f"gamif:level:toggle:{level_id}"}])

    # Eliminar
    keyboard.append([{"text": "🗑️ Eliminar", "callback_data": f"gamif:level:delete_confirm:{level_id}"}])

    # Volver
    keyboard.append([{"text": "🔙 Volver a Lista", "callback_data": "gamif:admin:levels"}])

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(keyboard),
        parse_mode="HTML"
    )
    await callback.answer()


# ========================================
# EDITAR CAMPOS
# ========================================

@router.callback_query(F.data.startswith("gamif:level:edit_field:"))
async def start_edit_field(callback: CallbackQuery, state: FSMContext):
    """Inicia edición de campo específico.

    Callback format: gamif:level:edit_field:{level_id}:{field}
    """
    parts = callback.data.split(":")
    level_id = int(parts[3])
    field = parts[4]

    await state.update_data(editing_level_id=level_id, editing_field=field)
    await state.set_state(LevelConfigStates.waiting_for_field_value)

    field_names = {
        "name": "Nombre del nivel",
        "min_besitos": "Besitos mínimos",
        "order": "Orden de progresión",
        "benefits": "Beneficios (JSON)"
    }

    examples = {
        "name": "Ejemplo: Maestro, Leyenda",
        "min_besitos": "Ejemplo: 5000",
        "order": "Ejemplo: 5",
        "benefits": 'Ejemplo: {"acceso_vip": true, "descuento": "10%"}'
    }

    text = f"""✏️ <b>Editar {field_names.get(field, field)}</b>

Envía el nuevo valor:

{examples.get(field, "")}"""

    keyboard = [[{"text": "❌ Cancelar", "callback_data": "gamif:level:cancel_edit"}]]

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(keyboard),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(LevelConfigStates.waiting_for_field_value)
async def process_field_edit(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa nuevo valor de campo y actualiza.

    Args:
        message: Mensaje del admin
        state: FSM context
        session: Sesión de BD
    """
    data = await state.get_data()
    level_id = data["editing_level_id"]
    field = data["editing_field"]
    new_value = message.text.strip()

    container = GamificationContainer(session, message.bot)
    level = await container.level.get_level_by_id(level_id)

    if not level:
        await message.answer("❌ Nivel no encontrado")
        await state.clear()
        return

    # Validar y convertir según campo
    try:
        if field == "name":
            if len(new_value) < 3:
                raise ValueError("El nombre debe tener al menos 3 caracteres")
            await container.level.update_level(level_id, name=new_value)
            success_msg = f"✅ Nombre actualizado a: <b>{new_value}</b>"

        elif field == "min_besitos":
            besitos = int(new_value)
            if besitos < 0:
                raise ValueError("Los besitos no pueden ser negativos")
            await container.level.update_level(level_id, min_besitos=besitos)
            success_msg = f"✅ Besitos mínimos actualizados a: <b>{besitos:,}</b>"

        elif field == "order":
            order = int(new_value)
            if order <= 0:
                raise ValueError("El orden debe ser mayor a 0")
            await container.level.update_level(level_id, order=order)
            success_msg = f"✅ Orden actualizado a: <b>{order}</b>"

        elif field == "benefits":
            # Validar que sea JSON válido
            benefits = json.loads(new_value)
            await container.level.update_level(level_id, benefits=benefits)
            success_msg = "✅ Beneficios actualizados"

        else:
            raise ValueError("Campo desconocido")

        logger.info(f"✅ Nivel {level_id} actualizado: {field} = {new_value}")

        keyboard = [
            [{"text": "👁️ Ver Nivel", "callback_data": f"gamif:level:view:{level_id}"}],
            [{"text": "📋 Lista Niveles", "callback_data": "gamif:admin:levels"}]
        ]

        await message.answer(
            success_msg,
            reply_markup=create_inline_keyboard(keyboard),
            parse_mode="HTML"
        )

    except ValueError as e:
        await message.answer(
            f"❌ Error de validación:\n\n{str(e)}\n\n"
            "Por favor, envía un valor válido.",
            parse_mode="HTML"
        )
        return

    except Exception as e:
        logger.error(f"Error actualizando nivel: {e}", exc_info=True)
        await message.answer(
            f"❌ Error al actualizar:\n\n{str(e)}\n\n"
            "Verifica el formato e intenta nuevamente."
        )
        return

    finally:
        await state.clear()


# ========================================
# ACTIVAR/DESACTIVAR
# ========================================

@router.callback_query(F.data.startswith("gamif:level:toggle:"))
async def toggle_level(callback: CallbackQuery, session: AsyncSession):
    """Activa o desactiva un nivel.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    level_id = int(callback.data.split(":")[-1])

    container = GamificationContainer(session, callback.bot)
    level = await container.level.get_level_by_id(level_id)

    if not level:
        await callback.answer("❌ Nivel no encontrado", show_alert=True)
        return

    # Toggle
    new_state = not level.active
    await container.level.update_level(level_id, active=new_state)

    status_text = "activado" if new_state else "desactivado"
    logger.info(f"🔄 Nivel {level_id} ({level.name}) {status_text}")

    await callback.answer(f"✅ Nivel {status_text}")

    # Refrescar vista
    await view_level_details(callback, session)


# ========================================
# ELIMINAR CON VALIDACIONES
# ========================================

@router.callback_query(F.data.startswith("gamif:level:delete_confirm:"))
async def confirm_delete_level(callback: CallbackQuery, session: AsyncSession):
    """Muestra confirmación antes de eliminar nivel.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    level_id = int(callback.data.split(":")[-1])

    container = GamificationContainer(session, callback.bot)
    level = await container.level.get_level_by_id(level_id)

    if not level:
        await callback.answer("❌ Nivel no encontrado", show_alert=True)
        return

    # Verificar si hay usuarios en este nivel
    users_in_level = await container.level.get_users_in_level(level_id, limit=100)
    users_count = len(users_in_level)

    if users_count > 0:
        # Hay usuarios, pedir reasignación
        text = f"""⚠️ <b>Advertencia: Nivel con Usuarios</b>

El nivel <b>{level.name}</b> tiene <b>{users_count} usuarios</b> asignados.

Antes de eliminar, debes reasignar estos usuarios a otro nivel.

<b>¿Qué deseas hacer?</b>"""

        # Obtener otros niveles para reasignar
        all_levels = await container.level.get_all_levels(active_only=False)
        other_levels = [l for l in all_levels if l.id != level_id]

        keyboard = []
        for other_level in other_levels:
            keyboard.append([{
                "text": f"→ Reasignar a {other_level.name}",
                "callback_data": f"gamif:level:reassign:{level_id}:{other_level.id}"
            }])

        keyboard.append([{"text": "❌ Cancelar", "callback_data": f"gamif:level:view:{level_id}"}])

        await callback.message.edit_text(
            text=text,
            reply_markup=create_inline_keyboard(keyboard),
            parse_mode="HTML"
        )
        await callback.answer()

    else:
        # No hay usuarios, confirmación simple
        text = f"""⚠️ <b>Confirmar Eliminación</b>

¿Estás seguro de eliminar el nivel <b>{level.name}</b>?

<b>Orden:</b> {level.order}
<b>Besitos mínimos:</b> {level.min_besitos:,}

Esta acción no se puede deshacer."""

        keyboard = [
            [
                {"text": "✅ Sí, Eliminar", "callback_data": f"gamif:level:delete:{level_id}"},
                {"text": "❌ Cancelar", "callback_data": f"gamif:level:view:{level_id}"}
            ]
        ]

        await callback.message.edit_text(
            text=text,
            reply_markup=create_inline_keyboard(keyboard),
            parse_mode="HTML"
        )
        await callback.answer()


@router.callback_query(F.data.startswith("gamif:level:reassign:"))
async def reassign_and_delete(callback: CallbackQuery, session: AsyncSession):
    """Reasigna usuarios a otro nivel y luego elimina.

    Callback format: gamif:level:reassign:{from_level_id}:{to_level_id}
    """
    parts = callback.data.split(":")
    from_level_id = int(parts[3])
    to_level_id = int(parts[4])

    container = GamificationContainer(session, callback.bot)

    from_level = await container.level.get_level_by_id(from_level_id)
    to_level = await container.level.get_level_by_id(to_level_id)

    if not from_level or not to_level:
        await callback.answer("❌ Niveles no encontrados", show_alert=True)
        return

    # Reasignar usuarios
    users = await container.level.get_users_in_level(from_level_id)
    reassigned_count = 0

    for user_gamif in users:
        await container.level.set_user_level(user_gamif.user_id, to_level_id)
        reassigned_count += 1

    logger.info(
        f"🔄 Reasignados {reassigned_count} usuarios de {from_level.name} "
        f"a {to_level.name}"
    )

    # Ahora eliminar nivel
    await container.level.delete_level(from_level_id)

    logger.info(f"🗑️ Nivel {from_level_id} ({from_level.name}) eliminado")

    text = f"""✅ <b>Nivel Eliminado</b>

• Nivel eliminado: {from_level.name}
• Usuarios reasignados: {reassigned_count}
• Nuevo nivel: {to_level.name}

Los usuarios han sido migrados correctamente."""

    keyboard = [[{"text": "📋 Ver Niveles", "callback_data": "gamif:admin:levels"}]]

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(keyboard),
        parse_mode="HTML"
    )
    await callback.answer("✅ Nivel eliminado y usuarios reasignados")


@router.callback_query(F.data.startswith("gamif:level:delete:"))
async def delete_level(callback: CallbackQuery, session: AsyncSession):
    """Elimina nivel sin usuarios.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    level_id = int(callback.data.split(":")[-1])

    container = GamificationContainer(session, callback.bot)
    level = await container.level.get_level_by_id(level_id)

    if not level:
        await callback.answer("❌ Nivel no encontrado", show_alert=True)
        return

    await container.level.delete_level(level_id)

    logger.info(f"🗑️ Nivel {level_id} ({level.name}) eliminado")

    text = f"""✅ <b>Nivel Eliminado</b>

El nivel <b>{level.name}</b> ha sido eliminado del sistema."""

    keyboard = [[{"text": "📋 Ver Niveles", "callback_data": "gamif:admin:levels"}]]

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(keyboard),
        parse_mode="HTML"
    )
    await callback.answer("✅ Nivel eliminado")


# ========================================
# CANCELAR EDICIÓN
# ========================================

@router.callback_query(F.data == "gamif:level:cancel_edit")
async def cancel_edit(callback: CallbackQuery, state: FSMContext):
    """Cancela edición en curso.

    Args:
        callback: Callback query
        state: FSM context
    """
    data = await state.get_data()
    level_id = data.get("editing_level_id")

    await state.clear()

    if level_id:
        text = "❌ Edición cancelada."
        keyboard = [[{"text": "👁️ Volver al Nivel", "callback_data": f"gamif:level:view:{level_id}"}]]
    else:
        text = "❌ Edición cancelada."
        keyboard = [[{"text": "📋 Ver Niveles", "callback_data": "gamif:admin:levels"}]]

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(keyboard)
    )
    await callback.answer()
