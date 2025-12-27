# Guía de Instalación - Módulo Narrativo

## 📋 Requisitos Previos

Antes de instalar el módulo narrativo, asegúrate de tener:

- Python 3.11+
- SQLAlchemy 2.0+
- Aiogram 3.4.1+
- SQLite (o PostgreSQL para producción)
- Alembic para migraciones
- Bot de Telegram con permisos adecuados
- Módulo de gamificación instalado y configurado (requerido)

## 🚀 Instalación Paso a Paso

### 1. Aplicar Migraciones de Base de Datos

El módulo narrativo requiere una estructura de base de datos específica. Aplica las migraciones:

```bash
alembic upgrade head
```

Esto creará las 6 tablas necesarias para el sistema narrativo:

- `narrative_chapters` - Capítulos narrativos
- `narrative_fragments` - Fragmentos narrativos dentro de capítulos
- `fragment_decisions` - Opciones de decisión disponibles en fragmentos
- `fragment_requirements` - Requisitos para acceder a fragmentos
- `user_narrative_progress` - Progreso individual de usuarios
- `user_decision_history` - Historial de decisiones tomadas por usuarios

### 2. Configurar Variables de Entorno

Agrega las siguientes variables al archivo `.env`:

```env
# Configuración del Módulo Narrativo
NARRATIVE_ENABLED=true
NARRATIVE_MAX_FRAGMENTS_PER_CHAPTER=50
NARRATIVE_MAX_DECISIONS_PER_FRAGMENT=5
NARRATIVE_ARCHETYPE_THRESHOLD=0.7  # Umbral para detectar arquetipo
NARRATIVE_DEFAULT_REWARD_BESITOS=10  # Besitos por completar fragmento
NARRATIVE_SAVE_PROGRESS_INTERVAL=300  # Intervalo para guardar progreso (segundos)
NARRATIVE_MAX_HISTORY_ITEMS=1000  # Límite de historial de decisiones

# Integración con Gamificación
NARRATIVE_INTEGRATION_ENABLED=true
NARRATIVE_MISSION_COMPLETION_REWARD=true
NARRATIVE_LEVEL_BONUS_ENABLED=true
```

### 3. Inicializar Datos Básicos

Después de aplicar migraciones, es recomendable iniciar con contenido básico:

```python
# Crear capítulo introductorio
from bot.narrative.services.container import NarrativeContainer

# Inicializar contenedor
container = NarrativeContainer(session)

# Crear capítulo introductorio
chapter = await container.chapter_service.create_chapter(
    title="Capítulo Inicial",
    description="Introducción a la historia",
    chapter_type="INTRO",
    order=1
)

# Crear fragmento inicial
fragment = await container.fragment_service.create_fragment(
    chapter_id=chapter.id,
    title="Inicio de la Aventura",
    content="Eres un personaje en un mundo desconocido...",
    order=1
)
```

### 4. Integrar con el Bot Existente

Asegúrate de registrar los handlers del módulo narrativo en tu bot principal:

```python
# En main.py
from bot.narrative.handlers.user import get_user_router
from bot.narrative.handlers.admin import get_admin_router

# Registrar routers
dp.include_router(get_user_router())
dp.include_router(get_admin_router())

# Inicializar contenedor global (opcional)
from bot.narrative.services.container import set_container, NarrativeContainer
global_container = NarrativeContainer(session, bot)
set_container(global_container)
```

### 5. Configurar Sistema de Arquetipos

El módulo incluye un sistema de detección de arquetipos. Para activarlo:

```python
# En initial setup
from bot.narrative.services.archetype import ArchetypeService

# El servicio se inicializará automáticamente con el contenedor
# pero puedes configurar límites personalizados
archetype_service = await container.get_archetype_service()
await archetype_service.set_analysis_parameters(
    min_decisions_for_detection=5,
    confidence_threshold=0.7,
    analysis_interval_seconds=3600  # Analizar cada hora
)
```

## 🔧 Configuración Avanzada

### Configuración Personalizada

Puedes personalizar el comportamiento del sistema creando entradas de configuración:

```python
from bot.narrative.database.models import NarrativeConfig

config = NarrativeConfig(
    max_fragments_per_chapter=50,
    max_decisions_per_fragment=5,
    archetype_threshold=0.7,
    default_reward_besitos=10,
    save_progress_interval=300
)

session.add(config)
await session.commit()
```

### Integración con Sistema de Gamificación

Para integrar con el sistema de gamificación existente:

```python
from bot.narrative.services.orchestrator import NarrativeOrchestrator

# Crear orquestador con servicios de gamificación
orchestrator = NarrativeOrchestrator(
    db_session=session,
    bot=bot,
    gamification_container=existing_gamification_container
)

# Crear contenido con recompensas integradas
await orchestrator.create_narrative_with_rewards({
    'chapter': {
        'title': 'Capítulo VIP',
        'description': 'Contenido exclusivo para VIPs',
        'requirements': [{'type': 'VIP', 'required': True}]
    },
    'fragments': [
        {
            'title': 'Fragmento Premium',
            'content': 'Contenido exclusivo...',
            'rewards': {
                'besitos': 50,
                'mission_id': 1,
                'badge_id': 'premium_reader'
            }
        }
    ]
})
```

## 🧪 Pruebas de Instalación

Después de la instalación, puedes verificar que todo esté funcionando:

1. Verifica que las tablas se hayan creado correctamente
2. Prueba el acceso a un capítulo inicial
3. Verifica que se pueda tomar una decisión en un fragmento
4. Confirma que se registra el progreso del usuario
5. Prueba la detección de arquetipos (si está configurada)

### Pruebas Básicas

```python
# Crear contenedor y probar servicios
container = NarrativeContainer(session)

# Verificar que todos los servicios estén disponibles
assert container.chapter_service is not None
assert container.fragment_service is not None
assert container.decision_service is not None
assert container.progress_service is not None
assert container.requirements_service is not None
assert container.archetype_service is not None

# Crear capítulo de prueba
chapter = await container.chapter_service.create_chapter(
    title="Prueba",
    description="Capítulo de prueba",
    chapter_type="MAIN",
    order=1
)

# Crear fragmento de prueba
fragment = await container.fragment_service.create_fragment(
    chapter_id=chapter.id,
    title="Fragmento de Prueba",
    content="Contenido de prueba",
    order=1
)

print("✅ Módulo narrativo instalado y funcionando correctamente")
```

## 🔍 Troubleshooting

### Problemas Comunes

**Error en migraciones**: Asegúrate de que alembic esté configurado correctamente con el módulo narrativo.

**No se detectan arquetipos**: Verifica que el umbral de confianza no sea demasiado alto y que el usuario haya tomado suficientes decisiones.

**No se registran decisiones**: Confirma que el servicio esté inicializado y que se estén cumpliendo los requisitos de acceso.

### Verificación de Salud

Puedes verificar el estado del sistema con:

```python
from bot.narrative.services.container import NarrativeContainer

container = NarrativeContainer(session)
health = {
    'services_loaded': container.get_loaded_services(),
    'chapters_count': await get_chapters_count(),
    'fragments_count': await get_fragments_count(),
    'active_users': await get_active_users_count()
}
print(health)
```

## 🔄 Actualización de Versiones

Para actualizar a nuevas versiones del módulo:

1. Aplica nuevas migraciones: `alembic upgrade head`
2. Verifica la compatibilidad con tu versión actual de Aiogram
3. Prueba las funcionalidades críticas en un entorno de test
4. Actualiza la integración con gamificación si es necesario

## ✅ Verificación Final

Después de completar la instalación:

- [ ] Migraciones aplicadas correctamente
- [ ] Variables de entorno configuradas
- [ ] Capítulo inicial creado
- [ ] Fragmento inicial creado
- [ ] Handlers registrados
- [ ] Pruebas básicas pasadas
- [ ] Integración con gamificación configurada
- [ ] Sistema de arquetipos configurado

---

**Última actualización:** 2025-12-26  
**Versión:** 1.0.0