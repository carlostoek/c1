"""
Entry point del Bot de Administración VIP/Free.
Gestiona el ciclo de vida completo del bot en Termux.
"""
import asyncio
import logging
import sys
import signal
import threading
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramNetworkError

from config import Config
from bot.database import init_db, close_db
from bot.background import start_background_tasks, stop_background_tasks

# Configurar logging
logger = logging.getLogger(__name__)


async def _get_bot_info_with_retry(bot: Bot, max_retries: int = 2, timeout: int = 5) -> dict | None:
    """
    Obtiene información del bot con reintentos rápidos.

    Args:
        bot: Instancia del bot
        max_retries: Número máximo de reintentos
        timeout: Timeout en segundos para cada intento

    Returns:
        Dict con info del bot o None si falla después de reintentos
    """
    for attempt in range(1, max_retries + 1):
        try:
            bot_info = await asyncio.wait_for(
                bot.get_me(request_timeout=timeout),
                timeout=timeout + 1
            )
            logger.info(f"✅ Bot verificado: @{bot_info.username}")
            return bot_info
        except (TelegramNetworkError, asyncio.TimeoutError) as e:
            logger.warning(f"⚠️ Intento {attempt}/{max_retries} falló: {type(e).__name__}")
            if attempt < max_retries:
                await asyncio.sleep(1)  # Espera corta: 1s
            else:
                logger.warning("⚠️ No se pudo verificar bot. Continuando sin verificación...")
                return None
        except Exception as e:
            logger.error(f"❌ Error al obtener info del bot: {e}")
            return None


async def on_startup(bot: Bot, dispatcher: Dispatcher) -> None:
    """
    Callback ejecutado al iniciar el bot.

    Tareas:
    - Validar configuración
    - Inicializar base de datos
    - Registrar handlers y middlewares
    - Notificar a admins que el bot está online

    Args:
        bot: Instancia del bot
        dispatcher: Instancia del dispatcher
    """
    logger.info("🚀 Iniciando bot...")

    # Validar configuración
    if not Config.validate():
        logger.error("❌ Configuración inválida. Revisa tu archivo .env")
        sys.exit(1)

    logger.info(Config.get_summary())

    # Inicializar base de datos
    try:
        await init_db()
    except Exception as e:
        logger.error(f"❌ Error al inicializar BD: {e}")
        sys.exit(1)

    # TODO: Registrar handlers (ONDA 1 - Fases siguientes)
    # from bot.handlers import register_all_handlers
    # register_all_handlers(dispatcher)

    # TODO: Registrar middlewares (ONDA 1 - Fase 1.3)
    # from bot.middlewares import DatabaseMiddleware, AdminAuthMiddleware
    # dispatcher.update.middleware(DatabaseMiddleware())
    # dispatcher.message.middleware(AdminAuthMiddleware())

    # Iniciar background tasks
    start_background_tasks(bot)

    # Notificar a admins que el bot está online (con reintentos)
    bot_info = await _get_bot_info_with_retry(bot)

    if bot_info:
        startup_message = (
            f"✅ Bot <b>@{bot_info.username}</b> iniciado correctamente\n\n"
            f"🤖 ID: <code>{bot_info.id}</code>\n"
            f"📝 Nombre: {bot_info.first_name}\n"
            f"🔧 Versión: ONDA 1 (MVP)\n\n"
            f"Usa /admin para gestionar los canales."
        )

        for admin_id in Config.ADMIN_USER_IDS:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=startup_message,
                    parse_mode="HTML"
                )
                logger.info(f"📨 Notificación enviada a admin {admin_id}")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo notificar a admin {admin_id}: {e}")
    else:
        logger.warning("⚠️ Bot iniciado pero sin verificación de conectividad. Revisa tu conexión de red.")

    logger.info("✅ Bot iniciado y listo para recibir mensajes")


async def on_shutdown(bot: Bot, dispatcher: Dispatcher) -> None:
    """
    Callback ejecutado al cerrar el bot (graceful shutdown).

    Tareas:
    - Cerrar base de datos
    - Detener background tasks
    - Notificar a admins que el bot está offline (con timeout)
    - Limpiar recursos

    Args:
        bot: Instancia del bot
        dispatcher: Instancia del dispatcher
    """
    logger.info("🛑 Cerrando bot...")

    # Activar timeout de emergencia por si el shutdown se cuelga
    _activate_shutdown_timeout()

    # Detener background tasks (sin bloquear)
    stop_background_tasks()

    # Notificar a admins (con timeout para no bloquear shutdown)
    shutdown_message = "🛑 Bot detenido correctamente"

    for admin_id in Config.ADMIN_USER_IDS:
        try:
            await asyncio.wait_for(
                bot.send_message(chat_id=admin_id, text=shutdown_message),
                timeout=5  # Timeout de 5s para cada notificación
            )
        except asyncio.TimeoutError:
            logger.warning(f"⚠️ Timeout notificando shutdown a admin {admin_id}")
        except Exception as e:
            logger.warning(f"⚠️ No se pudo notificar shutdown a admin {admin_id}: {e}")

    # Cerrar base de datos
    await close_db()

    logger.info("✅ Bot cerrado correctamente")


async def main() -> None:
    """
    Función principal que ejecuta el bot.

    Configuración:
    - Bot con parse_mode HTML por defecto
    - MemoryStorage para FSM (ligero, apropiado para Termux)
    - Dispatcher con callbacks de startup/shutdown
    - Polling con timeout de 30s (apropiado para Termux)
    """
    # Crear instancia del bot
    bot = Bot(
        token=Config.BOT_TOKEN,
        parse_mode="HTML"  # HTML por defecto para mensajes
    )

    # Crear storage para FSM (estados de conversación)
    storage = MemoryStorage()

    # Crear dispatcher
    dp = Dispatcher(storage=storage)

    # Registrar handlers ANTES de empezar el polling
    from bot.handlers import register_all_handlers
    register_all_handlers(dp)

    # Registrar callbacks de lifecycle
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    try:
        # Iniciar polling (long polling con timeout de 30s)
        logger.info("🔄 Iniciando polling...")
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            timeout=30,  # Timeout apropiado para conexiones inestables en Termux
            drop_pending_updates=True,  # Ignorar updates pendientes del pasado
            relax_timeout=True  # Reduce requests frecuentes
        )
    except KeyboardInterrupt:
        logger.info("⌨️ Interrupción por teclado (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Error crítico en polling: {e}", exc_info=True)
    finally:
        # Cleanup forceful
        logger.info("🧹 Limpiando recursos...")
        try:
            await bot.session.close()
            logger.info("🔌 Sesión del bot cerrada")
        except Exception as e:
            logger.warning(f"⚠️ Error cerrando sesión: {e}")


_shutdown_timeout_active = False


def _activate_shutdown_timeout():
    """
    Activa timeout de emergencia para forzar salida si el shutdown se cuelga.
    Esta función debe llamarse solo cuando se inicia el shutdown.
    """
    global _shutdown_timeout_active

    if _shutdown_timeout_active:
        return

    _shutdown_timeout_active = True

    def force_exit_after_timeout():
        """Fuerza salida si pasa demasiado tiempo en shutdown."""
        import time
        time.sleep(15)  # Dar 15s para shutdown limpio
        logger.critical("💥 TIMEOUT CRÍTICO: Forzando salida del proceso...")
        os._exit(1)  # Salida forzada

    # Registrar timeout thread (daemon para no bloquear)
    timeout_thread = threading.Thread(target=force_exit_after_timeout, daemon=True)
    timeout_thread.start()
    logger.info("⏱️ Timeout de shutdown activado (15s)")


if __name__ == "__main__":
    """
    Punto de entrada del script.

    Uso:
        python main.py

    Para ejecutar en background (Termux):
        nohup python main.py > bot.log 2>&1 &
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot detenido por el usuario")
    except Exception as e:
        logger.critical(f"💥 Error fatal: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Asegurar salida limpia
        logger.info("🛑 Finalizando...")
        sys.exit(0)
