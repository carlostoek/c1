# Módulo Narrativo - Sistema de Historias Interactivas con Decisiones

## 📋 Descripción General

El módulo narrativo es un sistema de historias interactivas que permite crear capítulos y fragmentos narrativos con decisiones del usuario, requisitos de acceso y tracking de progreso. El sistema detecta arquetipos de usuario basados en sus decisiones y adapta la narrativa en consecuencia.

## 🎯 Características Principales

- **Capítulos y fragmentos narrativos** - Estructura modular para historias
- **Decisiones del usuario** - Ramificaciones narrativas basadas en elecciones
- **Requisitos de acceso** - Control de acceso basado en VIP, besitos o arquetipo
- **Tracking de progreso** - Registro del avance del usuario en la narrativa
- **Detección de arquetipos** - Identificación de patrones de decisión del usuario
- **Integración con gamificación** - Recompensas y misiones vinculadas a la narrativa

## 🏗️ Arquitectura del Módulo

```
bot/narrative/
├── __init__.py                # Inicialización del módulo
├── database/                  # Modelos de base de datos
│   ├── __init__.py
│   ├── enums.py              # Enumeraciones (ChapterType, RequirementType, etc.)
│   └── models.py             # Modelos ORM (capítulos, fragmentos, decisiones)
├── services/                 # Lógica de negocio
│   ├── __init__.py
│   ├── archetype.py          # Detección de arquetipos de usuario
│   ├── chapter.py            # Gestión de capítulos narrativos
│   ├── container.py          # Contenedor de inyección de dependencias
│   ├── decision.py           # Procesamiento de decisiones del usuario
│   ├── fragment.py           # Gestión de fragmentos narrativos
│   ├── orchestrator.py       # Orquestador de narrativa con gamificación
│   ├── progress.py           # Seguimiento de progreso del usuario
│   └── requirements.py       # Validación de requisitos para acceso
├── handlers/                 # Handlers de comandos y callbacks
├── states/                   # Estados FSM para flujos narrativos
└── utils/                    # Utilidades auxiliares
```

## 📊 Modelos de Base de Datos

### Tipos de Capítulos (`ChapterType`)
- `INTRO`: Capítulo introductorio
- `MAIN`: Capítulo principal de la historia
- `CLIMAX`: Capítulo climático
- `CONCLUSION`: Capítulo final/conclusión

### Tipos de Requisitos (`RequirementType`)
- `VIP`: Requiere suscripción VIP
- `BESITOS`: Requiere cantidad específica de besitos
- `ARCHETYPE`: Requiere arquetipo específico del usuario
- `COMPLETED_CHAPTER`: Requiere haber completado un capítulo específico

### Tipos de Arquetipos (`ArchetypeType`)
- `IMPULSIVE`: Usuario que toma decisiones rápidas
- `CONTEMPLATIVE`: Usuario que reflexiona antes de decidir
- `SILENT`: Usuario que observa sin tomar muchas decisiones

## 🛠️ Servicios del Módulo

### 1. `NarrativeContainer` - Contenedor de Servicios

Contenedor de inyección de dependencias con lazy loading para gestionar el ciclo de vida de los servicios del módulo narrativo.

### 2. `ChapterService` - Gestión de Capítulos

Responsabilidades:
- CRUD de capítulos narrativos
- Validación de estructura de capítulo
- Consultas y listados de capítulos

### 3. `FragmentService` - Gestión de Fragmentos

Responsabilidades:
- CRUD de fragmentos narrativos
- Consultas de fragmentos por capítulo o usuario
- Validación de estructura de fragmento

### 4. `DecisionService` - Procesamiento de Decisiones

Responsabilidades:
- Procesamiento de decisiones del usuario
- Validación de decisiones y costos
- Registro en historial de decisiones
- Transición a fragmentos siguientes

### 5. `RequirementsService` - Validación de Requisitos

Responsabilidades:
- Validación de requisitos para acceso a fragmentos
- Verificación de VIP, besitos, arquetipo o capítulos completados
- Mensajes de error personalizados

### 6. `ProgressService` - Gestión de Progreso

Responsabilidades:
- Tracking de posición actual del usuario
- Registro de arquetipos detectados
- Estadísticas de progreso del usuario

### 7. `ArchetypeService` - Detección de Arquetipos

Responsabilidades:
- Análisis de patrones de respuesta del usuario
- Determinación de arquetipo (IMPULSIVE, CONTEMPLATIVE, SILENT)
- Adaptación de la narrativa según arquetipo

### 8. `NarrativeOrchestrator` - Orquestador de Narrativa

Responsabilidades:
- Integración con gamificación
- Creación de fragmentos narrativos con recompensas y misiones
- Gestión de recompensas por completar fragmentos

## 📁 Estructura de Datos

### NarrativeChapter
- `id`: ID único del capítulo
- `title`: Título del capítulo
- `description`: Descripción breve
- `chapter_type`: Tipo del capítulo (INTRO, MAIN, etc.)
- `order`: Orden de presentación
- `requirements`: Lista de requisitos para acceder
- `fragments`: Fragmentos asociados al capítulo

### NarrativeFragment
- `id`: ID único del fragmento
- `chapter_id`: Referencia al capítulo padre
- `title`: Título del fragmento
- `content`: Contenido narrativo
- `order`: Orden dentro del capítulo
- `requirements`: Requisitos para acceder a este fragmento

### FragmentDecision
- `id`: ID único de la decisión
- `fragment_id`: Fragmento al que pertenece
- `text`: Texto de la opción de decisión
- `next_fragment_id`: Fragmento destino tras la decisión
- `requirements`: Requisitos para seleccionar esta decisión
- `besitos_cost`: Costo en besitos (opcional)

### UserNarrativeProgress
- `user_id`: ID del usuario
- `current_fragment_id`: Fragmento actual del usuario
- `current_archetype`: Arquetipo detectado del usuario
- `completed_fragments`: Fragmentos completados
- `total_time_spent`: Tiempo total invertido en la narrativa

## 🔄 Flujo de Usuario Típico

1. **Inicio de narrativa**: Usuario accede al primer capítulo
2. **Validación de requisitos**: Sistema verifica si el usuario cumple requisitos
3. **Presentación de fragmento**: Se muestra contenido narrativo
4. **Toma de decisiones**: Usuario selecciona una opción disponible
5. **Procesamiento de decisión**: Sistema procesa la elección y sus consecuencias
6. **Transición**: Usuario se mueve al siguiente fragmento según decisión
7. **Actualización de progreso**: Sistema registra avance y actualiza arquetipos
8. **Bucle**: Se repite desde el paso 2 hasta completar capítulo/historia

## 🔧 Integración con Gamificación

El módulo narrativo se integra completamente con el sistema de gamificación:

- **Recompensas de besitos** por completar fragmentos
- **Misiones narrativas** que se desbloquean al tomar decisiones específicas
- **Niveles narrativos** basados en fragmentos completados
- **Badges raros** por arquetipos detectados o decisiones clave
- **Estadísticas** de participación narrativa

## 📊 Métricas y Estadísticas

- Progreso individual por usuario
- Decisiones más populares
- Arquetipos más comunes detectados
- Tiempo promedio de completión
- Tasa de finalización de capítulos
- Rendimiento de fragmentos según arquetipo

## 🚀 Inicio Rápido

### Instalación
1. Aplicar migraciones de base de datos
2. Configurar servicios en el contenedor principal
3. Registrar handlers en el router del bot

### Configuración Inicial
```python
from bot.narrative.services.container import get_container

# Obtener contenedor de servicios
container = get_container(session)

# Crear primer capítulo
chapter_service = container.chapter_service
chapter = await chapter_service.create_chapter(
    title="Capítulo Inicial",
    description="Descripción del capítulo",
    chapter_type="INTRO",
    order=1
)
```

## 🔐 Seguridad y Validaciones

- Validación de autorización para cada fragmento
- Control de acceso basado en requisitos
- Prevención de trampas o acceso anticipado
- Registro de intentos de acceso no autorizado

## 📈 Escalabilidad

- Diseño modular para añadir nuevos tipos de contenido
- Soporte para múltiples historias simultáneas
- Sistema de cache para contenido frecuente
- Integración con sistemas externos de contenido

---

**Última actualización:** 2025-12-26  
**Versión:** 1.0.0