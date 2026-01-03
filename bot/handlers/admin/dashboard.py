"""Dashboard Handlers - Panel de control completo del sistema.

Este módulo contiene los handlers para el panel de control completo del sistema,
que proporciona una visión general del estado del bot con health checks,
configuración, estadísticas clave, tareas en segundo plano y acciones rápidas.

Funcionalidades:
    - Dashboard general con estado del sistema
    - Health checks del sistema
    - Acciones rápidas para administradores
    - Visualización de estadísticas clave
    - Estado de tareas en segundo plano
"""
import logging
from datetime import datetime, timezone

from aiogram import F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.admin.main import admin_router
from bot.services.container import ServiceContainer
from bot.background.tasks import get_scheduler_status
from bot.utils.keyboards import create_inline_keyboard
from bot.utils.lucien_messages import LucienMessages

logger = logging.getLogger(__name__)


@admin_router.callback_query(F.data == "admin:dashboard")
async def callback_admin_dashboard(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Muestra dashboard completo del sistema.

    Incluye:
    - Estado de configuración (canales, reacciones)
    - Estadísticas clave (VIP, Free, Tokens)
    - Background tasks (estado, próxima ejecución)
    - Health checks
    - Acciones rápidas

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    logger.info(f"📊 Usuario {callback.from_user.id} abrió dashboard completo")

    await callback.answer("📊 Cargando dashboard...", show_alert=False)

    container = ServiceContainer(session, callback.bot)

    try:
        # Obtener datos del dashboard
        dashboard_data = await _gather_dashboard_data(container)

        # Formatear mensaje
        text = _format_dashboard_message(dashboard_data)

        # Keyboard con acciones rápidas
        keyboard = _create_dashboard_keyboard(dashboard_data)

        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        logger.debug("✅ Dashboard mostrado exitosamente")

    except Exception as e:
        logger.error(f"❌ Error generando dashboard: {e}", exc_info=True)

        await callback.message.edit_text(
            LucienMessages.errors("ERROR_LOADING"),
            reply_markup=create_inline_keyboard([
                [{"text": "🔄 Reintentar", "callback_data": "admin:dashboard"}],
                [{"text": "🔙 Volver", "callback_data": "admin:main"}]
            ]),
            parse_mode="HTML"
        )


async def _gather_dashboard_data(container: ServiceContainer) -> dict:
    """Recopila todos los datos necesarios para el dashboard.

    Args:
        container: Service container con acceso a los servicios del sistema.

    Returns:
        Dict con todos los datos del dashboard, incluyendo configuración,
        estadísticas, estado del scheduler y health checks.
    """
    # Configuración - get_config_status retorna: is_configured, vip_channel_id, free_channel_id, etc
    config_status = await container.config.get_config_status()

    is_configured = config_status["is_configured"]
    vip_configured = config_status["vip_channel_id"] is not None
    free_configured = config_status["free_channel_id"] is not None
    vip_reactions_count = config_status["vip_reactions_count"]
    free_reactions_count = config_status["free_reactions_count"]
    wait_time = config_status["wait_time_minutes"]

    # Estadísticas (con cache)
    overall_stats = await container.stats.get_overall_stats()

    # Background tasks
    scheduler_status = get_scheduler_status()

    # Health checks
    health = _perform_health_checks(
        vip_configured=vip_configured,
        free_configured=free_configured,
        scheduler_running=scheduler_status["running"],
        stats=overall_stats
    )

    return {
        "config": {
            "is_configured": is_configured,
            "vip_configured": vip_configured,
            "free_configured": free_configured,
            "vip_reactions_count": vip_reactions_count,
            "free_reactions_count": free_reactions_count,
            "wait_time": wait_time
        },
        "stats": overall_stats,
        "scheduler": scheduler_status,
        "health": health,
        "timestamp": datetime.now(timezone.utc)
    }


def _perform_health_checks(
    vip_configured: bool,
    free_configured: bool,
    scheduler_running: bool,
    stats
) -> dict:
    """Realiza health checks del sistema.

    Args:
        vip_configured: Indica si el canal VIP está configurado.
        free_configured: Indica si el canal Free está configurado.
        scheduler_running: Indica si el scheduler está corriendo.
        stats: Objeto OverallStats con estadísticas del sistema.

    Returns:
        Dict con resultados de health checks con la siguiente estructura:
        {
            "status": "healthy" | "degraded" | "down",
            "issues": [str],  # Lista de problemas encontrados
            "warnings": [str]  # Lista de advertencias
        }
    """
    issues = []
    warnings = []

    # Check: Canales configurados
    if not vip_configured and not free_configured:
        issues.append("Ningún canal configurado")
    elif not vip_configured:
        warnings.append("Canal VIP no configurado")
    elif not free_configured:
        warnings.append("Canal Free no configurado")

    # Check: Background tasks
    if not scheduler_running:
        issues.append("Background tasks no están corriendo")

    # Check: Tokens disponibles (warning si <3)
    if stats.total_tokens_available < 3:
        warnings.append(f"Pocos tokens disponibles ({stats.total_tokens_available})")

    # Check: VIPs próximos a expirar (warning si >10)
    if stats.total_vip_expiring_soon > 10:
        warnings.append(f"{stats.total_vip_expiring_soon} VIP expiran en 7 días")

    # Check: Cola Free muy grande (warning si >50)
    if stats.total_free_pending > 50:
        warnings.append(f"Cola Free grande ({stats.total_free_pending} pendientes)")

    # Determinar estado general
    if issues:
        status = "down"
    elif warnings:
        status = "degraded"
    else:
        status = "healthy"

    return {
        "status": status,
        "issues": issues,
        "warnings": warnings
    }


def _format_dashboard_message(data: dict) -> str:
    """Formatea el mensaje del dashboard.

    Args:
        data: Dict con datos del dashboard incluyendo configuración,
            estadísticas, scheduler y health checks.

    Returns:
        String HTML formateado con la información del dashboard.
    """
    config = data["config"]
    stats = data["stats"]
    scheduler = data["scheduler"]
    health = data["health"]

    # Header con health status
    status_emoji = {
        "healthy": "🟢",
        "degraded": "🟡",
        "down": "🔴"
    }.get(health["status"], "⚪")

    status_text = {
        "healthy": "Operativo",
        "degraded": "Funcionando con Advertencias",
        "down": "Problemas Detectados"
    }.get(health["status"], "Desconocido")

    message = f"""
📊 <b>Dashboard del Sistema</b>

{status_emoji} <b>Estado:</b> {status_text}
    """.strip()

    # Issues y warnings
    if health["issues"]:
        message += "\n\n🔴 <b>Problemas:</b>"
        for issue in health["issues"]:
            message += f"\n  • {issue}"

    if health["warnings"]:
        message += "\n\n🟡 <b>Advertencias:</b>"
        for warning in health["warnings"]:
            message += f"\n  • {warning}"

    # Configuración
    message += "\n\n┏━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    message += "\n┃ <b>⚙️ CONFIGURACIÓN</b>"
    message += "\n┣━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    vip_icon = "✅" if config["vip_configured"] else "❌"
    free_icon = "✅" if config["free_configured"] else "❌"

    message += f"\n┃ Canal VIP: {vip_icon}"
    if config["vip_configured"]:
        message += f" ({config['vip_reactions_count']} reacciones)"

    message += f"\n┃ Canal Free: {free_icon}"
    if config["free_configured"]:
        message += f" ({config['wait_time']} min espera)"

    message += "\n┗━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Estadísticas Clave
    message += "\n\n┏━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    message += "\n┃ <b>📈 ESTADÍSTICAS CLAVE</b>"
    message += "\n┣━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    message += f"\n┃ VIP Activos: <b>{stats.total_vip_active}</b>"
    message += f"\n┃ Free Pendientes: <b>{stats.total_free_pending}</b>"
    message += f"\n┃ Tokens Disponibles: <b>{stats.total_tokens_available}</b>"
    message += "\n┃"
    message += f"\n┃ Nuevos VIP (hoy): {stats.new_vip_today}"
    message += f"\n┃ Nuevos VIP (semana): {stats.new_vip_this_week}"
    message += "\n┗━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Background Tasks
    message += "\n\n┏━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    message += "\n┃ <b>🔄 BACKGROUND TASKS</b>"
    message += "\n┣━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if scheduler["running"]:
        message += f"\n┃ Estado: 🟢 Corriendo"
        message += f"\n┃ Jobs: {scheduler['jobs_count']}"

        # Próxima ejecución
        if scheduler["jobs"]:
            next_job = min(
                (j for j in scheduler["jobs"] if j["next_run_time"]),
                key=lambda j: j["next_run_time"],
                default=None
            )

            if next_job:
                next_time = next_job["next_run_time"]
                time_until = (next_time - datetime.now(timezone.utc)).total_seconds() / 60

                if time_until < 1:
                    time_text = "< 1 min"
                else:
                    time_text = f"{int(time_until)} min"

                message += f"\n┃ Próximo job: {time_text}"
    else:
        message += f"\n┃ Estado: 🔴 Detenido"

    message += "\n┗━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Footer con timestamp
    timestamp = data["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
    message += f"\n\n<i>Actualizado: {timestamp} UTC</i>"

    return message


def _create_dashboard_keyboard(data: dict) -> "InlineKeyboardMarkup":
    """Crea keyboard del dashboard con acciones rápidas.

    Args:
        data: Dict con datos del dashboard incluyendo configuración
            y estado del sistema.

    Returns:
        InlineKeyboardMarkup con acciones rápidas para administradores.
    """
    buttons = []

    # Fila 1: Stats y Config
    buttons.append([
        {"text": "📊 Estadísticas Detalladas", "callback_data": "admin:stats"},
        {"text": "⚙️ Configuración", "callback_data": "admin:config"}
    ])

    # Fila 2: Gestión (adaptativa según configuración)
    row_2 = []

    if data["config"]["vip_configured"]:
        row_2.append(
            {"text": "👥 Suscriptores VIP", "callback_data": "vip:list_subscribers"}
        )

    if data["config"]["free_configured"]:
        row_2.append(
            {"text": "📋 Cola Free", "callback_data": "free:view_queue"}
        )

    if row_2:
        buttons.append(row_2)

    # Fila 3: Actualizar y Volver
    buttons.append([
        {"text": "🔄 Actualizar", "callback_data": "admin:dashboard"},
        {"text": "🔙 Menú", "callback_data": "admin:main"}
    ])

    return create_inline_keyboard(buttons)
