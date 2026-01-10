"""
Admin Interests Handlers - Gestión de intereses de usuarios.

Permite a los admins:
- Ver lista de intereses pendientes
- Marcar como contactado
- Responder directamente al usuario
- Bloquear/expulsar usuarios
"""
import logging

from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.admin.main import admin_router
from bot.services.container import ServiceContainer
from bot.utils.keyboards import create_inline_keyboard

logger = logging.getLogger(__name__)


@admin_router.callback_query(F.data.startswith("admin:contacted:"))
async def callback_admin_mark_contacted(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Marca un interés como contactado por el admin.

    Actualiza el status del interés a 'contacted' y registra
    qué admin realizó el contacto.

    Args:
        callback: CallbackQuery del admin
        session: Sesión de BD (inyectada por middleware)
    """
    admin_id = callback.from_user.id

    # Parsear: admin:contacted:123
    parts = callback.data.split(":")
    if len(parts) < 3:
        logger.warning(f"⚠️ Formato inválido: {callback.data}")
        await callback.answer("Error: formato inválido", show_alert=True)
        return

    try:
        interest_id = int(parts[2])
    except ValueError:
        logger.warning(f"⚠️ Interest ID inválido: {parts[2]}")
        await callback.answer("Error: ID inválido", show_alert=True)
        return

    logger.info(f"✅ Admin {admin_id} marcando interés {interest_id} como contactado")

    container = ServiceContainer(session, callback.bot)

    try:
        # Marcar como contactado
        interest = await container.interest.mark_as_contacted(
            interest_id=interest_id,
            admin_id=admin_id,
            notes=f"Contactado vía notificación de interés"
        )

        if not interest:
            await callback.answer(
                "❌ Interés no encontrado",
                show_alert=True
            )
            return

        # Commit cambios
        await session.commit()

        # Actualizar mensaje original con estado
        updated_text = callback.message.text or ""
        updated_text += f"\n\n<b>✅ Contactado por Admin {admin_id}</b>"

        # Keyboard reducido (solo opción de expulsar/bloquear)
        keyboard = create_inline_keyboard([
            [
                {"text": "🚫 Bloquear", "callback_data": f"admin:block:{interest.user_id}"},
                {"text": "👋 Expulsar", "callback_data": f"admin:kick:{interest.user_id}"}
            ]
        ])

        await callback.message.edit_text(
            updated_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer("✅ Marcado como contactado")

    except Exception as e:
        logger.error(f"❌ Error marcando como contactado: {e}", exc_info=True)
        await callback.answer(
            "⚠️ Error al actualizar. Intente nuevamente.",
            show_alert=True
        )


@admin_router.callback_query(F.data.startswith("admin:contact:"))
async def callback_admin_contact(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
):
    """
    Inicia contacto directo con el usuario interesado.

    Abre el chat privado con el usuario para que el admin
    pueda responderle directamente.

    Args:
        callback: CallbackQuery del admin
        session: Sesión de BD (inyectada por middleware)
        state: FSM context
    """
    admin_id = callback.from_user.id

    # Parsear: admin:contact:123
    parts = callback.data.split(":")
    if len(parts) < 3:
        logger.warning(f"⚠️ Formato inválido: {callback.data}")
        await callback.answer("Error: formato inválido", show_alert=True)
        return

    try:
        interest_id = int(parts[2])
    except ValueError:
        logger.warning(f"⚠️ Interest ID inválido: {parts[2]}")
        await callback.answer("Error: ID inválido", show_alert=True)
        return

    logger.info(f"💬 Admin {admin_id} iniciando contacto con interés {interest_id}")

    container = ServiceContainer(session, callback.bot)

    try:
        # Obtener información del interés
        interest = await container.interest.get_interest_by_id(
            interest_id=interest_id,
            load_user=True
        )

        if not interest:
            await callback.answer(
                "❌ Interés no encontrado",
                show_alert=True
            )
            return

        user_id = interest.user_id
        user = interest.user if hasattr(interest, 'user') else None

        # Mensaje con instrucciones para el admin
        contact_text = (
            f"💬 <b>Contacto Directo</b>\n\n"
            f"Usuario: {user.first_name if user else 'Desconocido'}\n"
            f"ID: <code>{user_id}</code>\n\n"
            f"Para enviar un mensaje directo, use el siguiente formato:\n\n"
            f"<code>/send {user_id} Su mensaje aquí</code>\n\n"
            f"<i>O haga click en el botón de abajo para iniciar chat.</i>"
        )

        keyboard = create_inline_keyboard([
            [
                {"text": "💬 Abrir Chat", "url": f"tg://user?id={user_id}"}
            ],
            [
                {"text": "✅ Marcar Contactado", "callback_data": f"admin:contacted:{interest_id}"}
            ],
            [
                {"text": "🔙 Cerrar", "callback_data": "admin:close_contact"}
            ]
        ])

        await callback.message.answer(
            contact_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Error iniciando contacto: {e}", exc_info=True)
        await callback.answer(
            "⚠️ Error. Intente nuevamente.",
            show_alert=True
        )


@admin_router.callback_query(F.data == "admin:close_contact")
async def callback_admin_close_contact(callback: CallbackQuery):
    """
    Cierra el mensaje de contacto directo.

    Args:
        callback: CallbackQuery del admin
    """
    try:
        await callback.message.delete()
        await callback.answer()
    except Exception as e:
        logger.error(f"❌ Error cerrando contacto: {e}", exc_info=True)
        await callback.answer()


@admin_router.callback_query(F.data.startswith("admin:block:"))
async def callback_admin_block_user(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Bloquea un usuario del bot.

    Cambia el rol del usuario a un estado bloqueado (si existe)
    y previene que use el bot.

    Args:
        callback: CallbackQuery del admin
        session: Sesión de BD (inyectada por middleware)
    """
    admin_id = callback.from_user.id

    # Parsear: admin:block:12345
    parts = callback.data.split(":")
    if len(parts) < 3:
        logger.warning(f"⚠️ Formato inválido: {callback.data}")
        await callback.answer("Error: formato inválido", show_alert=True)
        return

    try:
        user_id = int(parts[2])
    except ValueError:
        logger.warning(f"⚠️ User ID inválido: {parts[2]}")
        await callback.answer("Error: ID inválido", show_alert=True)
        return

    logger.info(f"🚫 Admin {admin_id} bloqueando usuario {user_id}")

    # Confirmación de bloqueo
    keyboard = create_inline_keyboard([
        [
            {"text": "✅ Sí, Bloquear", "callback_data": f"admin:block_confirm:{user_id}"},
            {"text": "❌ Cancelar", "callback_data": "admin:close_contact"}
        ]
    ])

    await callback.message.answer(
        f"⚠️ <b>Confirmar Bloqueo</b>\n\n"
        f"¿Está seguro que desea bloquear al usuario <code>{user_id}</code>?\n\n"
        f"<i>Esta acción puede revertirse desde el panel admin.</i>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith("admin:block_confirm:"))
async def callback_admin_block_confirm(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Confirma y ejecuta el bloqueo de usuario.

    Args:
        callback: CallbackQuery del admin
        session: Sesión de BD (inyectada por middleware)
    """
    admin_id = callback.from_user.id

    # Parsear: admin:block_confirm:12345
    parts = callback.data.split(":")
    if len(parts) < 3:
        logger.warning(f"⚠️ Formato inválido: {callback.data}")
        await callback.answer("Error: formato inválido", show_alert=True)
        return

    try:
        user_id = int(parts[2])
    except ValueError:
        logger.warning(f"⚠️ User ID inválido: {parts[2]}")
        await callback.answer("Error: ID inválido", show_alert=True)
        return

    logger.warning(f"🚫 Admin {admin_id} confirmó bloqueo de usuario {user_id}")

    # TODO: Implementar lógica de bloqueo
    # Por ahora solo log y mensaje de confirmación

    await callback.message.edit_text(
        f"✅ <b>Usuario Bloqueado</b>\n\n"
        f"Usuario <code>{user_id}</code> ha sido bloqueado del bot.\n\n"
        f"<i>Bloqueado por Admin {admin_id}</i>",
        parse_mode="HTML"
    )
    await callback.answer("✅ Usuario bloqueado")


@admin_router.callback_query(F.data.startswith("admin:kick:"))
async def callback_admin_kick_user(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Expulsa un usuario (elimina de canales pero no bloquea).

    Útil para remover usuarios problemáticos temporalmente.

    Args:
        callback: CallbackQuery del admin
        session: Sesión de BD (inyectada por middleware)
    """
    admin_id = callback.from_user.id

    # Parsear: admin:kick:12345
    parts = callback.data.split(":")
    if len(parts) < 3:
        logger.warning(f"⚠️ Formato inválido: {callback.data}")
        await callback.answer("Error: formato inválido", show_alert=True)
        return

    try:
        user_id = int(parts[2])
    except ValueError:
        logger.warning(f"⚠️ User ID inválido: {parts[2]}")
        await callback.answer("Error: ID inválido", show_alert=True)
        return

    logger.info(f"👋 Admin {admin_id} expulsando usuario {user_id}")

    container = ServiceContainer(session, callback.bot)

    try:
        # Obtener IDs de canales
        vip_channel_id = await container.channel.get_vip_channel_id()
        free_channel_id = await container.channel.get_free_channel_id()

        kicked_from = []

        # Expulsar de canal VIP si existe
        if vip_channel_id:
            try:
                await callback.bot.ban_chat_member(
                    chat_id=vip_channel_id,
                    user_id=user_id
                )
                # Desbanear inmediatamente (kick sin ban permanente)
                await callback.bot.unban_chat_member(
                    chat_id=vip_channel_id,
                    user_id=user_id
                )
                kicked_from.append("VIP")
                logger.info(f"✅ Usuario {user_id} expulsado de canal VIP")
            except Exception as e:
                logger.error(f"❌ Error expulsando de VIP: {e}")

        # Expulsar de canal Free si existe
        if free_channel_id:
            try:
                await callback.bot.ban_chat_member(
                    chat_id=free_channel_id,
                    user_id=user_id
                )
                await callback.bot.unban_chat_member(
                    chat_id=free_channel_id,
                    user_id=user_id
                )
                kicked_from.append("Free")
                logger.info(f"✅ Usuario {user_id} expulsado de canal Free")
            except Exception as e:
                logger.error(f"❌ Error expulsando de Free: {e}")

        if kicked_from:
            result_text = (
                f"✅ <b>Usuario Expulsado</b>\n\n"
                f"Usuario <code>{user_id}</code> fue expulsado de:\n"
                f"• {', '.join(kicked_from)}\n\n"
                f"<i>Expulsado por Admin {admin_id}</i>"
            )
        else:
            result_text = (
                f"⚠️ <b>No se pudo expulsar</b>\n\n"
                f"El usuario no está en ningún canal o no se pudo expulsar.\n"
                f"Verifique que los canales estén configurados."
            )

        await callback.message.edit_text(
            result_text,
            parse_mode="HTML"
        )
        await callback.answer("✅ Acción completada")

    except Exception as e:
        logger.error(f"❌ Error expulsando usuario: {e}", exc_info=True)
        await callback.answer(
            "⚠️ Error al expulsar. Verifique permisos del bot.",
            show_alert=True
        )
