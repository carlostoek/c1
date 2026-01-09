# Arquitectura del Sistema de Narrativa Dual

## Introducción

El sistema de narrativa del bot está compuesto por dos motores distintos pero interconectados, diseñados para diferentes niveles de complejidad en la historia: un **Motor Básico** para secuencias lineales y un **Motor Inmersivo** para experiencias dinámicas y personalizadas.

Esta dualidad permite crear contenido simple rápidamente, mientras ofrece un conjunto de herramientas potentes para desarrollar arcos narrativos complejos y reactivos.

---

## 1. Motor Básico

Este motor gestiona secuencias narrativas simples y lineales. Es ideal para contenido de demostración, tutoriales o historias cortas que no requieren una lógica condicional compleja.

- **Propósito:** Historias lineales, contenido de prueba y `seeds` de base de datos.
- **Lógica Principal:** Fragmento -> Decisión -> Siguiente Fragmento.

### Componentes Clave

- **Modelos de Datos:**
  - Ubicación: `bot/narrative/database/models.py`
  - Modelos:
    - `NarrativeChapter`: Contenedor principal de la historia.
    - `NarrativeFragment`: Unidad mínima de contenido (una escena o mensaje).
    - `FragmentDecision`: Botón/opción que lleva de un fragmento a otro.
    - `FragmentRequirement`: Condición simple para acceder a un fragmento.

- **Ejemplo de Implementación:**
  - El script `scripts/seed_narrative.py` utiliza este motor para poblar la base de datos con un capítulo de demostración de forma programática, creando instancias de los modelos directamente.

---

## 2. Motor Inmersivo

Este es el motor avanzado que potencia la experiencia principal del usuario. No reemplaza al motor básico, sino que lo **extiende** con capas de lógica y funcionalidades complejas.

- **Propósito:** Historias dinámicas, contenido personalizado, acertijos y narrativas reactivas al contexto del usuario.
- **Lógica Principal:** Un flujo orquestado que evalúa el contexto del usuario, variantes de contenido, desafíos y cooldowns antes de presentar un fragmento.

### Componentes Clave

- **Orquestador Principal (Handler):**
  - **Archivo:** `bot/narrative/handlers/user/story.py`
  - **Responsabilidad:** Es el punto de entrada para toda la interacción del usuario con la narrativa inmersiva. Gestiona el estado del usuario y coordina los diferentes servicios para construir y presentar la escena.

- **Modelos de Datos (Extensión):**
  - **Ubicación:** `bot/narrative/database/models_immersive.py`
  - **Funcionalidad:** Estos modelos se enlazan con `NarrativeFragment` para añadir funcionalidades:
    - `FragmentVariant`: Permite que un fragmento tenga **múltiples versiones** de su contenido que se activan según el contexto (ej. primera visita vs. retorno).
    - `FragmentChallenge`: Implementa **acertijos o desafíos** que requieren una respuesta de texto del usuario.
    - `FragmentTimeWindow`: Restringe el acceso a fragmentos a **horarios o fechas específicas**.
    - `NarrativeCooldown`: Impone **tiempos de espera** antes de que un usuario pueda continuar.
    - `UserFragmentVisit`: Realiza un **seguimiento del engagement** del usuario con cada fragmento.
    - `DailyNarrativeLimit`: Controla la **cantidad de contenido** que un usuario puede consumir por día.

- **Capa de Servicios:**
  - **Ubicación:** `bot/narrative/services/`
  - **Responsabilidad:** Abstraen la lógica de negocio compleja. El orquestador (`story.py`) los utiliza para tomar decisiones.
  - **Ejemplo Clave:** `bot/narrative/services/variant.py` contiene la lógica para evaluar y seleccionar la `FragmentVariant` correcta a mostrar, a través de su método `get_fragment_with_variant`.

### Flujo de Ejecución del Motor Inmersivo

1.  Un usuario interactúa con la narrativa (ej. pulsa un botón de decisión).
2.  La acción es capturada por el manejador principal: `story.py`.
3.  El manejador recopila el **contexto del usuario** (progreso, arquetipo, inventario, etc.).
4.  Llama a los servicios del motor inmersivo en orden:
    a.  Verifica si hay `NarrativeCooldown` o `FragmentTimeWindow` que impidan el acceso.
    b.  Llama al `VariantService` para determinar si aplica una `FragmentVariant` al fragmento de destino.
    c.  Si una variante es seleccionada, su contenido (texto, decisiones, etc.) sobreescribe el del fragmento base.
    d.  Si no hay variante, se usa el contenido del `NarrativeFragment` base.
5.  El manejador comprueba si el fragmento resultante tiene un `FragmentChallenge` asociado. Si es así, entra en el sub-flujo del desafío.
6.  Finalmente, renderiza el contenido y los botones de decisión al usuario.
7.  Actualiza el `UserFragmentVisit` para registrar la interacción.

---

## 3. Sistema de Importación JSON (Admin)

Este sistema es la herramienta administrativa para cargar contenido masivo **directamente al Motor Inmersivo**.

- **Componentes Clave:**
  - **Handler:** `bot/handlers/admin/narrative/import_handler.py` (gestiona la interfaz con el admin en Telegram).
  - **Servicio:** `bot/narrative/services/import_service.py` (realiza la validación y el procesamiento del archivo JSON).

- **Formato JSON:**
  - El sistema espera un JSON con una clave `"type"` (`"chapter"` o `"fragments"`) y una lista de `"fragments"`.

  **Estructura completa para type="chapter":**
  ```json
  {
    "type": "chapter",
    "chapter": {
      "name": "Nombre del Capítulo",
      "slug": "slug-unico",
      "chapter_type": "free",
      "description": "Descripción opcional",
      "order": 0,
      "is_active": true
    },
    "fragments": [...]
  }
  ```

  **Estructura completa para type="fragments":**
  ```json
  {
    "type": "fragments",
    "chapter_slug": "slug-del-capitulo-existente",
    "fragments": [...]
  }
  ```

  **Estructura completa de un fragmento:**
  ```json
  {
    "fragment_key": "clave_unica",
    "title": "Título del fragmento",
    "speaker": "diana",
    "content": "Contenido del mensaje",
    "order": 0,
    "is_entry_point": false,
    "is_ending": false,
    "visual_hint": "Pista visual opcional",
    "media": "url_o_file_id_opcional",
    "auto_send_content": true,
    "decisions": [
      {
        "button_text": "Texto del botón",
        "button_emoji": "🔥",
        "target_fragment_key": "clave_destino",
        "order": 0,
        "besitos_cost": 0,
        "grants_besitos": 0,
        "affects_archetype": "valor_opcional"
      }
    ],
    "requirements": [
      {
        "requirement_type": "vip",
        "value": "true",
        "rejection_message": "Mensaje de rechazo"
      }
    ]
  }
  ```

  **Campos requeridos del fragmento:**
  - `fragment_key`: string único
  - `title`: string
  - `speaker`: string (valores válidos: "diana", "lucien", "narrator")
  - `content`: string

  **Campos opcionales del fragmento:**
  - `order`: número (default: 0)
  - `is_entry_point`: boolean (default: false)
  - `is_ending`: boolean (default: false)
  - `visual_hint`: string
  - `media`: string (URL o file_id de Telegram)
  - `auto_send_content`: boolean (default: true)
  - `decisions`: array de objetos
  - `requirements`: array de objetos

  **Requisitos (requirements):**
  - Valores válidos de `requirement_type`: "none", "vip", "besitos", "archetype", "decision"
  - **Importante:** La clave correcta para el valor es `"value"`, no `"requirement_data"`.

  ```json
  "requirements": [
    {
      "requirement_type": "vip",
      "value": "true",
      "rejection_message": "Este camino es solo para miembros VIP."
    },
    {
      "requirement_type": "besitos",
      "value": "100",
      "rejection_message": "Necesitas 100 besitos para continuar."
    }
  ]
  ```
