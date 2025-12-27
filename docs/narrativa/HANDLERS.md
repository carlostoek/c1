# Documentación de Handlers - Módulo Narrativo

## 📋 Descripción General

Los handlers del módulo narrativo gestionan las interacciones entre usuarios y la narrativa a través de comandos y callbacks. Incluyen flujos para mostrar fragmentos, tomar decisiones y gestionar el progreso narrativo.

## 🏗️ Estructura de Handlers

```
bot/narrative/handlers/
├── __init__.py                    # Exports y registro
├── admin/                        # Handlers de administración de narrativa
│   ├── __init__.py               # Exportación de routers de admin
│   └── narrative_admin.py        # Administración de capítulos/fragmentos
└── user/                         # Handlers de usuario narrativo
    ├── __init__.py               # Exportación de routers de usuario
    └── narrative_user.py         # Visualización y decisiones narrativas
```

## 🎯 Patrones de Handler

### Patrón General de Usuario

Todos los handlers de usuario del módulo narrativo siguen este patrón:

```python
from aiogram import Router
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from bot.narrative.services.container import NarrativeContainer

router = Router()

@router.message(Command("narrative"))
async def start_narrative(
    message: Message,
    session: AsyncSession
) -> None:
    """
    Inicia la experiencia narrativa para el usuario.
    
    Handler que permite al usuario comenzar la narrativa o continuar
    su progreso actual.
    """
    try:
        # 1. Crear contenedor de servicios
        container = NarrativeContainer(session, message.bot)
        
        # 2. Obtener progreso actual del usuario
        progress = await container.progress_service.get_user_progress(message.from_user.id)
        
        # 3. Determinar fragmento actual o inicial
        if progress and progress.current_fragment_id:
            current_fragment = await container.progress_service.get_current_fragment(message.from_user.id)
        else:
            current_fragment = await container.fragment_service.get_first_fragment()
        
        # 4. Mostrar contenido y opciones
        if current_fragment:
            await message.answer(
                text=current_fragment.content,
                reply_markup=await _create_decision_keyboard(container, message.from_user.id, current_fragment.id)
            )
        else:
            await message.answer("No hay contenido narrativo disponible en este momento.")
    
    except Exception as e:
        logger.error(f"Error en start_narrative: {e}", exc_info=True)
        await message.answer("❌ Error cargando contenido narrativo")
```

### Patrón de Callback de Decisión

Para procesar decisiones del usuario:

```python
@router.callback_query(F.data.startswith("narrative:decision:"))
async def handle_decision(
    callback: CallbackQuery,
    session: AsyncSession
) -> None:
    """
    Procesa una decisión del usuario en la narrativa.
    
    Callback data: "narrative:decision:{decision_id}"
    """
    try:
        # 1. Extraer ID de decisión
        decision_id = int(callback.data.split(":")[2])
        
        # 2. Crear contenedor
        container = NarrativeContainer(session, callback.bot)
        
        # 3. Procesar decisión
        success, message, next_fragment = await container.decision_service.make_decision(
            user_id=callback.from_user.id,
            decision_id=decision_id
        )
        
        if success:
            # 4. Actualizar vista con nuevo fragmento
            if next_fragment:
                await callback.message.edit_text(
                    text=next_fragment.content,
                    reply_markup=await _create_decision_keyboard(container, callback.from_user.id, next_fragment.id)
                )
            else:
                await callback.message.edit_text("🎉 ¡Has completado este capítulo!")
        else:
            await callback.answer(message, show_alert=True)
        
    except Exception as e:
        logger.error(f"Error en handle_decision: {e}", exc_info=True)
        await callback.answer("❌ Error procesando decisión", show_alert=True)
```

## 📚 Handlers de Usuario

### `narrative_user.py` - Experiencia Narrativa del Usuario

#### `/narrative` - Comando de Inicio Narrativo

**Responsabilidad:** Permite al usuario comenzar o continuar su experiencia narrativa.

```python
@router.message(Command("narrative"))
async def start_narrative(message: Message, session: AsyncSession) -> None:
    """
    Handler para el comando /narrative.
    
    Muestra el fragmento actual del usuario o comienza desde el inicio
    si es la primera vez que accede a la narrativa.
    """
    user_id = message.from_user.id
    
    container = NarrativeContainer(session, message.bot)
    
    try:
        # Verificar progreso existente
        progress = await container.progress_service.get_user_progress(user_id)
        
        if progress and progress.current_fragment_id:
            # Continuar desde el fragmento actual
            current_fragment = await container.progress_service.get_current_fragment(user_id)
            chapter = await container.chapter_service.get_chapter(current_fragment.chapter_id)
        else:
            # Comenzar desde el primer capítulo
            first_chapter = await container.chapter_service.get_chapters_by_type("INTRO")
            if first_chapter:
                chapter = first_chapter[0]
                first_fragment = await container.fragment_service.get_fragments_by_chapter(chapter.id)
                if first_fragment:
                    current_fragment = first_fragment[0]
                    await container.progress_service.update_user_progress(user_id, current_fragment.id)
        
        if current_fragment:
            # Validar requisitos para acceder al fragmento
            requirements = current_fragment.requirements or []
            can_access, req_message = await container.requirements_service.validate_access(
                user_id, requirements
            )
            
            if not can_access:
                await message.answer(f"🔒 {req_message}")
                return
            
            # Enviar contenido del fragmento
            keyboard = await _create_decision_keyboard(container, user_id, current_fragment.id)
            
            await message.answer(
                text=current_fragment.content,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            await message.answer("No hay contenido narrativo disponible en este momento.")
    
    except Exception as e:
        logger.error(f"Error en start_narrative: {e}", exc_info=True)
        await message.answer("Hubo un error al cargar la narrativa.")
```

#### Callback `narrative:decision:{id}` - Procesamiento de Decisiones

**Responsabilidad:** Procesa las decisiones tomadas por el usuario en la narrativa.

```python
@router.callback_query(F.data.startswith("narrative:decision:"))
async def process_user_decision(
    callback: CallbackQuery,
    session: AsyncSession
) -> None:
    """
    Procesa una decisión del usuario en la narrativa.
    
    Callback format: narrative:decision:{decision_id}
    """
    user_id = callback.from_user.id
    
    try:
        decision_id = int(callback.data.split(":")[2])
        
        container = NarrativeContainer(session, callback.bot)
        
        # Procesar decisión
        success, message, next_fragment = await container.decision_service.make_decision(
            user_id=user_id,
            decision_id=decision_id
        )
        
        if success:
            if next_fragment:
                # Validar acceso al siguiente fragmento
                requirements = next_fragment.requirements or []
                can_access, req_message = await container.requirements_service.validate_access(
                    user_id, requirements
                )
                
                if not can_access:
                    await callback.answer(req_message, show_alert=True)
                    return
                
                # Actualizar progreso
                await container.progress_service.update_user_progress(user_id, next_fragment.id)
                
                # Enviar nuevo fragmento
                keyboard = await _create_decision_keyboard(container, user_id, next_fragment.id)
                
                await callback.message.edit_text(
                    text=next_fragment.content,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            else:
                # Capítulo completado
                await callback.message.edit_text(
                    "🎉 ¡Has completado este capítulo!\n\n"
                    "Usa /narrative para continuar con el siguiente capítulo."
                )
        else:
            await callback.answer(message, show_alert=True)
        
        await callback.answer()
    
    except Exception as e:
        logger.error(f"Error en process_user_decision: {e}", exc_info=True)
        await callback.answer("Error procesando tu decisión.", show_alert=True)
```

#### Callback `narrative:chapter:{id}` - Selección de Capítulo

**Responsabilidad:** Permite al usuario seleccionar un capítulo específico para leer.

```python
@router.callback_query(F.data.startswith("narrative:chapter:"))
async def select_chapter(
    callback: CallbackQuery,
    session: AsyncSession
) -> None:
    """
    Permite al usuario seleccionar un capítulo específico.
    
    Callback format: narrative:chapter:{chapter_id}
    """
    user_id = callback.from_user.id
    chapter_id = int(callback.data.split(":")[2])
    
    container = NarrativeContainer(session, callback.bot)
    
    try:
        chapter = await container.chapter_service.get_chapter(chapter_id)
        
        if not chapter:
            await callback.answer("Capítulo no encontrado.", show_alert=True)
            return
        
        # Validar requisitos para el capítulo
        requirements = chapter.requirements or []
        can_access, req_message = await container.requirements_service.validate_access(
            user_id, requirements
        )
        
        if not can_access:
            await callback.answer(req_message, show_alert=True)
            return
        
        # Obtener primer fragmento del capítulo
        fragments = await container.fragment_service.get_fragments_by_chapter(chapter_id)
        if fragments:
            first_fragment = fragments[0]
            
            # Actualizar progreso
            await container.progress_service.update_user_progress(user_id, first_fragment.id)
            
            # Enviar fragmento
            keyboard = await _create_decision_keyboard(container, user_id, first_fragment.id)
            
            await callback.message.edit_text(
                text=first_fragment.content,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text("Este capítulo no tiene contenido disponible aún.")
    
    except Exception as e:
        logger.error(f"Error en select_chapter: {e}", exc_info=True)
        await callback.answer("Error accediendo al capítulo.", show_alert=True)
```

## 🛠️ Handlers de Administración

### `narrative_admin.py` - Administración de Contenido Narrativo

#### `/narrative_admin` - Panel de Administración

**Responsabilidad:** Muestra el panel de administración para crear y gestionar contenido narrativo.

```python
@admin_router.message(Command("narrative_admin"))
async def narrative_admin_panel(
    message: Message,
    session: AsyncSession
) -> None:
    """
    Panel de administración para gestionar contenido narrativo.
    """
    user_id = message.from_user.id
    
    if not Config.is_admin(user_id):
        await message.answer("❌ No tienes permisos para usar esta función.")
        return
    
    container = NarrativeContainer(session, message.bot)
    
    try:
        # Contar estadísticas
        chapters_count = await container.chapter_service.get_all_chapters()
        fragments_count = await container.fragment_service.get_all_fragments_count()
        
        text = (
            "<b>_PANEL DE ADMINISTRACIÓN NARRATIVO_</b>\n\n"
            f"📚 Capítulos: {len(chapters_count)}\n"
            f"📄 Fragmentos: {fragments_count}\n\n"
            "<b>Acciones disponibles:</b>\n"
            "• /create_chapter - Crear nuevo capítulo\n"
            "• /create_fragment - Crear nuevo fragmento\n"
            "• /list_chapters - Listar capítulos existentes\n"
            "• /list_fragments - Listar fragmentos existentes"
        )
        
        await message.answer(text, parse_mode="HTML")
    
    except Exception as e:
        logger.error(f"Error en narrative_admin_panel: {e}", exc_info=True)
        await message.answer("Error cargando panel de administración.")
```

#### `/create_chapter` - Crear Nuevo Capítulo

**Responsabilidad:** Inicia el proceso de creación de un nuevo capítulo narrativo.

```python
@admin_router.message(Command("create_chapter"))
async def start_chapter_creation(
    message: Message,
    session: AsyncSession
) -> None:
    """
    Inicia el proceso de creación de un nuevo capítulo.
    """
    user_id = message.from_user.id
    
    if not Config.is_admin(user_id):
        await message.answer("❌ No tienes permisos para crear capítulos.")
        return
    
    container = NarrativeContainer(session, message.bot)
    
    try:
        # Iniciar FSM para capturar datos del capítulo
        await state.set_state(NarrativeAdminStates.waiting_for_title)
        
        await message.answer(
            "📝 <b>Creación de Capítulo</b>\n\n"
            "Por favor, envía el título del nuevo capítulo:"
        )
    
    except Exception as e:
        logger.error(f"Error en start_chapter_creation: {e}", exc_info=True)
        await message.answer("Error iniciando creación de capítulo.")
```

## 🔄 Flujo de Usuarios

### Flujo de Lectura Narrativa

1. Usuario envía `/narrative`
2. Bot verifica progreso existente
3. Si no hay progreso, se comienza desde el primer capítulo
4. Bot muestra contenido del fragmento actual
5. Bot presenta opciones de decisión como botones inline
6. Usuario selecciona una decisión
7. Bot procesa la decisión con validaciones
8. Bot actualiza progreso del usuario
9. Bot muestra siguiente fragmento según decisión
10. Repetir desde paso 5 hasta completar capítulo

### Flujo de Decisión

1. Usuario presiona botón de decisión (ej: "Tomar la puerta roja")
2. Bot recibe callback "narrative:decision:{decision_id}"
3. Bot recupera información de la decisión
4. Bot valida consecuencias y requisitos de la decisión
5. Bot actualiza historial de decisiones del usuario
6. Bot determina siguiente fragmento según decisión
7. Bot actualiza posición actual del usuario
8. Bot muestra nuevo fragmento con nuevas decisiones

## 📊 Estadísticas y Seguimiento

### Progreso de Usuarios

El sistema mantiene estadísticas de:

- Fragmentos completados por usuario
- Decisiones tomadas
- Tiempo invertido
- Arquetipo detectado
- Capítulos desbloqueados

### Historial de Decisiones

Se registra:

- Cada decisión tomada
- Momento de la decisión
- Usuario que la tomó
- Consecuencias registradas
- Cambios en el estado de la narrativa

## 🔐 Validaciones y Seguridad

### Control de Acceso

Cada fragmento puede tener requisitos específicos:

- Nivel de suscripción (VIP/Free)
- Cantidad de besitos
- Arquetipo específico
- Completar capítulo previo

### Prevención de Trampas

- Validación de autorización antes de procesar decisiones
- Registro de intentos de acceso no autorizado
- Control de secuencia lógica de fragmentos

---

**Última actualización:** 2025-12-26  
**Versión:** 1.0.0