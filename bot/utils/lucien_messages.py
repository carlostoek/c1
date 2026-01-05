"""Biblioteca centralizada de mensajes de Lucien.

Esta clase contiene TODOS los mensajes que el bot enviará, escritos
con la voz y personalidad de Lucien, permitiendo consistencia de tono
en todo el bot.

Características de Lucien:
- Siempre usa \"usted\" (formal)
- Elegante, sofisticado, ligeramente irónico
- Evaluador constante, protector de Diana
- Sarcasmo sutil, nunca vulgar

Uso:
    from bot.utils.lucien_messages import LucienMessages as LM

    # Mensaje simple
    await message.answer(LM.START_NEW_USER_1, parse_mode="HTML")

    # Mensaje con placeholders
    await message.answer(
        LM.BESITOS_EARNED.format(amount=5),
        parse_mode="HTML"
    )"""

from typing import Optional


class LucienMessages:
    """Mensajes de Lucien centralizados para toda la aplicación.

    Todos los mensajes usan formato HTML para Telegram.
    Usan placeholders con formato {variable} para dinamismo.
    """

    # ============================================================ 
    # 1. ONBOARDING (Comando /start)
    # ============================================================ 

    START_NEW_USER_1 = (
        "<i>Buenas noches. O días. El tiempo es relativo cuando se trata de Diana.</i>\n\n"
        "Ha decidido cruzar el umbral. Interesante.\n\n"
        "Soy Lucien. Administro el acceso al universo de la Señorita. "
        "Mi trabajo es determinar si usted merece su atención."
    )

    START_NEW_USER_2 = (
        "Este universo funciona bajo reglas simples:\n\n"
        "• <b>Interactúe</b> y acumulará <b>Besitos</b>, el favor de Diana.\n"
        "• <b>Use sus Besitos</b> en mi Gabinete para adquirir objetos únicos.\n"
        "• <b>Complete Encargos</b> para demostrar su valía.\n\n"
        "<i>No se apresure. La calidad requiere calma.</i>"
    )

    START_RETURNING_USER = (
        "<i>Ha regresado, {user_name}.</i>\n\n"
        "Hace {days_away} días que no se dejaba ver. "
        "Esperemos que su ausencia valiera la pena."
    )
    
    START_INACTIVE_USER = (
        "<i>Una ausencia notable, {user_name}.</i>\n\n"
        "Casi le dábamos por perdido. Mucho ha ocurrido.\n\n"
        "Quizás desee ponerse al día."
    )
    
    START_LONG_INACTIVE_USER = (
        "<i>Bienvenido de vuelta, {user_name}.</i>\n\n"
        "El Diván casi se había olvidado de su rostro. Ha pasado mucho tiempo.\n\n"
        "Será como empezar de nuevo, pero con los recuerdos de lo que fue."
    )

    START_VIP_USER = (
        "Ah, <i>{user_name}</i>. Es un placer verle de nuevo.\n\n"
        "Su acceso privilegiado al círculo de Diana sigue vigente por <b>{days_remaining}</b> días más.\n\n"
        "Su nivel de <i>{level_name}</i> le precede. No nos decepcione."
    )

    START_ADMIN = (
        "Señor <i>{user_name}</i>, sus herramientas de administrador le esperan.\n\n"
        "El Diván funciona según sus directrices. Proceda."
    )
    
    CONFIRM_REGISTRATION = (
       "Su presencia ha sido registrada.\n\n"
       "Bienvenido al Diván. Todo lo que haga será... observado."
    )

    # ============================================================ 
    # 2. BESITOS (economía)
    # ============================================================ 
    
    BESITOS_BALANCE_LOW = (  # 0-10
       "Sus Besitos acumulados: <b>{total}</b>\n\n"
       "Apenas está comenzando. Diana otorga reconocimiento "
       "a quienes demuestran constancia."
    )
   
    BESITOS_BALANCE_GROWING = (  # 11-50
       "Sus Besitos acumulados: <b>{total}</b>\n\n"
       "Va construyendo su mérito. Continúe así y Diana "
       "comenzará a prestar atención."
    )
   
    BESITOS_BALANCE_GOOD = (  # 51-100
       "Sus Besitos acumulados: <b>{total}</b>\n\n"
       "Una cantidad respetable. Tiene opciones en el Gabinete. "
       "¿Los gastará o seguirá acumulando?"
    )
   
    BESITOS_BALANCE_HIGH = (  # 100+
       "Sus Besitos acumulados: <b>{total}</b>\n\n"
       "Impresionante reserva. Diana aprecia a quienes saben "
       "cuándo gastar y cuándo esperar. ¿Cuál es su estrategia?"
    )

    BESITOS_EARNED = (
        "+{amount} Besitos.\n\n"
        "<i>Diana lo nota.</i>"
    )

    BESITOS_EARNED_MILESTONE = (
        "Ha alcanzado <b>{total}</b> Besitos.\n\n"
        "Un hito. Diana ha sido informada de su progreso."
    )

    BESITOS_INSUFFICIENT = (
        "Sus Besitos son insuficientes para esto.\n\n"
        "Necesita {required} y tiene {current}. "
        "Diana no otorga crédito. Vuelva cuando tenga los medios."
    )

    # ============================================================ 
    # 3. PERFIL Y NIVELES
    # ============================================================ 

    PROFILE_HEADER = "Su expediente en el Diván. Todo queda registrado."
   
    PROFILE_LEVEL_LOW = (
       "Aún está en observación. No se lo tome personal... "
       "todos comienzan así."
    )
   
    PROFILE_LEVEL_MID = (
       "Ha demostrado cierta... persistencia. Diana comienza a notar "
       "su presencia."
    )
   
    PROFILE_LEVEL_HIGH = (
       "Debo admitir que ha superado mis expectativas iniciales. "
       "Diana habla de usted ocasionalmente."
    )
   
    PROFILE_LEVEL_MAX = (
       "Guardián de Secretos. El círculo más íntimo. "
       "Ya no necesita mi evaluación... pero la tendrá de todos modos."
    )

    CONFIRM_LEVEL_UP = (
       "Ha ascendido a <b>{level_name}</b>.\n\n"
       "{level_comment}"
    )

    # ============================================================ 
    # 4. GABINETE (Tienda)
    # ============================================================ 

    CABINET_WELCOME = (
       "Bienvenido a mi Gabinete.\n\n"
       "Aquí guardo ciertos artículos que Diana ha autorizado para intercambio. "
       "Los Besitos que ha acumulado pueden convertirse en algo más tangible.\n\n"
       "Examine con cuidado. No todo lo que brilla merece su inversión."
    )

    CABINET_CONFIRM_PURCHASE = (
       "¿Desea adquirir <b>{item_name}</b> por {price} Besitos?\n\n"
       "Una vez hecho, no hay devoluciones. Diana no admite arrepentimientos."
    )
   
    CABINET_PURCHASE_SUCCESS = (
       "Hecho. <b>{item_name}</b> ahora le pertenece.\n\n"
       "Diana ha sido notificada de su adquisición. "
       "Úselo sabiamente... o no. La elección es suya."
    )
    
    CABINET_INSUFFICIENT_FUNDS = (
       "Sus Besitos son insuficientes para esto.\n\n"
       "Necesita {required} y tiene {current}. "
       "Diana no otorga crédito. Vuelva cuando tenga los medios."
    )

    # ============================================================ 
    # 5. ENCARGOS (Misiones)
    # ============================================================ 

    ENCARGOS_WELCOME = (
       "Los Encargos del Diván.\n\n"
       "Tareas que Diana considera dignas de reconocimiento. "
       "Cumpla con ellas y será recompensado. Ignórelas... y lo notaré."
    )

    MISSION_PROGRESS = (
       "Progreso en '<b>{mission_name}</b>': {current}/{target}\n\n"
       "{lucien_comment}"
    )

    ENCARGOS_COMPLETED = (
       "Encargo cumplido: <b>{mission_name}</b>\n\n"
       "Ha ganado {reward} Besitos. Diana ha sido notificada de su diligencia."
    )
    
    ENCARGOS_EMPTY = (
       "No hay encargos pendientes en este momento.\n\n"
       "Diana preparará nuevas tareas pronto. "
       "Mientras tanto, explore el Diván."
    )

    # ============================================================ 
    # 6. ERRORES Y CONFIRMACIONES
    # ============================================================ 
    
    ERROR_GENERIC = "Algo ha fallado en el sistema. No es culpa suya... probablemente. Intente nuevamente en unos momentos."
    ERROR_NOT_FOUND = "Lo que busca no existe. O ya no existe. El Diván tiene sus misterios."
    ERROR_PERMISSION = "No tiene autorización para esto. Hay puertas que requieren llaves que aún no posee."
    ERROR_RATE_LIMITED = "Demasiado rápido. La paciencia es una virtud que Diana valora. Espere un momento."
    ERROR_INVALID_INPUT = "Eso no es lo que esperaba. Revise su entrada e intente de nuevo."
    ERROR_TIMEOUT = "El tiempo se ha agotado. Si desea continuar, deberá comenzar de nuevo."
    ERROR_MAINTENANCE = "El Diván está en mantenimiento. Diana está preparando algo. Vuelva pronto."

    CONFIRM_ACTION = "Hecho."
    CONFIRM_SAVED = "Registrado en los archivos del Diván."
    CONFIRM_VIP_ACTIVATION = (
        "🎉✨ <b>¡BIENVENIDO AL CÍRCULO ÍNTIMO!</b> ✨🎉\n"
        "<b>Acceso Activado Exitosamente</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>Plan:</b> {plan_name} ({plan_duration_days} días)\n"
        "<b>Precio:</b> {price_str}\n"
        "<b>Válido por:</b> {days_remaining} días más\n"
        "{user_role_emoji} <b>Su nuevo rol:</b> <code>{user_role_display_name}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>🔐 ACCESO AL CANAL</b>\n"
        "Haga click en el botón inferior para unirse al canal exclusivo. El enlace es personal y expira en 5 horas.\n"
    )
    
    # ============================================================ 
    # HELPERS
    # ============================================================ 

    @staticmethod
    def format_progress_bar(current: int, total: int, width: int = 10) -> str:
        """Genera una barra de progreso visual (corta)."""
        if total == 0: percentage = 0
        else: percentage = min(int((current / total) * 100), 100)
        filled = int(width * percentage / 100)
        return "▓" * filled + "░" * (width - filled)

    @staticmethod
    def format_besitos(amount: int) -> str:
        """Formatea cantidad de Besitos."""
        return f"{amount} Besito{'s' if amount != 1 else ''}"

# Alias corto para facilitar importación
Lucien = LucienMessages
