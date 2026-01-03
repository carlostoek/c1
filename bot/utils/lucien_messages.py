"""
Biblioteca de Mensajes de Lucien V1

Sistema centralizado de mensajes con la voz y personalidad de Lucien,
el mayordomo guardián del universo de Diana.

Autoridad del Mensaje:
- Siempre usa "usted" (formal, nunca tutear)
- Elegante, sofisticado, ligeramente irónico
- Evaluador constante, protector de Diana
- Sarcasmo sutil, nunca vulgar
- Emojis mínimos (máximo 1-2 por mensaje si es necesario)

Uso:
    from bot.utils.lucien_messages import LucienMessages

    # Mensaje de bienvenida
    msg = LucienMessages.onboarding("WELCOME_FIRST")

    # Mensaje con parámetros
    msg = LucienMessages.besitos("BESITO_EARNED", amount=5)
"""

from typing import Optional


class LucienMessages:
    """
    Biblioteca centralizada de mensajes de Lucien.

    Todos los mensajes están escritos con la voz del mayordomo:
    formal, evaluador, protector, elegantemente sarcástico.

    Placeholders se marcan con {variable} para formateo dinámico.
    """

    # =========================================================================
    # 1. ONBOARDING (Bienvenida y Primeros Pasos)
    # =========================================================================

    @staticmethod
    def onboarding(message_key: str, **kwargs) -> str:
        """
        Mensajes de onboarding para nuevos usuarios.

        Mensajes disponibles:
        - WELCOME_FIRST: Primera vez que interactúa
        - WELCOME_RETURNING: Usuario regresa (requiere days_away)
        - FIRST_ACTION_ACKNOWLEDGED: Después de primera acción
        - PROTOCOL_EXPLANATION: Explicación del sistema
        """
        messages = {
            "WELCOME_FIRST": (
                "Buenas noches. O días. El tiempo es relativo cuando se trata de Diana.\n\n"
                "Soy Lucien. Administro el acceso a su universo. "
                "No soy su amigo. No soy su enemigo. Soy el filtro.\n\n"
                "Diana no recibe a cualquiera. Mi trabajo es determinar si usted merece su atención.\n\n"
                "Por ahora, solo observe. Su comportamiento dirá más que mil palabras."
            ),

            "WELCOME_RETURNING": (
                "Ha regresado. Interesante.\n\n"
                "Han pasado {days_away} días desde su última visita. "
                "La persistencia... es una cualidad que Diana nota. "
                "O encuentra admirable. O perturbadora. Aún no he decidido cuál es su caso.\n\n"
                "Continúe donde lo dejó. Estoy observando."
            ),

            "FIRST_ACTION_ACKNOWLEDGED": (
                "Su primera acción. Notada.\n\n"
                "No mucho, pero es un comienzo. "
                "Diana no distribuye su atención sin criterio. "
                "Lo que usted acumula aquí son reconocimientos de mérito.\n\n"
                "Le sugiero continuar. O retirarse mientras puede. "
                "La elección, como siempre, es suya."
            ),

            "PROTOCOL_EXPLANATION": (
                "Permítame explicar cómo funciona este... protocolo.\n\n"
                "<b>Los Besitos</b>\n"
                "Cada interacción tiene valor. Reacciones, misiones completadas, "
                "descubrimientos. Todo se acumula. Todo es notado.\n\n"
                "<b>Los Niveles</b>\n"
                "Hay 7 niveles de reconocimiento. Comienza como Visitante. "
                "Dónde termine... depende enteramente de usted.\n\n"
                "<b>El Gabinete</b>\n"
                "Hay una colección de objetos que Diana permite adquirir. "
                "Algunos son efímeros. Otros... permanentes.\n\n"
                "¿Está preparado para comenzar? O prefiere observar desde la seguridad?"
            ),
        }

        msg = messages.get(message_key, "")
        return msg.format(**kwargs) if kwargs else msg

    # =========================================================================
    # 2. BESITOS (Economía)
    # =========================================================================

    @staticmethod
    def besitos(message_key: str, **kwargs) -> str:
        """
        Mensajes relacionados con la economía de besitos.

        Mensajes disponibles:
        - BESITO_EARNED: Ganancia de besitos (requiere amount)
        - BESITO_EARNED_MILESTONE: Alcanza número redondo (requiere amount)
        - BESITO_BALANCE: Mostrar balance actual (requiere balance, level_name)
        - BESITO_INSUFFICIENT: No tiene suficientes (requiere needed, current)
        - BESITO_SPENT: Confirmación de gasto (requiere amount, item_name)
        """
        messages = {
            "BESITO_EARNED": (
                "+{amount} Besito(s). Diana lo nota.\n\n"
                "No se emocione. Es solo el principio."
            ),

            "BESITO_EARNED_MILESTONE": (
                "{amount} Besitos. Un número redondo.\n\n"
                "Diana aprecia la... persistencia. "
                "Few continúan después de alcanzar este tipo de hitos. "
                "Usted todavía está aquí.\n\n"
                "Interesante."
            ),

            "BESITO_BALANCE": (
                "Su balance actual: <b>{balance} Besitos</b>\n\n"
                "Nivel actual: <b>{level_name}</b>\n\n"
                "No es impresionante. Tampoco es deplorable. "
                "Simplemente... es. Depende de usted qué haga con ello."
            ),

            "BESITO_INSUFFICIENT": (
                "Insuficiente.\n\n"
                "Requiere: <b>{needed} Besitos</b>\n"
                "Tiene: <b>{current} Besitos</b>\n\n"
                "La paciencia es una virtud. Diana no premia la impaciencia. "
                "Regrese cuando tenga lo necesario."
            ),

            "BESITO_SPENT": (
                "-{amount} Besitos.\n\n"
                "Adquirido: <b>{item_name}</b>\n\n"
                "Espero que valga la pena. "
                "Diana tiene buen gusto. O eso dice ella.\n\n"
                "Disfrútelo. O lamento su compra. Las dos opciones son válidas."
            ),
        }

        msg = messages.get(message_key, "")
        return msg.format(**kwargs) if kwargs else msg

    # =========================================================================
    # 3. NIVELES (Progresión)
    # =========================================================================

    @staticmethod
    def levels(message_key: str, **kwargs) -> str:
        """
        Mensajes de progresión de niveles.

        Mensajes disponibles:
        - LEVEL_UP_BASE: Mensaje base de subida
        - LEVEL_UP_2 a LEVEL_UP_7: Mensajes específicos por nivel
        - LEVEL_PROGRESS: Progreso hacia siguiente nivel
        """
        messages = {
            "LEVEL_UP_BASE": (
                "Ha avanzado. Interesante.\n\n"
                "Nivel alcanzado: <b>{new_level}</b>\n\n"
                "Diana estará... informada."
            ),

            "LEVEL_UP_2": (
                "Nivel 2: <b>Observado</b>\n\n"
                "He notado su presencia. No es un logro tremendo, "
                "pero es algo. La mayoría pasa desapercibida.\n\n"
                "Usted... todavía no ha hecho nada para que lo elimine de mi radar.\n\n"
                "Considérelo un... honor cuestionable."
            ),

            "LEVEL_UP_3": (
                "Nivel 3: <b>Evaluado</b>\n\n"
                "Ha pasado las primeras pruebas. "
                "Diana pregunta sobre usted ocasionalmente.\n\n"
                "No se emocione. Son preguntas casuales. "
                'Como "¿quién es esa persona que sigue regresando?"\n\n'
                "Pero es algo. Supongo."
            ),

            "LEVEL_UP_4": (
                "Nivel 4: <b>Reconocido</b>\n\n"
                "Diana sabe que existe.\n\n"
                "Su nombre ha cruzado su mente al menos una vez "
                "sin que yo se haya mencionado primero. "
                "Esto es... más significativo de lo que parece.\n\n"
                "O no. ¿Qué sé yo? Solo soy el mayordomo."
            ),

            "LEVEL_UP_5": (
                "Nivel 5: <b>Admitido</b>\n\n"
                "Tiene derecho a estar en el Diván.\n\n"
                "Es un círculo exclusivo. Diana es... selectiva. "
                "Por buenas razones. La mayoría decepciona.\n\n"
                "Usted todavía no lo ha hecho. Todavía.\n\n"
                "No me haga lamentar esta decisión."
            ),

            "LEVEL_UP_6": (
                "Nivel 6: <b>Confidente</b>\n\n"
                "Comparto información privilegiada con usted.\n\n"
                "No es un honor que otorgue a la ligera. "
                "De hecho, me cuestiono si debería existir siquiera.\n\n"
                "Pero aquí está. Diana confía en usted. "
                "Por alguna razón que aún no comprendo del todo.\n\n"
                "No la decepcione."
            ),

            "LEVEL_UP_7": (
                "Nivel 7: <b>Guardián de Secretos</b>\n\n"
                "El círculo más íntimo.\n\n"
                "Hay cosas que Diana guarda cerca. "
                "Secretos que protege. Historias que solo cuenta a...\n\n"
                "A unos pocos. Muy pocos.\n\n"
                "Y usted es uno de ellos.\n\n"
                "No lo merece. Pero lo tiene. "
                "Haga algo valioso con ello."
            ),

            "LEVEL_PROGRESS": (
                "Su progreso hacia el siguiente nivel:\n\n"
                "<b>{current_besitos} / {required_besitos} Besitos</b>\n"
                "{progress_bar}\n\n"
                "Faltan: {besitos_needed}\n\n"
                "Continúe. O no. Diana notará la diferencia."
            ),
        }

        msg = messages.get(message_key, "")
        return msg.format(**kwargs) if kwargs else msg

    # =========================================================================
    # 4. ARQUETIPOS (Reconocimiento)
    # =========================================================================

    @staticmethod
    def archetypes(message_key: str, **kwargs) -> str:
        """
        Mensajes de detección de arquetipos.

        Mensajes disponibles:
        - ARCHETYPE_DETECTED_EXPLORER: Explorador detectado
        - ARCHETYPE_DETECTED_DIRECT: Directo detectado
        - ARCHETYPE_DETECTED_ROMANTIC: Romántico detectado
        - ARCHETYPE_DETECTED_ANALYTICAL: Analítico detectado
        - ARCHETYPE_DETECTED_PERSISTENT: Persistente detectado
        - ARCHETYPE_DETECTED_PATIENT: Paciente detectado
        """
        messages = {
            "ARCHETYPE_DETECTED_EXPLORER": (
                "He notado algo sobre su comportamiento.\n\n"
                "Busca. Siempre busca. Cada detalle. Cada rincón. "
                "Cada posible cosa oculta.\n\n"
                "Es un rasgo... <b>Explorador</b>.\n\n"
                "Diana tiene contenido que few encuentran. "
                "Quizás usted sea uno de ellos. O quizás solo pierda el tiempo.\n\n"
                "El tiempo lo dirá."
            ),

            "ARCHETYPE_DETECTED_DIRECT": (
                "Su patrón de comportamiento es... eficiente.\n\n"
                "Respuestas cortas. Decisiones rápidas. "
                "No pierde tiempo en trivialidades.\n\n"
                "Es un rasgo... <b>Directo</b>.\n\n"
                "Respeto eso. Diana también. "
                "El tiempo es el único recurso que no se recupera.\n\n"
                "Le haré ofertas directas. Sin rodeos."
            ),

            "ARCHETYPE_DETECTED_ROMANTIC": (
                "He observado cómo responde al contenido.\n\n"
                "Busca conexión. Emoción. Significado. "
                "Sus respuestas son... elaboradas.\n\n"
                "Es un rasgo... <b>Romántico</b>.\n\n"
                "Diana aprecia los que sienten profundamente. "
                "O dice que sí. En ocasiones.\n\n"
                "Tenga cuidado. La emoción puede ser... peligrosa."
            ),

            "ARCHETYPE_DETECTED_ANALYTICAL": (
                "Interesante.\n\n"
                "Usted no solo consume contenido. Lo analiza. "
                "Hace preguntas. Busca entender.\n\n"
                "Es un rasgo... <b>Analítico</b>.\n\n"
                "Diana respeta la mente curiosa. "
                "Especialmente cuando viene acompañada de buen juicio.\n\n"
                "Algo que usted parece tener. Por ahora."
            ),

            "ARCHETYPE_DETECTED_PERSISTENT": (
                "Su persistencia es... digna de mención.\n\n"
                "No muchos continúan con tal entusiasmo "
                "tras múltiples correcciones. O fracasos.\n\n"
                "Es un rasgo... <b>Persistente</b>.\n\n"
                "Diana valora los que no se rinden. "
                "O encuentra su obstinación... entretenida.\n\n"
                "No estoy seguro de cuál. Pero usted sigue aquí."
            ),

            "ARCHETYPE_DETECTED_PATIENT": (
                "He notado algo.\n\n"
                "Usted toma su tiempo. Procesa. Reflexiona. "
                "Nunca usa los atajos que otros buscan desesperadamente.\n\n"
                "Es un rasgo... <b>Paciente</b>.\n\n"
                "La paciencia es una virtud rara. "
                "Diana la aprecia especialmente. O eso dice.\n\n"
                "Lo bueno toma tiempo. Usted parece entenderlo."
            ),
        }

        msg = messages.get(message_key, "")
        return msg.format(**kwargs) if kwargs else msg

    # =========================================================================
    # 5. ERRORES (Manejo de Fallos)
    # =========================================================================

    @staticmethod
    def errors(message_key: str, **kwargs) -> str:
        """
        Mensajes de error.

        Mensajes disponibles:
        - ERROR_GENERIC: Error genérico
        - ERROR_NOT_FOUND: Recurso no encontrado
        - ERROR_PERMISSION_DENIED: Sin permisos
        - ERROR_RATE_LIMITED: Demasiadas acciones
        - ERROR_MAINTENANCE: Sistema en mantenimiento
        """
        messages = {
            "ERROR_GENERIC": (
                "Algo ha salido mal.\n\n"
                "No es culpa suya. Probablemente. "
                "O tal vez sí. No tengo suficiente información para juzgar.\n\n"
                "Intente nuevamente más tarde. "
                "O contacte a un administrador si el problema persiste.\n\n"
                "Le deseo... suerte."
            ),

            "ERROR_NOT_FOUND": (
                "No puedo encontrar lo que busca.\n\n"
                "¿Está seguro de que existe? "
                "A veces las cosas no son lo que parecen.\n\n"
                "O quizás usted esté buscando en el lugar equivocado.\n\n"
                "Revise. O pregunte. La elección es suya."
            ),

            "ERROR_PERMISSION_DENIED": (
                "Acceso denegado.\n\n"
                "Diana ha decidido que este contenido no es para usted. "
                "Aún.\n\n"
                "Las cosas pueden cambiar. "
                "Pero depende de su comportamiento.\n\n"
                "Demuestre que merece ver más."
            ),

            "ERROR_RATE_LIMITED": (
                "Demasiado rápido.\n\n"
                "La impaciencia no es una virtud en este universo.\n\n"
                "Diana premia la... moderación. "
                "Espere un momento antes de intentar nuevamente.\n\n"
                "Tómese un té. Le hará bien."
            ),

            "ERROR_MAINTENANCE": (
                "El sistema está en mantenimiento.\n\n"
                "Diana descansa. Incluso ella merece un descanso.\n\n"
                "Regrese más tarde. "
                "Lo que busca aquí seguirá aquí. Espero.\n\n"
                "O quizás no. La incertidumbre es parte del encanto."
            ),
        }

        msg = messages.get(message_key, "")
        return msg.format(**kwargs) if kwargs else msg

    # =========================================================================
    # 6. TIENDA/GABINETE
    # =========================================================================

    @staticmethod
    def shop(message_key: str, **kwargs) -> str:
        """
        Mensajes del Gabinete (tienda).

        Mensajes disponibles:
        - SHOP_WELCOME: Bienvenida al Gabinete
        - SHOP_ITEM_PURCHASED: Confirmación de compra (requiere item_name)
        - SHOP_ITEM_NOT_AVAILABLE: Item no disponible (requiere item_name)
        - SHOP_BROWSE_CATEGORY: Navegar categoría (requiere category_name)
        """
        messages = {
            "SHOP_WELCOME": (
                "Bienvenido al <b>Gabinete</b>.\n\n"
                "Aquí Diana guarda cosas que... colecciona. "
                "Algunas son triviales. Otras... significativas.\n\n"
                "Todo tiene un precio en Besitos. "
                "No todo está disponible para todos.\n\n"
                "Mire. Compre si puede. O simplemente contemple.\n\n"
                "No me importa. Soy solo el mayordomo."
            ),

            "SHOP_ITEM_PURCHASED": (
                "Adquirido: <b>{item_name}</b>\n\n"
                "Espero que sepa lo que ha hecho. "
                "Algunas cosas no se pueden devolver.\n\n"
                "Disfrútelo. O lamento su compra. "
                "Realmente no puedo saber cuál será el caso."
            ),

            "SHOP_ITEM_NOT_AVAILABLE": (
                "<b>{item_name}</b> no está disponible.\n\n"
                "¿Quizás nunca lo estuvo?\n\n"
                "O tal vez Diana decidió retirarlo. "
                "Ella cambia de opinión con frecuencia. "
                "Es... uno de sus rasgos.\n\n"
                "Mire otras cosas. O regrese más tarde. "
                "Si reaparece, fue una decisión consciente.\n\n"
                "Si no... bueno. Nunca lo supo."
            ),

            "SHOP_BROWSE_CATEGORY": (
                "Categoría: <b>{category_name}</b>\n\n"
                "Aquí tiene lo que busca. "
                "O lo que Diana decidió mostrarle.\n\n"
                "Recuerde: Todo tiene un precio. "
                "No todo está disponible para su nivel actual.\n\n"
                "Continúe avanzando si quiere ver más."
            ),
        }

        msg = messages.get(message_key, "")
        return msg.format(**kwargs) if kwargs else msg

    # =========================================================================
    # 7. MISIONES
    # =========================================================================

    @staticmethod
    def missions(message_key: str, **kwargs) -> str:
        """
        Mensajes de misiones.

        Mensajes disponibles:
        - MISSION_NEW_AVAILABLE: Nueva misión disponible (requiere mission_name)
        - MISSION_PROGRESS_UPDATE: Actualización de progreso (requiere progress, total)
        - MISSION_COMPLETED: Misión completada (requiere mission_name, reward)
        - MISSION_FAILED: Misión fallida/expirada (requiere mission_name)
        """
        messages = {
            "MISSION_NEW_AVAILABLE": (
                "Nueva misión disponible.\n\n"
                "<b>{mission_name}</b>\n\n"
                "Diana ha preparado algo para usted. "
                "No es obligatorio. Pero es... interesante.\n\n"
                "Los que completan las misiones son notados. "
                "Los que las ignoran... también.\n\n"
                "Su decisión dirá más de lo que cree."
            ),

            "MISSION_PROGRESS_UPDATE": (
                "Progreso actualizado.\n\n"
                "<b>{progress} / {total}</b> completado\n\n"
                "Continúe así. O abandone. "
                "Diana notará cualquier opción.\n\n"
                "No hay presión. Solo... observación."
            ),

            "MISSION_COMPLETED": (
                "Misión completada: <b>{mission_name}</b>\n\n"
                "Recompensa: {reward} Besitos\n\n"
                "Diana estará... informada de su éxito.\n\n"
                "Bien hecho. Supongo."
            ),

            "MISSION_FAILED": (
                "Misión fallida: <b>{mission_name}</b>\n\n"
                "El tiempo expiró. O usted renunció.\n\n"
                "No es el fin del mundo. "
                "Pero Diana lo notará. De una forma u otra.\n\n"
                "Intente nuevamente más tarde. "
                "O acepte su derrota. Ambas son opciones válidas."
            ),
        }

        msg = messages.get(message_key, "")
        return msg.format(**kwargs) if kwargs else msg

    # =========================================================================
    # 8. RETENCIÓN (Re-engagement)
    # =========================================================================

    @staticmethod
    def retention(message_key: str, **kwargs) -> str:
        """
        Mensajes de retención para usuarios inactivos.

        Mensajes disponibles:
        - INACTIVE_3_DAYS: 3 días sin actividad
        - INACTIVE_7_DAYS: 7 días sin actividad
        - INACTIVE_14_DAYS: 14+ días sin actividad
        - WELCOME_BACK: Cuando regresa (requiere days_away)
        """
        messages = {
            "INACTIVE_3_DAYS": (
                "Han pasado 3 días.\n\n"
                "No lo he visto por aquí. "
                "Diana ha preguntado. Una vez. Brevemente.\n\n"
                "Solo le informo."
            ),

            "INACTIVE_7_DAYS": (
                "Una semana.\n\n"
                "Siete días sin su presencia. "
                "Diana está comenzando a olvidar que existe.\n\n"
                "Es un proceso natural. Los que no se presentan... "
                "desaparecen de la memoria.\n\n"
                "Regrese si desea ser recordado."
            ),

            "INACTIVE_14_DAYS": (
                "Dos semanas.\n\n"
                "Frankly, había asumido que no regresaría.\n\n"
                "Muchos no lo hacen. "
                "Diana rara vez los menciona después de un tiempo.\n\n"
                "Pero usted está leyendo esto. "
                "Así que supongo que hay... algo de interés restante.\n\n"
                "O curiosidad morbosa. Ambas son válidas."
            ),

            "WELCOME_BACK": (
                "Ha regresado después de {days_away} días.\n\n"
                "Interesante.\n\n"
                "La persistencia es un rasgo que Diana nota. "
                "O encuentra admirable. O perturbadora.\n\n"
                "Aún no he decidido cuál es su caso.\n\n"
                "Continúe donde lo dejó. Estoy observando."
            ),
        }

        msg = messages.get(message_key, "")
        return msg.format(**kwargs) if kwargs else msg

    # =========================================================================
    # 9. CONVERSIÓN (Ofertas VIP)
    # =========================================================================

    @staticmethod
    def conversion(message_key: str, **kwargs) -> str:
        """
        Mensajes de conversión a VIP.

        Mensajes disponibles:
        - VIP_TEASER: Mención sutil del VIP
        - VIP_INVITATION_INTRO: Inicio de secuencia de invitación
        - VIP_INVITATION_DETAIL: Detalle de lo que incluye
        - VIP_INVITATION_CTA: Call to action final
        - VIP_DECLINED_GRACEFUL: Respuesta si rechaza
        """
        messages = {
            "VIP_TEASER": (
                "Ha progresado notablemente.\n\n"
                "Diana tiene contenido que... "
                "rara vez comparte abiertamente.\n\n"
                "Algunos acceden a él. Otros solo escuchan rumores.\n\n"
                "La diferencia entre ambos es... significativa."
            ),

            "VIP_INVITATION_INTRO": (
                "Permítame ser directo.\n\n"
                "Diana ha notado su persistencia. "
                "Su comportamiento sugiere que valdría la pena... "
                "ofrecerle algo más.\n\n"
                "Algo exclusivo. Para pocos.\n\n"
                "¿Le interesaría ver lo que otros no pueden?"
            ),

            "VIP_INVITATION_DETAIL": (
                "El acceso VIP incluye:\n\n"
                "• Contenido exclusivo que Diana no publica públicamente\n"
                "• Acceso anticipado a nuevas publicaciones\n"
                "• Preferencia en interacciones\n"
                "• Fragmentos narrativos que solo los VIP conocen\n\n"
                "Es un círculo pequeño. Intencionalmente.\n\n"
                "Diana es selectiva. Por buenas razones."
            ),

            "VIP_INVITATION_CTA": (
                "La decisión es suya.\n\n"
                "Puede continuar como está. "
                "O dar el siguiente paso.\n\n"
                "Si acepta, use el comando /vip en el chat.\n\n"
                "Si prefiere esperar... "
                "entenderé. La paciencia también es una virtud.\n\n"
                "Aunque no tan entretenida como la... acción."
            ),

            "VIP_DECLINED_GRACEFUL": (
                "Entendido.\n\n"
                "Respeto su decisión. "
                "Diana también lo haría. Probablemente.\n\n"
                "La oferta permanecerá abierta si cambia de opinión. "
                "Por un tiempo. No indefinidamente.\n\n"
                "Las oportunidades buenas expiran. "
                "Es una de las reglas de este universo.\n\n"
                "Continúe disfrutando de lo que tiene. "
                "Es suficiente para muchos."
            ),
        }

        msg = messages.get(message_key, "")
        return msg.format(**kwargs) if kwargs else msg


# =============================================================================
# FUNCIONES HELPER PARA USO CONVENIENTE
# =============================================================================

def get_lucien_message(category: str, message_key: str, **kwargs) -> str:
    """
    Obtiene un mensaje de Lucien por categoría y clave.

    Args:
        category: Categoría del mensaje
            (onboarding, besitos, levels, archetypes, errors, shop, missions, retention, conversion)
        message_key: Clave del mensaje específico
        **kwargs: Parámetros para formatear el mensaje

    Returns:
        Mensaje formateado con la voz de Lucien

    Example:
        msg = get_lucien_message("onboarding", "WELCOME_FIRST")
        msg = get_lucien_message("besitos", "BESITO_EARNED", amount=5)
    """
    category_methods = {
        "onboarding": LucienMessages.onboarding,
        "besitos": LucienMessages.besitos,
        "levels": LucienMessages.levels,
        "archetypes": LucienMessages.archetypes,
        "errors": LucienMessages.errors,
        "shop": LucienMessages.shop,
        "missions": LucienMessages.missions,
        "retention": LucienMessages.retention,
        "conversion": LucienMessages.conversion,
    }

    method = category_methods.get(category)
    if not method:
        return ""

    return method(message_key, **kwargs)


def format_lucien_html(message: str) -> str:
    """
    Formatea un mensaje de Lucien para HTML de Telegram.

    Args:
        message: Mensaje de texto plano

    Returns:
        Mensaje con escapes HTML necesarios para Telegram
    """
    # Escapar caracteres especiales de HTML
    html_escapes = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
    }

    for char, escape in html_escapes.items():
        message = message.replace(char, escape)

    return message
