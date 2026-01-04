# TRACKING: Sistema Narrativo Inmersivo

**Fecha inicio:** 2025-12-28
**Estado:** ✅ COMPLETADO

---

## RESUMEN DEL SISTEMA

Sistema de narrativa inmersiva con:
- Pistas como items narrativos en la mochila unificada
- Variantes de fragmentos por contexto (primera visita, retorno, con pista, etc.)
- Sistema de cooldowns narrativos
- Diario de viaje para navegación
- Desafíos interactivos (acertijos, input del usuario)
- Mecánicas de slowdown (límites diarios, tiempos de espera)

---

## FASE 1: MODELOS Y MIGRACIONES

### Archivos modificados:
- [x] `bot/shop/database/enums.py` - Extender NarrativeItemMetadata con campos de pista
  - Añadido: is_clue, clue_category, clue_hint, source_fragment_key, required_for_fragments, clue_icon
  - Añadido: clase ObtainedVia con constantes (PURCHASE, GIFT, REWARD, ADMIN_GRANT, DISCOVERY)

- [x] `bot/narrative/database/enums.py` - Nuevos enums
  - Añadido en RequirementType: HAS_CLUE, VISITED, VISIT_COUNT, TIME_SPENT, COOLDOWN_PASSED, TIME_WINDOW, CHAPTER_COMPLETE
  - Nuevo enum: VariantConditionType
  - Nuevo enum: ChallengeType
  - Nuevo enum: CooldownType

### Archivos creados:
- [x] `bot/narrative/database/models_immersive.py` - Nuevos modelos:
  - FragmentVariant: Variantes de contenido por contexto
  - UserFragmentVisit: Tracking de visitas y tiempo
  - NarrativeCooldown: Cooldowns activos del usuario
  - FragmentChallenge: Desafíos/acertijos
  - FragmentTimeWindow: Ventanas de disponibilidad temporal
  - UserChallengeAttempt: Intentos de desafíos
  - ChapterCompletion: Capítulos completados por usuario
  - DailyNarrativeLimit: Límites diarios por usuario

- [x] `alembic/versions/013_add_immersive_narrative_system.py` - Migración (8 tablas)

---

## FASE 2: SERVICIOS CORE ✅ COMPLETADA

### Archivos creados:
- [x] `bot/narrative/services/engagement.py` - EngagementService (370 líneas)
  - record_visit(), get_visit_count(), has_visited()
  - start_reading(), stop_reading(), get_time_spent()
  - complete_chapter(), has_completed_chapter()
  - get_or_create_daily_limit(), check_daily_limit()
  - get_user_stats()

- [x] `bot/narrative/services/clue.py` - ClueService (290 líneas)
  - grant_clue(), grant_clue_from_fragment()
  - has_clue(), has_all_clues()
  - get_clue_by_slug(), get_all_clues()
  - get_user_clues(), get_clues_for_fragment()
  - get_clue_progress()

- [x] `bot/narrative/services/variant.py` - VariantService (350 líneas)
  - resolve_variant(), apply_variant()
  - _evaluate_condition() con 8 tipos de condiciones
  - get_variants_for_fragment(), create_variant()
  - update_variant(), delete_variant(), toggle_variant()
  - build_user_context()

- [x] `bot/narrative/services/cooldown.py` - CooldownService (270 líneas)
  - set_cooldown(), check_cooldown(), get_cooldown()
  - clear_cooldown(), clear_all_cooldowns(), clear_expired_cooldowns()
  - set_fragment_cooldown(), set_chapter_cooldown()
  - set_decision_cooldown(), set_challenge_cooldown()
  - can_take_decision(), can_access_fragment()

- [x] `bot/narrative/services/challenge.py` - ChallengeService (380 líneas)
  - get_challenge_for_fragment(), get_challenge_by_id()
  - validate_answer(), record_attempt()
  - has_completed_challenge(), can_attempt()
  - get_hint(), get_available_hints(), get_next_hint()
  - process_challenge_attempt()
  - create_challenge(), update_challenge(), delete_challenge()
  - get_challenge_stats()

- [x] `bot/narrative/services/container.py` - Actualizado
  - 5 nuevos properties: engagement, clue, variant, cooldown, challenge
  - get_loaded_services() actualizado
  - clear_cache() actualizado

---

## FASE 3: MOCHILA UNIFICADA ✅ COMPLETADA

### Archivos modificados:
- [x] `bot/shop/database/enums.py` - ObtainedVia class añadida (PURCHASE, GIFT, REWARD, ADMIN_GRANT, DISCOVERY)

- [x] `bot/shop/handlers/user/backpack.py` - Extendido (~250 líneas nuevas)
  - Nuevo filtro: "🔍 Pistas" con contador
  - Nuevo filtro: "🎁 Recompensas" con contador
  - Vista especial para pistas con metadata completa
  - Helper _is_clue_item() y _get_clue_metadata()
  - Handler callback_filter_clues() con paginación
  - Handler callback_clue_detail() con:
    - Categoría, descripción, lore
    - Fragmento origen con botón "Ver fragmento origen"
    - Lista de fragmentos que desbloquea
    - Pista/hint asociada
  - Handler callback_filter_rewards() con paginación
  - Keyboard principal actualizado con conteo de especiales

---

## FASE 4: SISTEMA DE VARIANTES ✅ COMPLETADA

### Archivos creados:
- [x] `bot/narrative/handlers/user/story.py` - Handler de historia (~400 líneas)
  - cmd_start_story(): Comando /historia para iniciar/continuar
  - callback_select_chapter(): Seleccionar capítulo
  - callback_process_decision(): Procesar decisiones del usuario
  - callback_goto_fragment(): Navegación directa a fragmentos
  - callback_show_journal(): Mostrar diario básico
  - callback_continue_story(): Continuar desde último punto
  - show_fragment(): Función principal que integra:
    - build_full_user_context(): Contexto completo del usuario
    - VariantService para contenido dinámico
    - EngagementService para tracking de visitas
    - CooldownService para verificar tiempos de espera
    - ClueService para otorgar pistas
    - DecisionService para mostrar opciones

### Archivos modificados:
- [x] `bot/narrative/services/chapter.py`
  - Añadido: get_chapters_by_type() para filtrar por tipo

- [x] `bot/narrative/handlers/user/__init__.py`
  - Exporta story_router

- [x] `bot/narrative/handlers/__init__.py`
  - Exporta story_router

---

## FASE 5: DIARIO DE VIAJE ✅ COMPLETADA

### Archivos creados:
- [x] `bot/narrative/services/journal.py` - JournalService (~450 líneas)
  - get_chapter_progress(): Progreso por capítulo
  - get_fragment_status(): Estado del fragmento (visited/available/locked/current)
  - get_fragments_by_status(): Fragmentos agrupados por estado
  - get_accessible_fragments(): Para navegación rápida
  - get_blocked_fragments_with_reasons(): Con razones de bloqueo
  - get_clues_summary(): Resumen de pistas
  - get_journey_stats(): Estadísticas completas del viaje
  - FragmentStatus: Enum de estados

- [x] `bot/narrative/handlers/user/journal.py` - Handler del diario (~380 líneas)
  - cmd_journal(): Comando /diario con estadísticas
  - callback_chapters_list(): Lista de capítulos con progreso
  - callback_chapter_detail(): Detalle de capítulo con fragmentos
  - callback_quick_navigation(): Navegación rápida
  - callback_clues_summary(): Resumen de pistas
  - callback_goto_from_journal(): Navegación a fragmento

### Archivos modificados:
- [x] `bot/narrative/services/container.py`
  - Añadido: journal property para JournalService
  - Actualizado: get_loaded_services() y clear_cache()

- [x] `bot/narrative/handlers/user/__init__.py`
  - Exporta journal_router

- [x] `bot/narrative/handlers/__init__.py`
  - Exporta journal_router

---

## FASE 6: COOLDOWNS Y SLOWDOWN ✅ COMPLETADA

### Archivos creados:
- [x] `bot/narrative/config.py` - NarrativeConfig (~200 líneas)
  - DECISION_COOLDOWN_SECONDS: 30
  - INTENSE_FRAGMENT_COOLDOWN_SECONDS: 300
  - CHAPTER_COMPLETION_COOLDOWN_SECONDS: 600
  - CHALLENGE_RETRY_COOLDOWN_SECONDS: 60
  - DAILY_FRAGMENT_LIMIT: 50
  - DAILY_DECISION_LIMIT: 30
  - DAILY_CHALLENGE_ATTEMPTS: 10
  - TIME_WINDOWS: morning/afternoon/evening/night
  - COOLDOWN_MESSAGES: Mensajes narrativos por tipo
  - get_cooldown_message(): Mensaje aleatorio
  - get_time_window(): Período actual
  - to_dict(): Exportar configuración

### Archivos modificados:
- [x] `bot/narrative/handlers/user/story.py`
  - Import de NarrativeConfig
  - callback_process_decision(): Verificar límite diario de decisiones
  - callback_process_decision(): Mensajes de cooldown narrativos
  - callback_process_decision(): Usar configuración para duración
  - show_fragment(): Verificar límite diario de fragmentos
  - show_fragment(): Mensaje especial al alcanzar límite
  - show_fragment(): Incrementar contador de fragmentos vistos

---

## FASE 7: DESAFIOS INTERACTIVOS ✅ COMPLETADA

### Archivos creados:
- [x] `bot/narrative/states/challenge.py` - Estados FSM
  - ChallengeStates: waiting_for_answer, showing_hint, showing_result

- [x] `bot/narrative/states/__init__.py`
  - Exporta ChallengeStates

- [x] `bot/narrative/handlers/user/challenge.py` - Handler de desafíos (~350 líneas)
  - callback_start_challenge(): Iniciar desafío con validaciones
  - process_challenge_answer(): Procesar respuesta de texto (FSM)
  - callback_get_hint(): Mostrar pista progresiva
  - callback_retry_challenge(): Reintentar desafío
  - callback_skip_challenge(): Saltar desafío (si permitido)
  - callback_cancel_challenge(): Cancelar y volver
  - format_challenge_message(): Formatear pregunta con stats
  - build_challenge_keyboard(): Teclado con opciones
  - build_result_keyboard(): Teclado de resultado

### Archivos modificados:
- [x] `bot/narrative/handlers/user/__init__.py`
  - Exporta challenge_router

- [x] `bot/narrative/handlers/__init__.py`
  - Exporta challenge_router

---

## NOTAS TÉCNICAS

### Integración con sistema existente:
- Las pistas son ShopItems con item_type=NARRATIVE y metadata.is_clue=True
- Se obtienen via obtained_via="discovery" cuando se encuentran en narrativa
- RequirementType.ITEM ya soporta validar posesión de items (incluidas pistas)
- El sistema de variantes es un layer sobre FragmentService, no reemplaza

### Dependencias:
- InventoryService para gestionar pistas
- RequirementsService para validar acceso
- ProgressService para tracking de posición
- DecisionService para historial de decisiones

---

## COMMITS REALIZADOS

(Se actualizará con cada commit)

---

## SIGUIENTE PASO

✅ SISTEMA COMPLETO - Todas las fases implementadas.

Próximos pasos opcionales:
- Crear contenido narrativo (capítulos, fragmentos, pistas)
- Configurar desafíos y variantes
- Testing E2E del flujo completo
- Integración con main.py para registrar routers
