# REQUERIMIENTO: FASE 3 - ARQUETIPOS EXPANDIDOS
## Proyecto: El Mayordomo del Diván
## Bot de Telegram para Señorita Kinky

---

# CONTEXTO

Los arquetipos son el sistema de "personalización invisible" del bot. Lucien observa el comportamiento del usuario y lo clasifica en uno de 6 arquetipos. Esta clasificación afecta:

- El tono de los mensajes de Lucien
- Las variaciones en la narrativa
- Las recomendaciones de contenido
- Los triggers de conversión
- Los badges disponibles

**Principio fundamental:** El usuario NO elige su arquetipo. Lucien lo detecta basándose en comportamiento real. Esto hace que el reconocimiento sea significativo - "Lucien realmente me observa".

**Dependencias:**
- Fase 0 completada (enums de arquetipos, modelo de datos)
- Fase 2
---

# LOS 6 ARQUETIPOS

## Visión general

| Arquetipo | Palabra clave | Comportamiento típico | Lucien lo ve como... |
|-----------|---------------|----------------------|---------------------|
| Explorer | Curiosidad | Revisa todo, busca secretos | "Insaciablemente curioso" |
| Direct | Eficiencia | Va al grano, acciones rápidas | "Refrescantemente directo" |
| Romantic | Emoción | Poético, busca conexión | "Peligrosamente sentimental" |
| Analytical | Lógica | Preguntas, análisis, estructura | "Irritantemente preciso" |
| Persistent | Tenacidad | Vuelve siempre, no se rinde | "Admirablemente terco" |
| Patient | Calma | Se toma su tiempo, no apresura | "Inquietantemente paciente" |

## Descripciones detalladas

### EXPLORER (El Explorador)

**Perfil psicológico:**
Necesita ver todo. No puede dejar piedra sin voltear. Su curiosidad es su motor principal. Disfruta el proceso de descubrimiento tanto como el resultado.

**Comportamientos característicos:**
- Visita múltiples secciones del bot en cada sesión
- Revisa contenido antiguo, no solo lo nuevo
- Encuentra easter eggs y contenido oculto
- Tiempo alto en cada pieza de contenido (lee todo)
- Explora opciones antes de decidir

**Lo que busca:**
- Secretos, contenido oculto
- Completar colecciones
- Saber que no se perdió nada

**Debilidad:**
- Puede dispersarse, no completar nada
- Ansiedad si siente que algo se le escapa

---

### DIRECT (El Directo)

**Perfil psicológico:**
Valora su tiempo. Sabe lo que quiere y va por ello. No necesita adornos ni ceremonias. Aprecia la claridad y la eficiencia.

**Comportamientos característicos:**
- Respuestas cortas (<15 palabras promedio)
- Tiempo de decisión rápido (<5 segundos)
- Usa botones en lugar de escribir texto libre
- Completa acciones en pocas interacciones
- Ignora contenido que considera "relleno"

**Lo que busca:**
- Resultados claros
- Acceso directo a lo que importa
- Sin rodeos ni explicaciones largas

**Debilidad:**
- Puede perderse matices importantes
- A veces parece frío o desinteresado

---

### ROMANTIC (El Romántico)

**Perfil psicológico:**
Busca conexión emocional genuina. Ve a Diana no solo como creadora de contenido sino como persona. Valora la vulnerabilidad y la intimidad por encima de lo explícito.

**Comportamientos característicos:**
- Respuestas largas con lenguaje emocional
- Usa adjetivos y metáforas
- Reacciona más a contenido emocional/personal
- Tiempo de respuesta variable (piensa antes de escribir)
- Hace preguntas sobre Diana como persona

**Lo que busca:**
- Conexión genuina
- Momentos de vulnerabilidad compartida
- Sentir que es especial para Diana

**Debilidad:**
- Puede idealizar la relación
- Decepción si siente distancia

---

### ANALYTICAL (El Analítico)

**Perfil psicológico:**
Necesita entender cómo funciona todo. Busca patrones, lógica, estructura. Disfruta los desafíos intelectuales y las evaluaciones.

**Comportamientos característicos:**
- Alto score en evaluaciones/cuestionarios
- Hace preguntas al bot
- Respuestas estructuradas (enumera, usa puntos)
- Lee descripciones completas antes de actuar
- Nota inconsistencias o errores

**Lo que busca:**
- Comprender el sistema
- Desafíos intelectuales
- Lógica detrás de las cosas

**Debilidad:**
- Puede sobre-analizar
- A veces pierde lo emocional por lo racional

---

### PERSISTENT (El Persistente)

**Perfil psicológico:**
No se rinde. Si falla, lo intenta de nuevo. Si se va, regresa. Su determinación es su característica definitoria.

**Comportamientos característicos:**
- Múltiples intentos en desafíos/evaluaciones
- Regresa después de períodos de inactividad
- Reintenta acciones fallidas
- No abandona flujos a medias
- Historial de re-engagement

**Lo que busca:**
- Sentir que su esfuerzo vale
- Reconocimiento de su dedicación
- Superar obstáculos

**Debilidad:**
- Puede frustrarse si no hay progreso
- A veces persiste en dirección equivocada

---

### PATIENT (El Paciente)

**Perfil psicológico:**
Entiende que lo valioso toma tiempo. No apresura las cosas. Disfruta el proceso gradual de construcción de la relación.

**Comportamientos característicos:**
- Tiempo de respuesta >30 segundos consistentemente
- No usa opciones de "skip" o "saltar"
- Rachas largas y consistentes
- No presiona por contenido/acceso
- Actividad regular pero no frenética

**Lo que busca:**
- Relación a largo plazo
- Profundidad sobre velocidad
- Apreciación de su constancia

**Debilidad:**
- Puede ser demasiado pasivo
- A veces espera cuando debería actuar

---

# F3.1: MODELO DE DATOS

## Señales a trackear (UserBehaviorSignals)

```
UserBehaviorSignals:
    user_id: int (FK, unique)
    
    # Métricas de exploración
    content_sections_visited: int        # Secciones únicas visitadas
    content_completion_rate: float       # % de contenido disponible visto
    easter_eggs_found: int               # Easter eggs encontrados
    avg_time_on_content: float           # Segundos promedio en contenido
    revisits_old_content: int            # Veces que revisó contenido antiguo
    
    # Métricas de velocidad/directness
    avg_response_time: float             # Segundos promedio para responder
    avg_response_length: float           # Palabras promedio por respuesta
    button_vs_text_ratio: float          # % de interacciones via botón vs texto
    avg_decision_time: float             # Segundos para tomar decisiones
    actions_per_session: float           # Acciones promedio por sesión
    
    # Métricas emocionales
    emotional_words_count: int           # Veces que usó palabras emocionales
    question_count: int                  # Preguntas hechas al bot
    long_responses_count: int            # Respuestas >50 palabras
    personal_questions_about_diana: int  # Preguntas sobre Diana como persona
    
    # Métricas de análisis
    quiz_avg_score: float                # Promedio en evaluaciones (0-100)
    structured_responses: int            # Respuestas con estructura (listas, puntos)
    error_reports: int                   # Veces que reportó errores/inconsistencias
    
    # Métricas de persistencia
    return_after_inactivity: int         # Veces que volvió después de 3+ días
    retry_failed_actions: int            # Reintentos de acciones fallidas
    incomplete_flows_completed: int      # Flujos abandonados y luego completados
    
    # Métricas de paciencia
    skip_actions_used: int               # Veces que usó "saltar" o similar
    current_streak: int                  # Racha actual (de F2.3)
    best_streak: int                     # Mejor racha histórica
    avg_session_duration: float          # Duración promedio de sesión
    
    # Metadata
    total_interactions: int              # Total de interacciones registradas
    first_interaction_at: datetime
    last_updated_at: datetime
```

## Clasificación del usuario (campos en User model)

```
User (agregar campos):
    archetype: enum (EXPLORER, DIRECT, ROMANTIC, ANALYTICAL, PERSISTENT, PATIENT) nullable
    archetype_confidence: float (0.0 - 1.0)
    archetype_scores: JSON  # {"EXPLORER": 0.7, "DIRECT": 0.3, ...}
    archetype_detected_at: datetime nullable
    archetype_version: int  # Para re-evaluar si cambia algoritmo
```

---

# F3.2: SERVICIO DE TRACKING (BehaviorTrackingService)

## Descripción
Servicio que registra cada interacción relevante para construir el perfil de comportamiento.

## Métodos principales

### Registrar interacción

```
track_interaction(
    user_id: int,
    interaction_type: InteractionType,
    metadata: dict
) -> None

InteractionType enum:
    BUTTON_CLICK
    TEXT_RESPONSE
    CONTENT_VIEW
    CONTENT_COMPLETE
    QUIZ_ANSWER
    DECISION_MADE
    MENU_NAVIGATION
    EASTER_EGG_FOUND
    SESSION_START
    SESSION_END
    RETURN_AFTER_INACTIVITY
    RETRY_ACTION
    SKIP_ACTION
    QUESTION_ASKED
```

### Actualizar métricas

```
update_metrics(user_id: int) -> None
    
    Recalcula todas las métricas derivadas:
    - Promedios (tiempo respuesta, longitud, etc.)
    - Ratios (botón vs texto)
    - Conteos acumulados
    
    Llamar periódicamente o después de N interacciones.
```

### Obtener señales

```
get_behavior_signals(user_id: int) -> UserBehaviorSignals
```

## Qué trackear en cada interacción

### BUTTON_CLICK
```
{
    "button_id": str,
    "context": str,  # Dónde estaba el botón
    "time_to_click": float  # Segundos desde que se mostró
}
```

### TEXT_RESPONSE
```
{
    "word_count": int,
    "has_emotional_words": bool,
    "has_questions": bool,
    "is_structured": bool,  # Tiene puntos, números, etc.
    "response_time": float
}
```

### CONTENT_VIEW
```
{
    "content_id": str,
    "content_type": str,
    "time_spent": float,
    "is_revisit": bool,
    "completion": float  # 0-1, qué tanto vio
}
```

### QUIZ_ANSWER
```
{
    "quiz_id": str,
    "question_id": str,
    "is_correct": bool,
    "time_to_answer": float
}
```

### DECISION_MADE (narrativa)
```
{
    "fragment_id": str,
    "decision_id": str,
    "time_to_decide": float,
    "options_available": int
}
```

---

# F3.3: SERVICIO DE DETECCIÓN (ArchetypeDetectionService)

## Descripción
Analiza las señales de comportamiento y determina el arquetipo del usuario.

## Algoritmo de detección

### Paso 1: Calcular scores por arquetipo

Cada arquetipo tiene una fórmula de scoring basada en las señales:

```
EXPLORER_SCORE = (
    (content_completion_rate * 0.25) +
    (normalize(easter_eggs_found, 0, 10) * 0.20) +
    (normalize(avg_time_on_content, 20, 120) * 0.20) +
    (normalize(revisits_old_content, 0, 20) * 0.15) +
    (normalize(content_sections_visited, 0, max_sections) * 0.20)
)

DIRECT_SCORE = (
    (1 - normalize(avg_response_time, 5, 60)) * 0.25 +
    (1 - normalize(avg_response_length, 5, 50)) * 0.20 +
    (button_vs_text_ratio * 0.25) +
    (1 - normalize(avg_decision_time, 3, 30)) * 0.15 +
    (normalize(actions_per_session, 5, 20) * 0.15)
)

ROMANTIC_SCORE = (
    (normalize(emotional_words_count, 0, 50) * 0.25) +
    (normalize(long_responses_count, 0, 20) * 0.20) +
    (normalize(personal_questions_about_diana, 0, 10) * 0.25) +
    (normalize(avg_response_length, 20, 100) * 0.15) +
    (emotional_content_preference * 0.15)  # Calculado de interacciones
)

ANALYTICAL_SCORE = (
    (quiz_avg_score / 100 * 0.30) +
    (normalize(question_count, 0, 30) * 0.20) +
    (normalize(structured_responses, 0, 15) * 0.20) +
    (normalize(error_reports, 0, 5) * 0.10) +
    (completion_before_action * 0.20)  # Lee todo antes de actuar
)

PERSISTENT_SCORE = (
    (normalize(return_after_inactivity, 0, 5) * 0.30) +
    (normalize(retry_failed_actions, 0, 10) * 0.25) +
    (normalize(incomplete_flows_completed, 0, 5) * 0.25) +
    (account_age_factor * 0.20)  # Más tiempo = más peso
)

PATIENT_SCORE = (
    (normalize(avg_response_time, 30, 120) * 0.20) +
    (1 - normalize(skip_actions_used, 0, 10)) * 0.20 +
    (normalize(current_streak, 7, 60) * 0.25) +
    (normalize(best_streak, 7, 100) * 0.15) +
    (session_consistency * 0.20)  # Regularidad de sesiones
)
```

### Función normalize

```
def normalize(value: float, min_val: float, max_val: float) -> float:
    """Normaliza valor a rango 0-1"""
    if value <= min_val:
        return 0.0
    if value >= max_val:
        return 1.0
    return (value - min_val) / (max_val - min_val)
```

### Paso 2: Determinar arquetipo dominante

```
def detect_archetype(user_id: int) -> ArchetypeResult:
    signals = get_behavior_signals(user_id)
    
    # Mínimo de interacciones para detectar
    if signals.total_interactions < MIN_INTERACTIONS_FOR_DETECTION:  # 15-20
        return ArchetypeResult(
            archetype=None,
            confidence=0,
            reason="insufficient_data"
        )
    
    scores = {
        "EXPLORER": calculate_explorer_score(signals),
        "DIRECT": calculate_direct_score(signals),
        "ROMANTIC": calculate_romantic_score(signals),
        "ANALYTICAL": calculate_analytical_score(signals),
        "PERSISTENT": calculate_persistent_score(signals),
        "PATIENT": calculate_patient_score(signals)
    }
    
    # Ordenar por score
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_archetype = sorted_scores[0][0]
    top_score = sorted_scores[0][1]
    second_score = sorted_scores[1][1]
    
    # Calcular confianza (qué tan dominante es)
    confidence = top_score - second_score + (top_score * 0.3)
    confidence = min(confidence, 1.0)
    
    # Umbral mínimo de confianza
    if confidence < MIN_CONFIDENCE_THRESHOLD:  # 0.3
        return ArchetypeResult(
            archetype=None,
            confidence=confidence,
            scores=scores,
            reason="low_confidence"
        )
    
    return ArchetypeResult(
        archetype=top_archetype,
        confidence=confidence,
        scores=scores,
        reason="detected"
    )
```

### Paso 3: Cuándo re-evaluar

```
Re-evaluar arquetipo cuando:
- Han pasado 7+ días desde última detección
- Usuario ha tenido 50+ interacciones nuevas desde detección
- Usuario solicita re-evaluación (¿feature?)
- Confianza actual < 0.5 y hay nuevos datos significativos
```

## Métodos del servicio

```
ArchetypeDetectionService:

    detect_archetype(user_id: int) -> ArchetypeResult
        Ejecuta detección completa.
    
    get_archetype(user_id: int) -> str | None
        Retorna arquetipo actual (de BD, no recalcula).
    
    get_archetype_scores(user_id: int) -> Dict[str, float]
        Retorna scores de todos los arquetipos.
    
    should_reevaluate(user_id: int) -> bool
        Determina si es momento de re-evaluar.
    
    force_reevaluation(user_id: int) -> ArchetypeResult
        Fuerza re-evaluación ignorando caché.
    
    get_archetype_insights(user_id: int) -> ArchetypeInsights
        Retorna información detallada para UI:
        - Arquetipo actual
        - Confianza
        - Top 3 arquetipos con scores
        - Comportamientos que más influyen
```

---

# F3.4: PALABRAS EMOCIONALES

## Lista de palabras para detectar contenido emocional

```python
EMOTIONAL_WORDS = {
    # Positivas intensas
    "amor", "amo", "quiero", "adoro", "deseo", "anhelo", "sueño",
    "pasión", "corazón", "alma", "sentir", "siento",
    
    # Conexión
    "conexión", "conectar", "especial", "único", "única", "íntimo",
    "cercano", "profundo", "verdadero", "auténtico", "genuino",
    
    # Vulnerabilidad
    "miedo", "temo", "vulnerable", "abierto", "honesto", "sincero",
    "confiar", "confianza", "entrega", "rendirme",
    
    # Intensidad
    "intenso", "increíble", "maravilloso", "hermoso", "perfecto",
    "mágico", "extraordinario", "inolvidable",
    
    # Relacionales
    "nosotros", "juntos", "compartir", "unir", "pertenecer",
    "acompañar", "entender", "comprender"
}

EMOTIONAL_PHRASES = [
    "me haces sentir",
    "no puedo dejar de",
    "significa mucho",
    "desde el corazón",
    "en el fondo",
    "lo que siento"
]
```

## Función de detección

```
def has_emotional_content(text: str) -> tuple[bool, int]:
    """
    Retorna (tiene_contenido_emocional, cantidad_palabras_emocionales)
    """
    text_lower = text.lower()
    count = 0
    
    for word in EMOTIONAL_WORDS:
        if word in text_lower:
            count += 1
    
    for phrase in EMOTIONAL_PHRASES:
        if phrase in text_lower:
            count += 2  # Frases pesan más
    
    return (count > 0, count)
```

---

# F3.5: INTEGRACIÓN CON HANDLERS

## Dónde agregar tracking

### En cada handler de callback/mensaje

```
# Pseudocódigo - agregar al inicio de cada handler relevante

async def some_handler(message/callback, ...):
    user_id = message.from_user.id
    
    # Track la interacción
    await behavior_tracking.track_interaction(
        user_id=user_id,
        interaction_type=InteractionType.BUTTON_CLICK,  # o el que corresponda
        metadata={
            "button_id": callback.data,
            "time_to_click": calculate_time_since_last_message(),
            # ... otros datos relevantes
        }
    )
    
    # Resto del handler...
```

### Handlers prioritarios para tracking

1. **start.py** - SESSION_START, RETURN_AFTER_INACTIVITY
2. **dynamic_menu.py** - MENU_NAVIGATION, BUTTON_CLICK
3. **story.py** - CONTENT_VIEW, DECISION_MADE
4. **decisions.py** - DECISION_MADE con tiempo
5. **shop.py** - BUTTON_CLICK, acciones de compra
6. **missions.py** - CONTENT_VIEW, completion
7. **Cualquier handler con input de texto** - TEXT_RESPONSE

### Middleware de tracking (alternativa)

Crear middleware que trackea automáticamente interacciones básicas:

```
class BehaviorTrackingMiddleware:
    async def __call__(self, handler, event, data):
        user_id = event.from_user.id
        
        # Pre-handler: registrar inicio
        start_time = time.time()
        
        # Ejecutar handler
        result = await handler(event, data)
        
        # Post-handler: registrar interacción básica
        elapsed = time.time() - start_time
        
        interaction_type = self._determine_type(event)
        await self.tracking_service.track_interaction(
            user_id=user_id,
            interaction_type=interaction_type,
            metadata={"processing_time": elapsed, ...}
        )
        
        return result
```

---

# F3.6: NOTIFICACIÓN DE ARQUETIPO DETECTADO

## Cuándo notificar

- Primera vez que se detecta arquetipo (después de suficientes interacciones)
- Cuando cambia el arquetipo (re-evaluación dio resultado diferente)

**NO notificar:**
- En cada re-evaluación que confirma el mismo arquetipo
- Si la confianza bajó pero sigue siendo el mismo

## Mensajes de Lucien por arquetipo

### EXPLORER detectado

```
"He observado algo en usted.

Su curiosidad es... insaciable. Revisa cada rincón, busca lo que otros ignoran, no deja piedra sin voltear.

Diana nota a quienes realmente miran. Usted no solo mira - explora.

A partir de ahora, el sistema reconoce su naturaleza exploradora. Habrá contenido que solo ojos como los suyos podrán encontrar."
```

### DIRECT detectado

```
"He llegado a una conclusión sobre usted.

No pierde tiempo en ceremonias. Sabe lo que quiere y va por ello. En un mundo de rodeos infinitos, su claridad es... refrescante.

Diana aprecia la eficiencia. Yo la respeto.

El sistema ahora reconoce su naturaleza directa. Las cosas serán más... concisas para usted."
```

### ROMANTIC detectado

```
"Hay algo que debo decirle.

He notado cómo escribe. Las palabras que elige. La emoción que impregna cada respuesta.

Busca algo más que contenido. Busca conexión. Eso es raro. Y peligrosamente hermoso.

Diana tiene debilidad por las almas románticas. Quizás porque reconoce algo de sí misma en ellas."
```

### ANALYTICAL detectado

```
"Debo reconocer algo sobre usted.

Su mente funciona con precisión admirable. Analiza, cuestiona, estructura. No acepta nada sin examinarlo primero.

Honestamente, es irritante. Pero también... respetable.

El sistema ahora reconoce su naturaleza analítica. Los desafíos que encontrará serán dignos de su intelecto."
```

### PERSISTENT detectado

```
"He notado un patrón en usted.

Vuelve. Siempre vuelve. Donde otros abandonan, usted persiste. Donde otros se rinden, usted reintenta.

Hay algo casi... conmovedor en esa tenacidad.

Diana respeta a quienes no se dan por vencidos. El sistema ahora reconoce su persistencia. Será recompensada."
```

### PATIENT detectado

```
"Debo hacerle una observación.

Se toma su tiempo. Procesa. No se apresura por agradar ni presiona por resultados inmediatos.

La paciencia es la virtud más subestimada. Usted la encarna.

El sistema ahora reconoce su naturaleza paciente. Las recompensas para quienes saben esperar son... especiales."
```

## Badge de arquetipo

Al detectar arquetipo, otorgar badge correspondiente:

| Arquetipo | Badge | Emoji |
|-----------|-------|-------|
| EXPLORER | "El Explorador" | 🔍 |
| DIRECT | "El Directo" | ⚡ |
| ROMANTIC | "El Romántico" | 💝 |
| ANALYTICAL | "El Analítico" | 🧠 |
| PERSISTENT | "El Persistente" | 🔄 |
| PATIENT | "El Paciente" | ⏳ |

---

# F3.7: ADAPTACIÓN DE CONTENIDO POR ARQUETIPO

## Variaciones de mensajes

Para mensajes clave, tener variaciones según arquetipo:

### Ejemplo: Mensaje de misión diaria disponible

**Base (sin arquetipo):**
```
"Hay un encargo pendiente para hoy."
```

**Para EXPLORER:**
```
"Hay un encargo pendiente. Pero quizás encuentre algo más mientras lo completa..."
```

**Para DIRECT:**
```
"Encargo del día disponible. Una acción, una recompensa."
```

**Para ROMANTIC:**
```
"Diana ha pensado en algo para usted hoy. Un pequeño encargo que la haría... sonreír."
```

**Para ANALYTICAL:**
```
"Protocolo diario activado. Parámetros: {detalles}. Recompensa calculada: {X} Favores."
```

**Para PERSISTENT:**
```
"Otro día, otra oportunidad de demostrar su constancia. El encargo espera."
```

**Para PATIENT:**
```
"El encargo de hoy está disponible. Como siempre, tómese el tiempo que necesite."
```

## Función helper para mensajes adaptados

```
def get_adapted_message(
    base_message_key: str,
    user_archetype: str | None,
    **format_args
) -> str:
    """
    Obtiene mensaje adaptado al arquetipo.
    Si no hay arquetipo o no hay variación, usa mensaje base.
    """
    if user_archetype:
        archetype_key = f"{base_message_key}_{user_archetype}"
        if has_message(archetype_key):
            return get_message(archetype_key).format(**format_args)
    
    return get_message(base_message_key).format(**format_args)
```

## Mensajes prioritarios para adaptar

1. Bienvenida de regreso
2. Notificación de misión
3. Confirmación de compra
4. Invitación a VIP (conversión)
5. Mensajes de la narrativa
6. Mensajes de racha/hitos

---

# F3.8: IMPACTO EN CONVERSIÓN

## Triggers de conversión por arquetipo

| Arquetipo | Trigger óptimo | Mensaje de conversión |
|-----------|---------------|----------------------|
| EXPLORER | Mostrar que hay contenido VIP que no puede ver | "Hay 47 archivos en el Diván que sus ojos de explorador aún no han visto..." |
| DIRECT | Oferta clara y directa | "VIP: Acceso completo. Sin rodeos. {precio}." |
| ROMANTIC | Apelar a conexión más profunda | "Diana reserva sus momentos más íntimos para el Diván. Momentos que solo comparte con quienes realmente quieren conocerla..." |
| ANALYTICAL | Mostrar valor objetivo | "El Diván contiene {X} publicaciones, {Y} exclusivos mensuales. ROI de contenido: {cálculo}." |
| PERSISTENT | Reconocer su dedicación | "Ha demostrado compromiso inusual. El siguiente paso natural es el Diván. Su persistencia merece ese acceso." |
| PATIENT | Indicar que es el momento | "Ha esperado. Ha observado. Ha construido mérito. El Diván está listo cuando usted lo esté." |

## Timing de oferta por arquetipo

| Arquetipo | Momento óptimo |
|-----------|---------------|
| EXPLORER | Cuando encuentra easter egg que requiere VIP |
| DIRECT | Después de completar acción, sin dilación |
| ROMANTIC | Después de fragmento narrativo emocional |
| ANALYTICAL | Después de evaluación con buen score |
| PERSISTENT | Cuando regresa después de inactividad |
| PATIENT | Después de completar racha de 7+ días |

---

# F3.9: COMANDOS DE ADMIN

## Ver arquetipo de usuario

```
/admin_archetype <user_id>

Muestra:
- Arquetipo actual
- Confianza
- Scores de todos los arquetipos
- Top 3 señales que más influyen
- Fecha de detección
- Interacciones desde detección
```

## Estadísticas de arquetipos

```
/admin_archetype_stats

Muestra:
- Distribución de arquetipos (% de usuarios)
- Arquetipo con mejor conversión a VIP
- Arquetipo con mejor retención
- Arquetipos por nivel
- Usuarios sin arquetipo definido
```

## Forzar re-evaluación

```
/admin_archetype_refresh <user_id>

Fuerza re-evaluación del arquetipo para debugging.
```

---

# CRITERIOS DE ACEPTACIÓN FASE 3

## F3.1 Modelo de datos
- [ ] Tabla UserBehaviorSignals creada con todos los campos
- [ ] Campos de arquetipo agregados a User
- [ ] Índices apropiados para queries frecuentes

## F3.2 Tracking
- [ ] Service de tracking creado
- [ ] Todas las interacciones relevantes se registran
- [ ] Métricas derivadas se calculan correctamente

## F3.3 Detección
- [ ] Algoritmo de scoring implementado para 6 arquetipos
- [ ] Detección funciona con umbral mínimo de interacciones
- [ ] Re-evaluación se dispara correctamente
- [ ] Scores se guardan en BD

## F3.4 Palabras emocionales
- [ ] Lista de palabras implementada
- [ ] Detección funciona en respuestas de texto

## F3.5 Integración handlers
- [ ] Tracking integrado en handlers principales
- [ ] No afecta performance significativamente

## F3.6 Notificación
- [ ] Usuario recibe mensaje al detectarse arquetipo
- [ ] Badge de arquetipo se otorga
- [ ] Mensaje es el correcto para cada arquetipo

## F3.7 Adaptación
- [ ] Al menos 5 mensajes tienen variaciones por arquetipo
- [ ] Helper de mensajes adaptados funciona

## F3.8 Conversión
- [ ] Triggers de conversión diferenciados por arquetipo
- [ ] Mensajes de conversión personalizados

## F3.9 Admin
- [ ] Comandos de admin funcionan
- [ ] Estadísticas de distribución disponibles

---

# CONFIGURACIÓN RECOMENDADA

```
# Detección
MIN_INTERACTIONS_FOR_DETECTION = 20
MIN_CONFIDENCE_THRESHOLD = 0.35
REEVALUATION_DAYS = 7
REEVALUATION_INTERACTIONS = 50

# Pesos de scoring (ajustables)
# Definir en tabla de configuración para poder ajustar sin deploy
```

---

# NOTAS DE IMPLEMENTACIÓN

1. **Performance:** El tracking debe ser no-bloqueante (fire-and-forget o queue)
2. **Privacy:** No guardar contenido de mensajes, solo métricas
3. **Gradual rollout:** Empezar trackeando sin detectar, luego activar detección
4. **A/B testing:** Posibilidad de comparar conversión con/sin personalización

---

# ARCHIVOS DE REFERENCIA

- Fase 0: Enums de arquetipos definidos
- Fase 1: Mensajes de Lucien base
- Fase 2: Sistema de Besitos para métricas de actividad
- `lucien_character_bible.md` - Cómo Lucien percibe cada arquetipo

---
