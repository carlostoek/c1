"""
Servicio de mensajes adaptados por arquetipo (FASE 3.7).

Permite personalizar el contenido que se muestra al usuario según su arquetipo
detectado, mejorando la experiencia y la conversión.

Author: Sistema de Gamificación
Version: 1.0
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from bot.gamification.services.archetype_detection import ArchetypeDetectionService
from bot.utils.lucien_messages import LucienMessages

logger = logging.getLogger(__name__)


class AdaptedMessageService:
    """
    Servicio de mensajes adaptados por arquetipo.

    Responsabilidades:
    - Obtener mensaje adaptado según arquetipo del usuario
    - Proporcionar variaciones de contenido personalizadas
    - Mantener fallback a mensaje genérico si no hay arquetipo
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio de mensajes adaptados.

        Args:
            session: Sesión de base de datos
        """
        self.session = session
        self.detection_service = ArchetypeDetectionService(session)

    async def get_adapted_message(
        self,
        user_id: int,
        message_variants: Dict[str, str],
        default_message: Optional[str] = None
    ) -> str:
        """
        Obtiene el mensaje adaptado según el arquetipo del usuario.

        Args:
            user_id: ID del usuario
            message_variants: Diccionario con variantes por arquetipo
                {
                    "EXPLORER": "Mensaje para exploradores...",
                    "DIRECT": "Mensaje directos...",
                    "ROMANTIC": "Mensaje románticos...",
                    "ANALYTICAL": "Mensaje analíticos...",
                    "PERSISTENT": "Mensaje persistentes...",
                    "PATIENT": "Mensaje pacientes...",
                    "default": "Mensaje genérico..."
                }
            default_message: Mensaje por defecto si no hay arquetipo (opcional)

        Returns:
            Mensaje adaptado al arquetipo o default_message
        """
        try:
            # Obtener arquetipo del usuario
            archetype = await self.detection_service.get_archetype(user_id)

            if not archetype:
                # No hay arquetipo detectado aún
                if default_message:
                    return default_message
                return message_variants.get("default", "")

            # Obtener variante para el arquetipo
            adapted_message = message_variants.get(archetype)

            if not adapted_message:
                # No hay variante para este arquetipo, usar default
                if default_message:
                    return default_message
                return message_variants.get("default", "")

            return adapted_message

        except Exception as e:
            logger.error(f"❌ Error obteniendo mensaje adaptado: {e}", exc_info=True)
            # Fallback a default en caso de error
            if default_message:
                return default_message
            return message_variants.get("default", "")

    async def get_adapted_vip_invitation(self, user_id: int) -> str:
        """
        Obtiene mensaje de invitación VIP adaptado al arquetipo.

        Args:
            user_id: ID del usuario

        Returns:
            Mensaje de invitación VIP personalizado
        """
        variants = {
            "EXPLORER": (
                "Su curiosidad lo ha traído lejos.\n\n"
                "Pero Diana tiene contenido que aún no ha visto. "
                "Cosas que很少有人 encuentran. Secretos ocultos.\n\n"
                "El acceso VIP le mostrará lo que otros no pueden ver.\n\n"
                "¿Quiere explorar más?"
            ),

            "DIRECT": (
                "Voy al grano.\n\n"
                "Diana tiene contenido exclusivo. "
                "Uso el comando /vip si quiere acceso.\n\n"
                "Simple. Eficiente."
            ),

            "ROMANTIC": (
                "He notado cómo busca conexión en cada interacción.\n\n"
                "Diana guarda sus pensamientos más íntimos "
                "para quienes demuestran... sensibilidad.\n\n"
                "El círculo VIP es donde comparte su alma. "
                "Quizás usted pertenezca allí.\n\n"
                "¿Se atreve a entrar?"
            ),

            "ANALYTICAL": (
                "Basado en su patrón de comportamiento, "
                "me permito sugerir algo.\n\n"
                "Diana tiene contenido que requiere "
                "un nivel de... comprensión superior.\n\n"
                "Análisis detallados. Insights exclusivos. "
                "Información que no está disponible públicamente.\n\n"
                "Si valora la información profunda, "
                "el acceso VIP es para usted."
            ),

            "PERSISTENT": (
                "Su dedicación es... notable.\n\n"
                "Muchos habrían abandonado hace tiempo. "
                "Usted sigue aquí. Interesante.\n\n"
                "Diana premia la persistencia. "
                "Tiene contenido reservado especialmente "
                "para quienes no se rinden.\n\n"
                "¿Quiere ver lo que ha ganado?"
            ),

            "PATIENT": (
                "He observado su paciencia.\n\n"
                "Es una virtud rara. Diana la valora especialmente.\n\n"
                "Las cosas buenas toman tiempo. "
                "Lo mejor del contenido de Diana está protegido. "
                "Esperando a quienes saben esperar.\n\n"
                "El acceso VIP le mostrará lo que "
                "la impaciencia nunca puede alcanzar."
            ),

            "default": LucienMessages.conversion("VIP_INVITATION_INTRO")
        }

        return await self.get_adapted_message(user_id, variants)

    async def get_adapted_mission_description(
        self,
        user_id: int,
        mission_name: str,
        base_description: str
    ) -> str:
        """
        Adapta la descripción de una misión según el arquetipo.

        Args:
            user_id: ID del usuario
            mission_name: Nombre de la misión
            base_description: Descripción base de la misión

        Returns:
            Descripción adaptada o base_description
        """
        # Para misiones, añadimos un intro personalizado
        # pero mantenemos la descripción base intacta
        intros = {
            "EXPLORER": (
                f"Una oportunidad de explorar: {mission_name}\n\n"
                f"{base_description}\n\n"
                "Quien sabe qué encontrará."
            ),

            "DIRECT": (
                f"{mission_name}\n\n"
                f"{base_description}"
            ),

            "ROMANTIC": (
                f"{mission_name}\n\n"
                f"{base_description}\n\n"
                "Diana siente que esto será... significativo para usted."
            ),

            "ANALYTICAL": (
                f"Misión: {mission_name}\n\n"
                f"{base_description}\n\n"
                "Complete esto para mejorar sus estadísticas."
            ),

            "PERSISTENT": (
                f"{mission_name}\n\n"
                f"{base_description}\n\n"
                "Un paso más. Continúe así."
            ),

            "PATIENT": (
                f"{mission_name}\n\n"
                f"{base_description}\n\n"
                "Tómese su tiempo. No hay prisa."
            ),

            "default": f"{mission_name}\n\n{base_description}"
        }

        return await self.get_adapted_message(user_id, intros)

    async def get_adapted_shop_hint(self, user_id: int) -> str:
        """
        Obtiene un hint para la tienda adaptado al arquetipo.

        Args:
            user_id: ID del usuario

        Returns:
            Hint personalizado para la tienda
        """
        hints = {
            "EXPLORER": (
                "Hay artículos ocultos en el Gabinete. "
                "Explore cada categoría."
            ),

            "DIRECT": (
                "Use sus Besitos eficientemente. "
                "Compre lo que necesita."
            ),

            "ROMANTIC": (
                "Diana ha puesto artículos especiales en la tienda. "
                "Cosas con... significado."
            ),

            "ANALYTICAL": (
                "Los precios están basados en la rareza y utilidad. "
                "Invierta sabiamente."
            ),

            "PERSISTENT": (
                "Su perseverancia le ha ganado Besitos. "
                "Gástelos en algo que valore."
            ),

            "PATIENT": (
                "No se apresure. "
                "El artículo correcto vale la espera."
            ),

            "default": "Explore el Gabinete. Todo tiene un precio."
        }

        return await self.get_adapted_message(user_id, hints)

    async def get_archetype_emoji(self, user_id: int) -> str:
        """
        Obtiene el emoji correspondiente al arquetipo del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Emoji del arquetipo o "❓"
        """
        try:
            archetype = await self.detection_service.get_archetype(user_id)

            emoji_map = {
                "EXPLORER": "🔍",
                "DIRECT": "⚡",
                "ROMANTIC": "💝",
                "ANALYTICAL": "🧠",
                "PERSISTENT": "🔄",
                "PATIENT": "⏳",
            }

            return emoji_map.get(archetype, "❓")

        except Exception as e:
            logger.error(f"❌ Error obteniendo emoji de arquetipo: {e}", exc_info=True)
            return "❓"

    async def get_archetype_name(self, user_id: int) -> str:
        """
        Obtiene el nombre del arquetipo del usuario en español.

        Args:
            user_id: ID del usuario

        Returns:
            Nombre del arquetipo o "Desconocido"
        """
        try:
            archetype = await self.detection_service.get_archetype(user_id)

            name_map = {
                "EXPLORER": "Explorador",
                "DIRECT": "Directo",
                "ROMANTIC": "Romántico",
                "ANALYTICAL": "Analítico",
                "PERSISTENT": "Persistente",
                "PATIENT": "Paciente",
            }

            return name_map.get(archetype, "Desconocido")

        except Exception as e:
            logger.error(f"❌ Error obteniendo nombre de arquetipo: {e}", exc_info=True)
            return "Desconocido"
