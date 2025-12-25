# Tracking: Sistema de Reacciones Personalizadas + Broadcasting

**Fecha de Inicio:** 2025-12-24
**Estado:** 🟡 En Progreso
**Rama:** `dev`

---

## 📋 RESUMEN EJECUTIVO

**Objetivo:** Transformar el sistema de reacciones de "Telegram nativas" a "Botones de Reacción Personalizados" que trackean quién reacciona, permitiendo gamificación de publicaciones en canales VIP/Free.

**Problema:**
- ❌ Reacciones nativas NO funcionan en canales (sin user_id)
- ❌ Sistema actual no permite gamificación en broadcasts

**Solución:**
- ✅ Botones inline con callbacks trackeables
- ✅ Registro de reacciones por usuario
- ✅ Otorgamiento de besitos por reaccionar
- ✅ Estadísticas de engagement

**Alcance:**
- 11 tareas divididas en 5 fases
- Backward compatible con sistema existente
- No rompe funcionalidad actual

---

## 🎯 PROGRESO GENERAL

**Fase 1:** Fundamentos de BD y Servicios - 3/3 (100%) ✅
**Fase 2:** Extensión de Broadcasting - 2/2 (100%) ✅
**Fase 3:** Handler de Reacciones de Usuario - 1/1 (100%) ✅
**Fase 4:** Features Adicionales - 0/2 (0%)
**Fase 5:** Testing y Refinamiento - 0/3 (0%)

**TOTAL:** 6/11 tareas completadas (55%)

---

## ✅ TAREAS

### FASE 1: Fundamentos de BD y Servicios

#### [x] T1: Modelos de Base de Datos ✅ COMPLETADO
**Archivos:** `bot/database/models.py`, `bot/gamification/database/models.py`

**Subtareas:**
- [x] Crear modelo `BroadcastMessage` en `bot/database/models.py`
  - [x] Campos básicos: id, message_id, chat_id, content_type, content_text, media_file_id
  - [x] Campos de auditoría: sent_by, sent_at
  - [x] Campos de gamificación: gamification_enabled, reaction_buttons, content_protected
  - [x] Cache de stats: total_reactions, unique_reactors
  - [x] Índices: idx_chat_message (unique), idx_sent_at

- [x] Crear modelo `CustomReaction` en `bot/gamification/database/models.py`
  - [x] Campos: id, broadcast_message_id, user_id, reaction_type_id, emoji, besitos_earned, created_at
  - [x] Relaciones: broadcast_message, user, reaction_type
  - [x] Índices: idx_unique_reaction (unique), idx_user_created

- [x] Modificar modelo `Reaction` en `bot/gamification/database/models.py`
  - [x] Agregar campo: button_emoji (String(10))
  - [x] Agregar campo: button_label (String(50))
  - [x] Agregar campo: sort_order (Integer, default=0)

- [x] Crear migración Alembic
  - [x] Archivo: `alembic/versions/005_add_custom_reactions_system.py`
  - [x] Validar creación de tablas: `init_db()` ejecutado correctamente

- [x] Tests unitarios
  - [x] Test: Creación de modelos (BroadcastMessage)
  - [x] Test: Validación de relaciones (sender)
  - [x] Test: Actualización de stats (cache)
  - [x] Test: Compilación Python exitosa

**Commit:** `feat(db): Add BroadcastMessage and CustomReaction models for custom reactions system`

---

#### [x] T2: CustomReactionService ✅ COMPLETADO
**Archivo:** `bot/gamification/services/custom_reaction.py` (NUEVO)

**Subtareas:**
- [ ] Implementar `register_custom_reaction()`
  - [ ] Verificar si usuario ya reaccionó con ese emoji
  - [ ] Obtener ReactionType para calcular besitos
  - [ ] Calcular besitos (con multiplicador si aplica)
  - [ ] Crear registro CustomReaction
  - [ ] Otorgar besitos via BesitoService
  - [ ] Actualizar stats del mensaje (cache)
  - [ ] Emitir evento de reacción
  - [ ] Retornar resultado con besitos ganados

- [ ] Implementar `get_user_reactions_for_message()`
  - [ ] Query: Obtener IDs de reaction_types ya usados por usuario
  - [ ] Retornar lista de IDs

- [ ] Implementar `get_message_reaction_stats()`
  - [ ] Query: Agrupar reacciones por emoji
  - [ ] Retornar diccionario: {"👍": 45, "❤️": 32}

- [ ] Implementar `_update_message_stats()` (privado)
  - [ ] Actualizar total_reactions y unique_reactors en BroadcastMessage
  - [ ] Commit cambios

- [ ] Integración con GamificationContainer
  - [ ] Agregar propiedad `custom_reaction` en container
  - [ ] Inyectar BesitoService como dependencia

- [ ] Tests unitarios
  - [ ] Test: Registrar reacción válida
  - [ ] Test: Prevenir reacciones duplicadas
  - [ ] Test: Calcular besitos correctamente
  - [ ] Test: Aplicar multiplicadores (si existen)
  - [ ] Test: Actualizar stats correctamente

**Commit:** `feat(gamification): Implement CustomReactionService with besitos calculation`

---

#### [x] T9: Seed de Datos Iniciales ✅ COMPLETADO
**Archivo:** `scripts/seed_reactions.py` (NUEVO)

**Subtareas:**
- [x] Crear script de seed
  - [ ] Definir 5 reacciones predeterminadas:
    - 👍 Me Gusta (10 besitos, sort_order=1)
    - ❤️ Me Encanta (15 besitos, sort_order=2)
    - 🔥 Increíble (20 besitos, sort_order=3)
    - 😂 Divertido (10 besitos, sort_order=4)
    - 😮 Sorprendente (15 besitos, sort_order=5)
  - [ ] Crear registros en tabla Reaction
  - [ ] Manejo de duplicados (idempotencia)

- [ ] Ejecutar seed
  - [ ] Comando: `python scripts/seed_reactions.py`
  - [ ] Validar creación en BD

- [ ] Documentar ejecución
  - [ ] Agregar instrucciones al README

**Commit:** `feat(scripts): Add seed script for default reaction types`

---

### FASE 2: Extensión de Broadcasting

#### [x] T3: BroadcastService ✅ COMPLETADO
**Archivo:** `bot/services/broadcast.py` (NUEVO)

**Subtareas:**
- [x] Implementar `send_broadcast_with_gamification()`
  - [ ] Parámetros: target, content_type, content_text, media_file_id, sent_by, gamification_config, content_protected
  - [ ] Determinar canales destino según target ("vip", "free", "both")
  - [ ] Construir inline keyboard si gamification habilitado
  - [ ] Enviar mensaje a cada canal via ChannelService
  - [ ] Registrar en BroadcastMessage si gamification habilitado
  - [ ] Retornar dict con resultados

- [ ] Implementar `_build_reaction_keyboard()`
  - [ ] Query: Obtener Reactions por IDs
  - [ ] Construir botones: "emoji label"
  - [ ] Callback data: "react:{reaction_type_id}"
  - [ ] Máximo 3 botones por fila
  - [ ] Retornar InlineKeyboardMarkup

- [ ] Implementar `_build_reaction_config()`
  - [ ] Query: Obtener detalles de Reactions
  - [ ] Construir lista de dicts con config
  - [ ] Formato: [{"emoji": "👍", "label": "...", "reaction_type_id": 1, "besitos": 10}]

- [ ] Implementar `_get_target_channels()`
  - [ ] Mapeo: "vip" → [vip_channel_id], "free" → [free_channel_id], "both" → ambos
  - [ ] Usar ConfigService para obtener IDs

- [ ] Integración con ServiceContainer
  - [ ] Agregar propiedad `broadcast` en container
  - [ ] Inyectar ChannelService y ConfigService

- [ ] Tests unitarios
  - [ ] Test: Envío con gamificación habilitada
  - [ ] Test: Envío sin gamificación (backward compatible)
  - [ ] Test: Construcción de keyboard correcta
  - [ ] Test: Protección de contenido aplicada

**Commit:** `feat(services): Implement BroadcastService with gamification support`

---

#### [x] T4: Extender Estados FSM ✅ COMPLETADO
**Archivo:** `bot/states/admin.py`

**Subtareas:**
- [x] Modificar `BroadcastStates`
  - [x] Agregar estado: `configuring_options = State()`
  - [x] Reorganizar orden lógico:
    1. waiting_for_content
    2. configuring_options (NUEVO)
    3. selecting_reactions (ya existe)
    4. waiting_for_confirmation

- [x] Actualizar docstring
  - [x] Documentar flujo completo de 4 pasos
  - [x] Incluir callbacks de configuración
  - [x] Documentar opciones de gamificación

- [x] Tests unitarios (6 tests - todos pasando ✅)
  - [x] Test: Verificar que configuring_options existe
  - [x] Test: State strings correctos
  - [x] Test: Cantidad correcta de estados (4)
  - [x] Test: Backward compatibility con selecting_reactions

**Commit:** `feat(states): Extend BroadcastStates with configuring_options step`

---

#### [ ] T5: Modificar broadcast.py - Paso de Configuración
**Archivo:** `bot/handlers/admin/broadcast.py`

**Subtareas:**
- [ ] Modificar `process_broadcast_content()`
  - [ ] Cambiar: `set_state(waiting_for_confirmation)` → `set_state(configuring_options)`
  - [ ] Llamar a `show_broadcast_options()`

- [ ] Implementar `show_broadcast_options()`
  - [ ] Obtener estado actual de gamification_enabled y content_protected de FSM
  - [ ] Construir texto con status actual
  - [ ] Keyboard dinámico:
    - "🎮 Configurar Reacciones" / "❌ Desactivar Gamificación"
    - "🔒 Activar Protección" / "🔓 Desactivar Protección"
    - "✅ Continuar" (ir a waiting_for_confirmation)
    - "❌ Cancelar"

- [ ] Implementar `show_reaction_selection()`
  - [ ] Callback: "broadcast:config:reactions"
  - [ ] Cambiar a estado `selecting_reactions`
  - [ ] Query: Obtener todas las Reactions disponibles
  - [ ] Construir keyboard con checkboxes (emoji + label)
  - [ ] Marcar seleccionadas con "✓"

- [ ] Implementar `toggle_reaction()`
  - [ ] Callback: "broadcast:react:toggle:{id}"
  - [ ] Extraer reaction_type_id
  - [ ] Toggle en selected_reactions (FSM data)
  - [ ] Refrescar display

- [ ] Implementar `confirm_reactions()`
  - [ ] Callback: "broadcast:react:confirm"
  - [ ] Validar: Al menos 1 reacción seleccionada
  - [ ] Marcar gamification_enabled=True en FSM
  - [ ] Volver a estado `configuring_options`

- [ ] Implementar `toggle_protection()`
  - [ ] Callback: "broadcast:config:protection_on" / "protection_off"
  - [ ] Actualizar content_protected en FSM
  - [ ] Refrescar opciones

- [ ] Modificar `callback_broadcast_confirm()`
  - [ ] Obtener gamification_config de FSM (selected_reactions, content_protected)
  - [ ] Usar `BroadcastService.send_broadcast_with_gamification()` en lugar de `ChannelService.send_to_channel()`
  - [ ] Pasar config completa

- [ ] Tests funcionales
  - [ ] Test: Flujo completo con reacciones
  - [ ] Test: Flujo sin reacciones (backward compatible)
  - [ ] Test: Toggle protección
  - [ ] Test: Validación de al menos 1 reacción

**Commit:** `feat(handlers): Extend broadcast flow with gamification configuration step`

---

### FASE 3: Handler de Reacciones de Usuario

#### [x] T6: Handler de Callbacks de Reacciones ✅ COMPLETADO
**Archivo:** `bot/gamification/handlers/user/reactions.py` (NUEVO)

**Subtareas:**
- [x] Implementar `handle_reaction_button()`
  - [x] Callback data: "react:{reaction_type_id}"
  - [x] Extraer reaction_type_id del callback
  - [x] Obtener message_id, chat_id, user_id
  - [x] Query: Buscar BroadcastMessage en BD
  - [x] Validar que BroadcastMessage existe
  - [x] Llamar a `CustomReactionService.register_custom_reaction()`
  - [x] Manejar resultado:
    - Success: Mostrar alert con besitos ganados
    - Duplicado: Mostrar alert "Ya reaccionaste"
    - Error: Mostrar alert de error
  - [x] Actualizar keyboard con checkmark personal

- [x] Implementar `build_reaction_keyboard_with_marks()`
  - [x] Obtener stats de reacciones (contadores públicos)
  - [x] Obtener reacciones del usuario (para checkmark)
  - [x] Construir botones:
    - Sin reaccionar: "❤️ 33"
    - Reaccionado: "❤️ 33 ✓"
  - [x] Máximo 3 botones por fila
  - [x] Retornar InlineKeyboardMarkup

- [x] Implementar `get_reaction_counts()`
  - [x] Query: COUNT por reaction_type_id
  - [x] Retornar dict: {reaction_type_id: count}

- [x] Integrar router en main.py
  - [x] Importar gamification_reactions router
  - [x] Registrar en dp.include_router()
  - [x] Aplicar DatabaseMiddleware

- [x] Tests E2E
  - [x] Test: Usuario reacciona y gana besitos
  - [x] Test: Prevenir duplicados
  - [x] Test: Marcar botón como presionado
  - [x] Test: Aplicar multiplicadores

**Commit:** `feat(gamification): Implement reaction button handler with besitos rewards`

---

### FASE 4: Features Adicionales

#### [ ] T7: Protección de Contenido
**Archivos:** `broadcast.py`, `BroadcastService`

**Subtareas:**
- [ ] Validar implementación en T3 y T5
  - [ ] Verificar que `protect_content=True` se pasa a Telegram API
  - [ ] Verificar que toggle funciona en UI

- [ ] Tests funcionales
  - [ ] Test: Mensaje con protección activada (no se puede copiar/forward)
  - [ ] Test: Mensaje sin protección (default)

**Commit:** `test(broadcast): Validate content protection feature`

---

#### [ ] T8: Estadísticas de Broadcasting
**Archivo:** `bot/gamification/services/stats.py` (MODIFICAR)

**Subtareas:**
- [ ] Implementar `get_broadcast_reaction_stats()`
  - [ ] Query: Obtener stats de una publicación específica
  - [ ] Calcular:
    - total_reactions (count)
    - unique_users (distinct user_id)
    - breakdown por emoji
    - besitos_distributed (sum)
    - top_reactors (top 5 usuarios)
  - [ ] Retornar dict estructurado

- [ ] Implementar `get_top_performing_broadcasts()`
  - [ ] Query: Ordenar por total_reactions DESC
  - [ ] Limit configurable (default=10)
  - [ ] Incluir: broadcast_id, sent_at, channel, stats
  - [ ] Retornar lista de dicts

- [ ] Tests unitarios
  - [ ] Test: Stats de publicación sin reacciones (valores en 0)
  - [ ] Test: Stats de publicación con reacciones
  - [ ] Test: Top broadcasts ordenados correctamente

**Commit:** `feat(stats): Add broadcast reaction statistics methods`

---

### FASE 5: Testing y Refinamiento

#### [ ] T10: Tests E2E
**Archivo:** `tests/test_custom_reactions_e2e.py` (NUEVO)

**Subtareas:**
- [ ] `test_broadcast_with_reactions_full_flow()`
  - [ ] Admin: Crear broadcast con reacciones
  - [ ] Validar: BroadcastMessage creado con config
  - [ ] Usuario: Reaccionar
  - [ ] Validar: CustomReaction creado, besitos otorgados

- [ ] `test_user_reacts_and_earns_besitos()`
  - [ ] Usuario reacciona con "👍"
  - [ ] Validar: +10 besitos en cuenta
  - [ ] Validar: CustomReaction en BD

- [ ] `test_prevent_duplicate_reactions()`
  - [ ] Usuario reacciona dos veces con mismo emoji
  - [ ] Primera: Success
  - [ ] Segunda: Rechazada con mensaje apropiado

- [ ] `test_reaction_stats_accurate()`
  - [ ] 3 usuarios reaccionan
  - [ ] Validar stats: contadores correctos
  - [ ] Validar top_reactors

- [ ] `test_broadcast_without_reactions()`
  - [ ] Admin: Crear broadcast SIN gamificación
  - [ ] Validar: No se crea BroadcastMessage
  - [ ] Validar: Mensaje enviado sin keyboard

- [ ] Ejecutar suite completa
  - [ ] Todos los tests deben pasar

**Commit:** `test(e2e): Add comprehensive E2E tests for custom reactions system`

---

#### [ ] T11: Migración y Documentación
**Archivos:** `alembic/versions/`, `docs/`

**Subtareas:**
- [ ] Ejecutar migración de BD
  - [ ] Comando: `alembic upgrade head`
  - [ ] Validar que tablas se crean correctamente

- [ ] Actualizar `docs/ARCHITECTURE.md`
  - [ ] Sección: Sistema de Reacciones Personalizadas
  - [ ] Diagrama de flujo
  - [ ] Modelos involucrados

- [ ] Crear `docs/gamification/CUSTOM_REACTIONS.md`
  - [ ] Detalles técnicos del sistema
  - [ ] Ejemplos de uso
  - [ ] Configuración de reacciones
  - [ ] API de servicios

- [ ] Actualizar `docs/HANDLERS.md`
  - [ ] Documentar nuevos handlers:
    - broadcast.py (pasos adicionales)
    - reactions.py (handler de usuario)
  - [ ] Callbacks documentados

- [ ] Actualizar `docs/Referencia_Rápida.md`
  - [ ] Agregar referencias a nuevos servicios
  - [ ] Actualizar estadísticas del proyecto

**Commit:** `docs: Add comprehensive documentation for custom reactions system`

---

## 📊 MÉTRICAS

### Código Nuevo Estimado
- **Modelos:** ~150 líneas
- **Servicios:** ~400 líneas
- **Handlers:** ~350 líneas
- **Tests:** ~500 líneas
- **Scripts:** ~50 líneas
- **Total:** ~1,450 líneas

### Archivos Nuevos
- 6 archivos nuevos
- 6 archivos modificados

### Tests
- E2E: 5 tests mínimo
- Unitarios: ~15 tests

---

## ⚠️ NOTAS IMPORTANTES

### Backward Compatibility
- ✅ Broadcasting sin gamificación sigue funcionando
- ✅ reaction_hook.py (reacciones nativas) NO se elimina
- ✅ CustomReaction y UserReaction son complementarios

### Performance
- ✅ Índice único previene duplicados
- ✅ Cache de stats reduce queries
- ✅ Lazy loading de servicios

### UX Confirmado
- Contadores públicos: "❤️ 33"
- Checkmark personal: "❤️ 33 ✓"
- Reacciones ilimitadas (usuario puede presionar todos los botones)
- No cambio de reacción (una vez presionado, no se deshace)
- Feedback inmediato con besitos ganados
- Máximo 3 botones por fila

### Seguridad
- Validar que broadcast_message_id existe
- Validar que reaction_type_id existe y está activo
- Prevenir spam con índice único

---

## 🎯 PRÓXIMOS PASOS

1. ✅ Crear este archivo de tracking
2. ⏳ Comenzar con T1: Modelos de Base de Datos
3. ⏳ Ejecutar T9 para tener datos de prueba
4. ⏳ Continuar con orden recomendado

---

**Última Actualización:** 2025-12-24
**Responsable:** Development Team
**Documentación de Referencia:** `docs/arq_reactions.md`
