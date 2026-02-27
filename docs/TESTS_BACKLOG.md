# Tests Backlog

Registro de tests pendientes por implementar para aumentar cobertura.

---

## 🔄 PROCESO DE REVISIÓN INCREMENTAL EN CURSO

### Contexto

El proyecto tiene commits acumulados con problemas de lógica, duplicaciones y código muerto.
Se está haciendo una revisión incremental antes de integrar a `main`.

### Ramas

| Rama | Descripción | Estado |
|------|-------------|--------|
| `main` | Rama estable, reseteada a estado limpio (≈T15-T16) | Base |
| `1` | Batch actual: T18-T19 (StatsService + Handler) | ✅ Revisado |
| `sologam` | Todos los commits (44 adelante de main) | Pendiente |

### Flujo de trabajo

```
1. Seleccionar batch de commits (por feature/tarea)
2. Crear rama o usar existente (ej: rama `1`)
3. Revisar cada commit:
   - Detectar bugs, duplicaciones, código muerto
   - Verificar coherencia arquitectónica
4. Corregir issues críticos
5. Documentar tests pendientes en este archivo
6. Push a rama
7. (Cuando esté listo) Merge a main
8. Repetir con siguiente batch
```

### Estado actual

**Batch 1:** T18-T19 (StatsService + Handler) ✅
- ✅ 4 commits originales revisados
- ✅ 1 bug crítico corregido (tokens expirados hardcodeaba 24h)
- ✅ 14 tests documentados

**Batch 2:** T20-T22 (Stats mejoradas + Broadcasting) ✅
- ✅ Cherry-pick selectivo (T21 tenía 23k líneas basura, limpiado)
- ✅ T20: Stats con análisis contextual
- ✅ T21: FSM states para broadcasting (solo bot/states/)
- ✅ T22: Handler broadcasting con preview
- ❌ T23: Reacciones ELIMINADO (no funciona en canales Telegram)
- ✅ Tests documentados

**Batch 3:** T24-T26 (Paginación) ✅
- ✅ T24: Sistema paginación reutilizable
- ✅ T25: Gestión paginada VIP (conflicto resuelto: sin reactions)
- ✅ T26: Visualización cola Free
- ✅ Tests documentados

**Próximo batch:** T27-T29 (Dashboard + Formatters + Tests ONDA 2)

### Issues conocidos pendientes (no críticos)

| Issue | Archivo | Descripción |
|-------|---------|-------------|
| Duplicación formatters | `stats.py:22-45` | `format_currency` y `format_percentage` duplicados con `bot/utils/formatters.py` (T28). Resolver al integrar T28. |
| Type hint `any` | `stats.py:178` | Usar `Any` (mayúscula) de typing |
| SQLAlchemy `== False` | `stats.py:573,628` | Cambiar a `.is_(False)` |
| Commit messages | varios | Quitar referencias a "Claude Code", "Qwen" |

### Cómo retomar

1. Leer esta sección para contexto
2. Ver rama actual: `git branch`
3. Ver commits pendientes vs main: `git log --oneline main..HEAD`
4. Ver commits en sologam vs rama actual: `git log --oneline HEAD..sologam`
5. Continuar con el flujo de trabajo descrito arriba

---

## Rama `1` - T18/T19 (StatsService + Handler Stats)

### T18: StatsService (`bot/services/stats.py`)

| Test | Descripción | Prioridad | Estado |
|------|-------------|-----------|--------|
| `test_count_expired_tokens_uses_duration_hours` | Verificar que tokens con diferentes `duration_hours` se calculan correctamente como expirados | 🔴 Alta | Pendiente |
| `test_count_expired_tokens_24h_token` | Token de 24h creado hace 25h debe contar como expirado | 🔴 Alta | Pendiente |
| `test_count_expired_tokens_48h_token` | Token de 48h creado hace 25h NO debe contar como expirado | 🔴 Alta | Pendiente |
| `test_cache_ttl_respected` | Cache expira después de 300 segundos | 🟡 Media | Pendiente |
| `test_force_refresh_ignores_cache` | `force_refresh=True` recalcula aunque cache sea fresco | 🟡 Media | Pendiente |
| `test_overall_stats_dataclass_serialization` | `to_dict()` serializa correctamente incluyendo datetime | 🟢 Baja | Pendiente |
| `test_vip_expiring_soon_counts_only_active` | Solo cuenta VIPs activos, no expirados | 🟡 Media | Pendiente |
| `test_projected_revenue_no_fees_configured` | Retorna 0.0 si no hay tarifas configuradas | 🟢 Baja | Pendiente |
| `test_avg_wait_time_no_processed_requests` | Retorna 0.0 si no hay solicitudes procesadas | 🟢 Baja | Pendiente |

### T19: Handler Stats (`bot/handlers/admin/stats.py`)

| Test | Descripción | Prioridad | Estado |
|------|-------------|-----------|--------|
| `test_callback_stats_general_renders_dashboard` | Verifica que el dashboard se renderiza correctamente | 🟡 Media | Pendiente |
| `test_callback_stats_refresh_forces_recalculation` | Refresh usa `force_refresh=True` | 🟡 Media | Pendiente |
| `test_format_currency_formats_correctly` | `$1,234.56` formato correcto | 🟢 Baja | Pendiente |
| `test_format_percentage_formats_correctly` | `85.5%` formato correcto | 🟢 Baja | Pendiente |
| `test_stats_error_handling_shows_error_message` | Error en service muestra mensaje amigable | 🟡 Media | Pendiente |

---

## Batch 2 - T20-T22 (Stats mejoradas + Broadcasting)

### T20: Stats Mejoradas (`bot/handlers/admin/stats.py`)

| Test | Descripción | Prioridad | Estado |
|------|-------------|-----------|--------|
| `test_retention_rate_calculation` | Tasa retención = activos/total_all_time | 🟡 Media | Pendiente |
| `test_retention_rate_zero_division` | Retorna 0 si total_all_time es 0 | 🟡 Media | Pendiente |
| `test_top_subscribers_emoji_colors` | 🟢>30d, 🟡7-30d, 🔴<7d | 🟢 Baja | Pendiente |
| `test_conversion_rate_analysis` | Análisis contextual 🟢>=80%, 🟡50-79%, 🔴<50% | 🟢 Baja | Pendiente |

### T21: FSM Broadcasting (`bot/states/admin.py`)

| Test | Descripción | Prioridad | Estado |
|------|-------------|-----------|--------|
| `test_broadcast_states_exist` | BroadcastStates tiene 2 estados (waiting_for_content, waiting_for_confirmation) | 🟢 Baja | Pendiente |

### T22: Handler Broadcasting (`bot/handlers/admin/broadcast.py`)

| Test | Descripción | Prioridad | Estado |
|------|-------------|-----------|--------|
| `test_broadcast_to_vip_requires_channel` | Error si canal VIP no configurado | 🔴 Alta | Pendiente |
| `test_broadcast_content_text` | Procesa contenido texto correctamente | 🟡 Media | Pendiente |
| `test_broadcast_content_photo` | Procesa foto con caption | 🟡 Media | Pendiente |
| `test_broadcast_content_video` | Procesa video con caption | 🟡 Media | Pendiente |
| `test_broadcast_confirm_sends_to_channel` | Confirmar envía al canal correcto | 🔴 Alta | Pendiente |
| `test_broadcast_cancel_clears_state` | Cancelar limpia FSM state | 🟡 Media | Pendiente |

### ~~T23: Reacciones~~ ❌ ELIMINADO

> **Razón:** Las reacciones en canales de Telegram no permiten identificar usuarios (solo en grupos). Funcionalidad eliminada por no ser útil y generar confusión.

---

## Batch 3 - T24-T26 (Paginación)

### T24: Sistema Paginación (`bot/utils/pagination.py`)

| Test | Descripción | Prioridad | Estado |
|------|-------------|-----------|--------|
| `test_paginator_basic` | Paginación de lista con múltiples páginas | 🔴 Alta | Pendiente |
| `test_paginator_empty_list` | Lista vacía retorna 1 página con 0 items | 🟡 Media | Pendiente |
| `test_paginator_single_page` | Lista pequeña cabe en 1 página | 🟡 Media | Pendiente |
| `test_page_indices` | start_index y end_index correctos | 🟡 Media | Pendiente |
| `test_pagination_keyboard` | Botones Anterior/Siguiente según contexto | 🟡 Media | Pendiente |
| `test_extract_page_from_callback` | Parsea correctamente callbacks | 🟢 Baja | Pendiente |

### T25: Gestión VIP Paginada (`bot/handlers/admin/management.py`)

| Test | Descripción | Prioridad | Estado |
|------|-------------|-----------|--------|
| `test_list_vip_subscribers_page1` | Muestra página 1 de suscriptores | 🔴 Alta | Pendiente |
| `test_vip_filter_active` | Filtro activos funciona | 🔴 Alta | Pendiente |
| `test_vip_filter_expired` | Filtro expirados funciona | 🟡 Media | Pendiente |
| `test_vip_filter_expiring` | Filtro "por expirar" (7 días) | 🟡 Media | Pendiente |
| `test_vip_subscriber_details` | Muestra detalles correctos | 🟡 Media | Pendiente |
| `test_vip_kick_subscriber` | Expulsión manual funciona | 🔴 Alta | Pendiente |

### T26: Cola Free Paginada (`bot/handlers/admin/management.py`)

| Test | Descripción | Prioridad | Estado |
|------|-------------|-----------|--------|
| `test_view_free_queue` | Muestra cola inicial | 🔴 Alta | Pendiente |
| `test_free_filter_pending` | Filtro pendientes funciona | 🔴 Alta | Pendiente |
| `test_free_filter_ready` | Filtro "listas" (tiempo cumplido) | 🟡 Media | Pendiente |
| `test_free_filter_processed` | Filtro procesadas funciona | 🟡 Media | Pendiente |
| `test_free_time_calculation` | Cálculo correcto de tiempo restante | 🔴 Alta | Pendiente |
| `test_free_emoji_by_time` | Emoji correcto según tiempo (⏳🟡🟢✅) | 🟢 Baja | Pendiente |

---

## Cómo agregar nuevos tests pendientes

Al hacer un fix o implementar una feature, agregar aquí:

```markdown
### [Tarea/Fix]: [Descripción breve]

| Test | Descripción | Prioridad | Estado |
|------|-------------|-----------|--------|
| `test_nombre_descriptivo` | Qué debe validar | 🔴/🟡/🟢 | Pendiente |
```

### Prioridades:
- 🔴 **Alta**: Bugs críticos, lógica de negocio core
- 🟡 **Media**: Flujos importantes, integraciones
- 🟢 **Baja**: Edge cases, formateo, UI

### Estados:
- **Pendiente**: No implementado
- **En progreso**: Siendo desarrollado
- **Implementado**: Test existe y pasa

---

## Resumen

| Área | Pendientes | Implementados | Cobertura |
|------|------------|---------------|-----------|
| T18 StatsService | 9 | 0 | 0% |
| T19 Handler Stats | 5 | 0 | 0% |
| T20 Stats Mejoradas | 4 | 0 | 0% |
| T21 FSM Broadcasting | 1 | 0 | 0% |
| T22 Handler Broadcast | 6 | 0 | 0% |
| ~~T23 Reacciones~~ | ~~6~~ | - | ❌ Eliminado |
| T24 Paginación | 6 | 0 | 0% |
| T25 Gestión VIP | 6 | 0 | 0% |
| T26 Cola Free | 6 | 0 | 0% |
| **Total rama 1** | **43** | **0** | **0%** |
