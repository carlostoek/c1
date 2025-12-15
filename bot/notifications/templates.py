"""
Notification Templates - Templates HTML para notificaciones.

Templates predefinidos con placeholders que se reemplazan dinámicamente.
"""
from typing import Dict, Any


class NotificationTemplates:
    """
    Repositorio de templates de notificaciones.

    Cada template es un string HTML con placeholders {variable}.
    """

    # ===== WELCOME MESSAGE =====

    WELCOME_DEFAULT = """👋 <b>¡Bienvenido/a {first_name}!</b>

{role_emoji} Tu rol actual: <b>{role_name}</b>

Este bot te da acceso a canales exclusivos y recompensas por participar.

<b>💋 Sistema de Besitos:</b>
Gana Besitos (puntos) por:
• Ingresar al canal Free
• Reaccionar a mensajes
• Login diario
• Referir amigos

<b>Usa /help para más información.</b>"""

    # ===== REWARD MESSAGES =====

    REWARD_BATCH = """🎉 <b>¡Recompensas Ganadas!</b>

<b>{action}</b>

{rewards_list}"""

    BESITOS_EARNED = """💋 <b>¡Ganaste Besitos!</b>

<b>+{amount} Besitos</b>

Razón: {reason}

Total acumulado: {total_besitos} 💋"""

    BADGE_UNLOCKED = """🏆 <b>¡Nueva Insignia Desbloqueada!</b>

{badge_icon} <b>{badge_name}</b>

{badge_description}

<i>Insignias desbloqueadas: {total_badges}</i>"""

    RANK_UP = """⭐ <b>¡Subiste de Rango!</b>

{old_rank} → {new_rank}

Total de Besitos: {total_besitos} 💋

¡Sigue participando para seguir subiendo!"""

    # ===== VIP MESSAGES =====

    VIP_ACTIVATED = """🎉 <b>¡Suscripción VIP Activada!</b>

<b>Plan:</b> {plan_name}
<b>Precio:</b> {price}
<b>Duración:</b> {duration_days} días
<b>Expira:</b> {expiry_date}

⭐ Tu rol ha sido actualizado a: <b>VIP</b>

Haz click en el botón para unirte al canal VIP."""

    VIP_EXPIRING_SOON = """⚠️ <b>Tu VIP Expira Pronto</b>

Tu suscripción VIP expira en <b>{days_remaining} días</b>.

Fecha de expiración: {expiry_date}

Renueva ahora para mantener tu acceso al canal VIP."""

    VIP_EXPIRED = """❌ <b>Tu VIP Ha Expirado</b>

Tu suscripción VIP expiró el {expiry_date}.

Has sido devuelto al rol <b>Free</b>.

Contacta al administrador para renovar."""

    # ===== DAILY REWARDS =====

    DAILY_LOGIN = """🎁 <b>¡Regalo Diario Reclamado!</b>

<b>+{besitos} Besitos 💋</b>

Días consecutivos: {streak_days} 🔥

{streak_bonus}

¡Vuelve mañana para mantener tu racha!"""

    STREAK_MILESTONE = """🔥 <b>¡Nuevo Récord de Racha!</b>

<b>{streak_days} días consecutivos</b>

Recompensa especial:
<b>+{bonus_besitos} Besitos 💋</b>

¡Sigue así, campeón/a!"""

    # ===== REFERRALS =====

    REFERRAL_SUCCESS = """👥 <b>¡Referido Exitoso!</b>

Tu amigo/a se unió usando tu link.

Recompensa:
<b>+{besitos} Besitos 💋</b>

Total de referidos: {total_referrals}"""

    # ===== INFO/ERROR/WARNING =====

    INFO = """ℹ️ <b>Información</b>

{message}"""

    WARNING = """⚠️ <b>Advertencia</b>

{message}"""

    ERROR = """❌ <b>Error</b>

{message}"""

    @classmethod
    def render(cls, template_name: str, context: Dict[str, Any]) -> str:
        """
        Renderiza un template con el contexto dado.

        Args:
            template_name: Nombre del template (ej: "WELCOME_DEFAULT")
            context: Dict con variables a reemplazar

        Returns:
            String HTML renderizado

        Examples:
            >>> template = NotificationTemplates.render(
            ...     "BESITOS_EARNED",
            ...     {"amount": 50, "reason": "Primera reacción", "total_besitos": 150}
            ... )
        """
        # Obtener template
        template = getattr(cls, template_name, None)

        if template is None:
            raise ValueError(f"Template no encontrado: {template_name}")

        # Reemplazar variables
        try:
            return template.format(**context)
        except KeyError as e:
            raise ValueError(f"Variable faltante en template: {e}")
