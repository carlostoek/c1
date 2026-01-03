# FASE 3: ARQUETIPOS EXPANDIDOS - TRACKING DE AVANCE

**Objetivo:** Implementar el sistema de detección de arquetipos corregido (sin dependencia de TEXT_RESPONSE).

---

## ESTADO DEL SISTEMA ANTES DE FASE 3

### Archivos Base Existentes (FASE 0 + FASE 1 + FASE 2)
- [x] `bot/gamification/config/archetypes.py` - 6 arquetipos expandidos
- [x] `bot/utils/lucien_messages.py` - Mensajes de Lucien incluyendo arquetipos
- [x] `bot/gamification/database/enums.py` - Enums base (MissionType, RewardType, etc.)
- [x] `bot/gamification/database/models.py` - Modelos base de gamificación

---

## TAREAS FASE 3

### F3.1 - Modelo de Datos
**Estado:** ✅ COMPLETADO

- [x] Agregar modelo `UserBehaviorSignals` en `models.py`
  - Métricas de exploración (EXPLORER)
  - Métricas de velocidad/eficiencia (DIRECT)
  - Métricas emocionales (ROMANTIC) - DERIVADAS DE TAGS
  - Métricas de análisis (ANALYTICAL)
  - Métricas de persistencia (PERSISTENT)
  - Métricas de paciencia (PATIENT)
  - Métricas generales
- [x] Agregar campos de arquetipo a `UserGamification`
  - `archetype`: String nullable
  - `archetype_confidence`: Int (0-100)
  - `archetype_scores`: JSON string
  - `archetype_detected_at`: DateTime
  - `archetype_version`: Int
- [x] Crear enum `InteractionType` en `enums.py`
  - 19 tipos de interacción
  - Sin dependencia de TEXT_RESPONSE

---

### F3.2 - Configuración de Detección
**Estado:** ✅ COMPLETADO

- [x] Crear `archetype_detection.py` con:
  - `ArchetypeDetectionConfig` - Umbrales y pesos
  - `NormalizationRanges` - Rangos para normalización
  - `ScoreDefinitions` - Algoritmos de scoring corregidos
  - `ArchetypeResult` y `ArchetypeInsights` - Data classes
- [x] Funciones de ayuda (`normalize`, `normalize_inverted`)
- [x] Actualizar `config/__init__.py` con exports

---

### F3.3 - Servicio de Tracking
**Estado:** ✅ COMPLETADO

- [x] Crear `BehaviorTrackingService` en `services/behavior_tracking.py`
  - `track_button_click()` - Tracking de clicks
  - `track_content_interaction()` - Tracking de contenido
  - `track_decision()` - Tracking de decisiones
  - `track_session()` - Tracking de sesiones
  - `track_skip_action()`, `track_retry_action()`, `track_info_request()`
  - `track_quiz()` - Tracking de evaluaciones
  - `sync_streak_data()` - Sincronización de rachas
  - `get_behavior_signals()` - Obtener señales
  - `get_signals_as_dict()` - Convertir a diccionario

---

### F3.4 - Servicio de Detección
**Estado:** ✅ COMPLETADO

- [x] Crear `ArchetypeDetectionService` en `services/archetype_detection.py`
  - `detect_archetype()` - Detección completa
  - `get_archetype()` - Obtener arquetipo actual
  - `get_archetype_scores()` - Obtener scores
  - `should_reevaluate()` - Determinar si re-evaluar
  - `force_reevaluation()` - Forzar re-evaluación
  - `get_archetype_insights()` - Insights detallados

---

### F3.5 - Migraciones y Seeds
**Estado:** ✅ COMPLETADO

- [x] Crear migración `015_add_archetype_detection_system.py`
  - Tabla `user_behavior_signals`
  - Campos de arquetipo en `user_gamification`
  - Índices optimizados
- [x] Crear script `seed_archetype_badges.py`
  - 6 badges de arquetipo
  - Iconos y rareza configurados

---

### F3.6 - Handlers Admin
**Estado:** ✅ COMPLETADO

- [x] Crear `handlers/admin/archetypes.py`
  - `/archetype <user_id>` - Ver arquetipo de usuario
  - `/archetype_stats` - Estadísticas globales
  - `/archetype_refresh <user_id>` - Forzar re-evaluación
  - `/behavior_signals <user_id>` - Ver señales
  - Menú de admin con callbacks

---

## CRITERIOS DE ACEPTACIÓN

### Funcionalidad
- [x] Modelo UserBehaviorSignals creado con todos los campos
- [x] Campos de arquetipo agregados a UserGamification
- [x] InteractionType enum creado con 19 tipos
- [x] BehaviorTrackingService con métodos de tracking
- [x] ArchetypeDetectionService con algoritmos corregidos
- [x] Configuración de umbrales y pesos
- [x] Migración para tablas y campos nuevos
- [x] Seed script para badges de arquetipo
- [x] Handlers admin con comandos completos

### Algoritmo Corregido
- [x] NO depende de TEXT_RESPONSE
- [x] Usa métricas de botones y navegación
- [x] ROMANTIC basado en tags de contenido
- [x] DIRECT basado en velocidad de click
- [x] Todas las métricas son medibles en bot real

---

## RESUMEN FASE 3 ✅ COMPLETADA

### Archivos Creados

**Modelos:**
- `bot/gamification/database/models.py` - UserBehaviorSignals model + archetype fields

**Enums:**
- `bot/gamification/database/enums.py` - InteractionType enum (19 tipos)

**Configuración:**
- `bot/gamification/config/archetype_detection.py` - Configuración completa de detección

**Servicios:**
- `bot/gamification/services/behavior_tracking.py` - BehaviorTrackingService
- `bot/gamification/services/archetype_detection.py` - ArchetypeDetectionService

**Handlers:**
- `bot/gamification/handlers/admin/archetypes.py` - Admin handlers para arquetipos

**Migraciones:**
- `alembic/versions/015_add_archetype_detection_system.py` - Migration

**Scripts:**
- `scripts/seed_archetype_badges.py` - Seed de badges

**Documentación:**
- `docs/dev/gamification/fase-3_tracking.md` - Este archivo

---

## PRÓXIMOS PASOS

### Integración Pendiente (Fase 3.5 del documento original)
- [ ] Integrar tracking en handlers de callbacks prioritarios
  - start.py - SESSION_START, RETURN_AFTER_INACTIVITY
  - dynamic_menu.py - MENU_NAVIGATION, BUTTON_CLICK
  - story.py - CONTENT_VIEW, DECISION_MADE
  - decisions.py - DECISION_MADE con tiempo
  - shop.py - BUTTON_CLICK, acciones de compra
  - missions.py - CONTENT_VIEW, completion

### Notificaciones (Fase 3.6 del documento original)
- [ ] Sistema de notificación de arquetipo detectado
- [ ] Otorgamiento automático de badge al detectar
- [ ] Integración con notification service

### Adaptación de Contenido (Fase 3.7 del documento original)
- [ ] Helper get_adapted_message()
- [ ] Mensajes adaptados para misiones diarias
- [ ] Variaciones por arquetipo en conversión VIP

### Testing (Fase 3.9 del documento original)
- [ ] Tests E2E para tracking service
- [ ] Tests E2E para detection service
- [ ] Tests de integración con handlers

---

## ALGORITMO CORREGIDO - RESUMEN

### Cambios Principales vs Original

| Métrica Original | Problema | Solución Corregida |
|-----------------|----------|-------------------|
| avg_response_length | No hay texto | Eliminada |
| avg_response_time | No hay respuestas | avg_time_to_click |
| emotional_words_count | No se analiza texto | emotional_content_views (tags) |
| question_count | No hay preguntas | info_requests (botones) |
| structured_responses | No hay respuestas | systematic_exploration |
| personal_questions | No hay interacción | personal_stories_accessed |

### Nuevas Métricas Basadas en Interacciones

- `avg_time_to_click` - Velocidad de click en botones
- `emotional_content_views` - Contenido con tags emotivos
- `personal_stories_accessed` - Historias personales de Diana
- `repeat_emotional_visits` - Revisitas a contenido emotivo
- `systematic_exploration` - Navegación en orden secuencial
- `info_requests` - Uso de botones "más info"
- `slow_decision_count` - Decisiones >30 segundos
- `skip_actions_used` - Veces que usó "saltar"

### Sistema de Tags de Contenido

Tags EMOCIONALES:
- "emotional", "personal", "vulnerable", "intimate"
- "diary", "letter", "confession", "memory"
- "diana_story"

Tags INFORMATIVOS:
- "informational", "instructional", "transactional"

---

*Archivo de tracking para FASE 3 - Arquetipos Expandidos*
