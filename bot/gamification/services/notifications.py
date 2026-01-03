"""
Sistema de notificaciones del módulo de gamificación.

Este servicio gestiona el envío de notificaciones push a usuarios sobre:
- Level-ups (subida de nivel)
- Misiones completadas
- Recompensas desbloqueadas
- Milestones de rachas
- Rachas perdidas
- Milestones de besitos totales
"""

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from bot.gamification.database.models import Mission, Reward, Level, GamificationConfig
from bot.gamification.config.economy import EconomyConfig
from bot.gamification.database.enums import ObtainedVia, TransactionType
from bot.utils.lucien_messages import LucienMessages

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Servicio de notificaciones del sistema de gamificación.

    Responsabilidades:
    - Enviar notificaciones formateadas a usuarios
    - Respetar configuración de notificaciones habilitadas
    - Implementar lógica de milestones inteligentes (evitar spam)
    - Manejar errores de envío (usuarios que bloquearon bot)
    - Usar voz de Lucien para todas las notificaciones
    """

    def __init__(self, bot: Bot, session: AsyncSession):
        """
        Inicializa el servicio de notificaciones.

        Args:
            bot: Instancia del bot de Telegram
            session: Sesión de base de datos
        """
        self.bot = bot
        self.session = session

    async def _send_notification(self, user_id: int, message: str) -> None:
        """
        Envía notificación si está habilitado en configuración.

        Args:
            user_id: ID del usuario a notificar
            message: Mensaje formateado en HTML o texto plano
        """
        config = await self.session.get(GamificationConfig, 1)
        if not config or not config.notifications_enabled:
            logger.debug(f"Notifications disabled, skipping notification to {user_id}")
            return

        try:
            await self.bot.send_message(user_id, message, parse_mode="HTML")
            logger.info(f"Notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send notification to {user_id}: {e}")

    async def notify_level_up(
        self,
        user_id: int,
        old_level: Level,
        new_level: Level
    ) -> None:
        """
        Notifica al usuario que subió de nivel.

        Args:
            user_id: ID del usuario
            old_level: Nivel anterior
            new_level: Nuevo nivel alcanzado
        """
        # Buscar mensaje específico del nivel si existe
        level_key = f"LEVEL_UP_{new_level.order}"
        message = LucienMessages.profile(level_key, new_level=new_level.name)

        await self._send_notification(user_id, message)

    async def notify_mission_completed(
        self,
        user_id: int,
        mission: Mission
    ) -> None:
        """
        Notifica al usuario que completó una misión.

        Args:
            user_id: ID del usuario
            mission: Misión completada
        """
        message = LucienMessages.missions(
            "MISSION_COMPLETED",
            mission_name=mission.name,
            reward=mission.besitos_reward
        )
        await self._send_notification(user_id, message)

    async def notify_reward_unlocked(
        self,
        user_id: int,
        reward: Reward
    ) -> None:
        """
        Notifica al usuario que desbloqueó una recompensa.

        Args:
            user_id: ID del usuario
            reward: Recompensa desbloqueada
        """
        # Usar mensaje de besitos para notificar recompensa desbloqueada
        message = (
            f"<b>Nueva Recompensa Disponible</b>\n\n"
            f"{reward.name}\n"
            f"{reward.description}\n\n"
            f"Visite su perfil para reclamarla."
        )
        await self._send_notification(user_id, message)

    async def notify_streak_milestone(
        self,
        user_id: int,
        days: int,
        bonus: float
    ) -> None:
        """
        Notifica milestone de racha (solo en hitos específicos).

        Solo notifica en milestones definidos en EconomyConfig.STREAK_MILESTONES.

        Args:
            user_id: ID del usuario
            days: Número de días de racha actual
            bonus: Cantidad de besitos de bonificación
        """
        # Solo notificar en milestones específicos
        if days not in EconomyConfig.STREAK_MILESTONES:
            logger.debug(f"Streak {days} days is not a milestone, skipping notification")
            return

        # Obtener message_key desde config
        milestone_info = EconomyConfig.STREAK_MILESTONES[days]
        message_key = milestone_info.get("message_key", f"MILESTONE_{days}")

        message = LucienMessages.streak(
            message_key,
            bonus=bonus
        )
        await self._send_notification(user_id, message)

    async def notify_streak_lost(
        self,
        user_id: int,
        days: int
    ) -> None:
        """
        Notifica racha perdida (solo si era significativa).

        Solo notifica si la racha era >= 7 días.

        Args:
            user_id: ID del usuario
            days: Número de días de racha perdida
        """
        # Solo notificar si racha era significativa
        if days < 7:
            logger.debug(f"Streak {days} days too short, skipping lost notification")
            return

        message = LucienMessages.streak("LOST", days=days)
        await self._send_notification(user_id, message)

    async def notify_besitos_milestone(
        self,
        user_id: int,
        total_besitos: int
    ) -> None:
        """
        Notifica milestone de besitos totales.

        Solo notifica si el total está en BESITOS_MILESTONES.

        Args:
            user_id: ID del usuario
            total_besitos: Total actual de besitos del usuario
        """
        # Verificar si es un milestone
        if not EconomyConfig.is_milestone(total_besitos):
            logger.debug(
                f"Besitos {total_besitos} is not a milestone, "
                f"skipping notification for user {user_id}"
            )
            return

        message = LucienMessages.besitos(
            "BESITO_EARNED_MILESTONE",
            amount=total_besitos
        )
        await self._send_notification(user_id, message)

        logger.info(
            f"Besitos milestone notification sent to user {user_id} "
            f"for {total_besitos} besitos"
        )

    # =========================================================================
    # FASE 3: ARQUETIPOS
    # =========================================================================

    async def notify_archetype_detected(
        self,
        user_id: int,
        archetype: str,
        confidence: float,
        previous_archetype: str = None
    ) -> None:
        """
        Notifica al usuario que se ha detectado su arquetipo.

        Args:
            user_id: ID del usuario
            archetype: Arquetipo detectado (EXPLORER, DIRECT, etc.)
            confidence: Confianza de la detección (0-1)
            previous_archetype: Arquetipo anterior (si es re-evaluación)
        """
        # Mapeo de arquetipos a claves de mensaje
        message_keys = {
            "EXPLORER": "ARCHETYPE_DETECTED_EXPLORER",
            "DIRECT": "ARCHETYPE_DETECTED_DIRECT",
            "ROMANTIC": "ARCHETYPE_DETECTED_ROMANTIC",
            "ANALYTICAL": "ARCHETYPE_DETECTED_ANALYTICAL",
            "PERSISTENT": "ARCHETYPE_DETECTED_PERSISTENT",
            "PATIENT": "ARCHETYPE_DETECTED_PATIENT",
        }

        message_key = message_keys.get(archetype)
        if not message_key:
            logger.warning(f"⚠️ No hay mensaje de Lucien para arquetipo: {archetype}")
            return

        # Obtener mensaje de Lucien
        message = LucienMessages.archetypes(message_key)

        # Enviar notificación
        await self._send_notification(user_id, message)
        logger.info(f"📧 Notificación de arquetipo enviada a {user_id}: {archetype}")

        # Otorgar badge del arquetipo
        await self._grant_archetype_badge(user_id, archetype)

        # Otorgar besitos de celebración
        await self._grant_archetype_bonus(user_id, archetype)

    async def _grant_archetype_badge(self, user_id: int, archetype: str) -> None:
        """
        Otorga el badge correspondiente al arquetipo detectado.

        Args:
            user_id: ID del usuario
            archetype: Arquetipo detectado
        """
        from bot.gamification.services.container import GamificationContainer

        # Mapeo de arquetipos a nombres de badge
        badge_names = {
            "EXPLORER": "El Explorador",
            "DIRECT": "El Directo",
            "ROMANTIC": "El Romántico",
            "ANALYTICAL": "El Analítico",
            "PERSISTENT": "El Persistente",
            "PATIENT": "El Paciente",
        }

        badge_name = badge_names.get(archetype)
        if not badge_name:
            logger.warning(f"⚠️ No hay badge para arquetipo: {archetype}")
            return

        try:
            gamification = GamificationContainer(self.session, self.bot)

            # Buscar reward con ese nombre
            rewards = await gamification.reward.get_all_rewards()
            target_reward = None

            for reward in rewards:
                if reward.name == badge_name:
                    target_reward = reward
                    break

            if not target_reward:
                logger.warning(f"⚠️ Badge '{badge_name}' no encontrado en BD")
                logger.info(f"💡 Ejecute: python scripts/seed_archetype_badges.py")
                return

            # Verificar si el usuario ya tiene este badge
            existing = await gamification.reward.get_user_reward(
                user_id=user_id,
                reward_id=target_reward.id
            )

            if existing:
                logger.info(f"🏆 Usuario {user_id} ya tiene el badge '{badge_name}'")
                return

            # Otorgar reward
            await gamification.reward.grant_reward(
                user_id=user_id,
                reward_id=target_reward.id,
                obtained_via=ObtainedVia.AUTO_UNLOCK,
                reference_id=None
            )

            logger.info(f"🏆 Badge '{badge_name}' otorgado a {user_id}")

        except Exception as e:
            logger.error(f"❌ Error otorgando badge: {e}", exc_info=True)

    async def _grant_archetype_bonus(
        self,
        user_id: int,
        archetype: str
    ) -> None:
        """
        Otorga besitos de celebración por detección de arquetipo.

        Args:
            user_id: ID del usuario
            archetype: Arquetipo detectado
        """
        from bot.gamification.services.besito import BesitoService

        try:
            # Bonus de besitos por detección de arquetipo
            besito_bonus = 10  # 10 besitos de celebración

            besito_service = BesitoService(self.session)
            await besito_service.grant_besitos(
                user_id=user_id,
                amount=besito_bonus,
                transaction_type=TransactionType.ADMIN_GRANT,
                description=f"Detección de arquetipo: {archetype}",
                reference_id=None
            )

            logger.info(f"💰 {besito_bonus} besitos otorgados a {user_id} por detección de arquetipo")

        except Exception as e:
            logger.error(f"❌ Error otorgando bonus de besitos: {e}", exc_info=True)

    async def check_and_notify_archetype(self, user_id: int) -> bool:
        """
        Verifica si se debe detectar/notificar arquetipo y lo hace si corresponde.

        Este método es el punto de entrada principal para activar
        la detección y notificación de arquetipo desde los handlers.

        Args:
            user_id: ID del usuario

        Returns:
            True si se detectó y notificó un nuevo arquetipo, False en caso contrario
        """
        from bot.gamification.services.archetype_detection import ArchetypeDetectionService

        try:
            detection_service = ArchetypeDetectionService(self.session)

            # Obtener arquetipo actual
            current_archetype = await detection_service.get_archetype(user_id)

            # Verificar si se debe re-evaluar
            should_reevaluate = await detection_service.should_reevaluate(user_id)

            if not should_reevaluate and current_archetype:
                # Ya tiene arquetipo y no toca re-evaluar
                return False

            # Ejecutar detección
            result = await detection_service.detect_archetype(user_id)

            if not result.archetype:
                # No se pudo detectar arquetipo
                return False

            # Verificar si se debe notificar
            if not self._should_notify_archetype(
                user_id=user_id,
                new_archetype=result.archetype,
                previous_archetype=current_archetype
            ):
                return False

            # Notificar al usuario
            await self.notify_archetype_detected(
                user_id=user_id,
                archetype=result.archetype,
                confidence=result.confidence,
                previous_archetype=current_archetype
            )

            return True

        except Exception as e:
            logger.error(f"❌ Error en check_and_notify_archetype: {e}", exc_info=True)
            return False

    def _should_notify_archetype(
        self,
        user_id: int,
        new_archetype: str,
        previous_archetype: str = None
    ) -> bool:
        """
        Determina si se debe notificar al usuario sobre el arquetipo.

        Args:
            user_id: ID del usuario
            new_archetype: Nuevo arquetipo detectado
            previous_archetype: Arquetipo anterior (si existe)

        Returns:
            True si se debe notificar, False en caso contrario
        """
        # Notificar si:
        # 1. Es la primera vez que se detecta (no hay previous_archetype)
        # 2. El arquetipo cambió (new_archetype != previous_archetype)

        if previous_archetype is None:
            # Primera detección - SI notificar
            return True

        if new_archetype != previous_archetype:
            # El arquetipo cambió - SI notificar
            return True

        # Mismo arquetipo - NO notificar (evitar spam)
        return False
