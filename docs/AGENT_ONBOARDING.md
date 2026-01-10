# Guía de Arquitectura y Convenciones para Agentes

Este documento proporciona la información esencial que un nuevo agente o desarrollador necesita para comprender la arquitectura, las convenciones y los sistemas principales de este bot de Telegram. El objetivo es permitir realizar modificaciones y añadir nuevas funcionalidades de forma coherente y segura.

## 1. Visión General de la Arquitectura

El bot sigue un patrón de diseño claro que separa las responsabilidades en tres capas principales:

- **Handlers (Manejadores)**: Ubicados en `bot/handlers/`. Su única función es recibir las actualizaciones de Telegram (mensajes, clics en botones, etc.), procesar la entrada inicial y llamar al servicio correspondiente. **Un handler nunca debe contener lógica de negocio.**
- **Services (Servicios)**: Ubicados en `bot/services/` y en los subdirectorios de módulos como `bot/gamification/services/`. Aquí es donde reside toda la lógica de negocio. Los servicios orquestan las operaciones, procesan datos y se comunican con la capa de la base de datos.
- **Models (Modelos)**: Ubicados en `bot/database/`. Definen la estructura de los datos utilizando SQLAlchemy. Son la representación de las tablas de nuestra base de datos.

**Flujo Típico:**
`Usuario interactúa con el Bot` -> `Telegram envía un evento` -> `Un Handler lo captura` -> `El Handler llama a un Service` -> `El Service ejecuta la lógica` -> `El Service usa un Model para leer/escribir en la BD` -> `El Service devuelve el resultado al Handler` -> `El Handler responde al Usuario`.

---

## 2. El Sistema de Menús

Nuestro sistema de menús es dinámico y se construye a partir de la información de la base de datos. Esto nos da flexibilidad para modificar menús sin necesidad de redesplegar código en la mayoría de los casos.

#### Componentes Clave:
- **Modelo de Datos**: `bot/database/models_menu.py`. Define la tabla `menu_items` donde cada fila representa un botón o un elemento de menú.
- **Script de Creación (Seed)**: `scripts/seed_menus.py`. **Este es el archivo más importante para modificar la estructura de un menú.** Contiene la definición canónica de todos los menús en forma de diccionarios de Python.
- **Handlers**: Los handlers utilizan los servicios para enviar los menús a los usuarios, pero la lógica de qué botón se pulsa se gestiona a través del `callback_data`.

#### Cómo Modificar, Agregar o Quitar un Botón de un Menú:

1.  **Localiza y Edita el Script de Seed**: Abre `scripts/seed_menus.py`.
2.  **Encuentra el Menú**: Busca la lista de diccionarios correspondiente al menú que quieres cambiar (e.g., `seed_free_menu` o `seed_vip_menu`).
3.  **Modifica la Lista**:
    - **Para agregar un botón**: Añade un nuevo diccionario a la lista. Debes especificar como mínimo `title`, `action_type` y `action_content`.
    - **Para quitar un botón**: Elimina su diccionario de la lista.
    - **Para cambiar un botón**: Modifica los valores en su diccionario existente.
4.  **Define la Acción (`action_content`)**: Este es el campo más crítico. Es el `callback_data` que se enviará cuando un usuario pulse el botón. Sigue la convención `namespace:accion` (e.g., `games:main`, `shop:open`).
5.  **Ejecuta el Script de Seed**: Después de guardar los cambios, debes ejecutar el script para que los cambios se reflejen en la base de datos. El script se encarga de actualizar los menús existentes de forma segura.

```bash
# Ejemplo de cómo se podría ejecutar el script (consulta la documentación del script para los detalles exactos)
python scripts/seed_menus.py
```

---

## 3. El Sistema de Gamificación

El sistema de gamificación está diseñado para ser altamente configurable por los administradores a través de "wizards" (asistentes conversacionales) directamente en el bot.

#### Componentes Clave:
- **Wizards de Administración**:
    - **Handlers**: `bot/gamification/handlers/admin/`. Contienen los manejadores que guían al administrador. `mission_wizard.py` es un excelente ejemplo.
    - **Estados (FSM)**: `bot/gamification/states/admin.py`. Define los pasos de la conversación para cada wizard (e.g., `MissionWizardStates`).
- **Orquestador de Configuración**: `bot/gamification/services/orchestrator/configuration.py`. Este servicio es el cerebro detrás de los wizards. Recibe la configuración final del wizard y crea todos los objetos de base de datos necesarios (misiones, recompensas, condiciones) en una única operación.
- **Artefactos Principales**: Misiones, Recompensas, Niveles. Estos se combinan para crear bucles de juego para el usuario. Un agente debe poder enlazar cualquier acción del bot (disparada por un menú u otro evento) como una condición para una misión.

---

## 4. Integración: Conectando Todo

La magia ocurre cuando un botón del menú activa una funcionalidad y, potencialmente, un evento de gamificación.

**El Flujo Completo:**

1.  Un botón se define en `scripts/seed_menus.py` con `action_content = 'games:main'`.
2.  El usuario ve el menú y presiona el botón "Juegos".
3.  Telegram envía un evento `callback_query` con `data='games:main'`.
4.  Un handler, decorado con `@router.callback_query(F.data == 'games:main')`, se activa. Un ejemplo se encuentra en `bot/handlers/user/teaser_handlers.py`.
5.  Este handler llama al `GamesService` correspondiente.
6.  Si la acción de "jugar un juego" es parte de una misión de gamificación, el `GamesService` a su vez notificará al `UserGamificationService` para que registre el progreso del usuario.

El `callback_data` (`action_content` en la BD) es el pegamento que une la Interfaz de Usuario (menús) con la Lógica de Negocio (handlers y servicios). Para conectar un artefacto nuevo a la gamificación, asegúrate de que el servicio que lo gestiona interactúe con el `UserGamificationService` para registrar los eventos relevantes.
