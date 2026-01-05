"""Handler de configuración de regalo diario para administradores.

Responsabilidades:
- Activar/desactivar sistema de regalo diario
- Configurar cantidad de besitos del regalo
- Visualizar estado del sistema
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares import DatabaseMiddleware
from bot.filters.admin import IsAdmin
from bot.gamification.states.admin import DailyGiftConfigStates
from bot.utils.keyboards import create_inline_keyboard
from bot.utils.lucien_messages import Lucien

logger = logging.getLogger(__name__)

# Router para configuración de regalo diario
router = Router(name="gamification_daily_gift_config")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())
router.message.middleware(DatabaseMiddleware())
router.callback_query.middleware(DatabaseMiddleware())


@router.callback_query(F.data == "gamif:config:daily_gift")
async def show_daily_gift_config(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Muestra configuración del sistema de regalo diario.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    logger.info(f"🎁 Usuario {callback.from_user.id} viendo config de regalo diario")

    from bot.gamification.database.models import GamificationConfig as DBConfig
    config = await session.get(DBConfig, 1)

    if not config:
        # Crear configuración por defecto
        config = DBConfig(id=1, daily_gift_enabled=True, daily_gift_besitos=10)
        session.add(config)
        await session.commit()
        await session.refresh(config)

    status_emoji = "✅" if config.daily_gift_enabled else "❌"
    status_text = "Activado" if config.daily_gift_enabled else "Desactivado"

    text = f"""🎁 <b>Configuración de Regalo Diario</b>

📊 <b>Estado actual:</b>
• Sistema: {status_emoji} {status_text}
• Besitos por regalo: {config.daily_gift_besitos}

<b>Descripción:</b>
El sistema de regalo diario permite a los usuarios reclamar besitos una vez al día. Los usuarios mantienen una racha de días consecutivos.

<b>Opciones:</b>"""

    toggle_text = "❌ Desactivar" if config.daily_gift_enabled else "✅ Activar"
    toggle_callback = "gamif:daily_gift:disable" if config.daily_gift_enabled else "gamif:daily_gift:enable"

    keyboard = [
        [{"text": toggle_text, "callback_data": toggle_callback}],
        [{"text": "💋 Cambiar Cantidad de Besitos", "callback_data": "gamif:daily_gift:set_besitos"}],
        [{"text": "🔙 Volver", "callback_data": "gamif:admin:config"}]
    ]

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(keyboard),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "gamif:daily_gift:enable")
async def enable_daily_gift(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Activa el sistema de regalo diario.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    from bot.gamification.database.models import GamificationConfig as DBConfig
    config = await session.get(DBConfig, 1)

    if config:
        config.daily_gift_enabled = True
        await session.commit()
        logger.info(f"✅ Regalo diario activado por usuario {callback.from_user.id}")
        await callback.answer("✅ Sistema de regalo diario activado", show_alert=True)
    else:
        await callback.answer(Lucien.ERROR_NOT_FOUND, show_alert=True)

    # Refrescar menú
    await show_daily_gift_config(callback, session)


@router.callback_query(F.data == "gamif:daily_gift:disable")
async def disable_daily_gift(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Desactiva el sistema de regalo diario.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    from bot.gamification.database.models import GamificationConfig as DBConfig
    config = await session.get(DBConfig, 1)

    if config:
        config.daily_gift_enabled = False
        await session.commit()
        logger.info(f"❌ Regalo diario desactivado por usuario {callback.from_user.id}")
        await callback.answer("❌ Sistema de regalo diario desactivado", show_alert=True)
    else:
        await callback.answer(Lucien.ERROR_NOT_FOUND, show_alert=True)

    # Refrescar menú
    await show_daily_gift_config(callback, session)


@router.callback_query(F.data == "gamif:daily_gift:set_besitos")
async def ask_daily_gift_besitos(
    callback: CallbackQuery,
    state: FSMContext
):
    """Inicia wizard para cambiar cantidad de besitos del regalo diario.

    Args:
        callback: Callback query
        state: FSM context
    """
    text = """💋 <b>Configurar Cantidad de Besitos</b>

Ingresa la cantidad de besitos que recibirán los usuarios por reclamar su regalo diario.

<b>Recomendaciones:</b>
• Valor mínimo: 1 besito
• Valor máximo: 100 besitos
• Valor recomendado: 5-20 besitos

Envía un mensaje con la cantidad (solo número):"""

    keyboard = [
        [{"text": "❌ Cancelar", "callback_data": "gamif:daily_gift:cancel"}]
    ]

    await state.set_state(DailyGiftConfigStates.waiting_for_besitos)

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(keyboard),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(StateFilter(DailyGiftConfigStates.waiting_for_besitos))
async def process_daily_gift_besitos(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa la cantidad de besitos ingresada.

    Args:
        message: Mensaje del admin
        state: FSM context
        session: Sesión de BD
    """
    try:
        besitos = int(message.text.strip())

        # Validar rango
        if besitos < 1 or besitos > 100:
            await message.answer(
                Lucien.ERROR_INVALID_INPUT,
                parse_mode="HTML"
            )
            return

        # Actualizar configuración
        from bot.gamification.database.models import GamificationConfig as DBConfig
        config = await session.get(DBConfig, 1)

        if config:
            config.daily_gift_besitos = besitos
            await session.commit()

            logger.info(
                f"✅ Besitos de regalo diario actualizados a {besitos} "
                f"por usuario {message.from_user.id}"
            )

            text = f"""✅ <b>Configuración Actualizada</b>

Los usuarios ahora recibirán <b>{besitos} besitos</b> al reclamar su regalo diario.

Esta configuración se aplicará a partir del próximo regalo reclamado."""

            keyboard = [
                [{"text": "🔙 Volver a Configuración", "callback_data": "gamif:config:daily_gift"}]
            ]

            await message.answer(
                text=text,
                reply_markup=create_inline_keyboard(keyboard),
                parse_mode="HTML"
            )

            await state.clear()

        else:
            await message.answer(
                Lucien.ERROR_GENERIC,
                parse_mode="HTML"
            )

    except ValueError:
        await message.answer(
            Lucien.ERROR_INVALID_INPUT,
            parse_mode="HTML"
        )


@router.callback_query(F.data == "gamif:daily_gift:cancel")
async def cancel_daily_gift_config(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Cancela el wizard de configuración de regalo diario.

    Args:
        callback: Callback query
        state: FSM context
        session: Sesión de BD
    """
    await state.clear()
    await callback.answer(Lucien.ERROR_GENERIC, show_alert=True)

    # Volver al menú de configuración de regalo diario
    await show_daily_gift_config(callback, session)
