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

**Último batch revisado:** Rama `1` (T18-T19)
- ✅ 4 commits originales revisados
- ✅ 1 bug crítico corregido (tokens expirados hardcodeaba 24h)
- ✅ 14 tests documentados como pendientes
- ⏳ Pendiente: merge a main cuando se decida

**Próximo batch:** Commits después de T19 en `sologam`
- Revisar desde commit siguiente a `11688f7`
- Incluye: T27 (Dashboard), T28 (Formatters), T29 (Tests E2E ONDA 2)

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
| **Total rama 1** | **14** | **0** | **0%** |
