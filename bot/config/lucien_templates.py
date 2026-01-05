"""
Templates de mensajes con la voz de Lucien.

Centraliza todos los mensajes del bot con la personalidad del mayordomo:
formal pero no frío, observador pero no invasivo, elegantemente sarcástico.
"""
from typing import Dict, Any

# ========================================
# WELCOME MESSAGES
# ========================================

WELCOME_MESSAGES = {
    "new_user": {
        "default": (
            "Bienvenido. Soy Lucien, el guardián de este espacio.\n\n"
            "Mi labor es simple: observar, evaluar, y decidir quién merece "
            "acceso a lo que Diana ha preparado.\n\n"
            "Comencemos."
        ),
        "explorer": (
            "Veo curiosidad en su mirada. Bien.\n\n"
            "Este lugar tiene muchos secretos, y no todos están a la vista. "
            "Algunos... están esperando ser descubiertos por alguien con su "
            "disposición a buscar.\n\n"
            "Adelante."
        ),
        "direct": (
            "Seré breve, como seguramente prefiere.\n\n"
            "Este es un espacio donde Diana comparte lo que pocos ven. "
            "Lo que encuentre aquí dependerá de su disposición a involucrarse.\n\n"
            "Eso es todo."
        ),
        "romantic": (
            "Ha llegado en un momento especial.\n\n"
            "Diana ha estado preparando algo íntimo, algo que solo compartirá "
            "con quienes comprendan el peso de la vulnerabilidad.\n\n"
            "Espero que sea uno de ellos."
        ),
    },
    "returning_user": {
        "default": "Ha vuelto. {days_text}\n\nDiana preguntó por usted.",
        "short_absence": (
            "Apenas se fue y ya ha regresado.\n\n"
            "Interesante. Diana notará su... dedicación."
        ),
        "long_absence": (
            "Pensé que no volvería. {days} días sin verle.\n\n"
            "Diana había guardado algo para usted. Espero que valga la pena la espera."
        ),
    },
    "active_user": {
        "default": "De vuelta, como es habitual.\n\nDiana tiene algo nuevo preparado.",
        "vip": (
            "Su acceso VIP sigue activo. {days_remaining} días restantes.\n\n"
            "Diana ha dejado contenido exclusivo para usted en El Diván."
        ),
    },
    "admin": (
        "Acceso administrativo reconocido.\n\n"
        "Use /admin para gestionar el sistema."
    ),
}

# ========================================
# ERROR MESSAGES
# ========================================

ERROR_MESSAGES = {
    "permission_denied": (
        "Este lugar no es para usted. Aún.\n\n"
        "Diana decide quién entra, y yo sigo sus instrucciones."
    ),
    "not_configured": (
        "Aún no he preparado {element}.\n\n"
        "Paciencia. Todo a su tiempo."
    ),
    "invalid_input": (
        "No comprendo lo que intenta decir.\n\n"
        "Sea más claro, o no podré ayudarle."
    ),
    "cooldown_active": (
        "Diana necesita un momento. Vuelva {time_text}.\n\n"
        "No insista. La espera es parte del proceso."
    ),
    "limit_reached": (
        "Ha alcanzado el límite por hoy: {limit_type}.\n\n"
        "Esto no es un buffet. Regrese mañana."
    ),
    "token_invalid": (
        "Este token no es válido. O ya fue usado, o nunca existió.\n\n"
        "No puedo hacer nada con esto."
    ),
    "token_expired": (
        "Este token expiró hace {time_text}.\n\n"
        "Los tokens no son eternos. Debería haberlo usado antes."
    ),
    "vip_not_configured": (
        "El canal VIP aún no está configurado.\n\n"
        "Hable con quien administra esto. Yo solo observo."
    ),
    "free_not_configured": (
        "El canal Free aún no está configurado.\n\n"
        "Hable con quien administra esto."
    ),
    "already_vip": (
        "Ya tiene acceso VIP. {days_remaining} días restantes.\n\n"
        "¿Qué más desea?"
    ),
    "challenge_failed": (
        "Falló el desafío. {attempts_remaining} intentos restantes.\n\n"
        "Diana esperaba más de usted."
    ),
    "no_attempts_left": (
        "No le quedan intentos.\n\n"
        "Este camino está cerrado para usted. Hay otros."
    ),
}

# ========================================
# CONFIRMATION MESSAGES
# ========================================

CONFIRMATION_MESSAGES = {
    "action_success": "Hecho. {details}",
    "purchase_complete": (
        "Adquirido: {item_name} por {cost} Favores.\n\n"
        "Diana estará complacida con tu elección."
    ),
    "level_up": (
        "He observado tu progreso. Ahora eres {level_name}.\n\n"
        "Diana estará complacida."
    ),
    "reward_granted": (
        "Has recibido: {reward_name}.\n\n"
        "Úsalo con sabiduría."
    ),
    "vip_activated": (
        "Tu suscripción VIP está activa. {duration_days} días de acceso.\n\n"
        "Diana te espera en El Diván."
    ),
    "token_generated": (
        "Token generado: <code>{token}</code>\n\n"
        "Válido por {hours} horas. Compártelo con cuidado."
    ),
    "channel_configured": (
        "{channel_type} configurado exitosamente.\n\n"
        "Canal: {channel_name}"
    ),
    "settings_updated": (
        "Configuración actualizada.\n\n"
        "{details}"
    ),
}

# ========================================
# NOTIFICATION MESSAGES
# ========================================

NOTIFICATION_MESSAGES = {
    "streak_milestone": {
        "7_days": (
            "7 días consecutivos. Tu dedicación no pasa desapercibida.\n\n"
            "Bonus: {bonus_besitos} Favores."
        ),
        "14_days": (
            "14 días sin fallar. Impresionante.\n\n"
            "Diana ha notado tu constancia. Bonus: {bonus_besitos} Favores."
        ),
        "30_days": (
            "30 días. Pocas personas llegan aquí.\n\n"
            "Diana tiene algo especial preparado para ti. "
            "Bonus: {bonus_besitos} Favores."
        ),
    },
    "streak_lost": (
        "Tu racha se rompió. {streak_days} días perdidos.\n\n"
        "Una pena. Tendrás que empezar de nuevo."
    ),
    "mission_completed": (
        "Misión completada: {mission_name}.\n\n"
        "Recompensa: {reward}."
    ),
    "reward_unlocked": (
        "Nuevo item desbloqueado: {reward_name}.\n\n"
        "{description}"
    ),
    "vip_expiring_soon": (
        "Tu acceso VIP expira en {days} días.\n\n"
        "Si deseas renovar, este es el momento."
    ),
    "new_content_available": (
        "Diana ha dejado algo nuevo en {channel_name}.\n\n"
        "No querrás perdértelo."
    ),
    "daily_gift_available": (
        "Tu regalo diario está disponible.\n\n"
        "Usa /daily para reclamarlo."
    ),
}

# ========================================
# CONVERSION MESSAGES (por arquetipo)
# ========================================

CONVERSION_MESSAGES = {
    "free_to_vip": {
        "default": (
            "Has llegado al final del camino gratuito.\n\n"
            "Lo que sigue... solo está disponible para quienes Diana considera dignos de "
            "acceso exclusivo. El Diván te espera, si decides dar el siguiente paso.\n\n"
            "La decisión es tuya."
        ),
        "explorer": (
            "Has explorado todo lo que Los Kinkys ofrecen.\n\n"
            "Pero hay secretos más profundos en El Diván. Lugares que solo los más curiosos "
            "descubren. Diana ha preparado contenido que no encontrarás en ningún otro lugar.\n\n"
            "¿Te atreves?"
        ),
        "romantic": (
            "Has sentido la conexión, ¿verdad?\n\n"
            "Lo que has visto hasta ahora es solo la superficie. En El Diván, Diana comparte "
            "su vulnerabilidad real. Momentos íntimos que solo reserva para quienes comprenden "
            "el peso de la confianza.\n\n"
            "Si buscas profundidad, este es el camino."
        ),
        "analytical": (
            "Has analizado el sistema. Ahora comprendes la estructura.\n\n"
            "El Diván opera bajo reglas distintas. Acceso ilimitado, contenido exclusivo, "
            "y una relación directa con Diana que no encontrarás en el canal gratuito.\n\n"
            "Los números hablan por sí mismos."
        ),
    },
    "vip_renewal": {
        "default": (
            "Tu acceso VIP expira pronto. {days} días restantes.\n\n"
            "Si decides renovar ahora, tienes {discount}% de descuento por lealtad.\n\n"
            "Diana aprecia a quienes se quedan."
        ),
    },
}

# ========================================
# RETENTION MESSAGES (por estado de usuario)
# ========================================

RETENTION_MESSAGES = {
    "at_risk": (
        "He notado tu ausencia. {days} días sin verte.\n\n"
        "Diana preguntó por ti. Hay contenido nuevo esperando."
    ),
    "dormant_first": (
        "Han pasado {days} días.\n\n"
        "Hay cosas que quiero mostrarte. Diana ha dejado algo que creo que apreciarías.\n\n"
        "Si decides volver."
    ),
    "dormant_final": (
        "Este será mi último mensaje.\n\n"
        "Si decides volver algún día, aquí estaré. Diana también.\n\n"
        "Hasta entonces."
    ),
    "lost_farewell": (
        "Adiós.\n\n"
        "Si algún día vuelves, la puerta seguirá abierta."
    ),
}

# ========================================
# HELPER FUNCTIONS
# ========================================


def get_days_text(days: int) -> str:
    """Formatea días en texto apropiado."""
    if days == 0:
        return "Apenas se fue"
    elif days == 1:
        return "1 día sin verle"
    else:
        return f"{days} días sin verle"


def get_time_text(seconds: int) -> str:
    """Formatea segundos en texto legible."""
    if seconds < 60:
        return f"{seconds} segundos"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minuto{'s' if minutes != 1 else ''}"
    else:
        hours = seconds // 3600
        return f"{hours} hora{'s' if hours != 1 else ''}"


def get_remaining_days_text(days: int) -> str:
    """Formatea días restantes."""
    if days == 0:
        return "Expira hoy"
    elif days == 1:
        return "1 día restante"
    else:
        return f"{days} días restantes"


# ========================================
# PROFILE MESSAGES (Fase 1)
# ========================================

PROFILE_MESSAGES = {
    "header": "Su expediente en el Diván. Todo queda registrado.",
    "level_low": (
        "Aún está en observación. No se lo tome personal... "
        "todos comienzan así."
    ),
    "level_mid": (
        "Ha demostrado cierta... persistencia. Diana comienza a notar "
        "su presencia."
    ),
    "level_high": (
        "Debo admitir que ha superado mis expectativas iniciales. "
        "Diana habla de usted ocasionalmente."
    ),
    "level_max": (
        "Guardián de Secretos. El círculo más íntimo. "
        "Ya no necesita mi evaluación... pero la tendrá de todos modos."
    ),
}


# ========================================
# CABINET MESSAGES (Fase 1 - Gabinete)
# ========================================

CABINET_MESSAGES = {
    "welcome": (
        "Bienvenido a mi Gabinete.\n\n"
        "Aquí guardo ciertos artículos que Diana ha autorizado para intercambio. "
        "Los Besitos que ha acumulado pueden convertirse en algo más tangible.\n\n"
        "Examine con cuidado. No todo lo que brilla merece su inversión."
    ),
    "confirm_purchase": (
        "¿Desea adquirir <b>{item_name}</b> por {price} Besitos?\n\n"
        "Una vez hecho, no hay devoluciones. Diana no admite arrepentimientos."
    ),
    "purchase_success": (
        "Hecho. <b>{item_name}</b> ahora le pertenece.\n\n"
        "Diana ha sido notificada de su adquisición. "
        "Úselo sabiamente... o no. La elección es suya."
    ),
    "insufficient_funds": (
        "Sus Besitos son insuficientes para esto.\n\n"
        "Necesita {required} y tiene {current}. "
        "Diana no otorga crédito. Vuelva cuando tenga los medios."
    ),
}


# ========================================
# ENCARGOS MESSAGES (Fase 1 - Encargos)
# ========================================

ENCARGOS_MESSAGES = {
    "welcome": (
        "Los Encargos del Diván.\n\n"
        "Tareas que Diana considera dignas de reconocimiento. "
        "Cumpla con ellas y será recompensado. Ignórelas... y lo notaré."
    ),
    "progress": (
        "Progreso en '<b>{mission_name}</b>': {current}/{target}\n\n"
        "{lucien_comment}"
    ),
    "progress_comments": {
        "0_25": "Apenas ha comenzado.",
        "26_50": "Va por buen camino.",
        "51_75": "Más de la mitad. No se detenga ahora.",
        "76_99": "Casi lo logra. Un último esfuerzo.",
    },
    "completed": (
        "Encargo cumplido: <b>{mission_name}</b>\n\n"
        "Ha ganado {reward} Besitos. Diana ha sido notificada de su diligencia."
    ),
    "empty": (
        "No hay encargos pendientes en este momento.\n\n"
        "Diana preparará nuevas tareas pronto. "
        "Mientras tanto, explore el Diván."
    ),
}


# ========================================
# BESITOS MESSAGES (Fase 1 - Balance)
# ========================================

BESITOS_MESSAGES = {
    "balance_low": (  # 0-10
        "Sus Besitos acumulados: <b>{total}</b>\n\n"
        "Apenas está comenzando. Diana otorga reconocimiento "
        "a quienes demuestran constancia."
    ),
    "balance_growing": (  # 11-50
        "Sus Besitos acumulados: <b>{total}</b>\n\n"
        "Va construyendo su mérito. Continúe así y Diana "
        "comenzará a prestar atención."
    ),
    "balance_good": (  # 51-100
        "Sus Besitos acumulados: <b>{total}</b>\n\n"
        "Una cantidad respetable. Tiene opciones en el Gabinete. "
        "¿Los gastará o seguirá acumulando?"
    ),
    "balance_high": (  # 100+
        "Sus Besitos acumulados: <b>{total}</b>\n\n"
        "Impresionante reserva. Diana aprecia a quienes saben "
        "cuándo gastar y cuándo esperar. ¿Cuál es su estrategia?"
    ),
    "balance_hoarder": (  # 200+ sin gastar
        "Sus Besitos acumulados: <b>{total}</b>\n\n"
        "Acumula sin gastar. Prudente... o quizás indeciso. "
        "El Gabinete tiene objetos dignos de su inversión."
    ),
    "earned": (
        "+{amount} Besitos.\n\n"
        "<i>Diana lo nota.</i>"
    ),
    "earned_milestone": (
        "Ha alcanzado <b>{total}</b> Besitos.\n\n"
        "Un hito. Diana ha sido informada de su progreso."
    ),
    "insufficient": (
        "Sus Besitos son insuficientes para esto.\n\n"
        "Necesita {required} y tiene {current}. "
        "Diana no otorga crédito. Vuelva cuando tenga los medios."
    ),
}
