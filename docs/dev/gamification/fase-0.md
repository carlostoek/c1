# FASE 0: FUNDAMENTOS
## Requerimientos para Implementación - Bot "El Mayordomo del Diván"

---

## 🎯 CONTEXTO GENERAL

Este bot es para una creadora de contenido adulto llamada "Señorita Kinky" (Diana). El bot será la voz de "Lucien", un mayordomo elegante que actúa como guardián y evaluador de los usuarios que buscan acceder al contenido de Diana.

**Objetivos del bot:**
1. Conversión Free → VIP (canal de pago)
2. Upsell VIP → Premium (contenido exclusivo)
3. Engagement y retención de usuarios

**Tono de Lucien:**
- Siempre usa "usted" (formal)
- Elegante, sofisticado, ligeramente irónico
- Evaluador constante, protector de Diana
- Sarcasmo sutil, nunca vulgar: 
```

---

## 📋 ENTREGABLE F0.2: BIBLIOTECA DE MENSAJES DE LUCIEN V1

### Instrucción para Claude Code

```
TAREA: Crear biblioteca centralizada de mensajes con la voz de Lucien

ANTES DE ESCRIBIR CÓDIGO:
1. Revisa bot/handlers/user/ para ver cómo se envían mensajes actualmente
2. Revisa bot/utils/ para ver si existe algún sistema de mensajes/templates
3. Revisa bot/gamification/services/notification_service.py para ver templates existentes

OBJETIVO:
Crear un archivo centralizado con TODOS los mensajes que el bot enviará, escritos con la voz y personalidad de Lucien. Esto permitirá consistencia de tono en todo el bot.

UBICACIÓN DEL NUEVO ARCHIVO:
bot/utils/lucien_messages.py

CONTENIDO REQUERIDO:

Clase LucienMessages con las siguientes categorías:

1. ONBOARDING (bienvenida y primeros pasos):
   - WELCOME_FIRST: Mensaje de primera vez que un usuario interactúa
   - WELCOME_RETURNING: Mensaje para usuarios que regresan (con placeholder {days_away})
   - FIRST_ACTION_ACKNOWLEDGED: Después de su primera acción
   - PROTOCOL_EXPLANATION: Explicación de cómo funciona el sistema

2. Besitos (economía):
   - FAVOR_EARNED: "+{amount} Favor(es). Diana lo nota."
   - FAVOR_EARNED_MILESTONE: Cuando alcanza números redondos (10, 50, 100)
   - FAVOR_BALANCE: Mostrar balance actual con contexto
   - FAVOR_INSUFFICIENT: Cuando no tiene suficientes para algo
   - FAVOR_SPENT: Confirmación de gasto

3. NIVELES (progresión):
   - LEVEL_UP_BASE: Mensaje base de subida de nivel
   - LEVEL_UP_2 a LEVEL_UP_7: Mensajes específicos por cada nivel
   - LEVEL_PROGRESS: Mostrar progreso hacia siguiente nivel

4. ARQUETIPOS (reconocimiento):
   - ARCHETYPE_DETECTED_EXPLORER: Cuando se detecta arquetipo Explorador
   - ARCHETYPE_DETECTED_DIRECT: Cuando se detecta arquetipo Directo
   - ARCHETYPE_DETECTED_ROMANTIC: Cuando se detecta arquetipo Romántico
   - ARCHETYPE_DETECTED_ANALYTICAL: Cuando se detecta arquetipo Analítico
   - ARCHETYPE_DETECTED_PERSISTENT: Cuando se detecta arquetipo Persistente
   - ARCHETYPE_DETECTED_PATIENT: Cuando se detecta arquetipo Paciente

5. ERRORES (manejo de fallos):
   - ERROR_GENERIC: Error genérico
   - ERROR_NOT_FOUND: Recurso no encontrado
   - ERROR_PERMISSION_DENIED: Sin permisos
   - ERROR_RATE_LIMITED: Demasiadas acciones
   - ERROR_MAINTENANCE: Sistema en mantenimiento

6. TIENDA/GABINETE:
   - SHOP_WELCOME: Bienvenida al Gabinete
   - SHOP_ITEM_PURCHASED: Confirmación de compra
   - SHOP_ITEM_NOT_AVAILABLE: Item no disponible
   - SHOP_BROWSE_CATEGORY: Al navegar categoría

7. MISIONES:
   - MISSION_NEW_AVAILABLE: Nueva misión disponible
   - MISSION_PROGRESS_UPDATE: Actualización de progreso
   - MISSION_COMPLETED: Misión completada
   - MISSION_FAILED: Misión fallida/expirada

8. RETENCIÓN (re-engagement):
   - INACTIVE_3_DAYS: Después de 3 días sin actividad
   - INACTIVE_7_DAYS: Después de 7 días sin actividad
   - INACTIVE_14_DAYS: Después de 14+ días sin actividad
   - WELCOME_BACK: Cuando regresa después de inactividad

9. CONVERSIÓN (ofertas):
   - VIP_TEASER: Mención sutil del VIP
   - VIP_INVITATION_INTRO: Inicio de secuencia de invitación
   - VIP_INVITATION_DETAIL: Detalle de lo que incluye
   - VIP_INVITATION_CTA: Call to action final
   - VIP_DECLINED_GRACEFUL: Respuesta si rechaza

ESTILO DE LUCIEN - EJEMPLOS DE REFERENCIA:

Formal pero no frío:
"Buenas noches. O días. El tiempo es relativo cuando se trata de Diana."

Evaluador constante:
"Su respuesta es... reveladora. Dice más de lo que quizás pretendía mostrar."

Protector de Diana:
"Diana no distribuye su atención sin criterio. Lo que usted acumula son reconocimientos de mérito."

Sarcasmo elegante:
"Su persistencia es admirable. No muchos continúan con tal... entusiasmo tras múltiples correcciones."

Aprobación grudging:
"Debo admitir... eso fue inesperadamente perspicaz. Quizás hay sustancia tras la superficie."

RESTRICCIONES:
- Todos los mensajes deben usar "usted", nunca tutear
- Evitar emojis excesivos (máximo 1-2 por mensaje si es necesario)
- Los mensajes largos deben usar \n\n para separar párrafos
- Incluir placeholders con formato {variable} donde sea necesario
- Documentar cada mensaje con su contexto de uso
- NO modificar archivos existentes, solo crear este nuevo
```

---

## 📋 ENTREGABLE F0.3: MAPEO DE ARQUETIPOS EXPANDIDO

### Instrucción para Claude Code

```
TAREA: Expandir el sistema de arquetipos de 3 básicos a 6 completos

ANTES DE ESCRIBIR CÓDIGO:
1. Revisa bot/narrative/database/enums.py para ver UserArchetype actual (IMPULSIVE, CONTEMPLATIVE, SILENT)
2. Revisa bot/narrative/services/ para ver cómo se detectan arquetipos actualmente
3. Revisa bot/narrative/database/models.py para ver UserNarrativeProgress y campos relacionados

OBJETIVO:
Diseñar la expansión del sistema de arquetipos sin romper compatibilidad con datos existentes.

UBICACIÓN DE ARCHIVOS A CREAR/MODIFICAR:
1. CREAR: bot/gamification/config/archetypes.py (nuevo archivo de configuración)
2. NOTA: La migración de enums se hará en fase posterior

CONTENIDO DEL NUEVO ARCHIVO archetypes.py:

1. Enum ExpandedArchetype:
   - EXPLORER = "explorer"  # El que busca cada detalle
   - DIRECT = "direct"  # Respuestas concisas, al punto
   - ROMANTIC = "romantic"  # Poético, busca conexión emocional
   - ANALYTICAL = "analytical"  # Reflexivo, comprensión intelectual
   - PERSISTENT = "persistent"  # No se rinde, múltiples intentos
   - PATIENT = "patient"  # Procesa profundamente, toma tiempo

2. Clase ArchetypeDetectionRules con reglas de detección:

   EXPLORER:
   - content_view_percentage > 80%  # Ve más del 80% del contenido disponible
   - easter_eggs_found > 0  # Ha encontrado contenido oculto
   - avg_time_per_content > 30s  # Tiempo alto en cada contenido
   - revisits_content = True  # Vuelve a ver contenido previo

   DIRECT:
   - avg_response_length < 10 palabras  # Respuestas cortas
   - decision_time < 5 segundos  # Decide rápido
   - skips_optional_content = True  # Salta contenido opcional
   - linear_navigation = True  # Navegación lineal, sin explorar

   ROMANTIC:
   - uses_emotional_language = True  # Detectar palabras emocionales
   - avg_response_length > 30 palabras  # Respuestas elaboradas
   - reacts_to_emotional_content = True  # Reacciona a contenido sentimental
   - uses_adjectives_frequently = True  # Lenguaje descriptivo

   ANALYTICAL:
   - asks_questions = True  # Hace preguntas en sus respuestas
   - evaluation_scores > 80%  # Alto puntaje en evaluaciones
   - structured_responses = True  # Respuestas organizadas
   - seeks_clarification = True  # Pide aclaraciones

   PERSISTENT:
   - return_after_inactivity_count > 2  # Regresa múltiples veces
   - retry_failed_challenges = True  # Reintenta desafíos fallidos
   - total_sessions > avg_sessions * 1.5  # Más sesiones que promedio
   - completes_difficult_missions = True  # Completa misiones difíciles

   PATIENT:
   - avg_response_time > 30 segundos  # Respuestas pensadas
   - never_uses_skip = True  # Nunca usa funciones de saltar
   - streak_length > 14 días  # Rachas largas
   - consistent_daily_activity = True  # Actividad consistente

3. Mapeo de compatibilidad con arquetipos antiguos:
   IMPULSIVE → puede mapearse a DIRECT o EXPLORER (según otras señales)
   CONTEMPLATIVE → puede mapearse a ANALYTICAL o PATIENT (según otras señales)
   SILENT → requiere más datos para clasificar

4. Clase ArchetypeScorer con método:
   calculate_archetype_scores(user_data: dict) -> dict[ExpandedArchetype, float]
   
   Retorna puntuación 0-100 para cada arquetipo basado en los datos del usuario.
   El arquetipo dominante es el que tiene >60% de score.
   Si ninguno supera 60%, el usuario permanece como "Observado" (sin arquetipo asignado).

5. Diccionario ARCHETYPE_TRAITS con características narrativas:
   {
       "EXPLORER": {
           "lucien_tone": "desafiante, le oculta cosas deliberadamente",
           "mission_type": "búsqueda, descubrimiento",
           "conversion_trigger": "contenido oculto exclusivo VIP"
       },
       "DIRECT": {
           "lucien_tone": "conciso, sin rodeos, respeto por su tiempo",
           "mission_type": "acciones claras y medibles",
           "conversion_trigger": "oferta directa con beneficios listados"
       },
       # ... etc para cada arquetipo
   }

RESTRICCIONES:
- Este archivo es solo configuración, NO modifica modelos de BD aún
- Debe ser importable sin dependencias de base de datos
- Usar typing completo
- Documentar cada regla de detección con su justificación
```

---

## 📋 ENTREGABLE F0.4: INVENTARIO DEL GABINETE (TIENDA)

### Instrucción para Claude Code

```
TAREA: Crear configuración de items iniciales para el Gabinete de Lucien

ANTES DE ESCRIBIR CÓDIGO:
1. Revisa bot/shop/database/enums.py para ver ItemType, ItemRarity existentes
2. Revisa bot/shop/database/models.py para ver estructura de ShopItem, ItemCategory
3. Revisa bot/shop/services/shop.py para ver cómo se crean items

OBJETIVO:
Crear un archivo de configuración con los items iniciales del Gabinete, siguiendo la estructura existente pero con contenido narrativo apropiado.

UBICACIÓN DEL NUEVO ARCHIVO:
bot/shop/config/initial_inventory.py

CONTENIDO REQUERIDO:

1. Mapeo de categorías existentes a nombres narrativos:
   CATEGORY_MAPPING = {
       "CONSUMABLE": "Efímeros",  # Placeres de un solo uso
       "COSMETIC": "Distintivos",  # Marcas visibles de posición
       "NARRATIVE": "Llaves",  # Abren puertas a contenido oculto
       "DIGITAL": "Reliquias"  # Objetos más valiosos
   }

2. Descripciones de categoría (para UI):
   CATEGORY_DESCRIPTIONS = {
       "Efímeros": "Placeres de un solo uso. Intensos pero fugaces.",
       "Distintivos": "Marcas visibles de su posición. Para quienes valoran el reconocimiento.",
       "Llaves": "Abren puertas a contenido que otros no pueden ver.",
       "Reliquias": "Los objetos más valiosos del Gabinete. Requieren Besitos... y dignidad."
   }

3. Lista INITIAL_ITEMS con estructura:
   [
       {
           "name": "Sello del Visitante",
           "internal_code": "badge_visitor",
           "category": "COSMETIC",
           "rarity": "COMMON",
           "price_favors": 2,
           "description_short": "Primera marca de reconocimiento",
           "description_lucien": "Una marca visible en su perfil. Indica que ha dado el primer paso. No es mucho, pero es un comienzo.",
           "effect_type": "BADGE",
           "effect_data": {"badge_id": "visitor_seal"},
           "stock": null,  # Infinito
           "level_required": 1,
           "is_active": true
       },
       {
           "name": "Susurro Efímero",
           "internal_code": "audio_whisper_01",
           "category": "CONSUMABLE",
           "rarity": "UNCOMMON",
           "price_favors": 3,
           "description_short": "Un mensaje de voz exclusivo de Diana",
           "description_lucien": "Un susurro que Diana grabó en un momento de... inspiración. Úselo cuando necesite motivación. Solo puede escucharlo una vez.",
           "effect_type": "UNLOCK_AUDIO",
           "effect_data": {"audio_id": "whisper_01", "duration_seconds": 15},
           "stock": null,
           "level_required": 2,
           "is_active": true
       },
       {
           "name": "Pase de Prioridad",
           "internal_code": "priority_pass",
           "category": "CONSUMABLE",
           "rarity": "RARE",
           "price_favors": 5,
           "description_short": "Acceso anticipado al próximo contenido",
           "description_lucien": "Cuando Diana prepare algo nuevo, usted estará primero en la fila. La paciencia tiene recompensas... pero a veces, también la impaciencia.",
           "effect_type": "PRIORITY_ACCESS",
           "effect_data": {"duration_hours": 24},
           "stock": 50,  # Limitado
           "level_required": 3,
           "is_active": true
       },
       {
           "name": "Insignia del Observador",
           "internal_code": "badge_observer",
           "category": "COSMETIC",
           "rarity": "UNCOMMON",
           "price_favors": 5,
           "description_short": "Lucien lo ha notado",
           "description_lucien": "Esta insignia indica que he prestado atención a su comportamiento. No todos ameritan mi observación. Considérelo un... honor cuestionable.",
           "effect_type": "BADGE",
           "effect_data": {"badge_id": "observer_mark"},
           "stock": null,
           "level_required": 2,
           "is_active": true
       },
       {
           "name": "Llave del Fragmento Oculto",
           "internal_code": "key_fragment_01",
           "category": "NARRATIVE",
           "rarity": "RARE",
           "price_favors": 10,
           "description_short": "Desbloquea un fragmento narrativo secreto",
           "description_lucien": "Hay historias que Diana no cuenta públicamente. Este fragmento es una de ellas. ¿Está preparado para lo que podría encontrar?",
           "effect_type": "UNLOCK_NARRATIVE",
           "effect_data": {"fragment_id": "secret_01"},
           "stock": null,
           "level_required": 3,
           "is_active": true
       },
       {
           "name": "Vistazo al Sensorium",
           "internal_code": "sensorium_preview",
           "category": "CONSUMABLE",
           "rarity": "EPIC",
           "price_favors": 15,
           "description_short": "Muestra del contenido Sensorium",
           "description_lucien": "El Sensorium es contenido diseñado para despertar sentidos que olvidó que tenía. Esta es solo una muestra. 30 segundos de lo que Diana puede hacer cuando realmente se concentra.",
           "effect_type": "UNLOCK_CONTENT",
           "effect_data": {"content_id": "sensorium_sample_01", "duration_seconds": 30},
           "stock": 100,
           "level_required": 4,
           "is_active": true
       },
       {
           "name": "El Primer Secreto",
           "internal_code": "key_chapter_secret",
           "category": "NARRATIVE",
           "rarity": "EPIC",
           "price_favors": 20,
           "description_short": "Un capítulo que pocos conocen",
           "description_lucien": "Diana tiene secretos. Este es uno de los primeros que decidió documentar. No es para los curiosos casuales. Es para quienes realmente quieren entender.",
           "effect_type": "UNLOCK_CHAPTER",
           "effect_data": {"chapter_id": "secret_chapter_01"},
           "stock": null,
           "level_required": 4,
           "is_active": true
       },
       {
           "name": "Marca del Confidente",
           "internal_code": "badge_confidant",
           "category": "COSMETIC",
           "rarity": "LEGENDARY",
           "price_favors": 25,
           "description_short": "El nivel más alto de reconocimiento",
           "description_lucien": "Esta marca indica que he decidido confiar en usted. No la otorgo a la ligera. De hecho, me cuestiono si debería existir siquiera. Pero aquí está.",
           "effect_type": "BADGE",
           "effect_data": {"badge_id": "confidant_mark"},
           "stock": 25,
           "level_required": 6,
           "is_active": true
       },
       {
           "name": "Reliquia de Diana",
           "internal_code": "relic_diana_01",
           "category": "DIGITAL",
           "rarity": "LEGENDARY",
           "price_favors": 40,
           "description_short": "Un objeto único del universo de Diana",
           "description_lucien": "Hay objetos que Diana guarda cerca. Este es uno de ellos. No puedo explicar qué es exactamente. Solo puedo decir que tiene significado. Para ella. Y ahora, para usted.",
           "effect_type": "COLLECTIBLE",
           "effect_data": {"collectible_id": "relic_01", "unique": true},
           "stock": 10,
           "level_required": 5,
           "is_active": true
       }
   ]

4. Función helper para seed data:
   def get_seed_data() -> list[dict]:
       """Retorna los items listos para insertar en BD"""
       return INITIAL_ITEMS

5. Validación de items:
   def validate_item(item: dict) -> bool:
       """Valida que un item tenga todos los campos requeridos"""
       # Implementar validación

RESTRICCIONES:
- NO ejecutar inserts a BD en este archivo, solo definir datos
- Los internal_code deben ser únicos
- Los precios deben estar dentro de los rangos definidos en economy.py
- Usar los ItemType y ItemRarity existentes en bot/shop/database/enums.py
- Documentar cada item con su propósito narrativo
```

---

## 📋 ENTREGABLE F0.5: ESTRUCTURA DE CONTENIDO NARRATIVO

### Instrucción para Claude Code

```
TAREA: Crear estructura de datos para el contenido narrativo del guión

ANTES DE ESCRIBIR CÓDIGO:
1. Revisa bot/narrative/database/models.py para ver Chapter, Fragment, Decision, UserNarrativeProgress
2. Revisa bot/narrative/database/enums.py para ver ChapterType, FragmentType, NarrativeChannel
3. Revisa bot/narrative/services/ para entender cómo se procesa la narrativa

OBJETIVO:
Crear un archivo de configuración con la estructura completa del contenido narrativo, organizado por niveles y listo para seed data.

UBICACIÓN DEL NUEVO ARCHIVO:
bot/narrative/config/story_content.py

CONTENIDO REQUERIDO:

1. Estructura de capítulos FREE (Niveles 1-3):

CHAPTERS_FREE = [
    {
        "id": "ch_free_01",
        "title": "Los Kinkys - Bienvenida",
        "chapter_type": "FREE",
        "narrative_level": 1,
        "order": 1,
        "description": "Primera interacción con el universo de Diana",
        "fragments": [
            {
                "id": "frag_1_1",
                "fragment_type": "DIALOGUE",
                "speaker": "diana",
                "order": 1,
                "content": "Así que decidiste entrar. Interesante.\n\nNo todos dan ese paso. La mayoría observa desde afuera, preguntándose qué hay aquí. Pero tú... tú cruzaste el umbral.\n\nSoy Diana. Aunque aquí me conocen de otras formas.",
                "triggers_next_on": "auto",
                "delay_seconds": 3
            },
            {
                "id": "frag_1_2",
                "fragment_type": "DIALOGUE",
                "speaker": "lucien",
                "order": 2,
                "content": "Permítame presentarme. Soy Lucien.\n\nAdministro el acceso al universo de la Señorita. No soy su amigo. No soy su enemigo. Soy... el filtro.\n\nDiana no recibe a cualquiera. Mi trabajo es determinar si usted merece su atención.",
                "triggers_next_on": "auto",
                "delay_seconds": 4
            },
            {
                "id": "frag_1_3",
                "fragment_type": "CHALLENGE",
                "speaker": "lucien",
                "order": 3,
                "content": "Su primer desafío es simple. Diana acaba de publicar algo en el canal. Su reacción es... esperada.\n\nNo me decepcione.",
                "challenge_type": "REACT_TO_LAST_MESSAGE",
                "challenge_data": {"timeout_hours": 24},
                "reward_favors": 1.0
            },
            {
                "id": "frag_1_4a",
                "fragment_type": "RESPONSE",
                "speaker": "lucien",
                "order": 4,
                "condition": "challenge_completed_fast",  # <30 segundos
                "content": "Rápido. Muy rápido.\n\nLa impulsividad puede ser virtud o defecto. El tiempo dirá cuál es en su caso.\n\nHa ganado su primer Favor. Diana lo nota... apenas.",
                "grants_archetype_signal": "DIRECT"
            },
            {
                "id": "frag_1_4b",
                "fragment_type": "RESPONSE",
                "speaker": "lucien",
                "order": 4,
                "condition": "challenge_completed_slow",  # >5 minutos
                "content": "Se tomó su tiempo. Procesó. No reaccionó por impulso.\n\nEso es... inusual. La mayoría se apresura por agradar.\n\nHa ganado su primer Favor. Diana nota a quienes no se apresuran.",
                "grants_archetype_signal": "PATIENT"
            },
            {
                "id": "frag_1_5",
                "fragment_type": "CLUE",
                "speaker": "lucien",
                "order": 5,
                "content": "Su Mochila del Viajero ahora contiene algo.\n\nPista 1 del mapa hacia Diana. Hay más. Aparecerán cuando Diana sienta que usted está listo.",
                "grants_item": "clue_map_01"
            }
        ]
    },
    {
        "id": "ch_free_02",
        "title": "Los Kinkys - Observación",
        "chapter_type": "FREE",
        "narrative_level": 2,
        "order": 2,
        "unlock_condition": {"level_required": 2, "previous_chapter": "ch_free_01"},
        "description": "Misión de observación de 3 días",
        "fragments": [
            # ... fragmentos del nivel 2
        ]
    },
    {
        "id": "ch_free_03",
        "title": "Los Kinkys - Perfil de Deseo",
        "chapter_type": "FREE",
        "narrative_level": 3,
        "order": 3,
        "unlock_condition": {"level_required": 3, "previous_chapter": "ch_free_02"},
        "description": "Cuestionario personal y punto de conversión",
        "fragments": [
            # ... fragmentos del nivel 3
            # El último fragmento es la invitación "Llave del Diván"
        ]
    }
]

2. Estructura de capítulos VIP (Niveles 4-6):

CHAPTERS_VIP = [
    {
        "id": "ch_vip_01",
        "title": "El Diván - Entrada",
        "chapter_type": "VIP",
        "narrative_level": 4,
        # ...
    },
    # ...
]

3. Diccionario de SPEAKERS:
SPEAKERS = {
    "diana": {
        "name": "Diana",
        "display_name": "🌙 Diana",
        "style": "íntima, misteriosa, vulnerable calculada, primera persona"
    },
    "lucien": {
        "name": "Lucien",
        "display_name": "🎩 Lucien",
        "style": "formal, evaluador, protector, elegante sarcasmo"
    }
}

4. Tipos de desafíos soportados:
CHALLENGE_TYPES = {
    "REACT_TO_LAST_MESSAGE": "Reaccionar a la última publicación del canal",
    "FIND_EASTER_EGGS": "Encontrar elementos ocultos en publicaciones",
    "ANSWER_QUESTIONS": "Responder preguntas de comprensión",
    "WAIT_TIME": "Esperar un período de tiempo",
    "WRITE_RESPONSE": "Escribir respuesta reflexiva",
    "COMPLETE_PROFILE": "Completar perfil de deseo"
}

5. Función helper:
def get_chapter_by_level(level: int, is_vip: bool) -> dict | None
def get_fragments_for_chapter(chapter_id: str) -> list[dict]
def get_next_chapter(current_chapter_id: str, user_is_vip: bool) -> dict | None

NOTA: El contenido completo de todos los fragmentos se completará en Fase 5.
Por ahora, crear la estructura con los primeros fragmentos del Nivel 1 como ejemplo.

RESTRICCIONES:
- Mantener compatibilidad con modelos existentes en bot/narrative/database/models.py
- Usar los enums existentes donde aplique
- NO insertar datos a BD, solo definir estructura
- Documentar el formato esperado de cada campo
```

---

## 🔄 ORDEN DE IMPLEMENTACIÓN FASE 0

```
1. F0.1: Economy Config      → Base para todo el sistema de recompensas
         ↓
2. F0.2: Lucien Messages     → Define el tono de toda la aplicación
         ↓
3. F0.3: Archetypes Config   → Sistema de personalización
         ↓
4. F0.4: Shop Inventory      → Items del Gabinete (depende de F0.1 para precios)
         ↓
5. F0.5: Story Content       → Contenido narrativo (depende de F0.2 para mensajes)
```

---

## ✅ CRITERIOS DE ACEPTACIÓN FASE 0

Antes de pasar a Fase 1, verificar:

- [ ] Archivo economy.py existe y es importable sin errores
- [ ] Archivo lucien_messages.py existe con todas las categorías requeridas
- [ ] Archivo archetypes.py existe con los 6 arquetipos y reglas de detección
- [ ] Archivo initial_inventory.py existe con los 9 items definidos
- [ ] Archivo story_content.py existe con estructura de al menos Nivel 1 completo
- [ ] Ningún archivo existente fue modificado
- [ ] Todos los archivos tienen type hints completos
- [ ] Todos los archivos están documentados

---

## 📁 ESTRUCTURA DE ARCHIVOS ESPERADA POST-FASE 0

```
bot/
├── gamification/
│   └── config/              # NUEVO DIRECTORIO
│       ├── __init__.py
│       ├── economy.py       # F0.1
│       └── archetypes.py    # F0.3
├── shop/
│   └── config/              # NUEVO DIRECTORIO
│       ├── __init__.py
│       └── initial_inventory.py  # F0.4
├── narrative/
│   └── config/              # NUEVO DIRECTORIO
│       ├── __init__.py
│       └── story_content.py # F0.5
└── utils/
    └── lucien_messages.py   # F0.2
```
