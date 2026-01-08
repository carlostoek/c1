"""
Handler de administración para Content Sets.

Panel de gestión completa para admins crear, editar, eliminar y
probar el envío de content sets multimedia.
"""

import logging
from typing import Optional, List

from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.shop.services.content_service import ContentService
from bot.shop.database.models import ContentSet
from bot.shop.database.enums import ContentType, ContentTier
from bot.services.lucien_voice import LucienVoiceService
from bot.middlewares.database import DatabaseMiddleware
from bot.middlewares.admin_auth import AdminAuthMiddleware
from bot.states.admin import ContentAdminStates
from config import Config

logger = logging.getLogger(__name__)

router = Router(name="content_admin")

# Middlewares
router.message.middleware(DatabaseMiddleware())
router.message.middleware(AdminAuthMiddleware())
router.callback_query.middleware(DatabaseMiddleware())
router.callback_query.middleware(AdminAuthMiddleware())


# ============================================================
# MENÚ PRINCIPAL
# ============================================================

@router.callback_query(F.data == "admin:content")
async def show_content_menu(callback: CallbackQuery, session: AsyncSession):
    """Muestra menú principal de gestión de Content Sets."""
    content_service = ContentService(session, callback.bot)
    content_sets = await content_service.list_content_sets(limit=1000)

    total_active = len([cs for cs in content_sets if cs.is_active])

    text = f"""🎬 <b>Gestión de Content Sets</b>

📊 <b>Estadísticas:</b>
• Total: <b>{len(content_sets)}</b>
• Activos: <b>{total_active}</b>
• Inactivos: <b>{len(content_sets) - total_active}</b>

<i>Administra el contenido multimedia que se entrega a través de
shop, narrativa y gamificación.</i>
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Listar Content Sets", callback_data="admin:content:list:1")],
        [InlineKeyboardButton(text="➕ Crear Content Set", callback_data="unified:create:content")],
        [InlineKeyboardButton(text="📊 Estadísticas de Uso", callback_data="admin:content:stats")],
        [InlineKeyboardButton(text="🔙 Volver", callback_data="admin:main")]
    ])

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()


# ============================================================
# LISTAR CONTENT SETS
# ============================================================

PAGE_SIZE = 5  # Content sets por página


@router.callback_query(F.data.startswith("admin:content:list:"))
async def list_content_sets(callback: CallbackQuery, session: AsyncSession):
    """Lista content sets con paginación."""
    page = int(callback.data.split(":")[-1])

    content_service = ContentService(session, callback.bot)
    all_sets = await content_service.list_content_sets(limit=1000)

    # Ordenar: activos primero, luego por created_at desc
    all_sets.sort(key=lambda x: (x.is_active, x.created_at), reverse=True)

    # Paginar
    start_idx = (page - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    page_sets = all_sets[start_idx:end_idx]
    total_pages = (len(all_sets) + PAGE_SIZE - 1) // PAGE_SIZE

    if not page_sets:
        await callback.answer("⚠️ No hay content sets en esta página", show_alert=True)
        return

    # Construir lista
    rows = []
    for cs in page_sets:
        status_emoji = "✅" if cs.is_active else "❌"
        tier_emoji = "🆓" if cs.tier == "free" else "👑" if cs.tier == "vip" else "💎"
        try:
            content_type = ContentType(cs.content_type)
            type_emoji = content_type.emoji
        except ValueError:
            type_emoji = "📦"

        rows.append([
            InlineKeyboardButton(
                text=f"{status_emoji} {tier_emoji} {type_emoji} {cs.name}",
                callback_data=f"admin:content:view:{cs.id}"
            )
        ])

    # Navegación
    nav_rows = []
    if page > 1:
        nav_rows.append([
            InlineKeyboardButton(text="⬅️ Página anterior", callback_data=f"admin:content:list:{page-1}")
        ])

    if page < total_pages:
        nav_rows.append([
            InlineKeyboardButton(text="➡️ Página siguiente", callback_data=f"admin:content:list:{page+1}")
        ])

    nav_rows.append([InlineKeyboardButton(text="🔙 Volver", callback_data="admin:content")])

    if nav_rows:
        rows.extend(nav_rows)

    rows.append([InlineKeyboardButton(text="➕ Crear Content Set", callback_data="unified:create:content")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=rows)

    text = f"""📋 <b>Content Sets (Página {page}/{total_pages})</b>

Mostrando: <b>{len(page_sets)}</b> de {len(all_sets)} totales

<i>Selecciona un content set para ver detalles o acciones.</i>
"""

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()


# ============================================================
# VER DETALLES
# ============================================================

@router.callback_query(F.data.startswith("admin:content:view:"))
async def view_content_set(callback: CallbackQuery, session: AsyncSession):
    """Muestra detalles de un content set."""
    content_set_id = int(callback.data.split(":")[-1])

    content_service = ContentService(session, callback.bot)
    content_set = await content_service.get_content_set(content_set_id)

    if not content_set:
        await callback.answer("❌ Content set no encontrado", show_alert=True)
        return

    stats = await content_service.get_content_set_stats(content_set_id)

    # Obtener referencias
    from bot.shop.services.shop import ShopService
    from bot.narrative.services.fragment import FragmentService
    from bot.gamification.services.reward import RewardService

    shop_service = ShopService(session)
    fragment_service = FragmentService(session)
    reward_service = RewardService(session)

    # Buscar referencias de forma eficiente
    shop_with_content = await content_service.get_content_set_shop_items(content_set_id)

    try:
        content_type = ContentType(content_set.content_type)
        type_name = content_type.display_name
    except ValueError:
        type_name = content_set.content_type

    try:
        content_tier = ContentTier(content_set.tier)
        tier_name = content_tier.display_name
    except ValueError:
        tier_name = content_set.tier

    text = f"""🎬 <b>{content_set.name}</b>

{'✅ Activo' if content_set.is_active else '❌ Inactivo'} • {tier_name}

<b>ID:</b> {content_set.id}
<b>Slug:</b> <code>{content_set.slug}</code>
<b>Tipo:</b> {type_name}
<b>Categoría:</b> {content_set.category or 'Sin categoría'}

<b>Archivos:</b> {len(content_set.file_ids)}
<b>Descripción:</b> {content_set.description or 'Sin descripción'}

<b>Estadísticas de Uso:</b>
• Total accesos: {stats['total_access']}
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Enviar a Usuario", callback_data=f"admin:content:send:{content_set.id}")],
        [InlineKeyboardButton(text="✏️ Editar", callback_data=f"admin:content:edit:{content_set.id}")],
        [
            InlineKeyboardButton(text="🗑️ Eliminar", callback_data=f"admin:content:delete:{content_set.id}"),
            InlineKeyboardButton(text="🔙 Volver", callback_data="admin:content:list:1")
        ]
    ])

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()


# ============================================================
# ELIMINAR CONTENT SET
# ============================================================

@router.callback_query(F.data.startswith("admin:content:delete:"))
async def delete_content_set(callback: CallbackQuery, session: AsyncSession):
    """Elimina (soft delete) un content set."""
    content_set_id = int(callback.data.split(":")[-1])

    content_service = ContentService(session, callback.bot)
    content_set = await content_service.get_content_set(content_set_id)

    if not content_set:
        await callback.answer("❌ Content set no encontrado", show_alert=True)
        return

    # Confirmación
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Sí, eliminar", callback_data=f"admin:content:delete_confirm:{content_set_id}"),
            InlineKeyboardButton(text="❌ Cancelar", callback_data=f"admin:content:view:{content_set_id}")
        ]
    ])

    await callback.message.edit_text(
        f"⚠️ <b>¿Eliminar Content Set?</b>\n\n"
        f"<b>{content_set.name}</b>\n\n"
        f"<i>Se desactivará el content set. No se eliminarán los datos.</i>",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:content:delete_confirm:"))
async def confirm_delete_content_set(callback: CallbackQuery, session: AsyncSession):
    """Confirma eliminación de content set."""
    content_set_id = int(callback.data.split(":")[-1])

    content_service = ContentService(session, callback.bot)

    try:
        await content_service.delete_content_set(content_set_id, soft_delete=True)
        await session.commit()

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Volver", callback_data="admin:content:list:1")]
        ])

        await callback.message.edit_text(
            "✅ <b>Content Set desactivado correctamente</b>\n\n"
            "<i>El content set ya no estará disponible para nuevos usuarios.</i>",
            parse_mode="HTML",
            reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Error deleting content set {content_set_id}: {e}")
        await callback.message.edit_text(
            f"❌ <b>Error al eliminar:</b>\n\n{str(e)}",
            parse_mode="HTML"
        )

    await callback.answer()


# ============================================================
# ENVIAR CONTENT SET A USUARIO (TESTING)
# ============================================================

@router.callback_query(F.data.startswith("admin:content:send:"))
async def prompt_send_content_set(callback: CallbackQuery, state: FSMContext):
    """Solicita ID de usuario para enviar content set (testing)."""
    content_set_id = int(callback.data.split(":")[-1])

    await state.update_data(test_content_set_id=content_set_id)

    await callback.message.edit_text(
        "📤 <b>Enviar Content Set a Usuario</b>\n\n"
        "Ingresa el ID del usuario de Telegram (user_id):\n\n"
        "<i>Formato: número (ej: 123456789)</i>\n\n"
        "<i>Esta función es para testing del contenido.</i>",
        parse_mode="HTML"
    )
    await state.set_state(ContentAdminStates.waiting_test_user_id)
    await callback.answer()


@router.message(ContentAdminStates.waiting_test_user_id)
async def send_test_content_set(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    """Envía content set a usuario para testing."""
    # DEBUG: Log estado actual
    current_state = await state.get_state()
    logger.info(f"🔍 Handler ejecutado! Estado actual: {current_state}")
    logger.info(f"🔍 Mensaje recibido: {message.text} de user {message.from_user.id}")

    if not message.text or not message.text.strip().isdigit():
        logger.info("❌ Validación falló: no es un número")
        await message.answer("❌ Ingresa un ID de usuario válido (números)")
        return

    logger.info("✅ Validación pasó: es un número")
    user_id = int(message.text.strip())
    logger.info(f"✅ user_id extraído: {user_id}")

    data = await state.get_data()
    logger.info(f"🔍 State data: {data}")
    content_set_id = data.get('test_content_set_id')

    logger.info(f"📤 Enviando content_set_id={content_set_id} a user_id={user_id}")

    if not content_set_id:
        logger.error("❌ content_set_id es None! No se puede enviar.")
        await message.answer("❌ Error: no se pudo identificar el content set")
        await state.clear()
        return

    logger.info("✅ content_set_id válido, creando ContentService...")
    content_service = ContentService(session, bot)
    logger.info("✅ ContentService creado, iniciando envío...")

    try:
        success, msg = await content_service.send_content_set(
            user_id=user_id,
            content_set_id=content_set_id,
            context_message="🧪 <b>Test de Envío</b>\n\nContenido de prueba desde admin panel.",
            delivery_context="admin_test",
            trigger_type="manual",
            skip_vip_validation=True  # Admin testing mode - saltar validación VIP
        )

        logger.info(f"📤 Resultado envío: success={success}, msg={msg}")

        if success:
            await message.answer(
                f"✅ <b>Content Set enviado</b>\n\n{msg}\n\n"
                f"<i>Usuario: {user_id}</i>",
                parse_mode="HTML"
            )
        else:
            await message.answer(
                f"❌ <b>Error al enviar:</b>\n\n{msg}",
                parse_mode="HTML"
            )

    except Exception as e:
        logger.error(f"Error sending test content set: {e}", exc_info=True)
        await message.answer(
            f"❌ <b>Error:</b>\n\n{str(e)}",
            parse_mode="HTML"
        )

    await state.clear()


# ============================================================
# ESTADÍSTICAS
# ============================================================

@router.callback_query(F.data == "admin:content:stats")
async def show_content_stats(callback: CallbackQuery, session: AsyncSession):
    """Muestra estadísticas de uso de content sets."""
    content_service = ContentService(session, callback.bot)
    content_sets = await content_service.list_content_sets(limit=1000)

    if not content_sets:
        await callback.answer("⚠️ No hay content sets para mostrar estadísticas", show_alert=True)
        return

    # Calcular estadísticas
    total_access = 0
    most_used = []
    tier_counts = {"free": 0, "vip": 0, "premium": 0, "gift": 0}
    type_counts = {}

    for cs in content_sets:
        stats = await content_service.get_content_set_stats(cs.id)
        total_access += stats['total_access']
        tier_counts[cs.tier] = tier_counts.get(cs.tier, 0) + stats['total_access']
        type_counts[cs.content_type] = type_counts.get(cs.content_type, 0) + stats['total_access']

        if stats['total_access'] > 0:
            most_used.append((cs, stats['total_access']))

    # Top 5 más usados
    most_used.sort(key=lambda x: x[1], reverse=True)
    top_5 = most_used[:5]

    text = f"""📊 <b>Estadísticas de Content Sets</b>

<b>Resumen General:</b>
• Total content sets: <b>{len(content_sets)}</b>
• Total accesos: <b>{total_access}</b>
• Promedio por set: <b>{total_access / len(content_sets):.1f}</b>

<b>Por Tier:</b>
• 🆓 Gratis: {tier_counts['free']} accesos
• 👑 VIP: {tier_counts['vip']} accesos
• 💎 Premium: {tier_counts['premium']} accesos
• 🎁 Regalo: {tier_counts['gift']} accesos

<b>Top 5 Más Usados:</b>
"""

    for i, (cs, count) in enumerate(top_5, 1):
        tier_emoji = "🆓" if cs.tier == "free" else "👑" if cs.tier == "vip" else "💎"
        text += f"\n{i}. {tier_emoji} <b>{cs.name}</b>: {count} accesos"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Volver", callback_data="admin:content")]
    ])

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()


# ============================================================
# EDITAR CONTENT SET
# ============================================================

@router.callback_query(F.data.startswith("admin:content:edit:"))
async def start_edit_content_set(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Inicia edición de content set."""
    content_set_id = int(callback.data.split(":")[-1])

    content_service = ContentService(session, callback.bot)
    content_set = await content_service.get_content_set(content_set_id)

    if not content_set:
        await callback.answer("❌ Content set no encontrado", show_alert=True)
        return

    await state.update_data(edit_content_set_id=content_set_id)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Nombre", callback_data="admin:content:edit:name")],
        [InlineKeyboardButton(text="📝 Descripción", callback_data="admin:content:edit:description")],
        [InlineKeyboardButton(text="🔄 Cambiar Estado", callback_data="admin:content:edit:toggle")],
        [InlineKeyboardButton(text="🔙 Volver", callback_data=f"admin:content:view:{content_set_id}")]
    ])

    await callback.message.edit_text(
        f"✏️ <b>Editar Content Set</b>\n\n"
        f"<b>{content_set.name}</b>\n\n"
        f"¿Qué deseas modificar?",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "admin:content:edit:toggle")
async def toggle_content_set_status(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Activa/desactiva un content set."""
    data = await state.get_data()
    content_set_id = data.get('edit_content_set_id')

    if not content_set_id:
        await callback.answer("❌ Error: no se pudo identificar el content set", show_alert=True)
        await state.clear()
        return

    content_service = ContentService(session, callback.bot)
    content_set = await content_service.get_content_set(content_set_id)

    if not content_set:
        await callback.answer("❌ Content set no encontrado", show_alert=True)
        await state.clear()
        return

    # Toggle status
    new_status = not content_set.is_active
    await content_service.update_content_set(content_set_id, is_active=new_status)
    await session.commit()

    status_text = "activado" if new_status else "desactivado"
    status_emoji = "✅" if new_status else "❌"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Volver", callback_data=f"admin:content:view:{content_set_id}")]
    ])

    await callback.message.edit_text(
        f"{status_emoji} <b>Content Set {status_text}</b>\n\n"
        f"<b>{content_set.name}</b>\n\n"
        f"El content set ahora está {'activo' if new_status else 'inactivo'}.",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "admin:content:edit:name")
async def prompt_edit_content_set_name(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Solicita nuevo nombre para content set."""
    data = await state.get_data()
    content_set_id = data.get('edit_content_set_id')

    if not content_set_id:
        await callback.answer("❌ Error: no se pudo identificar el content set", show_alert=True)
        await state.clear()
        return

    content_service = ContentService(session, callback.bot)
    content_set = await content_service.get_content_set(content_set_id)

    if not content_set:
        await callback.answer("❌ Content set no encontrado", show_alert=True)
        await state.clear()
        return

    await callback.message.edit_text(
        f"✏️ <b>Editar Nombre de Content Set</b>\n\n"
        f"<b>Actual:</b> {content_set.name}\n\n"
        f"Ingresa el nuevo nombre:",
        parse_mode="HTML"
    )
    await state.set_state(ContentAdminStates.waiting_content_set_name)
    await callback.answer()


@router.message(ContentAdminStates.waiting_content_set_name)
async def edit_content_set_name(message: Message, state: FSMContext, session: AsyncSession):
    """Actualiza nombre del content set."""
    if not message.text or len(message.text.strip()) < 3:
        await message.answer("❌ El nombre debe tener al menos 3 caracteres")
        return

    new_name = message.text.strip()
    data = await state.get_data()
    content_set_id = data.get('edit_content_set_id')

    if not content_set_id:
        await message.answer("❌ Error: no se pudo identificar el content set")
        await state.clear()
        return

    content_service = ContentService(session, message.bot)

    try:
        await content_service.update_content_set(content_set_id, name=new_name)
        await session.commit()

        await message.answer(
            f"✅ <b>Nombre actualizado</b>\n\n"
            f"Nuevo nombre: <b>{new_name}</b>",
            parse_mode="HTML"
        )
        await state.clear()

    except Exception as e:
        logger.error(f"Error updating content set name {content_set_id}: {e}")
        await message.answer(
            f"❌ <b>Error al actualizar:</b>\n\n{str(e)}",
            parse_mode="HTML"
        )


@router.callback_query(F.data == "admin:content:edit:description")
async def prompt_edit_content_set_description(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Solicita nueva descripción para content set."""
    data = await state.get_data()
    content_set_id = data.get('edit_content_set_id')

    if not content_set_id:
        await callback.answer("❌ Error: no se pudo identificar el content set", show_alert=True)
        await state.clear()
        return

    content_service = ContentService(session, callback.bot)
    content_set = await content_service.get_content_set(content_set_id)

    if not content_set:
        await callback.answer("❌ Content set no encontrado", show_alert=True)
        await state.clear()
        return

    await callback.message.edit_text(
        f"✏️ <b>Editar Descripción de Content Set</b>\n\n"
        f"<b>Actual:</b> {content_set.description or 'Sin descripción'}\n\n"
        f"Ingresa la nueva descripción:",
        parse_mode="HTML"
    )
    await state.set_state(ContentAdminStates.waiting_content_set_description)
    await callback.answer()


@router.message(ContentAdminStates.waiting_content_set_description)
async def edit_content_set_description(message: Message, state: FSMContext, session: AsyncSession):
    """Actualiza descripción del content set."""
    if not message.text or len(message.text.strip()) < 10:
        await message.answer("❌ La descripción debe tener al menos 10 caracteres")
        return

    new_description = message.text.strip()
    data = await state.get_data()
    content_set_id = data.get('edit_content_set_id')

    if not content_set_id:
        await message.answer("❌ Error: no se pudo identificar el content set")
        await state.clear()
        return

    content_service = ContentService(session, message.bot)

    try:
        await content_service.update_content_set(content_set_id, description=new_description)
        await session.commit()

        await message.answer(
            f"✅ <b>Descripción actualizada</b>\n\n"
            f"Nueva descripción: <b>{new_description}</b>",
            parse_mode="HTML"
        )
        await state.clear()

    except Exception as e:
        logger.error(f"Error updating content set description {content_set_id}: {e}")
        await message.answer(
            f"❌ <b>Error al actualizar:</b>\n\n{str(e)}",
            parse_mode="HTML"
        )
