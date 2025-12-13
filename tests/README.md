# Tests - Bot Telegram VIP/Free

Suite de tests para validar funcionalidad completa del bot.

## Estructura

```
tests/
├── conftest.py           # Fixtures compartidos
├── test_e2e_flows.py     # Tests end-to-end (flujos completos)
├── test_integration.py   # Tests de integracion
└── __init__.py          # Package marker
```

## Instalacion de Dependencias

```bash
# Instalar pytest y pytest-asyncio
pip install pytest==7.4.3 pytest-asyncio==0.21.1 --break-system-packages
```

## Ejecutar Tests

### Todos los tests
```bash
pytest tests/ -v
```

### Solo tests E2E
```bash
pytest tests/test_e2e_flows.py -v
```

### Solo tests de integracion
```bash
pytest tests/test_integration.py -v
```

### Test especifico
```bash
pytest tests/test_e2e_flows.py::test_vip_flow_complete -v
```

### Con output detallado (muestra prints)
```bash
pytest tests/ -v -s
```

### Detener en primer fallo
```bash
pytest tests/ -x
```

## Tests E2E Disponibles

### `test_vip_flow_complete`
Valida flujo VIP completo:
1. Admin genera token VIP (16 caracteres)
2. Usuario canjea token (valida token, crea suscripcion)
3. Usuario obtiene acceso VIP (is_vip_active=True)
4. Verificacion en BD (token marcado usado, suscriptor activo)

**Validaciones:**
- Token generado correctamente
- Suscriptor creado con status='active'
- Token marcado como used despues del canje
- dias_remaining() > 0

### `test_free_flow_complete`
Valida flujo Free completo:
1. Usuario solicita acceso Free
2. Solicitud queda pendiente (processed=False)
3. Tiempo de espera pasa (simular request_date antigua)
4. Solicitud se procesa (processed=True, processed_at set)
5. No se procesa dos veces (segunda llamada retorna [])

**Validaciones:**
- Solicitud creada correctamente
- No se procesa inmediatamente
- Se procesa despues del wait_time
- No hay duplicacion

### `test_vip_expiration`
Valida expiracion automatica de VIP:
1. Crear VIP con expiry_date en el pasado
2. Ejecutar tarea de expiracion (expire_vip_subscribers)
3. Verificar marcado como expired (status='expired')
4. Verificar is_vip_active() retorna False

**Validaciones:**
- is_expired() detecta expiracion
- expire_vip_subscribers() marca correctamente
- Status cambio a 'expired'
- is_vip_active() retorna False

### `test_token_validation_edge_cases`
Valida casos edge de tokens:
- Token no existe: validate_token retorna False + "no encontrado"
- Token usado: validate_token retorna False + "usado"
- Token expirado: validate_token retorna False + "expirado"
- Token valido: validate_token retorna True + "valido"

**Validaciones:**
- Cada caso rechaza/acepta correctamente
- Mensajes claros y especificos

### `test_duplicate_free_request_prevention`
Valida prevencion de solicitudes duplicadas:
1. Usuario crea primera solicitud Free
2. Intenta crear segunda solicitud
3. Segunda retorna solicitud existente (no crea duplicada)

**Validaciones:**
- Primera solicitud creada
- Segunda retorna existente (mismo id)

## Tests de Integracion Disponibles

### `test_service_container_lazy_loading`
Valida que ServiceContainer carga services lazy:
- Container comienza sin services
- Primer acceso carga el service
- Acceso posterior reutiliza instancia
- get_loaded_services() muestra loaded

### `test_config_service_singleton`
Valida que BotConfig es singleton:
- BotConfig siempre tiene id=1
- Cambios persisten en BD
- Siguiente get_config() ve cambios

### `test_database_session_management`
Valida manejo de sesiones de BD:
- Multiples sesiones ven cambios reciprocos
- No hay conflictos de sesion
- Transacciones se aplican correctamente

### `test_error_handling_across_services`
Valida manejo de errores entre servicios:
- Token invalido rechazado
- Token inexistente detectado
- Solicitudes sin errores
- Mensajes claros

## Estructura de Fixtures

### `setup_database` (function scope)
```python
@pytest.fixture(scope="function")
async def setup_database():
    await init_db()
    yield
    await close_db()
```

- Inicializa BD antes de cada test
- Limpia BD despues (garantiza BD limpia)
- Scope "function" = nueva BD por test

### `mock_bot`
```python
@pytest.fixture
def mock_bot():
    bot = Mock()
    bot.get_chat = AsyncMock()
    bot.send_message = AsyncMock()
    # ... mas mocks
```

- Mock del bot de Telegram
- Todos los metodos retornan AsyncMock
- No hace llamadas reales a API Telegram

## Debugging Tests

### Ver prints en test
```bash
pytest tests/test_e2e_flows.py::test_vip_flow_complete -v -s
```

La flag `-s` muestra todos los `print()` en tests.

### Ver traceback completo
```bash
pytest tests/ --tb=long
```

Opciones: `short`, `long`, `line`, `no`

### Ejecutar test especifico con pdb
```bash
pytest tests/test_e2e_flows.py::test_vip_flow_complete -v -s --pdb
```

Se abrira debugger en asserts fallidos.

## Limpieza Manual

Si tests dejan BD sucia:
```bash
rm bot.db bot.db-shm bot.db-wal
```

Siguiente test reiniciara BD limpia.

## Expected Output

```
tests/test_e2e_flows.py::test_vip_flow_complete PASSED        [  16%]
tests/test_e2e_flows.py::test_free_flow_complete PASSED       [  33%]
tests/test_e2e_flows.py::test_vip_expiration PASSED           [  50%]
tests/test_e2e_flows.py::test_token_validation_edge_cases PASSED [  66%]
tests/test_e2e_flows.py::test_duplicate_free_request_prevention PASSED [  83%]
tests/test_integration.py::test_service_container_lazy_loading PASSED [100%]
tests/test_integration.py::test_config_service_singleton PASSED
tests/test_integration.py::test_database_session_management PASSED
tests/test_integration.py::test_error_handling_across_services PASSED

========================= 9 passed in X.XXs =========================
```

## Anti-Patterns a Evitar

- ❌ NO compartir estado entre tests (usar fixtures)
- ❌ NO hardcodear valores (usar variables descriptivas)
- ❌ NO tests muy largos (dividir en multiples tests)
- ❌ NO assertions sin mensaje (siempre incluir assert message)
- ❌ NO olvidar fixture en parametros test (test no ve BD limpia)

## Recursos

- [pytest docs](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [unittest.mock docs](https://docs.python.org/3/library/unittest.mock.html)
