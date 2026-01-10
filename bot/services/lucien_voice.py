"""
Servicio de voz de Lucien.

Centraliza todos los mensajes del bot con la personalidad de Lucien:
formal pero no frío, observador pero no invasivo, protector de Diana,
elegantemente sarcástico cuando corresponde, respetuoso siempre.
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from bot.config import lucien_templates as templates

logger = logging.getLogger(__name__)


class LucienVoiceService:
    """Servicio centralizado para la voz y personalidad de Lucien."""

    def __init__(self):
        """Inicializa el servicio de voz."""
        pass

    async def get_welcome_message(
        self,
        user_type: str,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Obtiene mensaje de bienvenida adaptado al tipo de usuario.

        Args:
            user_type: Tipo de usuario ("new_user", "returning_user", "active_user", "admin", "vip_user", "free_user")
            user_context: Contexto adicional del usuario
                - archetype: Arquetipo detectado (opcional)
                - days_absent: Días desde última visita
                - is_vip: Si es VIP
                - vip_days_remaining: Días VIP restantes
                - completed_onboarding: Si completó onboarding (para free_user)

        Returns:
            str: Mensaje personalizado
        """
        user_context = user_context or {}

        if user_type == "admin":
            return templates.WELCOME_MESSAGES["admin"]

        # Usuario VIP (menú diferenciado)
        if user_type == "vip_user":
            return templates.WELCOME_MESSAGES["vip_user"]

        # Usuario FREE (menú diferenciado)
        if user_type == "free_user":
            return templates.WELCOME_MESSAGES["free_user"]

        # Usuario nuevo
        if user_type == "new_user":
            archetype = user_context.get("archetype", "default")
            messages = templates.WELCOME_MESSAGES["new_user"]
            return messages.get(archetype, messages["default"])

        # Usuario que regresa
        if user_type == "returning_user":
            days_absent = user_context.get("days_absent", 0)
            messages = templates.WELCOME_MESSAGES["returning_user"]

            if days_absent <= 3:
                return messages["short_absence"]
            elif days_absent >= 7:
                days_text = templates.get_days_text(days_absent)
                return messages["long_absence"].format(
                    days=days_absent, days_text=days_text
                )
            else:
                days_text = templates.get_days_text(days_absent)
                return messages["default"].format(days_text=days_text)

        # Usuario activo
        if user_type == "active_user":
            is_vip = user_context.get("is_vip", False)
            messages = templates.WELCOME_MESSAGES["active_user"]

            if is_vip:
                days_remaining = user_context.get("vip_days_remaining", 0)
                days_text = templates.get_remaining_days_text(days_remaining)
                return messages["vip"].format(
                    days_remaining=days_remaining, days_text=days_text
                )
            else:
                return messages["default"]

        # Fallback
        return templates.WELCOME_MESSAGES["new_user"]["default"]

    async def format_error(
        self,
        error_type: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Formatea un mensaje de error con la voz de Lucien.

        Args:
            error_type: Tipo de error (ver ERROR_MESSAGES en templates)
            details: Detalles adicionales para formatear el mensaje
                - element: Elemento no configurado
                - time_seconds: Segundos de cooldown restante
                - limit_type: Tipo de límite alcanzado
                - days_remaining: Días VIP restantes
                - attempts_remaining: Intentos restantes

        Returns:
            str: Mensaje de error formateado
        """
        details = details or {}
        message_template = templates.ERROR_MESSAGES.get(error_type)

        if not message_template:
            logger.warning(f"Tipo de error no encontrado: {error_type}")
            return "Ha ocurrido un error. Lucien investigará."

        # Formatear según el tipo de error
        if error_type == "not_configured":
            element = details.get("element", "esto")
            return message_template.format(element=element)

        elif error_type == "cooldown_active":
            time_seconds = details.get("time_seconds", 60)
            time_text = templates.get_time_text(time_seconds)
            return message_template.format(time_text=time_text)

        elif error_type == "limit_reached":
            limit_type = details.get("limit_type", "el límite")
            return message_template.format(limit_type=limit_type)

        elif error_type == "token_expired":
            time_text = details.get("time_text", "hace tiempo")
            return message_template.format(time_text=time_text)

        elif error_type == "already_vip":
            days_remaining = details.get("days_remaining", 0)
            days_text = templates.get_remaining_days_text(days_remaining)
            return message_template.format(
                days_remaining=days_remaining, days_text=days_text
            )

        elif error_type == "challenge_failed":
            attempts_remaining = details.get("attempts_remaining", 0)
            return message_template.format(
                attempts_remaining=attempts_remaining
            )

        else:
            return message_template

    async def format_confirmation(
        self,
        action_type: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Formatea un mensaje de confirmación con la voz de Lucien.

        Args:
            action_type: Tipo de acción (ver CONFIRMATION_MESSAGES)
            details: Detalles de la acción
                - item_name: Nombre del item
                - cost: Costo en besitos
                - level_name: Nombre del nivel
                - reward_name: Nombre de la recompensa
                - token: Token generado
                - hours: Horas de validez
                - channel_type: Tipo de canal
                - channel_name: Nombre del canal

        Returns:
            str: Mensaje de confirmación formateado
        """
        details = details or {}
        message_template = templates.CONFIRMATION_MESSAGES.get(action_type)

        if not message_template:
            logger.warning(f"Tipo de confirmación no encontrado: {action_type}")
            return "Hecho."

        # Formatear según el tipo de confirmación
        try:
            return message_template.format(**details)
        except KeyError as e:
            logger.error(
                f"Falta parámetro en confirmación {action_type}: {e}"
            )
            return message_template

    async def get_notification(
        self,
        notification_type: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Obtiene un mensaje de notificación con la voz de Lucien.

        Args:
            notification_type: Tipo de notificación
            data: Datos de la notificación

        Returns:
            str: Mensaje de notificación formateado
        """
        data = data or {}

        # Streak milestones
        if notification_type.startswith("streak_milestone"):
            days = data.get("streak_days", 0)
            bonus_besitos = data.get("bonus_besitos", 0)

            if days >= 30:
                key = "30_days"
            elif days >= 14:
                key = "14_days"
            elif days >= 7:
                key = "7_days"
            else:
                return ""

            message = templates.NOTIFICATION_MESSAGES["streak_milestone"][key]
            return message.format(bonus_besitos=bonus_besitos)

        # Streak perdido
        elif notification_type == "streak_lost":
            streak_days = data.get("streak_days", 0)
            return templates.NOTIFICATION_MESSAGES["streak_lost"].format(
                streak_days=streak_days
            )

        # Misión completada
        elif notification_type == "mission_completed":
            mission_name = data.get("mission_name", "Misión")
            reward = data.get("reward", "")
            return templates.NOTIFICATION_MESSAGES[
                "mission_completed"
            ].format(mission_name=mission_name, reward=reward)

        # Recompensa desbloqueada
        elif notification_type == "reward_unlocked":
            reward_name = data.get("reward_name", "Recompensa")
            description = data.get("description", "")
            return templates.NOTIFICATION_MESSAGES["reward_unlocked"].format(
                reward_name=reward_name, description=description
            )

        # VIP por expirar
        elif notification_type == "vip_expiring_soon":
            days = data.get("days_remaining", 0)
            return templates.NOTIFICATION_MESSAGES[
                "vip_expiring_soon"
            ].format(days=days)

        # Contenido nuevo
        elif notification_type == "new_content_available":
            channel_name = data.get("channel_name", "el canal")
            return templates.NOTIFICATION_MESSAGES[
                "new_content_available"
            ].format(channel_name=channel_name)

        # Regalo diario
        elif notification_type == "daily_gift_available":
            return templates.NOTIFICATION_MESSAGES["daily_gift_available"]

        else:
            logger.warning(
                f"Tipo de notificación no encontrado: {notification_type}"
            )
            return ""

    async def get_conversion_message(
        self,
        conversion_type: str,
        archetype: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Obtiene un mensaje de conversión adaptado al arquetipo del usuario.

        Args:
            conversion_type: Tipo de conversión ("free_to_vip", "vip_renewal")
            archetype: Arquetipo del usuario para personalización
            data: Datos adicionales (días, descuentos, etc.)

        Returns:
            str: Mensaje de conversión personalizado
        """
        data = data or {}
        messages = templates.CONVERSION_MESSAGES.get(conversion_type)

        if not messages:
            return ""

        # Free to VIP
        if conversion_type == "free_to_vip":
            archetype_key = archetype or "default"
            message = messages.get(archetype_key, messages["default"])
            return message

        # VIP renewal
        elif conversion_type == "vip_renewal":
            days = data.get("days_remaining", 0)
            discount = data.get("discount_percent", 0)
            return messages["default"].format(days=days, discount=discount)

        return ""

    async def get_retention_message(
        self, user_state: str, days_inactive: int
    ) -> str:
        """
        Obtiene un mensaje de retención según el estado del usuario.

        Args:
            user_state: Estado del usuario ("at_risk", "dormant_first", "dormant_final", "lost")
            days_inactive: Días sin actividad

        Returns:
            str: Mensaje de retención, o cadena vacía si no aplica
        """
        message_template = templates.RETENTION_MESSAGES.get(user_state)

        if not message_template:
            return ""

        return message_template.format(days=days_inactive)

    async def personalize_by_archetype(
        self, base_message: str, archetype: str
    ) -> str:
        """
        Personaliza un mensaje base según el arquetipo del usuario.

        Agrega pequeños ajustes de tono según la personalidad detectada.

        Args:
            base_message: Mensaje base
            archetype: Arquetipo del usuario

        Returns:
            str: Mensaje personalizado
        """
        # Prefijos por arquetipo (formalidad "usted")
        prefixes = {
            "explorer": "Observo su curiosidad. ",
            "direct": "",  # Sin prefijo, directo al punto
            "romantic": "He notado su sensibilidad. ",
            "analytical": "Comprendo su necesidad de claridad. ",
            "persistent": "Su determinación no pasa desapercibida. ",
            "patient": "Aprecio su paciencia. ",
        }

        prefix = prefixes.get(archetype, "")
        return f"{prefix}{base_message}" if prefix else base_message

    async def get_profile_message(
        self, level: int, besitos: int, archetype: Optional[str] = None
    ) -> str:
        """
        Obtiene mensaje de perfil con comentario según nivel.

        Args:
            level: Nivel del usuario (1-7)
            besitos: Cantidad de besitos
            archetype: Arquetipo detectado (opcional)

        Returns:
            str: Mensaje de perfil formateado
        """
        # Determinar comentario según nivel
        if level <= 2:
            level_comment = templates.PROFILE_MESSAGES["level_low"]
        elif level <= 4:
            level_comment = templates.PROFILE_MESSAGES["level_mid"]
        elif level <= 6:
            level_comment = templates.PROFILE_MESSAGES["level_high"]
        else:
            level_comment = templates.PROFILE_MESSAGES["level_max"]

        message = (
            f"{level_comment}\n\n"
            f"📊 <b>Su Expediente</b>\n\n"
        )

        if archetype:
            from bot.narrative.config_data.archetypes import ExpandedArchetype
            arch = ExpandedArchetype(archetype)
            message += f"\n\nArquetipo: {arch.display_name}\n{arch.emoji}"

        return message

    async def get_cabinet_message(
        self, message_type: str, details: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Obtiene mensaje del Gabinete con voz de Lucien.

        Args:
            message_type: Tipo de mensaje (welcome, confirm_purchase, purchase_success, insufficient_funds)
            details: Detalles para formatear (item_name, price, required, current)

        Returns:
            str: Mensaje formateado
        """
        details = details or {}
        message_template = templates.CABINET_MESSAGES.get(message_type)

        if not message_template:
            logger.warning(f"Tipo de mensaje de gabinete no encontrado: {message_type}")
            return ""

        try:
            return message_template.format(**details)
        except KeyError as e:
            logger.error(f"Falta parámetro en mensaje de gabinete {message_type}: {e}")
            return message_template

    async def get_encargos_message(
        self, message_type: str, details: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Obtiene mensaje de Encargos con voz de Lucien.

        Args:
            message_type: Tipo de mensaje (welcome, progress, completed, empty)
            details: Detalles para formatear (mission_name, current, target, reward, progress_pct)

        Returns:
            str: Mensaje formateado
        """
        details = details or {}

        if message_type == "progress":
            # Determinar comentario según progreso
            progress_pct = details.get("progress_pct", 0)
            if progress_pct <= 25:
                comment_key = "0_25"
            elif progress_pct <= 50:
                comment_key = "26_50"
            elif progress_pct <= 75:
                comment_key = "51_75"
            else:
                comment_key = "76_99"

            details["lucien_comment"] = templates.ENCARGOS_MESSAGES["progress_comments"][comment_key]

        message_template = templates.ENCARGOS_MESSAGES.get(message_type)

        if not message_template:
            logger.warning(f"Tipo de mensaje de encargos no encontrado: {message_type}")
            return ""

        try:
            return message_template.format(**details)
        except KeyError as e:
            logger.error(f"Falta parámetro en mensaje de encargos {message_type}: {e}")
            return message_template

    async def get_besitos_message(
        self, message_type: str, details: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Obtiene mensaje de Besitos con voz de Lucien.

        Args:
            message_type: Tipo de mensaje (balance_low, balance_growing, balance_good, balance_high,
                          balance_hoarder, earned, earned_milestone, insufficient)
            details: Detalles para formatear (total, amount, required, current)

        Returns:
            str: Mensaje formateado
        """
        details = details or {}
        message_template = templates.BESITOS_MESSAGES.get(message_type)

        if not message_template:
            logger.warning(f"Tipo de mensaje de besitos no encontrado: {message_type}")
            return ""

        try:
            return message_template.format(**details)
        except KeyError as e:
            logger.error(f"Falta parámetro en mensaje de besitos {message_type}: {e}")
            return message_template

    async def get_content_set_message(
        self,
        message_type: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Obtiene mensaje de Content Set con voz de Lucien.

        Args:
            message_type: Tipo de mensaje (content_delivered, content_delivered_from_shop,
                          content_delivered_from_reward, content_delivered_from_narrative,
                          content_gift_received, content_vip_required, content_premium_required,
                          content_gift_only, content_not_found, content_access_denied,
                          content_no_files, content_delivery_failed, content_set_created,
                          content_set_updated, content_set_deleted, content_set_test_sent)
            details: Detalles para formatear (content_name, description, item_name, user_id)

        Returns:
            str: Mensaje formateado
        """
        details = details or {}
        message_template = templates.CONTENT_SET_MESSAGES.get(message_type)

        if not message_template:
            logger.warning(f"Tipo de mensaje de content set no encontrado: {message_type}")
            return ""

        try:
            return message_template.format(**details)
        except KeyError as e:
            logger.error(f"Falta parámetro en mensaje de content set {message_type}: {e}")
            return message_template

    def get_voice_characteristics(self) -> Dict[str, str]:
        """
        Obtiene las características de la voz de Lucien para referencia.

        Returns:
            dict: Guía de estilo de Lucien
        """
        return {
            "tone": "Formal pero no frío",
            "role": "Observador pero no invasivo",
            "relationship": "Protector de Diana",
            "style": "Elegantemente sarcástico cuando corresponde",
            "principle": "Respetuoso siempre",
            "never": "Servil, agresivo, vendedor, casual, robótico",
            "examples": {
                "good": [
                    "He preparado algo que podría interesarte. Si decides verlo.",
                    "Han pasado días desde tu última visita. Diana preguntó por ti.",
                    "He observado tu progreso. Ahora eres Iniciado. Diana estará complacida.",
                ],
                "bad": [
                    "¡Hey! ¡Tenemos ofertas increíbles para ti! 🎉",
                    "¡Te extrañamos! Vuelve pronto 😢",
                    "¡Felicidades! ¡Subiste de nivel! 🎊",
                ],
            },
        }

    async def get_teaser_message(
        self,
        teaser_type: str,
    ) -> str:
        """
        Obtiene un mensaje teaser para contenido bloqueado por onboarding.

        Args:
            teaser_type: Tipo de teaser ("narrative_blocked", "profile_blocked", "games_blocked")

        Returns:
            str: Mensaje teaser formateado con la voz de Lucien
        """
        message_template = templates.TEASER_MESSAGES.get(teaser_type)

        if not message_template:
            logger.warning(f"Tipo de teaser no encontrado: {teaser_type}")
            # Fallback a onboarding_required genérico
            return templates.ERROR_MESSAGES.get("onboarding_required",
                "🎩 <b>Lucien:</b>\n<i>Complete el tutorial para acceder.</i>")

        return message_template
