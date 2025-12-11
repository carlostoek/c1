# Changelog

Historial de cambios, versiones y actualizaciones del bot.

## Convención de Versionado

Usamos [Semantic Versioning](https://semver.org/):
- `MAJOR.MINOR.PATCH` (ej: 1.0.0)
- MAJOR: Cambios incompatibles
- MINOR: Nuevas features (compatible)
- PATCH: Bug fixes

## Versiones

### 0.1.0 (Actual - 2025-12-11)

**Status:** ONDA 1 Fase 1.1 - MVP Básico

**Funcionalidades Completadas:**

- [x] Setup del proyecto con estructura modular
- [x] Configuración centralizada (config.py)
- [x] Base de datos con SQLAlchemy + SQLite
  - [x] Modelo BotConfig (singleton)
  - [x] Modelo InvitationToken
  - [x] Modelo VIPSubscriber
  - [x] Modelo FreeChannelRequest
- [x] Engine SQLite con WAL mode
  - [x] Context manager para sesiones
  - [x] Índices optimizados
  - [x] Foreign keys y cascades
- [x] Entry point del bot (main.py)
  - [x] Startup callback (inicialización)
  - [x] Shutdown callback (cleanup)
  - [x] Polling con long timeout
  - [x] Error handling
- [x] Documentación completa (8 documentos)
- [x] Logging configurado
- [x] .env template

**Cambios Técnicos:**

```
Initial commit:
  - Estructura base del proyecto
  - Setup inicial de Git

ONDA 1 Fase 1.1:
  + Configuración completa
  + Database models y engine
  + Main.py con startup/shutdown
  + Documentación integral
```

**Dependencias (Locked):**
```
aiogram==3.4.1
sqlalchemy==2.0.25
aiosqlite==0.19.0
APScheduler==3.10.4
python-dotenv==1.0.0
```

**Python:** 3.11+

**Notas:**
- Bot funcional pero sin handlers
- Handlers serán en Fase 1.2+
- Pronto para testing en Termux
- Documentación lista para developers

---

## Próximas Versiones

### 0.2.0 (Planeado - ONDA 1 Fase 1.2)

**Features:**
- [ ] Admin handlers (menú principal, generación de tokens)
- [ ] VIP management handlers
- [ ] Free management handlers
- [ ] Admin FSM states
- [ ] Inline keyboards

**Breaking Changes:**
- N/A

---

### 0.3.0 (Planeado - ONDA 1 Fase 1.3)

**Features:**
- [ ] User /start handler
- [ ] VIP canje handler y flow
- [ ] Free solicitud handler y flow
- [ ] User FSM states
- [ ] Callback handlers para botones

---

### 0.4.0 (Planeado - ONDA 1 Fase 1.4)

**Features:**
- [ ] DatabaseMiddleware (inyección de sesión)
- [ ] AdminAuthMiddleware (validación de permisos)
- [ ] SubscriptionService
- [ ] ChannelService
- [ ] ConfigService

---

### 0.5.0 (Planeado - ONDA 1 Fase 1.5)

**Features:**
- [ ] Background tasks con APScheduler
- [ ] Cleanup de suscriptores expirados
- [ ] Processing de cola Free
- [ ] Alerts y notificaciones
- [ ] Tests unitarios básicos

---

### 1.0.0 (Planeado - ONDA 1 Completa)

**Status:** MVP Completo funcional

**Todo de ONDA 1:**
- [x] Documentación integral
- [x] Configuración robusta
- [x] Base de datos optimizada
- [x] Entry point del bot
- [ ] Handlers admin
- [ ] Handlers user
- [ ] Middlewares
- [ ] Services
- [ ] Background tasks
- [ ] Testing básico

---

## ONDA 2 (2026+)

**Features Planeadas:**
- Redis para FSM persistente
- Webhook updates (reemplazar polling)
- Sistema de pagos/suscripción
- Estadísticas avanzadas
- Múltiples canales por categoría
- Tests completos (pytest)
- API REST (FastAPI)
- Documentación OpenAPI
- Docker support
- CI/CD (GitHub Actions)

---

## ONDA 3 (2026+)

**Features Planeadas:**
- PostgreSQL (reemplazar SQLite)
- Microservicios
- Load balancing
- Kubernetes deployment
- Redis cluster
- Monitoring (Prometheus, Grafana)
- Alerting
- 100% code coverage
- Performance optimization

---

## Breaking Changes por Versión

### 0.1.0 → 0.2.0
- Ninguno (fase inicial)

### 0.2.0 → 0.3.0
- Posible: Cambio en estructura de routers
- Posible: Cambio en nombres de states

### 0.3.0 → 0.4.0
- Middlewares obligatorios en dispatcher

### 0.4.0 → 0.5.0
- APScheduler integrado

### 0.5.0 → 1.0.0
- Ninguno (consolidación)

### 1.0.0 → 2.0.0 (ONDA 2)
- Cambios significativos en storage FSM
- Posible: Cambios en modelos de BD
- Posible: Nuevas dependencias

---

## Notas de Compatibility

### Backward Compatible
- Modelos de BD estables
- Config backward compatible
- API de servicios estable

### Forward Compatible
- Migrations futuras planeadas (Alembic)
- Extensión sin breaking changes

---

## Recursos de Actualización

### De 0.1.0 a 0.2.0
1. Actualizar `requirements.txt`
2. Ejecutar `pip install -r requirements.txt`
3. No hay cambios en config o BD
4. Leer [HANDLERS.md](./HANDLERS.md) para nuevos handlers

### De 0.x.x a 1.0.0
1. Actualizar todos los archivos
2. No hay migrations de BD necesarias
3. Testing completo recomendado

### De 1.0.0 a 2.0.0
- Se requerirán cambios en arquitectura
- Documentación de migración será proporcionada
- Período de deprecation antes de release

---

## Git Tags

```bash
# Versiones released
git tag v0.1.0    # Initial MVP
git tag v0.2.0    # Admin handlers
git tag v0.3.0    # User handlers
git tag v0.4.0    # Services & Middlewares
git tag v0.5.0    # Background tasks
git tag v1.0.0    # ONDA 1 Complete

# Ver tag específico
git checkout v0.1.0

# Ver todos tags
git tag -l
```

---

## Autores y Contribuidores

### ONDA 1 (Actual)
- Desarrollador Principal: [Your Name]
- Fecha Inicio: 2025-12-10
- Fecha Completion: 2025-12-11 (Fase 1.1)

### Contribuidores Futuros
- [Espacio para futuros contributores]

---

## Agradecimientos

- Comunidad de Aiogram
- Documentación de SQLAlchemy
- Telegram Bot API

---

## Roadmap Visual

```
MVP (0.1.0)              Admin Features (0.2.0)      User Features (0.3.0)
┌──────────────┐         ┌──────────────┐            ┌──────────────┐
│ Estructura   │────────→│ Handlers     │────────→   │ Handlers     │
│ Base de Datos│         │ Admin        │            │ User Flows   │
│ Config       │         │ VIP Mgmt     │            │ Free Flows   │
│ Entry Point  │         │ Free Mgmt    │            │ FSM States   │
└──────────────┘         └──────────────┘            └──────────────┘
    2025-12-10              2025-12-15?               2026-01-?

Services (0.4.0)         Background (0.5.0)         Complete (1.0.0)
┌──────────────┐         ┌──────────────┐            ┌──────────────┐
│ Middlewares  │────────→│ Schedulers   │────────→   │ MVP          │
│ Services     │         │ Cleanup      │            │ Functional   │
│ Dependency   │         │ Processing   │            │ Tested       │
│ Injection    │         │ Alerts       │            │ Documented   │
└──────────────┘         └──────────────┘            └──────────────┘
    2026-01-?              2026-02-?                  2026-02-?

┌──────────────────────────────────────────────────────────────────┐
│ ONDA 2: Features Avanzadas (2026+)                               │
│ Redis │ Webhook │ Payments │ Multi-Channel │ Analytics │ Testing │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ ONDA 3: Optimización (2026+)                                     │
│ PostgreSQL │ Microservices │ K8s │ Monitoring │ Performance      │
└──────────────────────────────────────────────────────────────────┘
```

---

## Cómo Contribuir

Para futuras versiones:

1. Fork del repositorio
2. Crear branch: `git checkout -b feature/descripcion`
3. Hacer cambios y commit
4. Push a branch: `git push origin feature/descripcion`
5. Crear Pull Request
6. Asegúrate de:
   - Tests pasen
   - Documentación actualizada
   - Código sigue convenciones
   - Mensaje de commit descriptivo

---

**Última actualización:** 2025-12-11
**Versión Actual:** 0.1.0 (MVP Basic)
**Estado:** ONDA 1 Fase 1.1 Completada
