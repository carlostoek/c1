# FASE 3: ARQUETIPOS - MODELO DE TRACKING CORREGIDO

## Problema Identificado

El algoritmo original en `fase-3.md` asume un chatbot con mensajes de texto libre (TEXT_RESPONSE), pero el flujo real del bot es principalmente con **botones, callbacks y navegación**. Esto causa que varias métricas clave sean siempre nulas o inválidas.

## Métricas Inválidas (Dependen de TEXT_RESPONSE)

| Métrica | Problema | Impacto |
|---------|----------|---------|
| `avg_response_length` | No hay respuestas de texto | ROMANTIC, DIRECT afectados |
| `emotional_words_count` | No se puede analizar texto | ROMANTIC completamente invalidado |
| `question_count` | No hay preguntas en texto | ANALYTICAL parcialmente afectado |
| `personal_questions_about_diana` | No hay interacción con texto | ROMANTIC afectado |
| `long_responses_count` | No hay respuestas largas | ROMANTIC afectado |
| `structured_responses` | No hay formato de texto | ANALYTICAL parcialmente afectado |
| `avg_response_time` | Tiempo para "responder" mensaje | DIRECT, PATIENT afectados |

## Solución: Nuevo Modelo de Tracking Basado en Interacciones Reales

---

# F3.1: MODELO DE DATOS CORREGIDO

## UserBehaviorSignals - Versión Sin Chat

```python
UserBehaviorSignals:
    user_id: int (FK, unique)

    # ========================================
    # 1. MÉTRICAS DE EXPLORACIÓN (EXPLORER)
    # ========================================
    content_sections_visited: int          # Secciones únicas visitadas
    content_completion_rate: float         # % de contenido disponible visto
    easter_eggs_found: int                 # Easter eggs encontrados
    avg_time_on_content: float             # Segundos promedio en contenido
    revisits_old_content: int              # Veces que revisó contenido antiguo (>7 días)
    unique_content_per_session: float      # Contenido único promedio por sesión
    explore_depth: int                     # Profundidad máxima de navegación

    # ========================================
    # 2. MÉTRICAS DE VELOCIDAD/EFICIENCIA (DIRECT)
    # ========================================
    avg_time_to_click: float               # Segundos desde ver botón hasta click
    avg_decision_time: float               # Segundos para tomar decisión narrativa
    actions_per_session: float             # Acciones promedio por sesión
    quick_actions_count: int               # Clicks < 3 segundos
    direct_navigation_ratio: float         # % de acciones que van directo al objetivo
    skips_explanation: int                 # Veces que saltó explicación (si existe opción)

    # ========================================
    # 3. MÉTRICAS EMOCIONALES (ROMANTIC) - DERIVADAS
    # ========================================
    emotional_content_views: int          # Veces que vio contenido emocional/personal
    personal_stories_accessed: int         # Veces que accedió a historias personales de Diana
    likes_vs_saves_ratio: float            # Ratio de reacciones emocionales vs acciones frías
    repeat_emotional_visits: int          # Veces que revisó contenido emotivo
    diana_mnemonics_interactions: int      # Interacciones con mementos/referencias a Diana

    # ========================================
    # 4. MÉTRICAS DE ANÁLISIS (ANALYTICAL)
    # ========================================
    evaluation_scores_avg: float           # Promedio en evaluaciones (si existen)
    evaluation_completion_rate: float      # % de evaluaciones completadas
    info_requests: int                     # Veces que pidió "más info" (si existe botón)
    systematic_exploration: int            # Visitó secciones en orden secuencial
    details_viewed: int                    # Veces que expandió detalles/leyendas
    puzzle_completion_time: float          # Tiempo promedio en resolver puzzles

    # ========================================
    # 5. MÉTRICAS DE PERSISTENCIA (PERSISTENT)
    # ========================================
    return_after_inactivity: int           # Veces que volvió después de 7+ días
    retry_failed_actions: int              # Reintentos de acciones fallidas
    incomplete_flows_completed: int        # Flujos abandonados y luego completados
    account_age_days: int                  # Días desde primera interacción
    return_rate: float                     # % de veces que regresa después de inactividad
    streak_restarts: int                   # Veces que reinició racha perdida

    # ========================================
    # 6. MÉTRICAS DE PACIENCIA (PATIENT)
    # ========================================
    skip_actions_used: int                 # Veces que usó "saltar" o "skip"
    current_streak: int                    # Racha actual (de F2.3)
    best_streak: int                       # Mejor racha histórica
    avg_session_duration: float            # Duración promedio de sesión
    session_consistency: float             # Regularidad de sesiones (desviación estándar)
    slow_decision_count: int               # Decisiones tomadas > 30 segundos

    # ========================================
    # 7. MÉTRICAS GENERALES
    # ========================================
    total_interactions: int                # Total de interacciones registradas
    total_sessions: int                    # Total de sesiones
    first_interaction_at: datetime
    last_interaction_at: datetime
    last_updated_at: datetime
```

---

# F3.2: SERVICIO DE TRACKING CORREGIDO

## InteractionType Enum - Actualizado

```python
InteractionType enum:
    # Navegación
    BUTTON_CLICK                    # Click en botón inline
    MENU_NAVIGATION                 # Navegación entre menús
    BACK_CLICKED                    # Click en "volver"

    # Contenido
    CONTENT_VIEW                    # Vio contenido
    CONTENT_COMPLETE                # Completó contenido (llegó al final)
    CONTENT_REVISIT                 # Revisitó contenido antiguo
    EASTER_EGG_FOUND                # Encontró easter egg
    DETAILS_EXPANDED                # Expandió detalles/leyenda

    # Decisiones
    DECISION_MADE                   # Tomó decisión narrativa
    CHOICE_SELECTED                 # Selección en opciones

    # Evaluaciones/Desafíos
    QUIZ_START                      # Inició evaluación
    QUIZ_ANSWER                     # Respondió pregunta
    QUIZ_COMPLETE                   # Completó evaluación
    PUZZLE_SOLVED                   # Resolver puzzle/código

    # Sesión
    SESSION_START                   # Inicio de sesión
    SESSION_END                     # Fin de sesión (inactividad)
    RETURN_AFTER_INACTIVITY         # Regresó después de X días

    # Acciones específicas
    SKIP_ACTION                     # Usó "saltar"
    RETRY_ACTION                    # Reintentó acción fallida
    INFO_REQUEST                    # Pidió más información

    # Contenido específico
    EMOTIONAL_VIEW                  # Vio contenido emocional/personal
    PERSONAL_STORY_VIEW             # Vio historia personal de Diana
```

## Métodos de Tracking

### track_button_click

```python
track_button_click(
    user_id: int,
    button_id: str,
    context: str,           # Dónde estaba el botón
    time_to_click: float,   # Segundos desde que se mostró
    is_exploration: bool,    # Si es navegación exploratoria
    is_direct_action: bool   # Si es acción directa al objetivo
)
```

### track_content_interaction

```python
track_content_interaction(
    user_id: int,
    content_id: str,
    content_type: str,      # "story", "profile", "shop", etc.
    interaction_type: str,  # "view", "complete", "revisit", "easter_egg"
    time_spent: float,      # Segundos en el contenido
    completion: float,      # 0-1, qué tanto completó
    is_emotional: bool,     # Si es contenido emocional/personal
    is_personal: bool       # Si es sobre Diana personalmente
)
```

### track_decision

```python
track_decision(
    user_id: int,
    decision_id: str,
    time_to_decide: float,
    options_available: int,
    decision_type: str,     # "narrative", "choice", "path"
    is_systematic: bool,    # Si sigue patrón lógico
    is_emotional: bool      # Si la elección fue emocional
)
```

### track_session

```python
track_session(
    user_id: int,
    session_type: str,      # "start", "end", "return"
    duration: float,        # Duración de sesión
    actions_count: int,     # Cantidad de acciones
    navigation_depth: int   # Profundidad de navegación alcanzada
)
```

---

# F3.3: ALGORITMO DE DETECCIÓN CORREGIDO

## EXPLORER_SCORE (Sin cambios significativos)

```python
EXPLORER_SCORE = (
    (normalize(content_completion_rate, 0.1, 0.8) * 0.25) +
    (normalize(easter_eggs_found, 0, 10) * 0.20) +
    (normalize(avg_time_on_content, 30, 180) * 0.20) +
    (normalize(revisits_old_content, 0, 20) * 0.15) +
    (normalize(unique_content_per_session, 2, 8) * 0.20)
)
```

**Justificación:** EXPLORER sigue siendo detectable por patrones de exploración de contenido, no necesita mensajes de texto.

---

## DIRECT_SCORE (Corregido - Sin avg_response_length)

```python
DIRECT_SCORE = (
    (normalize(avg_time_to_click, 1, 10) * 0.30) +              # Más peso a velocidad de click
    (1 - normalize(avg_decision_time, 5, 45) * 0.25) +          # Tiempo de decisión
    (normalize(actions_per_session, 3, 15) * 0.20) +            # Muchas acciones rápidas
    (normalize(direct_navigation_ratio, 0.6, 1.0) * 0.15) +     # Va directo al objetivo
    (1 - normalize(avg_session_duration, 60, 600) * 0.10)       # Sesiones cortas y eficientes
)
```

**Cambios:**
- Eliminado `avg_response_length` (no existe)
- Aumentado peso de `avg_time_to_click` (30%)
- Añadido `direct_navigation_ratio` (qué tanto va directo al objetivo)

---

## ROMANTIC_SCORE (Completamente Rediseñado)

```python
ROMANTIC_SCORE = (
    (normalize(emotional_content_views, 5, 30) * 0.30) +       # Busca contenido emotivo
    (normalize(personal_stories_accessed, 2, 15) * 0.25) +     # Interés en Diana persona
    (normalize(repeat_emotional_visits, 3, 20) * 0.20) +       # Revisa contenido emotivo
    (normalize(diana_mnemonics_interactions, 1, 10) * 0.15) +   # Interactúa con mementos
    (normalize(likes_vs_saves_ratio, 0.3, 0.8) * 0.10)         # Prefiere lo emotivo vs funcional
)
```

**Lógica del nuevo ROMANTIC:**
- En lugar de analizar palabras emocionales, trackea **qué tipo de contenido consume**
- Si busca contenido emocional/personal de Diana repetidamente → ROMANTIC
- Si interactúa con mementos, historias personales → ROMANTIC
- `likes_vs_saves_ratio`: Preferencia por contenido emotivo (likes, corazones) vs funcional (guardar, compartir)

**Cómo detectar `is_emotional` en contenido:**
```python
# Tags en contenido/narrativa
EMOTIONAL_CONTENT_TAGS = [
    "personal", "intimate", "vulnerable", "emotional",
    "diary", "letter", "confession", "memory"
]

# El contenido se marca con tags al crearse
story.tags = ["emotional", "personal", "diana_story"]
```

---

## ANALYTICAL_SCORE (Corregido - Sin question_count)

```python
ANALYTICAL_SCORE = (
    (normalize(evaluation_scores_avg, 60, 95) * 0.30) +        # Buen score en evaluaciones
    (normalize(evaluation_completion_rate, 0.7, 1.0) * 0.20) + # Completa evaluaciones
    (normalize(systematic_exploration, 0.6, 0.95) * 0.20) +  # Exploración ordenada
    (normalize(details_viewed, 5, 30) * 0.15) +               # Expande detalles
    (normalize(info_requests, 2, 15) * 0.15)                  # Pide más info
)
```

**Cambios:**
- Eliminado `question_count` (no hay preguntas en texto)
- Eliminado `structured_responses` (no hay respuestas)
- Añadido `systematic_exploration` (navega en orden lógico)
- Añadido `info_requests` (usa botones de "más info")

**Cómo detectar `systematic_exploration`:**
```python
# Analizar secuencia de navegación
# Si el usuario navega A → B → C → D en orden sistemático
# vs navega aleatoriamente A → C → A → D → B

def calculate_systematic_ratio(user_sequence: List[str]) -> float:
    """
    Calcula qué tan sistemática es la navegación.
    1.0 = completamente secuencial
    0.0 = completamente aleatoria
    """
    expected_order = ["A", "B", "C", "D"]  # Orden lógico del menú

    # Contar cuántas veces siguió el orden esperado
    sequential_count = 0
    for i in range(len(user_sequence) - 1):
        current_idx = expected_order.index(user_sequence[i])
        next_idx = expected_order.index(user_sequence[i + 1])
        if next_idx == current_idx + 1:
            sequential_count += 1

    return sequential_count / (len(user_sequence) - 1) if len(user_sequence) > 1 else 0
```

---

## PERSISTENT_SCORE (Sin cambios)

```python
PERSISTENT_SCORE = (
    (normalize(return_after_inactivity, 0, 5) * 0.30) +
    (normalize(retry_failed_actions, 0, 10) * 0.25) +
    (normalize(incomplete_flows_completed, 0, 5) * 0.25) +
    (normalize(streak_restarts, 0, 5) * 0.10) +
    (normalize(account_age_days, 30, 365) * 0.10)
)
```

**Justificación:** PERSISTENT se basa en patrones de retorno y re-intento, no necesita mensajes de texto.

---

## PATIENT_SCORE (Corregido - Sin avg_response_time)

```python
PATIENT_SCORE = (
    (normalize(slow_decision_count, 3, 15) * 0.25) +           # Decisiones lentas
    (1 - normalize(skip_actions_used, 0, 5) * 0.20) +          # Raramente salta
    (normalize(current_streak, 7, 60) * 0.25) +                # Racha actual
    (normalize(best_streak, 14, 100) * 0.15) +                # Mejor racha
    (normalize(session_consistency, 0.7, 0.95) * 0.15)        # Regularidad de sesiones
)
```

**Cambios:**
- Eliminado `avg_response_time` (no hay respuesta a mensajes)
- Añadido `slow_decision_count` (decisiones narrativas >30 seg)

**Cómo calcular `session_consistency`:**
```python
def calculate_session_consistency(session_times: List[datetime]) -> float:
    """
    Calcula qué tan consistente es la actividad del usuario.
    1.0 = actividad perfectamente regular (cada día a la misma hora)
    0.0 = completamente irregular
    """
    if len(session_times) < 7:
        return 0.0

    # Convertir a horas del día (0-23)
    hours = [t.hour for t in session_times]

    # Calcular desviación estándar
    import statistics
    if len(hours) > 1:
        std_dev = statistics.stdev(hours)
        # Convertir a consistencia (menor std = más consistente)
        consistency = max(0, 1 - (std_dev / 12))  # 12 horas = 0 consistencia
        return consistency

    return 0.0
```

---

# F3.4: DETECCIÓN DE CONTENIDO EMOCIONAL

## Sistema de Tags para Contenido

En lugar de analizar texto, el contenido se marca con tags al crearse:

```python
ContentTags:
    # Emocional/Personal
    "emotional"         # Contenido emotivo
    "personal"          # Sobre Diana personalmente
    "vulnerable"        # Diana mostrando vulnerabilidad
    "intimate"          # Contenido íntimo

    # Funcional
    "informational"     # Informativo
    "instructional"     # Instrucciones
    "transactional"     # Transacciones (tienda, etc.)

    # Narrativo
    "story"             # Historia narrativa
    "lore"              # Lore del universo
    "character"         # Sobre personajes

    # Estructura
    "explorable"        # Tiene secrets/easter eggs
    "choice"            # Requiere decisión
    "evaluation"        # Es evaluación/cuestionario
```

## Ejemplo de marcado de contenido

```python
# Al crear fragmento narrativo
narrative_fragment = {
    "id": "diana_diary_001",
    "tags": ["emotional", "personal", "vulnerable", "story"],
    "content": "...",
    "is_diana_personal": True,
    "emotional_intensity": 0.8  # 0-1
}

# Al crear página de perfil
profile_page = {
    "id": "profile_diana",
    "tags": ["informational", "character"],
    "emotional_intensity": 0.3
}
```

## Detección automática

```python
def track_content_view(user_id: int, content: Content):
    """Trackea vista de contenido y actualiza métricas emocionales."""

    # Actualizar conteos según tags
    if "emotional" in content.tags:
        signals.emotional_content_views += 1

    if "personal" in content.tags or content.get("is_diana_personal"):
        signals.personal_stories_accessed += 1

    # Detectar revisita de contenido emotivo
    if "emotional" in content.tags and was_visited_before(user_id, content.id):
        signals.repeat_emotional_visits += 1

    # Actualizar intensity score promedio
    if content.get("emotional_intensity"):
        update_emotional_intensity_average(user_id, content["emotional_intensity"])
```

---

# F3.5: INTEGRACIÓN CON HANDLERS

## Puntos de tracking prioritarios

### 1. Menús y Navegación

```python
# bot/handlers/navegación.py

@router.callback_query(F.data.startswith("menu:"))
async def menu_navigation(callback: CallbackQuery):
    user_id = callback.from_user.id

    # Calcular time_to_click
    time_to_click = calculate_time_since_last_message(callback.message)

    # Determinar si es exploración o acción directa
    is_exploration = is_exploratory_navigation(callback.data)
    is_direct_action = is_direct_action_navigation(callback.data)

    await behavior_tracking.track_button_click(
        user_id=user_id,
        button_id=callback.data,
        context="menu_navigation",
        time_to_click=time_to_click,
        is_exploration=is_exploration,
        is_direct_action=is_direct_action
    )
```

### 2. Contenido Narrativo

```python
# bot/handlers/story.py

@router.callback_query(F.data.startswith("story:"))
async def story_view(callback: CallbackQuery):
    user_id = callback.from_user.id
    story_id = extract_story_id(callback.data)

    story = await get_story(story_id)

    # Marcar inicio de timer
    start_time = time.time()

    # ... mostrar historia ...

    # Al salir/continuar
    time_spent = time.time() - start_time

    await behavior_tracking.track_content_interaction(
        user_id=user_id,
        content_id=story_id,
        content_type="story",
        interaction_type="view",
        time_spent=time_spent,
        completion=0.0,  # Se actualiza al completar
        is_emotional="emotional" in story.tags,
        is_personal="personal" in story.tags
    )
```

### 3. Decisiones Narrativas

```python
# bot/handlers/decisions.py

@router.callback_query(F.data.startswith("decision:"))
async def decision_made(callback: CallbackQuery):
    user_id = callback.from_user.id

    # Calcular tiempo de decisión
    time_to_decide = calculate_time_since_options_shown(user_id)

    # Determinar tipo de decisión
    decision_data = parse_decision_callback(callback.data)

    # Detectar si es elección sistemática (analiza secuencias previas)
    is_systematic = await check_if_systematic_choice(user_id, decision_data)

    # Detectar si es elección emocional (basada en tags de opciones)
    is_emotional = decision_data.get("is_emotional_choice", False)

    await behavior_tracking.track_decision(
        user_id=user_id,
        decision_id=decision_data["decision_id"],
        time_to_decide=time_to_decide,
        options_available=decision_data["options_count"],
        decision_type="narrative",
        is_systematic=is_systematic,
        is_emotional=is_emotional
    )
```

### 4. Easter Eggs

```python
# bot/handlers/easter_eggs.py

@router.callback_query(F.data == "easter_egg:secret_001")
async def easter_egg_found(callback: CallbackQuery):
    user_id = callback.from_user.id

    await behavior_tracking.track_content_interaction(
        user_id=user_id,
        content_id="easter_egg_001",
        content_type="easter_egg",
        interaction_type="EASTER_EGG_FOUND",
        time_spent=0,
        completion=1.0,
        is_emotional=False,
        is_personal=False
    )

    # ... dar recompensa ...
```

### 5. Skip/Saltar

```python
# bot/handlers/common.py

@router.callback_query(F.data.endswith(":skip"))
async def skip_action(callback: CallbackQuery):
    user_id = callback.from_user.id

    await behavior_tracking.track_interaction(
        user_id=user_id,
        interaction_type=InteractionType.SKIP_ACTION,
        metadata={"skipped_content": callback.data.split(":")[0]}
    )
```

---

# F3.6: CONFIGURACIÓN

```python
# bot/gamification/config/archetype_detection.py

class ArchetypeDetectionConfig:
    """Configuración del sistema de detección de arquetipos."""

    # Umbrales
    MIN_INTERACTIONS_FOR_DETECTION = 25      # Aumentado de 20
    MIN_INTERACTIONS_FOR_REEVALUATION = 50   # Para re-evaluar
    MIN_CONFIDENCE_THRESHOLD = 0.35

    # Timing
    REEVALUATION_DAYS = 7
    REEVALUATION_INTERACTIONS = 50

    # Pesos (ajustables sin deploy)
    EXPLORER_WEIGHTS = {
        "completion_rate": 0.25,
        "easter_eggs": 0.20,
        "time_on_content": 0.20,
        "revisits": 0.15,
        "unique_content": 0.20
    }

    DIRECT_WEIGHTS = {
        "time_to_click": 0.30,
        "decision_time": 0.25,
        "actions_per_session": 0.20,
        "direct_nav": 0.15,
        "session_duration": 0.10
    }

    ROMANTIC_WEIGHTS = {
        "emotional_views": 0.30,
        "personal_stories": 0.25,
        "repeat_visits": 0.20,
        "mnemonics": 0.15,
        "likes_ratio": 0.10
    }

    ANALYTICAL_WEIGHTS = {
        "quiz_scores": 0.30,
        "quiz_completion": 0.20,
        "systematic": 0.20,
        "details": 0.15,
        "info_requests": 0.15
    }

    PERSISTENT_WEIGHTS = {
        "returns": 0.30,
        "retries": 0.25,
        "completed_flows": 0.25,
        "streak_restarts": 0.10,
        "account_age": 0.10
    }

    PATIENT_WEIGHTS = {
        "slow_decisions": 0.25,
        "no_skips": 0.20,
        "current_streak": 0.25,
        "best_streak": 0.15,
        "consistency": 0.15
    }
```

---

# RESUMEN DE CAMBIOS

## Métricas Eliminadas (Dependían de TEXT_RESPONSE)

| Métrica | Arquetipo afectado | Solución |
|---------|-------------------|----------|
| avg_response_length | ROMANTIC, DIRECT | Eliminar, usar otros indicadores |
| avg_response_time | PATIENT, DIRECT | Usar avg_time_to_click, avg_decision_time |
| emotional_words_count | ROMANTIC | Usar emotional_content_views (tags) |
| question_count | ANALYTICAL | Usar info_requests (botones "más info") |
| long_responses_count | ROMANTIC | Usar repeat_emotional_visits |
| personal_questions | ROMANTIC | Usar personal_stories_accessed |
| structured_responses | ANALYTICAL | Usar systematic_exploration |

## Nuevas Métricas Agregadas

| Métrica | Propósito | Arquetipo |
|---------|-----------|-----------|
| avg_time_to_click | Velocidad de interacción | DIRECT, PATIENT |
| direct_navigation_ratio | Eficiencia | DIRECT |
| emotional_content_views | Preferencia emotiva | ROMANTIC |
| personal_stories_accessed | Interés en Diana | ROMANTIC |
| repeat_emotional_visits | Reiteración emotiva | ROMANTIC |
| diana_mnemonics_interactions | Conexión personal | ROMANTIC |
| systematic_exploration | Orden lógico | ANALYTICAL |
| info_requests | Busca información | ANALYTICAL |
| details_viewed | Profundidad | ANALYTICAL |
| slow_decision_count | Tiempo en decidir | PATIENT |
| session_consistency | Regularidad | PATIENT |

## Cambios en Algoritmos

1. **EXPLORER**: Sin cambios significativos (ya usaba métricas de contenido)
2. **DIRECT**: Corregido para usar time_to_click en lugar de response_time
3. **ROMANTIC**: Completamente rediseñado (basado en tags de contenido)
4. **ANALYTICAL**: Parcialmente corregido (systematic exploration)
5. **PERSISTENT**: Sin cambios (ya usaba métricas de retorno)
6. **PATIENT**: Corregido para usar slow_decision_count

---

*Documento de corrección del algoritmo de detección de arquetipos para FASE 3*
