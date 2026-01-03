"""
Stats Handlers - Visualización de estadísticas del sistema.

Handlers para:
- Dashboard general de estadísticas
- Estadísticas detalladas VIP
- Estadísticas detalladas Free
- Estadísticas de tokens
"""
import logging
from aiogram import F
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.admin.main import admin_router
from bot.services.container import ServiceContainer
from bot.utils.keyboards import stats_menu_keyboard, back_to_main_menu_keyboard
from bot.utils.lucien_messages import LucienMessages

logger = logging.getLogger(__name__)


def format_currency(amount: float) -> str:
    """
    Formatea cantidad como moneda.

    Args:
        amount: Cantidad a formatear

    Returns:
        String formateado (ej: "$1,234.56")
    """
    return f"${amount:,.2f}"


def format_percentage(value: float) -> str:
    """
    Formatea porcentaje.

    Args:
        value: Valor a formatear

    Returns:
        String formateado (ej: "85.5%")
    """
    return f"{value:.1f}%"


@admin_router.callback_query(F.data == "admin:stats")
async def callback_stats_general(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra dashboard de estadísticas generales.

    Incluye:
    - Resumen VIP (activos, expirados, próximos a expirar)
    - Resumen Free (pendientes, procesadas)
    - Resumen Tokens (generados, usados, disponibles)
    - Actividad reciente (hoy, semana, mes)
    - Proyección de ingresos

    Args:
        callback: Callback query
        session: Sesión de BD (inyectada por middleware)
    """
    logger.info(f"📊 Usuario {callback.from_user.id} abrió estadísticas generales")

    # Mostrar "cargando..." temporalmente
    try:
        await callback.answer("📊 Calculando estadísticas...", show_alert=False)
    except TelegramBadRequest as e:
        if "query is too old" in str(e):
            logger.warning(f"⚠️ Callback expirado: {e}")
            return
        raise

    container = ServiceContainer(session, callback.bot)

    try:
        # Obtener estadísticas generales (con cache)
        stats = await container.stats.get_overall_stats()

        # Construir mensaje
        text = _format_overall_stats_message(stats)

        await callback.message.edit_text(
            text=text,
            reply_markup=stats_menu_keyboard(),
            parse_mode="HTML"
        )

        logger.debug(f"✅ Stats generales mostradas a user {callback.from_user.id}")

    except TelegramBadRequest as e:
        if "query is too old" in str(e):
            logger.warning(f"⚠️ Timeout procesando stats: {e}")
            try:
                # Intentar responder al usuario de otra forma
                await callback.answer("⚠️ La solicitud tardó demasiado. Intenta nuevamente.", show_alert=True)
            except Exception:
                pass  # El callback ya expiró, no hay nada que hacer
        else:
            logger.error(f"❌ Error Telegram: {e}")
            try:
                await callback.message.edit_text(
                    LucienMessages.errors("ERROR_LOADING"),
                    reply_markup=back_to_main_menu_keyboard(),
                    parse_mode="HTML"
                )
            except Exception:
                pass

    except Exception as e:
        logger.error(f"❌ Error obteniendo stats: {e}", exc_info=True)

        try:
            await callback.message.edit_text(
                LucienMessages.errors("ERROR_LOADING"),
                reply_markup=back_to_main_menu_keyboard(),
                parse_mode="HTML"
            )
        except Exception:
            logger.warning(f"⚠️ No se pudo enviar mensaje de error")


@admin_router.callback_query(F.data == "admin:stats:refresh")
async def callback_stats_refresh(callback: CallbackQuery, session: AsyncSession):
    """
    Actualiza estadísticas (fuerza recálculo, ignora cache).

    Args:
        callback: Callback query
        session: Sesión de BD (inyectada por middleware)
    """
    logger.info(f"🔄 Usuario {callback.from_user.id} forzando refresh de stats")

    try:
        await callback.answer("🔄 Recalculando estadísticas...", show_alert=False)
    except TelegramBadRequest as e:
        if "query is too old" in str(e):
            logger.warning(f"⚠️ Callback expirado: {e}")
            return
        raise

    container = ServiceContainer(session, callback.bot)

    try:
        # Force refresh (ignora cache)
        stats = await container.stats.get_overall_stats(force_refresh=True)

        text = _format_overall_stats_message(stats)

        await callback.message.edit_text(
            text=text,
            reply_markup=stats_menu_keyboard(),
            parse_mode="HTML"
        )

        # Notificar que se actualizó
        try:
            await callback.answer("✅ Estadísticas actualizadas", show_alert=False)
        except TelegramBadRequest:
            pass  # Callback puede haber expirado, ignorar

        logger.debug("✅ Stats actualizadas exitosamente")

    except TelegramBadRequest as e:
        if "query is too old" in str(e):
            logger.warning(f"⚠️ Timeout refrescando stats: {e}")
        else:
            logger.error(f"❌ Error Telegram: {e}")
            try:
                await callback.answer(LucienMessages.errors("LOADING_SHORT"), show_alert=True)
            except Exception:
                pass

    except Exception as e:
        logger.error(f"❌ Error refrescando stats: {e}", exc_info=True)
        try:
            await callback.answer(LucienMessages.errors("LOADING_SHORT"), show_alert=True)
        except Exception:
            pass


@admin_router.callback_query(F.data == "admin:stats:vip")
async def callback_stats_vip(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra estadísticas detalladas de VIP.

    Incluye:
    - Total activos, expirados, histórico
    - Expiración próxima (hoy, semana, mes)
    - Actividad reciente (hoy, semana, mes)
    - Top suscriptores por días restantes

    Args:
        callback: Callback query
        session: Sesión de BD (inyectada por middleware)
    """
    logger.info(f"📊 Usuario {callback.from_user.id} abrió stats VIP detalladas")

    try:
        await callback.answer("📊 Calculando estadísticas VIP...", show_alert=False)
    except TelegramBadRequest as e:
        if "query is too old" in str(e):
            logger.warning(f"⚠️ Callback expirado: {e}")
            return
        raise

    container = ServiceContainer(session, callback.bot)

    try:
        vip_stats = await container.stats.get_vip_stats()

        text = _format_vip_stats_message(vip_stats)

        await callback.message.edit_text(
            text=text,
            reply_markup=stats_menu_keyboard(),
            parse_mode="HTML"
        )

        logger.debug(f"✅ VIP stats mostradas a user {callback.from_user.id}")

    except TelegramBadRequest as e:
        if "query is too old" in str(e):
            logger.warning(f"⚠️ Timeout procesando VIP stats: {e}")
        else:
            logger.error(f"❌ Error Telegram: {e}")
            try:
                await callback.message.edit_text(
                    LucienMessages.errors("ERROR_LOADING"),
                    reply_markup=stats_menu_keyboard(),
                    parse_mode="HTML"
                )
            except Exception:
                pass

    except Exception as e:
        logger.error(f"❌ Error obteniendo VIP stats: {e}", exc_info=True)

        try:
            await callback.message.edit_text(
                LucienMessages.errors("ERROR_LOADING"),
                reply_markup=stats_menu_keyboard(),
                parse_mode="HTML"
            )
        except Exception:
            pass


@admin_router.callback_query(F.data == "admin:stats:free")
async def callback_stats_free(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra estadísticas detalladas de Free.

    Incluye:
    - Total pendientes, procesadas, histórico
    - Estado de procesamiento (listos, esperando)
    - Tiempo promedio de espera
    - Actividad reciente (hoy, semana, mes)
    - Próximas a procesar

    Args:
        callback: Callback query
        session: Sesión de BD (inyectada por middleware)
    """
    logger.info(f"📊 Usuario {callback.from_user.id} abrió stats Free detalladas")

    try:
        await callback.answer("📊 Calculando estadísticas Free...", show_alert=False)
    except TelegramBadRequest as e:
        if "query is too old" in str(e):
            logger.warning(f"⚠️ Callback expirado: {e}")
            return
        raise

    container = ServiceContainer(session, callback.bot)

    try:
        free_stats = await container.stats.get_free_stats()

        text = _format_free_stats_message(free_stats)

        await callback.message.edit_text(
            text=text,
            reply_markup=stats_menu_keyboard(),
            parse_mode="HTML"
        )

        logger.debug(f"✅ Free stats mostradas a user {callback.from_user.id}")

    except TelegramBadRequest as e:
        if "query is too old" in str(e):
            logger.warning(f"⚠️ Timeout procesando Free stats: {e}")
        else:
            logger.error(f"❌ Error Telegram: {e}")
            try:
                await callback.message.edit_text(
                    LucienMessages.errors("ERROR_LOADING"),
                    reply_markup=stats_menu_keyboard(),
                    parse_mode="HTML"
                )
            except Exception:
                pass

    except Exception as e:
        logger.error(f"❌ Error obteniendo Free stats: {e}", exc_info=True)

        try:
            await callback.message.edit_text(
                LucienMessages.errors("ERROR_LOADING"),
                reply_markup=stats_menu_keyboard(),
                parse_mode="HTML"
            )
        except Exception:
            pass


@admin_router.callback_query(F.data == "admin:stats:tokens")
async def callback_stats_tokens(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra estadísticas detalladas de Tokens.

    Incluye:
    - Total generados, usados, expirados, disponibles
    - Generados por período (hoy, semana, mes)
    - Usados por período (hoy, semana, mes)
    - Tasa de conversión

    Args:
        callback: Callback query
        session: Sesión de BD (inyectada por middleware)
    """
    logger.info(f"📊 Usuario {callback.from_user.id} abrió stats Tokens detalladas")

    try:
        await callback.answer("📊 Calculando estadísticas de Tokens...", show_alert=False)
    except TelegramBadRequest as e:
        if "query is too old" in str(e):
            logger.warning(f"⚠️ Callback expirado: {e}")
            return
        raise

    container = ServiceContainer(session, callback.bot)

    try:
        token_stats = await container.stats.get_token_stats()

        text = _format_token_stats_message(token_stats)

        await callback.message.edit_text(
            text=text,
            reply_markup=stats_menu_keyboard(),
            parse_mode="HTML"
        )

        logger.debug(f"✅ Token stats mostradas a user {callback.from_user.id}")

    except TelegramBadRequest as e:
        if "query is too old" in str(e):
            logger.warning(f"⚠️ Timeout procesando Token stats: {e}")
        else:
            logger.error(f"❌ Error Telegram: {e}")
            try:
                await callback.message.edit_text(
                    LucienMessages.errors("ERROR_LOADING"),
                    reply_markup=stats_menu_keyboard(),
                    parse_mode="HTML"
                )
            except Exception:
                pass

    except Exception as e:
        logger.error(f"❌ Error obteniendo Token stats: {e}", exc_info=True)

        try:
            await callback.message.edit_text(
                LucienMessages.errors("ERROR_LOADING"),
                reply_markup=stats_menu_keyboard(),
                parse_mode="HTML"
            )
        except Exception:
            pass


def _format_overall_stats_message(stats) -> str:
    """
    Formatea mensaje de estadísticas generales.

    Args:
        stats: OverallStats dataclass

    Returns:
        String HTML formateado para Telegram
    """
    # Calcular totales
    total_vip = stats.total_vip_active + stats.total_vip_expired
    total_free = stats.total_free_pending + stats.total_free_processed

    # Iconos de estado
    vip_icon = "🟢" if stats.total_vip_active > 0 else "⚪"
    free_icon = "🟢" if stats.total_free_pending > 0 else "⚪"
    token_icon = "🟢" if stats.total_tokens_available > 0 else "🟡"

    message = f"""
📊 <b>Dashboard de Estadísticas</b>

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ <b>📺 CANAL VIP</b> {vip_icon}
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ Activos: <b>{stats.total_vip_active}</b>
┃ Expirados: {stats.total_vip_expired}
┃ Total histórico: {total_vip}
┃
┃ ⏱️ Próximos a expirar (7 días): <b>{stats.total_vip_expiring_soon}</b>
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ <b>📺 CANAL FREE</b> {free_icon}
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ Pendientes: <b>{stats.total_free_pending}</b>
┃ Procesadas: {stats.total_free_processed}
┃ Total histórico: {total_free}
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ <b>🎟️ TOKENS</b> {token_icon}
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ Generados: {stats.total_tokens_generated}
┃ Usados: {stats.total_tokens_used}
┃ Expirados: {stats.total_tokens_expired}
┃ Disponibles: <b>{stats.total_tokens_available}</b>
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ <b>📈 ACTIVIDAD RECIENTE</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ Nuevos VIP hoy: {stats.new_vip_today}
┃ Nuevos VIP esta semana: {stats.new_vip_this_week}
┃ Nuevos VIP este mes: {stats.new_vip_this_month}
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ <b>💰 PROYECCIÓN DE INGRESOS</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ Mensual: <b>{format_currency(stats.projected_monthly_revenue)}</b>
┃ Anual: <b>{format_currency(stats.projected_yearly_revenue)}</b>
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━

<i>Actualizado: {stats.calculated_at.strftime('%Y-%m-%d %H:%M')} UTC</i>
    """.strip()

    return message


def _format_vip_stats_message(stats) -> str:
    """
    Formatea mensaje de estadísticas VIP detalladas.

    Incluye:
    - Totales y tasa de retención
    - Breakdown de expiración próxima
    - Actividad reciente
    - Top suscriptores con emojis contextuales

    Args:
        stats: VIPStats dataclass

    Returns:
        String HTML formateado para Telegram
    """
    # Calcular tasa de retención
    retention_rate = (stats.total_active / stats.total_all_time * 100) if stats.total_all_time > 0 else 0

    message = f"""
📊 <b>Estadísticas VIP Detalladas</b>

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ <b>📈 TOTALES</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ Activos: <b>{stats.total_active}</b>
┃ Expirados: {stats.total_expired}
┃ Total histórico: {stats.total_all_time}
┃
┃ Tasa retención: <b>{format_percentage(retention_rate)}</b>
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ <b>⏱️ PRÓXIMAS A EXPIRAR</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ Hoy: <b>{stats.expiring_today}</b>
┃ Esta semana: <b>{stats.expiring_this_week}</b>
┃ Este mes: {stats.expiring_this_month}
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ <b>📅 ACTIVIDAD RECIENTE</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ Nuevos hoy: {stats.new_today}
┃ Nuevos esta semana: {stats.new_this_week}
┃ Nuevos este mes: {stats.new_this_month}
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """.strip()

    # Agregar top subscribers si hay
    if stats.top_subscribers:
        message += "\n\n┏━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += "┃ <b>👥 TOP SUSCRIPTORES</b>\n"
        message += "┣━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        for i, sub in enumerate(stats.top_subscribers[:5], 1):
            days = sub["days_remaining"]
            user_id = sub["user_id"]

            # Emoji según días restantes
            if days > 30:
                emoji = "🟢"
            elif days > 7:
                emoji = "🟡"
            else:
                emoji = "🔴"

            message += f"┃ {emoji} <code>{user_id}</code>: <b>{days}d</b>\n"

        message += "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    message += f"\n\n<i>Actualizado: {stats.calculated_at.strftime('%Y-%m-%d %H:%M')} UTC</i>"

    return message


def _format_free_stats_message(stats) -> str:
    """
    Formatea mensaje de estadísticas Free detalladas.

    Incluye:
    - Totales y tasa de procesamiento
    - Estado de cola y tiempo promedio
    - Actividad reciente
    - Próximas a procesar con emojis contextuales

    Args:
        stats: FreeStats dataclass

    Returns:
        String HTML formateado para Telegram
    """
    # Calcular tasa de procesamiento
    processing_rate = (stats.total_processed / stats.total_all_time * 100) if stats.total_all_time > 0 else 0

    message = f"""
📊 <b>Estadísticas Free Detalladas</b>

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ <b>📈 TOTALES</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ Pendientes: <b>{stats.total_pending}</b>
┃ Procesadas: {stats.total_processed}
┃ Total histórico: {stats.total_all_time}
┃
┃ Tasa procesamiento: <b>{format_percentage(processing_rate)}</b>
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ <b>⏱️ ESTADO DE COLA</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ Listas para procesar: <b>{stats.ready_to_process}</b>
┃ Aún esperando: {stats.still_waiting}
┃
┃ Tiempo promedio: <b>{stats.avg_wait_time_minutes:.1f} min</b>
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ <b>📅 ACTIVIDAD RECIENTE</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ Nuevas hoy: {stats.new_requests_today}
┃ Nuevas esta semana: {stats.new_requests_this_week}
┃ Nuevas este mes: {stats.new_requests_this_month}
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """.strip()

    # Agregar próximas a procesar si hay
    if stats.next_to_process:
        message += "\n\n┏━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += "┃ <b>🔜 PRÓXIMAS A PROCESAR</b>\n"
        message += "┣━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        for i, req in enumerate(stats.next_to_process[:5], 1):
            minutes = req["minutes_remaining"]
            user_id = req["user_id"]

            # Emoji según tiempo restante
            if minutes <= 0:
                emoji = "✅"
                time_text = "Listo"
            elif minutes < 2:
                emoji = "🟡"
                time_text = f"{minutes:.0f}m"
            else:
                emoji = "⏱️"
                time_text = f"{minutes:.0f}m"

            message += f"┃ {emoji} <code>{user_id}</code>: <b>{time_text}</b>\n"

        message += "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    message += f"\n\n<i>Actualizado: {stats.calculated_at.strftime('%Y-%m-%d %H:%M')} UTC</i>"

    return message


def _format_token_stats_message(stats) -> str:
    """
    Formatea mensaje de estadísticas de Tokens detalladas.

    Incluye:
    - Totales y tasa de conversión
    - Generados y usados por período
    - Análisis contextual (estado de conversión)
    - Warnings si hay problemas

    Args:
        stats: TokenStats dataclass

    Returns:
        String HTML formateado para Telegram
    """
    message = f"""
📊 <b>Estadísticas de Tokens Detalladas</b>

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ <b>📈 TOTALES</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ Generados: {stats.total_generated}
┃ Usados: {stats.total_used}
┃ Expirados: {stats.total_expired}
┃ Disponibles: <b>{stats.total_available}</b>
┃
┃ Tasa conversión: <b>{format_percentage(stats.conversion_rate)}</b>
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ <b>🎟️ GENERADOS POR PERÍODO</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ Hoy: {stats.generated_today}
┃ Esta semana: {stats.generated_this_week}
┃ Este mes: {stats.generated_this_month}
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ <b>✅ USADOS POR PERÍODO</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ Hoy: {stats.used_today}
┃ Esta semana: {stats.used_this_week}
┃ Este mes: {stats.used_this_month}
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """.strip()

    # Agregar análisis contextual
    if stats.total_generated > 0:
        message += "\n\n┏━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += "┃ <b>📊 ANÁLISIS</b>\n"
        message += "┣━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        # Estado de conversión
        if stats.conversion_rate >= 80:
            message += "┃ 🟢 Conversión excelente\n"
        elif stats.conversion_rate >= 50:
            message += "┃ 🟡 Conversión moderada\n"
        else:
            message += "┃ 🔴 Conversión baja\n"

        # Porcentaje de tokens sin usar
        avail_pct = (stats.total_available / stats.total_generated * 100)
        message += f"┃ Sin usar: <b>{format_percentage(avail_pct)}</b>\n"

        # Warning si muchos tokens expirados
        if stats.total_generated > 0:
            expired_pct = (stats.total_expired / stats.total_generated * 100)
            if expired_pct > 20:
                message += f"┃ ⚠️ Expirados: {format_percentage(expired_pct)}\n"

        message += "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    message += f"\n\n<i>Actualizado: {stats.calculated_at.strftime('%Y-%m-%d %H:%M')} UTC</i>"

    return message
