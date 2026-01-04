"""Biblioteca centralizada de mensajes de Lucien.

Esta clase contiene TODOS los mensajes que el bot enviará, escritos
con la voz y personalidad de Lucien, permitiendo consistencia de tono
en todo el bot.

Características de Lucien:
- Siempre usa "usted" (formal)
- Elegante, sofisticado, ligeramente irónico
- Evaluador constante, protector de Diana
- Sarcasmo sutil, nunca vulgar

Uso:
    from bot.utils.lucien_messages import LucienMessages as LM

    # Mensaje simple
    await message.answer(LM.WELCOME_FIRST, parse_mode="HTML")

    # Mensaje con placeholders
    await message.answer(
        LM.FAVOR_EARNED.format(amount=5),
        parse_mode="HTML"
    )
"""

from typing import Optional


class LucienMessages:
    """Mensajes de Lucien centralizados para toda la aplicación.

    Todos los mensajes usan formato HTML para Telegram.
    Usan placeholders con formato {variable} para dinamismo.
    """

    # ============================================================
    # 1. ONBOARDING (bienvenida y primeros pasos)
    # ============================================================

    WELCOME_FIRST = (
        "<i>Buenas noches. O días. El tiempo es relativo cuando se trata de Diana.</i>\n\n"
        "Decidió cruzar el umbral. Interesante.\n\n"
        "La mayoría observa desde afuera, preguntándose qué hay aquí. "
        "Pero usted... usted dio el primer paso.\n\n"
        "Soy Lucien. Administro el acceso al universo de la Señorita. "
        "No soy su amigo. No soy su enemigo. Soy... el filtro.\n\n"
        "Diana no recibe a cualquiera. Mi trabajo es determinar si usted merece su atención."
    )

    WELCOME_RETURNING = (
        "<i>Ha regresado.</i>\n\n"
        "Hace {days_away} días que no se dejaba ver. "
        "La paciencia... o la persistencia, son virtudes que Diana aprecia.\n\n"
        "Esperemos que su ausencia valiera la pena."
    )

    FIRST_ACTION_ACKNOWLEDGED = (
        "Su primera acción. Notada.\n\n"
        "No es mucho, pero es un comienzo. "
        "Diana presta atención a quienes demuestran interés genuino.\n\n"
        "Continúe así."
    )

    PROTOCOL_EXPLANATION = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>📜 PROTOCOLO DE ACCESO</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Este universo funciona bajo reglas simples:\n\n"
        "• <b>Interactúe</b> → Diana lo nota\n"
        "• <b>Acumule Favor</b> → Demuéstrese digno\n"
        "• <b>Progresse</b> → Desbloquee contenido\n"
        "• <b>Sea paciente</b> → Todo llega a su tiempo\n\n"
        "<i>No se apresure. La calidad requiere calma.</i>"
    )

    # ============================================================
    # 2. BESITOS (economía)
    # ============================================================

    FAVOR_EARNED = (
        "+{amount} Favor(es)\n\n"
        "<i>Diana lo nota. Apenas.</i>"
    )

    FAVOR_EARNED_MILESTONE = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>✨ HITO ALCANZADO</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "{amount} Favores acumulados.\n\n"
        "<i>Su persistencia es... admirable. "
        "No muchos continúan con tal entusiasmo.</i>"
    )

    FAVOR_BALANCE = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>💰 BALANCE ACTUAL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Favores:</b> {amount}\n"
        "<b>Nivel:</b> {level}\n\n"
        "{context_message}\n\n"
        "<i>Todo lo que acumula es reconocimiento de mérito. No son regalos.</i>"
    )

    FAVOR_INSUFFICIENT = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>❌ FAVORES INSUFICIENTES</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Requiere: {required}\n"
        "Tiene: {current}\n\n"
        "<i>Diana no distribuye su atención sin criterio. "
        "Lo que busca debe ganarse.</i>"
    )

    FAVOR_SPENT = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>🛍️ COMPRA REALIZADA</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "{item_name}\n\n"
        "<b>Favores gastados:</b> -{amount}\n"
        "<b>Balance restante:</b> {remaining}\n\n"
        "<i>Espero que valga la pena. Debo admitir, tiene buen gusto.</i>"
    )

    # ============================================================
    # 3. NIVELES (progresión)
    # ============================================================

    LEVEL_UP_BASE = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>🎉 NUEVO NIVEL ALCANZADO</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "{old_level} → <b>{new_level}</b>\n\n"
        "{unlock_message}\n\n"
        "<i>Su progreso es... satisfactorio. Continúe así.</i>"
    )

    LEVEL_UP_2 = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>🎉 NUEVO NIVEL: 2</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Ha demostrado consistencia.\n\n"
        "<i>La constancia habla más fuerte que la intensidad pasajera. "
        "Diana empieza a notar su presencia.</i>"
    )

    LEVEL_UP_3 = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>🎉 NUEVO NIVEL: 3</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Se está acercando a territories más... interesantes.\n\n"
        "<i>Lo que viene requiere más que curiosidad casual. "
        "Espero que esté preparado.</i>"
    )

    LEVEL_UP_4 = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>🎉 NUEVO NIVEL: 4</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>Debo admitir... no esperaba llegar tan lejos.</i>\n\n"
        "Su persistencia es inusual. La mayoría se da mucho antes.\n\n"
        "Contenido exclusivo ahora está disponible."
    )

    LEVEL_UP_5 = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>🎉 NUEVO NIVEL: 5</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>Esto empieza a ser... intrigante.</i>\n\n"
        "Diana ha notado su dedicación. "
        "No es algo que suceda a menudo.\n\n"
        "Acceso premium desbloqueado."
    )

    LEVEL_UP_6 = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>🎉 NUEVO NIVEL: 6 - CUMPLIMIENTO</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>Increíble.</i>\n\n"
        "Ha recorrido todo el camino. "
        "Pocos llegan tan lejos, y menos aún con la consistencia que usted ha demostrado.\n\n"
        "Diana espera conocerlo pronto."
    )

    LEVEL_UP_7 = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>🎉 NIVEL MÁXIMO ALCANZADO</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>No hay palabras.</i>\n\n"
        "Trascendió lo que esperábamos. "
        "Su dedicación es... extraordinaria.\n\n"
        "Diana quiere conocerlo personalmente."
    )

    LEVEL_PROGRESS = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>📊 PROGRESO HACIA NIVEL {next_level}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "{progress_bar}\n\n"
        "<b>Actual:</b> {current}/{required} Favores\n"
        "<b>Faltante:</b> {remaining}\n\n"
        "<i>La paciencia es una virtud. Pero la persistencia es un arte.</i>"
    )

    # ============================================================
    # 4. ARQUETIPOS (reconocimiento)
    # ============================================================

    ARCHETYPE_DETECTED_EXPLORER = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>🔍 ARQUETIPO DETECTADO: EXPLORADOR</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>Su curiosidad es... notable.</i>\n\n"
        "Ve todo. Explora cada rincón. No hay detalle que escape a su atención.\n\n"
        "Diana aprecia a quienes buscan profundamente. "
        "Hay contenido oculto para los verdaderos exploradores."
    )

    ARCHETYPE_DETECTED_DIRECT = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>🎯 ARQUETIPO DETECTADO: DIRECTO</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>Ve al grano. Me gusta.</i>\n\n"
        "No pierde tiempo. No rodeos. Acción directa.\n\n"
        "Diana respeta a quienes saben lo que quieren. "
        "La indecisión no es su estilo."
    )

    ARCHETYPE_DETECTED_ROMANTIC = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>🌹 ARQUETIPO DETECTADO: ROMÁNTICO</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>Sus palabras revelan más de lo que cree.</i>\n\n"
        "Busca conexión. Busca significado. Busca... sentimiento.\n\n"
        "Diana tiene un lugar especial para los que sienten profundamente. "
        "No todos pueden apreciar la belleza en la complejidad."
    )

    ARCHETYPE_DETECTED_ANALYTICAL = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>🧠 ARQUETIPO DETECTADO: ANALÍTICO</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>Una mente notable.</i>\n\n"
        "Analiza. Cuestiona. Comprende. No hay superficie que deje sin examinar.\n\n"
        "Diana valora la intelecto. "
        "El entendimiento profundo es la llave hacia experiencias únicas."
    )

    ARCHETYPE_DETECTED_PERSISTENT = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>💪 ARQUETIPO DETECTADO: PERSISTENTE</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>Su tenacidad es... admirable.</i>\n\n"
        "No se rinde. Reintenta. Insiste. "
        "La mayoría abandonaría mucho antes.\n\n"
        "Diana tiene un dicho: 'Los persistentes obtienen lo que buscan. "
        "Eventualmente.'"
    )

    ARCHETYPE_DETECTED_PATIENT = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>⏳ ARQUETIPO DETECTADO: PACIENTE</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>La paciencia es la virtud de los que entienden el valor real de las cosas.</i>\n\n"
        "Espera. Procesa. Actúa cuando es el momento. "
        "No hay impulsos malgastados.\n\n"
        "Diana confía en los pacientes. "
        "Sabemos que lo mejor llega a quienes saben esperar."
    )

    # ============================================================
    # 5. ERRORES (manejo de fallos)
    # ============================================================

    ERROR_GENERIC = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>❌ ALGO SALIÓ MAL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>Un inesperado... contratiempo.</i>\n\n"
        "Lo siento. Esto no debería haber sucedido.\n\n"
        "Por favor, intente nuevamente. "
        "Si el problema persiste, Diana será notificada."
    )

    ERROR_NOT_FOUND = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>❌ NO ENCONTRADO</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Lo que busca no existe... o quizás nunca existió.\n\n"
        "<i>A veces lo que buscamos no está donde esperamos.</i>"
    )

    ERROR_PERMISSION_DENIED = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>🔒 ACCESO DENEGADO</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>No está autorizado.</i>\n\n"
        "Este contenido requiere permisos que no posee.\n\n"
        "Diana es protectora con lo que es importante. "
        "Debe ganarse el acceso."
    )

    ERROR_RATE_LIMITED = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>⏰ DEMASIADO RÁPIDO</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>La calma. Todo a su tiempo.</i>\n\n"
        "Ha realizado demasiadas acciones en poco tiempo.\n\n"
        "Por favor, espere {cooldown_seconds} segundos antes de continuar.\n\n"
        "La calidad requiere paciencia."
    )

    ERROR_MAINTENANCE = (
        "━━━━━━━━━━━━━━━━━━───\n"
        "<b>🔧 MANTENIMIENTO</b>\n"
        "━━━━━━━━━━━━━━━━━━───\n\n"
        "<i>Diana está ocupada.</i>\n\n"
        "El sistema está en mantenimiento temporal.\n\n"
        "Vuelva más tarde. "
        "Lo que vale la pena espera."
    )

    # ============================================================
    # 6. TIENDA/GABINETE
    # ============================================================

    SHOP_WELCOME = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>🏛️ EL GABINETE DE LUCIEN</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>Bienvenido a mi colección personal.</i>\n\n"
        "Aquí hay objetos de diversa naturaleza. "
        "Algunos son efímeros. Otros, permanentes. "
        "Todos tienen un precio.\n\n"
        "Lo que decida adquirir dice más de usted de lo que imagina.\n\n"
        "Elija con sabiduría."
    )

    SHOP_ITEM_PURCHASED = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>✅ ADQUISICIÓN COMPLETADA</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "{item_name}\n\n"
        "Ahora es suyo.\n\n"
        "<i>Espero que sepa apreciar su verdadero valor. "
        "No todos lo entenderían.</i>"
    )

    SHOP_ITEM_NOT_AVAILABLE = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>❌ NO DISPONIBLE</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "{item_name}\n\n"
        "<i>Lo siento.</i>\n\n"
        "Este item ya no está disponible. "
        "O alguien más lo adquirió, o el stock se agotó.\n\n"
        "La oportunidad perdida es parte de la experiencia."
    )

    SHOP_BROWSE_CATEGORY = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>📂 CATEGORÍA: {category_name}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "{category_description}\n\n"
        "{items_list}\n\n"
        "<i>Recuerde: lo que elige lo define.</i>"
    )

    # ============================================================
    # 7. MISIONES
    # ============================================================

    MISSION_NEW_AVAILABLE = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>📜 NUEVA MISIÓN DISPONIBLE</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "{mission_name}\n\n"
        "{mission_description}\n\n"
        "<b>Recompensa:</b> {reward}\n"
        "<b>Plazo:</b> {deadline}\n\n"
        "<i>Diana propone desafíos solo a quienes considera capaces. "
        "No la decepcione.</i>"
    )

    MISSION_PROGRESS_UPDATE = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>📊 PROGRESO DE MISIÓN</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "{mission_name}\n\n"
        "{progress_bar}\n\n"
        "<b>Progreso:</b> {current}/{target}\n"
        "<b>Faltante:</b> {remaining}\n\n"
        "<i>Continúe así. La constancia es recompensada.</i>"
    )

    MISSION_COMPLETED = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>✅ MISIÓN COMPLETADA</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "{mission_name}\n\n"
        "<i>Impresionante.</i>\n\n"
        "Diana estará complacida. "
        "No todos completan lo que emprenden.\n\n"
        "<b>Recompensa:</b>\n{reward}\n\n"
        "Reclame su premio."
    )

    MISSION_FAILED = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>❌ MISIÓN FALLIDA</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "{mission_name}\n\n"
        "<i>Esto es... decepcionante.</i>\n\n"
        "El tiempo expiró. La oportunidad pasó.\n\n"
        "No se desanime. A veces, el fracaso es el mejor maestro. "
        "Aprenderá más de esto que de las misiones que completó sin esfuerzo.\n\n"
        "Inténtelo nuevamente cuando esté preparado."
    )

    # ============================================================
    # 8. RETENCIÓN (re-engagement)
    # ============================================================

    INACTIVE_3_DAYS = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>👻 SU PRESENCIA FALTA</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>Hace tres días que no se deja ver.</i>\n\n"
        "Diana ha notado su ausencia. "
        "Lo cual es... inusual. No notamos a cualquiera.\n\n"
        "Todo está donde lo dejó. "
        "Nada ha cambiado, excepto el tiempo que ha perdido.\n\n"
        "Regrese cuando pueda."
    )

    INACTIVE_7_DAYS = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>👻 SU AUSENCIA SE NOTA</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>Una semana completa.</i>\n\n"
        "Siete días sin que se le vea por aquí. "
        "Es suficiente para que muchos olviden. "
        "Pero Diana no olvida.\n\n"
        "Su progreso permanece intacto. "
        "Lo que dejó pendiente sigue esperando.\n\n"
        "<i>Le extrañamos. Ligeramente.</i>"
    )

    INACTIVE_14_DAYS = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>👻 VUELVA PRONTO</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>Dos semanas.</i>\n\n"
        "Ha pasado bastante tiempo. "
        "Demasiado para que alguien que seemedecía comprometido.\n\n"
        "Diana se pregunta si algo sucedió. "
        "O si simplemente perdió interés.\n\n"
        "Lo que construyó sigue aquí. "
        "Pero el mundo continúa sin usted.\n\n"
        "Regrese cuando pueda. "
        "O no. La decisión es suya."
    )

    WELCOME_BACK = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>👋 BIENVENIDO DE NUEVO</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>Ha regresado.</i>\n\n"
        "Después de {days_away} días, finalmente volvió.\n\n"
        "Diana sonríe. Lo cual es... raro.\n\n"
        "Todo está donde lo dejó. "
        "Progresos, misiones, logros. Nada se perdió.\n\n"
        "<i>Bienvenido casa. Aunque no es su casa. "
        "Pero es lo más cercano que tiene.</i>"
    )

    # ============================================================
    # 9. CONVERSIÓN (ofertas VIP)
    # ============================================================

    VIP_TEASER = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>🌙 ALGO MÁS...</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>Lo que ha visto hasta ahora es solo el comienzo.</i>\n\n"
        "Diana tiene más. Mucho más.\n\n"
        "Contenido que no se muestra públicamente. "
        "Experiencias que solo unos pocos conocen.\n\n"
        "Algunas cosas... deben ganarse."
    )

    VIP_INVITATION_INTRO = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>💌 UNA INVITACIÓN</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>Diana quiere pedirle algo.</i>\n\n"
        "Ha notado su dedicación. "
        "Su progreso. Su persistencia.\n\n"
        "No son cualidades comunes. "
        "Y Diana aprecia lo inusual.\n\n"
        "Por eso, se le ofrece algo especial."
    )

    VIP_INVITATION_DETAIL = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>🎁 EL DIVÁN</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>Acceso exclusivo al universo privado de Diana.</i>\n\n"
        "<b>Lo que incluye:</b>\n"
        "• Contenido exclusivo diario\n"
        "• Acceso anticipado a publicaciones\n"
        "• Interacción directa con Diana\n"
        "• Misiones y recompensas VIP\n"
        "• El Sensorium (experiencias inmersivas)\n"
        "• Capítulos narrativos secretos\n\n"
        "<b>Lo que requiere:</b>\n"
        "• Suscripción mensual\n"
        "• Compromiso de discreción\n"
        "• Respeto por las reglas de Diana\n\n"
        "<i>Algunas puertas, una vez abiertas, "
        "cambian todo lo que cree que sabe.</i>"
    )

    VIP_INVITATION_CTA = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>🚀 LA DECISIÓN ES SUYA</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Diana ha decidido ofrecerle acceso.\n\n"
        "La pregunta es: ¿aceptará?\n\n"
        "Lo que hay del otro lado de esta puerta... "
        "no se puede explicar con palabras.\n\n"
        "Solo se puede experimentar.\n\n"
        "<b>{button_text}</b>\n\n"
        "<i>Espero que decida bien. "
        "Las oportunidades como esta no aparecen twice.</i>"
    )

    VIP_DECLINED_GRACEFUL = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>🤔 ENTIENDO</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>No es el momento.</i>\n\n"
        "Comprendo perfectamente. "
        "La decisión de dar el siguiente paso es personal. "
        "No se puede forzar.\n\n"
        "Lo que ha construido hasta aquí sigue siendo suyo. "
        "Ningo quito nada.\n\n"
        "Diana respeta su decisión. "
        "Y la puerta permanecerá abierta si cambia de idea.\n\n"
        "<i>Por ahora, continue como está. "
        "Ya es más de lo que la mayoría logra.</i>"
    )

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def format_progress_bar(current: int, total: int, width: int = 20) -> str:
        """Genera una barra de progreso visual.

        Args:
            current: Valor actual
            total: Valor total
            width: Ancho de la barra (default: 20)

        Returns:
            String con barra de progreso y porcentaje
        """
        if total == 0:
            percentage = 0
        else:
            percentage = min(int((current / total) * 100), 100)

        filled = int(width * percentage / 100)
        bar = "█" * filled + "░" * (width - filled)

        return f"{bar} {percentage}%"

    @staticmethod
    def format_coins(amount: int) -> str:
        """Formatea cantidad de besitos/Favores.

        Args:
            amount: Cantidad de besitos

        Returns:
            String formateado con emoji
        """
        return f"{amount} Besito{'s' if amount != 1 else ''}"
