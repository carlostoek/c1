"""
Background Tasks - Tareas programadas automáticas.

Tareas:
- Expulsión de VIPs expirados del canal
- Procesamiento de cola Free (envío de invite links)
- Limpieza de datos antiguos
"""
import logging
from typing import Optional

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from bot.database import get_session
from bot.services.container import ServiceContainer
from config import Config

logger = logging.getLogger(__name__)

# Scheduler global
_scheduler: Optional[AsyncIOScheduler] = None


async def expire_and_kick_vip_subscribers(bot: Bot):
    """
    Tarea: Expulsar suscriptores VIP expirados del canal.

    Proceso:
    1. Marca como expirados los suscriptores cuya fecha pasó
    2. Expulsa del canal VIP a los expirados
    3. Loguea resultados

    Args:
        bot: Instancia del bot de Telegram
    """
    logger.info("🔄 Ejecutando tarea: Expulsión VIP expirados")

    try:
        async with get_session() as session:
            container = ServiceContainer(session, bot)

            # Verificar que canal VIP está configurado
            vip_channel_id = await container.channel.get_vip_channel_id()

            if not vip_channel_id:
                logger.warning("⚠️ Canal VIP no configurado, saltando expulsión")
                return

            # Marcar como expirados
            expired_count = await container.subscription.expire_vip_subscribers()

            if expired_count > 0:
                logger.info(f"⏱️ {expired_count} suscriptor(es) VIP expirados")

                # Expulsar del canal
                kicked_count = await container.subscription.kick_expired_vip_from_channel(
                    vip_channel_id
                )

                logger.info(f"✅ {kicked_count} usuario(s) expulsados del canal VIP")
            else:
                logger.debug("✓ No hay VIPs expirados")

    except Exception as e:
        logger.error(f"❌ Error en tarea de expulsión VIP: {e}", exc_info=True)


async def process_free_queue(bot: Bot):
    """
    Tarea: Procesar cola de solicitudes Free.

    Proceso:
    1. Busca solicitudes que cumplieron el tiempo de espera
    2. Para cada solicitud:
       - Marca como procesada
       - Crea invite link
       - Envía link al usuario por mensaje privado
    3. Loguea resultados

    Args:
        bot: Instancia del bot de Telegram
    """
    logger.info("🔄 Ejecutando tarea: Procesamiento cola Free")

    try:
        async with get_session() as session:
            container = ServiceContainer(session, bot)

            # Verificar que canal Free está configurado
            free_channel_id = await container.channel.get_free_channel_id()

            if not free_channel_id:
                logger.warning("⚠️ Canal Free no configurado, saltando procesamiento")
                return

            # Obtener tiempo de espera configurado
            wait_time = await container.config.get_wait_time()

            # Buscar solicitudes listas para procesar
            ready_requests = await container.subscription.process_free_queue(wait_time)

            if not ready_requests:
                logger.debug("✓ No hay solicitudes Free listas")
                return

            logger.info(f"📋 Procesando {len(ready_requests)} solicitud(es) Free")

            # Procesar cada solicitud
            success_count = 0
            error_count = 0

            for request in ready_requests:
                user_id = request.user_id

                try:
                    # Crear invite link personal
                    invite_link = await container.subscription.create_invite_link(
                        channel_id=free_channel_id,
                        user_id=user_id,
                        expire_hours=24  # Link Free válido por 24 horas
                    )

                    # Enviar link al usuario por mensaje privado
                    message_text = (
                        f"✅ <b>¡Tu Acceso Free está Listo!</b>\n\n"
                        f"Has esperado {wait_time} minutos como se requiere.\n\n"
                        f"👇 Usa este link para unirte al canal Free:\n"
                        f"{invite_link.invite_link}\n\n"
                        f"⚠️ <b>Importante:</b>\n"
                        f"• El link expira en 24 horas\n"
                        f"• Solo puedes usarlo 1 vez\n"
                        f"• No lo compartas con otros\n\n"
                        f"Disfruta del contenido! 🎉"
                    )

                    await bot.send_message(
                        chat_id=user_id,
                        text=message_text,
                        parse_mode="HTML"
                    )

                    success_count += 1
                    logger.info(f"✅ Link Free enviado a user {user_id}")

                except Exception as e:
                    error_count += 1
                    logger.error(
                        f"❌ Error enviando link Free a user {user_id}: {e}",
                        exc_info=True
                    )
                    # Continuar con siguiente usuario

            logger.info(
                f"✅ Cola Free procesada: {success_count} éxitos, {error_count} errores"
            )

    except Exception as e:
        logger.error(f"❌ Error en tarea de procesamiento Free: {e}", exc_info=True)


async def cleanup_old_data(bot: Bot):
    """
    Tarea: Limpieza de datos antiguos.

    Proceso:
    1. Elimina solicitudes Free procesadas hace más de 30 días
    2. (Futuro: Limpiar tokens expirados muy antiguos)

    Args:
        bot: Instancia del bot
    """
    logger.info("🔄 Ejecutando tarea: Limpieza de datos antiguos")

    try:
        async with get_session() as session:
            container = ServiceContainer(session, bot)

            # Limpiar solicitudes Free antiguas
            deleted_count = await container.subscription.cleanup_old_free_requests(
                days_old=30
            )

            if deleted_count > 0:
                logger.info(f"🗑️ {deleted_count} solicitud(es) Free antiguas eliminadas")
            else:
                logger.debug("✓ No hay datos antiguos para limpiar")

    except Exception as e:
        logger.error(f"❌ Error en tarea de limpieza: {e}", exc_info=True)


def start_background_tasks(bot: Bot):
    """
    Inicia el scheduler con todas las tareas programadas.

    Configuración:
    - Expulsión VIP: Cada 60 minutos (configurable)
    - Procesamiento Free: Cada 5 minutos (o según wait_time)
    - Limpieza: Cada 24 horas (diaria a las 3 AM)

    Args:
        bot: Instancia del bot de Telegram
    """
    global _scheduler

    if _scheduler is not None:
        logger.warning("⚠️ Scheduler ya está corriendo")
        return

    logger.info("🚀 Iniciando background tasks...")

    _scheduler = AsyncIOScheduler(timezone="UTC")

    # Tarea 1: Expulsión VIP expirados
    # Frecuencia: Cada 60 minutos (Config.CLEANUP_INTERVAL_MINUTES)
    _scheduler.add_job(
        expire_and_kick_vip_subscribers,
        trigger=IntervalTrigger(minutes=Config.CLEANUP_INTERVAL_MINUTES),
        args=[bot],
        id="expire_vip",
        name="Expulsar VIPs expirados",
        replace_existing=True,
        max_instances=1  # No permitir múltiples instancias simultáneas
    )
    logger.info(
        f"✅ Tarea programada: Expulsión VIP (cada {Config.CLEANUP_INTERVAL_MINUTES} min)"
    )

    # Tarea 2: Procesamiento cola Free
    # Frecuencia: Cada 5 minutos (Config.PROCESS_FREE_QUEUE_MINUTES)
    _scheduler.add_job(
        process_free_queue,
        trigger=IntervalTrigger(minutes=Config.PROCESS_FREE_QUEUE_MINUTES),
        args=[bot],
        id="process_free_queue",
        name="Procesar cola Free",
        replace_existing=True,
        max_instances=1
    )
    logger.info(
        f"✅ Tarea programada: Cola Free (cada {Config.PROCESS_FREE_QUEUE_MINUTES} min)"
    )

    # Tarea 3: Limpieza de datos antiguos
    # Frecuencia: Diaria a las 3 AM UTC
    _scheduler.add_job(
        cleanup_old_data,
        trigger=CronTrigger(hour=3, minute=0, timezone="UTC"),
        args=[bot],
        id="cleanup_old_data",
        name="Limpieza de datos antiguos",
        replace_existing=True,
        max_instances=1
    )
    logger.info("✅ Tarea programada: Limpieza (diaria 3 AM UTC)")

    # Iniciar scheduler
    _scheduler.start()
    logger.info("✅ Background tasks iniciados correctamente")


def stop_background_tasks():
    """
    Detiene el scheduler y todas las tareas programadas.

    Debe llamarse en el shutdown del bot para cleanup limpio.
    Con wait=False para permitir shutdown rápido incluso si hay jobs.
    """
    global _scheduler

    if _scheduler is None:
        logger.warning("⚠️ Scheduler no está corriendo")
        return

    logger.info("🛑 Deteniendo background tasks...")

    try:
        # wait=False para shutdown rápido sin bloquear
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("✅ Background tasks detenidos")
    except Exception as e:
        logger.warning(f"⚠️ Error deteniendo scheduler: {e}")
        _scheduler = None


def get_scheduler_status() -> dict:
    """
    Obtiene el estado actual del scheduler de background tasks.

    Returns:
        Dict con info del scheduler:
        {
            "running": bool,
            "jobs_count": int,
            "jobs": [
                {
                    "id": str,
                    "name": str,
                    "next_run_time": datetime or None,
                    "trigger": str
                }
            ]
        }

    Examples:
        >>> status = get_scheduler_status()
        >>> if status["running"]:
        ...     print(f"{status['jobs_count']} jobs activos")
    """
    if _scheduler is None:
        return {
            "running": False,
            "jobs_count": 0,
            "jobs": []
        }

    jobs_info = []
    for job in _scheduler.get_jobs():
        jobs_info.append({
            "id": job.id,
            "name": job.name or job.id,
            "next_run_time": job.next_run_time,
            "trigger": str(job.trigger)
        })

    return {
        "running": _scheduler.running,
        "jobs_count": len(jobs_info),
        "jobs": jobs_info
    }
