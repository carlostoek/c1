# Referencia de API - Servicios del Módulo Narrativo

## 📚 Índice

1. [NarrativeContainer](#narrativecontainer)
2. [ChapterService](#chapterservice)
3. [FragmentService](#fragmentservice)
4. [DecisionService](#decisionservice)
5. [ProgressService](#progressservice)
6. [RequirementsService](#requirementsservice)
7. [ArchetypeService](#archetypeservice)
8. [NarrativeOrchestrator](#narrativeorchestrator)

---

## NarrativeContainer

Contenedor de inyección de dependencias que gestiona todos los servicios del módulo narrativo con lazy loading para optimizar memoria.

### Instanciación

```python
from bot.narrative.services.container import NarrativeContainer

container = NarrativeContainer(session, bot)
```

### Propiedades

- `chapter_service` - Servicio de gestión de capítulos
- `fragment_service` - Servicio de gestión de fragmentos
- `decision_service` - Servicio de procesamiento de decisiones
- `progress_service` - Servicio de seguimiento de progreso
- `requirements_service` - Servicio de validación de requisitos
- `archetype_service` - Servicio de detección de arquetipos
- `orchestrator` - Orquestador de narrativa integrado

---

## ChapterService

Gestiona capítulos narrativos con validación de estructura, consultas y operaciones CRUD.

### Métodos

#### `create_chapter(title: str, description: str, chapter_type: ChapterType, order: int, requirements: List[Dict] = None) -> NarrativeChapter`
Crea un nuevo capítulo con validación de tipo y estructura.

```python
chapter = await container.chapter_service.create_chapter(
    title="Capítulo de Prueba",
    description="Descripción del capítulo",
    chapter_type=ChapterType.INTRO,
    order=1
)
```

#### `get_chapter(chapter_id: int) -> Optional[NarrativeChapter]`
Obtiene un capítulo por ID.

```python
chapter = await container.chapter_service.get_chapter(1)
```

#### `get_chapters_by_type(chapter_type: ChapterType) -> List[NarrativeChapter]`
Obtiene capítulos filtrados por tipo.

```python
intro_chapters = await container.chapter_service.get_chapters_by_type(ChapterType.INTRO)
```

#### `get_all_chapters() -> List[NarrativeChapter]`
Obtiene todos los capítulos ordenados por posición.

```python
all_chapters = await container.chapter_service.get_all_chapters()
```

#### `update_chapter(chapter_id: int, **kwargs) -> Optional[NarrativeChapter]`
Actualiza campos de un capítulo existente.

```python
updated_chapter = await container.chapter_service.update_chapter(
    chapter_id=1,
    title="Nuevo Título"
)
```

#### `delete_chapter(chapter_id: int) -> bool`
Elimina un capítulo (y fragmentos asociados).

```python
deleted = await container.chapter_service.delete_chapter(1)
```

---

## FragmentService

Gestiona fragmentos narrativos con operaciones CRUD y consultas especializadas.

### Métodos

#### `create_fragment(chapter_id: int, title: str, content: str, order: int, requirements: List[Dict] = None) -> NarrativeFragment`
Crea un nuevo fragmento en un capítulo específico.

```python
fragment = await container.fragment_service.create_fragment(
    chapter_id=1,
    title="Fragmento Inicial",
    content="Contenido narrativo del fragmento...",
    order=1
)
```

#### `get_fragment(fragment_id: int) -> Optional[NarrativeFragment]`
Obtiene un fragmento por ID.

```python
fragment = await container.fragment_service.get_fragment(1)
```

#### `get_fragments_by_chapter(chapter_id: int) -> List[NarrativeFragment]`
Obtiene todos los fragmentos de un capítulo ordenados por posición.

```python
chapter_fragments = await container.fragment_service.get_fragments_by_chapter(1)
```

#### `get_next_fragments(fragment_id: int, user_id: int) -> List[NarrativeFragment]`
Obtiene fragmentos accesibles como siguientes desde un fragmento específico.

```python
next_fragments = await container.fragment_service.get_next_fragments(1, user_id=123456789)
```

#### `update_fragment(fragment_id: int, **kwargs) -> Optional[NarrativeFragment]`
Actualiza campos de un fragmento existente.

```python
updated_fragment = await container.fragment_service.update_fragment(
    fragment_id=1,
    content="Nuevo contenido narrativo"
)
```

---

## DecisionService

Procesa decisiones del usuario con validación, costos y transiciones de fragmentos.

### Métodos

#### `make_decision(user_id: int, fragment_id: int, decision_id: int) -> Tuple[bool, str, Optional[NarrativeFragment]]`
Procesa una decisión del usuario con validación de requisitos y costos.

```python
success, message, next_fragment = await container.decision_service.make_decision(
    user_id=123456789,
    fragment_id=1,
    decision_id=2
)
```

#### `get_available_decisions(user_id: int, fragment_id: int) -> List[FragmentDecision]`
Obtiene decisiones disponibles para un usuario en un fragmento específico.

```python
decisions = await container.decision_service.get_available_decisions(123456789, 1)
```

#### `record_decision(user_id: int, decision_id: int, timestamp: datetime = None) -> bool`
Registra una decisión tomada en el historial del usuario.

```python
recorded = await container.decision_service.record_decision(123456789, 1)
```

#### `get_user_decision_history(user_id: int, limit: int = 10) -> List[UserDecisionHistory]`
Obtiene historial de decisiones tomadas por un usuario.

```python
history = await container.decision_service.get_user_decision_history(123456789, limit=20)
```

---

## ProgressService

Gestiona el progreso del usuario en la narrativa con tracking de posición y arquetipos.

### Métodos

#### `get_user_progress(user_id: int) -> Optional[UserNarrativeProgress]`
Obtiene el progreso actual del usuario en la narrativa.

```python
progress = await container.progress_service.get_user_progress(123456789)
```

#### `update_user_progress(user_id: int, current_fragment_id: int) -> bool`
Actualiza la posición actual del usuario en la narrativa.

```python
updated = await container.progress_service.update_user_progress(123456789, 5)
```

#### `get_current_fragment(user_id: int) -> Optional[NarrativeFragment]`
Obtiene el fragmento actual donde se encuentra el usuario.

```python
current = await container.progress_service.get_current_fragment(123456789)
```

#### `mark_fragment_completed(user_id: int, fragment_id: int) -> bool`
Marca un fragmento como completado por el usuario.

```python
marked = await container.progress_service.mark_fragment_completed(123456789, 1)
```

#### `get_completed_fragments(user_id: int) -> List[NarrativeFragment]`
Obtiene fragmentos completados por el usuario.

```python
completed = await container.progress_service.get_completed_fragments(123456789)
```

---

## RequirementsService

Valida los requisitos necesarios para que un usuario acceda a fragmentos o capítulos.

### Métodos

#### `validate_access(user_id: int, requirements: List[Dict]) -> Tuple[bool, str]`
Valida si un usuario cumple con todos los requisitos dados.

```python
can_access, message = await container.requirements_service.validate_access(
    user_id=123456789,
    requirements=[
        {"type": "VIP", "required": True},
        {"type": "BESITOS", "amount": 100}
    ]
)
```

#### `check_vip_requirement(user_id: int) -> bool`
Verifica si el usuario tiene suscripción VIP activa.

```python
is_vip = await container.requirements_service.check_vip_requirement(123456789)
```

#### `check_besitos_requirement(user_id: int, required_amount: int) -> bool`
Verifica si el usuario tiene la cantidad suficiente de besitos.

```python
has_besitos = await container.requirements_service.check_besitos_requirement(123456789, 100)
```

#### `check_archetype_requirement(user_id: int, required_archetype: ArchetypeType) -> bool`
Verifica si el usuario tiene el arquetipo requerido.

```python
matches_archetype = await container.requirements_service.check_archetype_requirement(
    user_id=123456789,
    required_archetype=ArchetypeType.IMPULSIVE
)
```

#### `check_completed_chapter_requirement(user_id: int, chapter_id: int) -> bool`
Verifica si el usuario ha completado un capítulo específico.

```python
completed = await container.requirements_service.check_completed_chapter_requirement(123456789, 1)
```

---

## ArchetypeService

Detecta y analiza arquetipos del usuario basados en sus patrones de decisión.

### Métodos

#### `analyze_user_responses(user_id: int) -> Tuple[ArchetypeType, float]`
Analiza las decisiones pasadas del usuario para determinar su arquetipo.

```python
archetype, confidence = await container.archetype_service.analyze_user_responses(123456789)
```

#### `get_user_archetype(user_id: int) -> Optional[ArchetypeType]`
Obtiene el arquetipo detectado actual del usuario.

```python
archetype = await container.archetype_service.get_user_archetype(123456789)
```

#### `update_user_archetype(user_id: int, archetype: ArchetypeType) -> bool`
Actualiza el arquetipo registrado del usuario.

```python
updated = await container.archetype_service.update_user_archetype(123456789, ArchetypeType.CONTEMPLATIVE)
```

#### `get_user_decision_patterns(user_id: int) -> Dict[str, Any]`
Obtiene estadísticas sobre los patrones de decisión del usuario.

```python
patterns = await container.archetype_service.get_user_decision_patterns(123456789)
```

#### `adapt_content_for_archetype(archetype: ArchetypeType, content: str) -> str`
Adapta contenido narrativo según el arquetipo.

```python
adapted_content = await container.archetype_service.adapt_content_for_archetype(
    ArchetypeType.IMPULSIVE,
    "Contenido narrativo general..."
)
```

---

## NarrativeOrchestrator

Orquestador que integra narrativa con gamificación, creando recompensas y misiones vinculadas.

### Métodos

#### `create_narrative_with_rewards(config: Dict) -> Dict`
Crea fragmentos narrativos con recompensas y misiones integradas.

```python
config = {
    'chapter': {
        'title': 'Capítulo de Prueba',
        'description': 'Capítulo con recompensas'
    },
    'fragments': [
        {
            'title': 'Fragmento 1',
            'content': 'Contenido del fragmento',
            'rewards': {
                'besitos': 50,
                'mission_id': 1,
                'level_id': 2
            }
        }
    ]
}

result = await container.orchestrator.create_narrative_with_rewards(config)
```

#### `process_completion_rewards(user_id: int, fragment_id: int) -> List[Dict]`
Procesa recompensas otorgadas por completar un fragmento.

```python
rewards = await container.orchestrator.process_completion_rewards(123456789, 1)
```

#### `create_mission_linked_to_decision(user_id: int, decision_id: int) -> Optional[Mission]`
Crea una misión especial basada en una decisión específica tomada.

```python
mission = await container.orchestrator.create_mission_linked_to_decision(123456789, 1)
```

#### `track_narrative_gamification(user_id: int) -> Dict`
Obtiene estadísticas de integración entre narrativa y gamificación.

```python
stats = await container.orchestrator.track_narrative_gamification(123456789)
```

---

**Última actualización:** 2025-12-26  
**Versión:** 1.0.0