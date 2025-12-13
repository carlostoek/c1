# Tests E2E - ONDA 2

Suite de tests end-to-end para validar features de ONDA 2.

## 📋 Coverage

### Estadísticas (T18-T20)
- ✅ StatsService - Overall stats
- ✅ StatsService - VIP stats
- ✅ StatsService - Free stats
- ✅ StatsService - Token stats
- ✅ Cache de estadísticas (TTL 5 min)
- ✅ Force refresh

### Paginación (T24)
- ✅ Paginador básico (10 items/página)
- ✅ Paginador vacío (0 items)
- ✅ Navegación (anterior/siguiente)
- ✅ Índices de página (start/end)

### Formatters (T28)
- ✅ Formateo de fechas (ISO simplificado)
- ✅ Tiempo relativo (hace X, en X)
- ✅ Monedas ($1,234.56)
- ✅ Porcentajes (85.5%)
- ✅ Duraciones (65 min → 1 hora, 5 minutos)
- ✅ Emojis de estado (🟢🟡🔴⚪)

### Flujos Integrados
- ✅ Gestión VIP paginada
- ✅ Cola Free paginada

## 🚀 Ejecutar Tests

```bash
# Todos los tests ONDA 2
pytest tests/test_e2e_onda2.py -v

# Test específico
pytest tests/test_e2e_onda2.py::test_stats_overall -v

# Con output verbose y pausa en errores
pytest tests/test_e2e_onda2.py -vvs

# Con coverage
pytest tests/test_e2e_onda2.py --cov=bot.services --cov=bot.utils --cov-report=html
```

## 📊 Métricas Esperadas

- **Total Tests:** 12
- **Coverage:** >85% de código ONDA 2
- **Duración:** <30 segundos
- **Todos PASANDO:** ✅

## Tests Incluidos

### Test 1: Estadísticas Generales
Valida el cálculo de:
- VIP activos, expirados, próximos a expirar
- Free pendientes y procesadas
- Tokens generados, usados, expirados
- Disponibles = generados - usados - expirados

**Datos:** 3 VIPs, 5 tokens, 5 solicitudes Free

### Test 2: Estadísticas VIP
Valida:
- Total activos
- Total expirados
- Total all-time

**Datos:** 5 suscriptores VIP

### Test 3: Estadísticas Free
Valida:
- Solicitudes pendientes
- Solicitudes procesadas
- Total all-time

**Datos:** 7 solicitudes Free

### Test 4: Estadísticas Tokens
Valida:
- Total generados
- Total usados
- Conversion rate (usado / generado * 100)

**Datos:** 10 tokens, 6 usados (60%)

### Test 5: Cache de Estadísticas
Valida:
- Cache hit (mismo timestamp)
- Cache invalidation con force_refresh
- Cache expiration (5 minutos)

### Test 6: Paginación Básica
Valida:
- Total items y pages
- Navegación (anterior/siguiente)
- Índices (start/end)
- Items por página

**Datos:** 25 elementos, 10 por página → 3 páginas

### Test 7: Paginación Vacía
Valida:
- Manejo de listas vacías
- is_empty property
- Siempre retorna mínimo 1 página

**Datos:** 0 elementos

### Test 8: Formateo de Fechas
Valida:
- format_datetime con hora
- format_datetime sin hora
- Formato ISO: YYYY-MM-DD HH:MM

### Test 9: Tiempo Relativo
Valida:
- "hace X minutos"
- "en X horas"
- "hace X días"

### Test 10: Formateo de Números
Valida:
- Monedas: $1,234.56
- Porcentajes: 85.5%
- Duraciones: 1 hora, 5 minutos
- Emojis: 🟢🟡🔴⚪

### Test 11: Gestión VIP Paginada
Flujo integrado:
1. Crear 15 suscriptores (10 activos, 5 expirados)
2. Filtrar solo activos
3. Paginar (10 por página)
4. Validar página 1 = 10 items

### Test 12: Cola Free Paginada
Flujo integrado:
1. Crear 12 solicitudes (10 pendientes, 2 procesadas)
2. Filtrar solo pendientes
3. Paginar (10 por página)
4. Validar página 1 = 10 items

## 🔧 Troubleshooting

### Error: "Database locked"
**Causa:** Tests corriendo en paralelo
**Solución:** Ejecutar con `-n 1` (sin paralelización)
```bash
pytest tests/test_e2e_onda2.py -n 1 -v
```

### Error: "Fixture not found"
**Causa:** pytest-asyncio no instalado
**Solución:** Instalar dependencia
```bash
pip install pytest-asyncio==0.21.1
```

### Error: "No module named 'bot.services.stats'"
**Causa:** Módulo StatsService no encontrado
**Solución:** Verificar que existe `bot/services/stats.py`

### Tests tardan mucho
**Causa:** Database init/close es lento
**Solución:** Normal (esperar 30 segundos aprox)

## 📝 Añadir Nuevos Tests

Template para tests E2E:

```python
@pytest.mark.asyncio
async def test_my_feature(setup_database):
    """Descripción clara del test."""
    print("\n🧪 Test N: Mi Feature")

    async with get_session() as session:
        # 1. Setup: Crear datos
        for i in range(1, 6):
            obj = MyModel(data=i)
            session.add(obj)
        await session.commit()

        # 2. Action: Ejecutar lógica
        result = await my_service.do_something(session)

        # 3. Assert: Verificar resultados
        assert result.count == 5
        assert result.is_valid == True

        # 4. Print: Confirmar éxito
        print(f"✅ Mi feature funciona")
```

## 📚 Recursos

- pytest: https://docs.pytest.org/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/
- SQLAlchemy ORM: https://docs.sqlalchemy.org/

## ✅ Checklist de Calidad

- [x] ¿Todos los tests pasan?
- [x] ¿Coverage >85% de ONDA 2?
- [x] ¿Tests son independientes?
- [x] ¿Setup/teardown funcionan?
- [x] ¿Assertions son específicas?
- [x] ¿Print statements útiles?
- [x] ¿README documenta tests?
- [x] ¿Script run_tests.sh funciona?

---

**Status:** ✅ Tests E2E ONDA 2 Completados
**Última Actualización:** 2025-12-13
