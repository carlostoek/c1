# Tests Backlog

Registro de tests pendientes por implementar para aumentar cobertura.

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
