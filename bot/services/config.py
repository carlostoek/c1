"""
Config Service - Gestión de configuración global del bot.

Responsabilidades:
- Obtener/actualizar configuración de BotConfig (singleton)
- Gestionar tiempo de espera Free
- Gestionar reacciones de canales
- Validar que configuración está completa
"""
import logging
from typing import List, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import BotConfig

logger = logging.getLogger(__name__)


class ConfigService:
    """
    Service para gestionar configuración global del bot.

    BotConfig es singleton (1 solo registro con id=1).
    Todos los métodos operan sobre ese registro.
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el service.

        Args:
            session: Sesión de base de datos
        """
        self.session = session
        logger.debug("✅ ConfigService inicializado")

    # ===== GETTERS =====

    async def get_config(self) -> BotConfig:
        """
        Obtiene la configuración del bot (singleton).

        Returns:
            BotConfig: Configuración global

        Raises:
            RuntimeError: Si BotConfig no existe (no debería pasar)
        """
        config = await self.session.get(BotConfig, 1)

        if config is None:
            raise RuntimeError(
                "BotConfig no encontrado. "
                "Ejecuta init_db() para crear la configuración inicial."
            )

        return config

    async def get_wait_time(self) -> int:
        """
        Obtiene el tiempo de espera para canal Free (en minutos).

        Returns:
            Tiempo de espera en minutos
        """
        config = await self.get_config()
        return config.wait_time_minutes

    async def get_vip_channel_id(self) -> Optional[str]:
        """
        Obtiene el ID del canal VIP configurado.

        Returns:
            ID del canal, o None si no configurado
        """
        config = await self.get_config()
        return config.vip_channel_id if config.vip_channel_id else None

    async def get_free_channel_id(self) -> Optional[str]:
        """
        Obtiene el ID del canal Free configurado.

        Returns:
            ID del canal, o None si no configurado
        """
        config = await self.get_config()
        return config.free_channel_id if config.free_channel_id else None

    async def get_vip_reactions(self) -> List[str]:
        """
        Obtiene las reacciones configuradas para el canal VIP.

        Returns:
            Lista de emojis (ej: ["👍", "❤️", "🔥"])
        """
        config = await self.get_config()
        return config.vip_reactions if config.vip_reactions else []

    async def get_free_reactions(self) -> List[str]:
        """
        Obtiene las reacciones configuradas para el canal Free.

        Returns:
            Lista de emojis
        """
        config = await self.get_config()
        return config.free_reactions if config.free_reactions else []

    async def get_subscription_fees(self) -> Dict[str, float]:
        """
        Obtiene las tarifas de suscripción configuradas.

        Returns:
            Dict con tarifas (ej: {"monthly": 10, "yearly": 100})
        """
        config = await self.get_config()
        return config.subscription_fees if config.subscription_fees else {}

    # ===== SETTERS =====

    async def set_wait_time(self, minutes: int) -> None:
        """
        Actualiza el tiempo de espera para canal Free.

        Args:
            minutes: Tiempo en minutos (debe ser >= 1)

        Raises:
            ValueError: Si minutes < 1
        """
        if minutes < 1:
            raise ValueError("Tiempo de espera debe ser al menos 1 minuto")

        config = await self.get_config()
        old_value = config.wait_time_minutes
        config.wait_time_minutes = minutes

        await self.session.commit()

        logger.info(
            f"⏱️ Tiempo de espera Free actualizado: "
            f"{old_value} min → {minutes} min"
        )

    async def set_vip_reactions(self, reactions: List[str]) -> None:
        """
        Actualiza las reacciones del canal VIP.

        Args:
            reactions: Lista de emojis (ej: ["👍", "❤️"])

        Raises:
            ValueError: Si la lista está vacía o tiene más de 10 elementos
        """
        if not reactions:
            raise ValueError("Debe haber al menos 1 reacción")

        if len(reactions) > 10:
            raise ValueError("Máximo 10 reacciones permitidas")

        config = await self.get_config()
        config.vip_reactions = reactions

        await self.session.commit()

        logger.info(f"✅ Reacciones VIP actualizadas: {', '.join(reactions)}")

    async def set_free_reactions(self, reactions: List[str]) -> None:
        """
        Actualiza las reacciones del canal Free.

        Args:
            reactions: Lista de emojis

        Raises:
            ValueError: Si la lista está vacía o tiene más de 10 elementos
        """
        if not reactions:
            raise ValueError("Debe haber al menos 1 reacción")

        if len(reactions) > 10:
            raise ValueError("Máximo 10 reacciones permitidas")

        config = await self.get_config()
        config.free_reactions = reactions

        await self.session.commit()

        logger.info(f"✅ Reacciones Free actualizadas: {', '.join(reactions)}")

    async def set_subscription_fees(self, fees: Dict[str, float]) -> None:
        """
        Actualiza las tarifas de suscripción.

        Args:
            fees: Dict con tarifas (ej: {"monthly": 10, "yearly": 100})

        Raises:
            ValueError: Si fees está vacío o contiene valores negativos
        """
        if not fees:
            raise ValueError("Debe haber al menos 1 tarifa configurada")

        # Validar que todos los valores sean positivos
        for key, value in fees.items():
            if value < 0:
                raise ValueError(f"Tarifa '{key}' no puede ser negativa: {value}")

        config = await self.get_config()
        config.subscription_fees = fees

        await self.session.commit()

        logger.info(f"💰 Tarifas actualizadas: {fees}")

    # ===== VALIDACIÓN =====

    async def is_fully_configured(self) -> bool:
        """
        Verifica si el bot está completamente configurado.

        Configuración completa requiere:
        - Canal VIP configurado
        - Canal Free configurado
        - Tiempo de espera > 0

        Returns:
            True si configuración está completa, False si no
        """
        config = await self.get_config()

        if not config.vip_channel_id:
            return False

        if not config.free_channel_id:
            return False

        if config.wait_time_minutes < 1:
            return False

        return True

    async def get_config_status(self) -> Dict[str, any]:
        """
        Obtiene el estado de la configuración (para dashboard).

        Returns:
            Dict con información de configuración:
            {
                "is_configured": bool,
                "vip_channel_id": str | None,
                "free_channel_id": str | None,
                "wait_time_minutes": int,
                "vip_reactions_count": int,
                "free_reactions_count": int,
                "missing": List[str]  # Lista de elementos faltantes
            }
        """
        config = await self.get_config()

        missing = []

        if not config.vip_channel_id:
            missing.append("Canal VIP")

        if not config.free_channel_id:
            missing.append("Canal Free")

        if config.wait_time_minutes < 1:
            missing.append("Tiempo de espera")

        return {
            "is_configured": len(missing) == 0,
            "vip_channel_id": config.vip_channel_id,
            "free_channel_id": config.free_channel_id,
            "wait_time_minutes": config.wait_time_minutes,
            "vip_reactions_count": len(config.vip_reactions) if config.vip_reactions else 0,
            "free_reactions_count": len(config.free_reactions) if config.free_reactions else 0,
            "missing": missing
        }

    # ===== UTILIDADES =====

    async def reset_to_defaults(self) -> None:
        """
        Resetea la configuración a valores por defecto.

        ADVERTENCIA: Esto elimina la configuración de canales.
        Solo usar en caso de necesitar resetear completamente.
        """
        config = await self.get_config()

        config.vip_channel_id = None
        config.free_channel_id = None
        config.wait_time_minutes = 5
        config.vip_reactions = []
        config.free_reactions = []
        config.subscription_fees = {"monthly": 10, "yearly": 100}

        await self.session.commit()

        logger.warning("⚠️ Configuración reseteada a valores por defecto")

    async def get_config_summary(self) -> str:
        """
        Retorna un resumen de la configuración en formato texto.

        Útil para mostrar en mensajes de Telegram.

        Returns:
            String formateado con información de configuración
        """
        config = await self.get_config()
        status = await self.get_config_status()

        vip_status = "✅ Configurado" if config.vip_channel_id else "❌ No configurado"
        free_status = "✅ Configurado" if config.free_channel_id else "❌ No configurado"

        summary = f"""
📊 <b>Estado de Configuración</b>

<b>Canal VIP:</b> {vip_status}
{f"ID: <code>{config.vip_channel_id}</code>" if config.vip_channel_id else ""}

<b>Canal Free:</b> {free_status}
{f"ID: <code>{config.free_channel_id}</code>" if config.free_channel_id else ""}

<b>Tiempo de Espera:</b> {config.wait_time_minutes} minutos

<b>Reacciones VIP:</b> {len(config.vip_reactions) if config.vip_reactions else 0} configuradas
<b>Reacciones Free:</b> {len(config.free_reactions) if config.free_reactions else 0} configuradas
        """.strip()

        if not status["is_configured"]:
            summary += f"\n\n⚠️ <b>Faltante:</b> {', '.join(status['missing'])}"

        return summary
