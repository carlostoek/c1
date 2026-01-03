# FASE 1: LA VOZ DE LUCIEN
## Requerimientos para Implementación - Bot "El Mayordomo del Diván"

---

## 🎯 OBJETIVO DE ESTA FASE

Transformar todos los mensajes del bot de genéricos a la voz de Lucien. El bot debe "sentirse" diferente: elegante, evaluador, con personalidad consistente.

**Resultado esperado:** Un usuario que interactúe con el bot sentirá que habla con un mayordomo sofisticado, no con un bot genérico.

---

## 📚 ARCHIVOS DE REFERENCIA (FASE 0 COMPLETADA)

Estos archivos fueron creados en Fase 0 y contienen la configuración base:

| Archivo | Contenido |
|---------|-----------|
| `bot/utils/lucien_messages.py` | Biblioteca de mensajes con voz de Lucien |
| `bot/gamification/config/economy.py` | Economía de besitos, niveles, precios |
| `bot/gamification/config/archetypes.py` | 6 arquetipos y reglas de detección |
| `bot/shop/config/initial_inventory.py` | Items del Gabinete |
| `bot/narrative/config/story_content.py` | Estructura narrativa |

---

## 📋 ENTREGABLE F1.1: REESCRIBIR /start

### Instrucción para Claude Code

```
TAREA: Reescribir el comando /start para usar la voz de Lucien

ANTES DE ESCRIBIR CÓDIGO:
1. Lee completamente bot/handlers/user/start.py para entender el flujo actual
2. Lee bot/utils/lucien_messages.py para ver los mensajes disponibles (clase LucienMessages)
3. Lee bot/gamification/config/economy.py para ver la estructura de niveles
4. Revisa bot/services/container.py para entender cómo acceder a servicios

OBJETIVO:
Modificar el handler /start para que use los mensajes de LucienMessages en lugar de los mensajes genéricos actuales. Implementar flujos diferenciados según el tipo de usuario.

ARCHIVO A MODIFICAR:
bot/handlers/user/start.py

CAMBIOS REQUERIDOS:

1. IMPORTAR LucienMessages:
   from bot.utils.lucien_messages import LucienMessages, Lucien

2. FLUJOS A IMPLEMENTAR:

   FLUJO A - Usuario Completamente Nuevo (primera vez):
   - Detectar: usuario no existe en BD o es su primera interacción
   - Mensaje 1: LucienMessages.START_NEW_USER_1
   - (opcional delay de 2-3 segundos)
   - Mensaje 2: LucienMessages.START_NEW_USER_2
   - Registrar usuario en BD con nivel 1 ("Visitante")
   - Mostrar menú principal

   FLUJO B - Usuario que Regresa (< 7 días de ausencia):
   - Detectar: usuario existe, última actividad < 7 días
   - Mensaje: LucienMessages.START_RETURNING_USER
   - Formatear con: {user_name}, {days_away}
   - Mostrar menú principal

   FLUJO C - Usuario Inactivo (7-14 días):
   - Detectar: última actividad entre 7-14 días
   - Mensaje: LucienMessages.START_INACTIVE_USER
   - Mostrar menú con opción de "ponerse al día"

   FLUJO D - Usuario Muy Inactivo (14+ días):
   - Detectar: última actividad > 14 días
   - Mensaje: LucienMessages.START_LONG_INACTIVE_USER
   - Tono de "bienvenido de vuelta, mucho ha pasado"

   FLUJO E - Usuario VIP:
   - Detectar: usuario tiene suscripción VIP activa
   - Mensaje: LucienMessages.START_VIP_USER
   - Formatear con: {user_name}, {days_remaining}, {level_name}
   - Menú diferenciado para VIP

   FLUJO F - Admin:
   - Detectar: Config.is_admin(user_id)
   - Mantener redirección a /admin pero con mensaje de Lucien
   - Usar: LucienMessages.START_ADMIN (si existe) o crear uno apropiado

3. MENÚ PRINCIPAL:
   
   Botones para usuario FREE:
   - "📜 Mi Perfil" → callback: user:profile
   - "🎯 Encargos" → callback: user:missions  
   - "🏛️ El Gabinete" → callback: shop:main
   - "💋 Mis Besitos" → callback: user:besitos
   - "📖 Mi Historia" → callback: narrative:main
   - "🔑 Acceso VIP" → callback: vip:info

   Botones para usuario VIP (adicionales):
   - "⭐ Contenido Premium" → callback: premium:browse
   - "🗺️ Mapa del Deseo" → callback: mapa:info

4. ACTUALIZAR ÚLTIMA ACTIVIDAD:
   - Al procesar /start, actualizar campo last_activity del usuario
   - Esto permitirá detectar inactividad en futuras visitas

5. ELIMINAR MENSAJES GENÉRICOS:
   - Reemplazar TODO "👋 Hola {user_name}!" por mensajes de Lucien
   - Reemplazar "✅ Tienes acceso VIP activo" por versión Lucien
   - Reemplazar cualquier emoji excesivo (mantener máximo 1-2 por mensaje)

EJEMPLO DE TRANSFORMACIÓN:

ANTES (genérico):
```python
await message.answer(
    f"👋 Hola <b>{user_name}</b>!\n\n"
    f"Eres administrador. Usa /admin para gestionar los canales.",
    parse_mode="HTML"
)
```

DESPUÉS (Lucien):
```python
await message.answer(
    LucienMessages.START_ADMIN.format(user_name=user_name),
    parse_mode="HTML"
)
```

NOTAS IMPORTANTES:
- Si un mensaje de LucienMessages no existe, créalo en lucien_messages.py primero
- Mantener la lógica de deep links existente (activación de tokens)
- No romper funcionalidad existente, solo cambiar los textos
- Los delays entre mensajes son opcionales (nice-to-have)
- Usar parse_mode="HTML" para formato
```

---

## 📋 ENTREGABLE F1.2: REESCRIBIR MENÚ DINÁMICO

### Instrucción para Claude Code

```
TAREA: Actualizar el menú dinámico para usar mensajes de Lucien

ANTES DE ESCRIBIR CÓDIGO:
1. Lee bot/handlers/user/dynamic_menu.py completamente
2. Lee bot/utils/lucien_messages.py para ver mensajes disponibles
3. Revisa bot/utils/menu_helpers.py si existe

ARCHIVO A MODIFICAR:
bot/handlers/user/dynamic_menu.py

CAMBIOS REQUERIDOS:

1. IMPORTAR LucienMessages:
   from bot.utils.lucien_messages import LucienMessages, Lucien

2. CALLBACK "dynmenu:back":
   - Cuando usuario regresa al menú principal
   - Usar mensaje contextual de Lucien, no genérico
   - Ejemplo: "Ha decidido volver. Prudente." o similar

3. MENSAJES DE ERROR EN MENÚ:
   - Reemplazar "❌ Opción no disponible" por Lucien.ERROR_NOT_FOUND
   - Reemplazar "❌ Error al regresar" por Lucien.ERROR_GENERIC

4. RESPUESTAS A ITEMS DE MENÚ:
   - Cuando action_type == "info": usar formato de Lucien
   - Cuando action_type == "contact": usar formato de Lucien
   - Mantener funcionalidad pero cambiar presentación

5. CALLBACKS DE NAVEGACIÓN:
   - Agregar mensajes de transición cuando usuario navega
   - Ejemplo: al ir a tienda, mostrar bienvenida del Gabinete

EJEMPLO:

ANTES:
```python
await callback.answer("❌ Opción no disponible", show_alert=True)
```

DESPUÉS:
```python
await callback.answer(Lucien.ERROR_NOT_FOUND, show_alert=True)
```

NOTA: Los mensajes de callback.answer() tienen límite de 200 caracteres.
Usar versiones cortas para estos casos.
```

---

## 📋 ENTREGABLE F1.3: REESCRIBIR MENSAJES DE PERFIL

### Instrucción para Claude Code

```
TAREA: Actualizar la vista de perfil para usar voz de Lucien

ANTES DE ESCRIBIR CÓDIGO:
1. Busca el handler de perfil: puede estar en:
   - bot/handlers/user/profile.py
   - bot/gamification/handlers/user/profile.py
   - O como callback en start.py (callback: user:profile)
2. Lee bot/utils/lucien_messages.py sección de PERFIL
3. Lee bot/gamification/config/economy.py para niveles

ARCHIVOS A MODIFICAR:
- El handler que maneja callback "user:profile" o comando /perfil

CAMBIOS REQUERIDOS:

1. IMPORTAR:
   from bot.utils.lucien_messages import LucienMessages, Lucien
   from bot.gamification.config.economy import EconomyConfig

2. VISTA DE PERFIL DEBE MOSTRAR:
   
   Estructura del mensaje:
   ```
   [Comentario de Lucien según nivel del usuario]
   
   📊 <b>Su Expediente</b>
   
   Nivel: {level_name} ({level_number}/7)
   [Barra de progreso visual]
   Besitos: {besitos_total}
   
   [Si tiene arquetipo detectado]:
   Arquetipo: {archetype_name}
   "{archetype_description}"
   
   [Si tiene badges]:
   Distintivos: {badges_list}
   ```

3. BARRA DE PROGRESO VISUAL:
   - Usar caracteres: ▓ (lleno) y ░ (vacío)
   - 10 segmentos total
   - Ejemplo 60%: ▓▓▓▓▓▓░░░░

4. COMENTARIO DE LUCIEN SEGÚN NIVEL:
   - Nivel 1-2: Lucien.PROFILE_LEVEL_LOW (escéptico, evaluando)
   - Nivel 3-4: Lucien.PROFILE_LEVEL_MID (reconocimiento grudging)
   - Nivel 5-6: Lucien.PROFILE_LEVEL_HIGH (respeto, confianza)
   - Nivel 7: Lucien.PROFILE_LEVEL_MAX (colaborador, confidente)

5. SI NO EXISTEN LOS MENSAJES:
   Agregar a lucien_messages.py:
   
   PROFILE_HEADER = "Su expediente en el Diván. Todo queda registrado."
   
   PROFILE_LEVEL_LOW = (
       "Aún está en observación. No se lo tome personal... "
       "todos comienzan así."
   )
   
   PROFILE_LEVEL_MID = (
       "Ha demostrado cierta... persistencia. Diana comienza a notar "
       "su presencia."
   )
   
   PROFILE_LEVEL_HIGH = (
       "Debo admitir que ha superado mis expectativas iniciales. "
       "Diana habla de usted ocasionalmente."
   )
   
   PROFILE_LEVEL_MAX = (
       "Guardián de Secretos. El círculo más íntimo. "
       "Ya no necesita mi evaluación... pero la tendrá de todos modos."
   )

EJEMPLO DE SALIDA:

```
Ha demostrado cierta... persistencia. Diana comienza a notar su presencia.

📊 <b>Su Expediente</b>

Nivel: Reconocido (4/7)
▓▓▓▓▓▓░░░░ 60%
Besitos: 42.5

Arquetipo: El Paciente
"Procesa profundamente, toma su tiempo"

Distintivos: 🎭 Observador, 🔍 Explorador
```
```

---

## 📋 ENTREGABLE F1.4: REESCRIBIR TIENDA/GABINETE

### Instrucción para Claude Code

```
TAREA: Transformar la tienda en "El Gabinete de Lucien"

ANTES DE ESCRIBIR CÓDIGO:
1. Busca handlers de tienda:
   - bot/shop/handlers/user/shop.py
   - bot/handlers/user/shop.py
   - O callbacks que empiecen con "shop:"
2. Lee bot/utils/lucien_messages.py sección GABINETE/CABINET
3. Lee bot/shop/config/initial_inventory.py para items

ARCHIVOS A MODIFICAR:
- Handler(s) de tienda encontrado(s)

CAMBIOS REQUERIDOS:

1. RENOMBRAR EN UI:
   - "Tienda" → "El Gabinete"
   - "Comprar" → "Adquirir" o "Obtener"
   - "Productos" → "Artículos" o "Objetos"

2. MENSAJE DE BIENVENIDA AL GABINETE:
   Usar: Lucien.CABINET_WELCOME
   
   Si no existe, agregar:
   ```
   CABINET_WELCOME = (
       "Bienvenido a mi Gabinete.\n\n"
       "Aquí guardo ciertos artículos que Diana ha autorizado para intercambio. "
       "Los Besitos que ha acumulado pueden convertirse en algo más tangible.\n\n"
       "Examine con cuidado. No todo lo que brilla merece su inversión."
   )
   ```

3. CATEGORÍAS CON DESCRIPCIONES DE LUCIEN:
   
   Al mostrar categoría, incluir descripción:
   - Efímeros: "Placeres de un solo uso. Intensos pero fugaces."
   - Distintivos: "Marcas visibles de su posición. Para quienes valoran el reconocimiento."
   - Llaves: "Abren puertas a contenido que otros no pueden ver."
   - Reliquias: "Los objetos más valiosos. Requieren Besitos... y dignidad."

4. VISTA DE ITEM:
   Mostrar description_lucien del item, no description genérica
   (ver initial_inventory.py para las descripciones)

5. FLUJO DE COMPRA:
   
   Confirmación (antes de comprar):
   ```
   CABINET_CONFIRM_PURCHASE = (
       "¿Desea adquirir <b>{item_name}</b> por {price} Besitos?\n\n"
       "Una vez hecho, no hay devoluciones. Diana no admite arrepentimientos."
   )
   ```
   
   Éxito:
   ```
   CABINET_PURCHASE_SUCCESS = (
       "Hecho. <b>{item_name}</b> ahora le pertenece.\n\n"
       "Diana ha sido notificada de su adquisición. "
       "Úselo sabiamente... o no. La elección es suya."
   )
   ```
   
   Sin fondos:
   ```
   CABINET_INSUFFICIENT_FUNDS = (
       "Sus Besitos son insuficientes para esto.\n\n"
       "Necesita {required} y tiene {current}. "
       "Diana no otorga crédito. Vuelva cuando tenga los medios."
   )
   ```

6. BOTONES:
   - "🏛️ Ver Categorías" 
   - "📦 {categoria_name}" para cada categoría
   - "💎 Ver detalles" para items
   - "✅ Confirmar" / "❌ Cancelar" para compra
   - "🔙 Volver" para navegación
```

---

## 📋 ENTREGABLE F1.5: REESCRIBIR MISIONES/ENCARGOS

### Instrucción para Claude Code

```
TAREA: Transformar vista de misiones en "Encargos de Lucien"

ANTES DE ESCRIBIR CÓDIGO:
1. Busca handlers de misiones:
   - bot/gamification/handlers/user/missions.py
   - Callbacks con "mission:" o "user:missions"
2. Lee bot/utils/lucien_messages.py sección MISSIONS/ENCARGOS

ARCHIVOS A MODIFICAR:
- Handler(s) de misiones encontrado(s)

CAMBIOS REQUERIDOS:

1. RENOMBRAR EN UI:
   - "Misiones" → "Encargos"
   - "Completar" → "Cumplir"
   - "Recompensa" → "Reconocimiento"

2. MENSAJE DE BIENVENIDA A ENCARGOS:
   ```
   MISSIONS_WELCOME = (
       "Los Encargos del Diván.\n\n"
       "Tareas que Diana considera dignas de reconocimiento. "
       "Cumpla con ellas y será recompensado. Ignórelas... y lo notaré."
   )
   ```

3. ESTRUCTURA DE LISTA DE ENCARGOS:
   
   Agrupar por tipo:
   - 📅 Protocolos Diarios (misiones diarias)
   - 📆 Encargos Semanales (misiones semanales)
   - ⭐ Encargos Especiales (misiones únicas/eventos)
   
   Para cada misión mostrar:
   - Nombre
   - Descripción breve
   - Progreso: {current}/{target}
   - Recompensa: {besitos} Besitos

4. MENSAJES DE PROGRESO:
   
   Al actualizar progreso:
   ```
   MISSION_PROGRESS = (
       "Progreso en '<b>{mission_name}</b>': {current}/{target}\n\n"
       "{lucien_comment}"
   )
   ```
   
   Comentarios según progreso:
   - 0-25%: "Apenas ha comenzado."
   - 26-50%: "Va por buen camino."
   - 51-75%: "Más de la mitad. No se detenga ahora."
   - 76-99%: "Casi lo logra. Un último esfuerzo."

5. MENSAJE DE ENCARGO COMPLETADO:
   ```
   MISSION_COMPLETED = (
       "Encargo cumplido: <b>{mission_name}</b>\n\n"
       "Ha ganado {reward} Besitos. Diana ha sido notificada de su diligencia."
   )
   ```

6. SIN ENCARGOS DISPONIBLES:
   ```
   MISSIONS_EMPTY = (
       "No hay encargos pendientes en este momento.\n\n"
       "Diana preparará nuevas tareas pronto. "
       "Mientras tanto, explore el Diván."
   )
   ```

7. BOTONES:
   - "📋 Ver Encargos Activos"
   - "✅ Reclamar Recompensa" (si completado)
   - "🔙 Volver al Menú"
```

---

## 📋 ENTREGABLE F1.6: REESCRIBIR COMANDO /besitos (O EQUIVALENTE)

### Instrucción para Claude Code

```
TAREA: Crear o actualizar comando para ver balance de Besitos con voz de Lucien

ANTES DE ESCRIBIR CÓDIGO:
1. Busca si existe handler para besitos/puntos:
   - Puede ser comando /besitos, /puntos, /balance
   - O callback "user:besitos" o "start:favors"
2. Lee bot/utils/lucien_messages.py sección BESITOS/FAVORS
3. Lee bot/gamification/services/besito_service.py para entender el servicio

SI NO EXISTE, CREAR:
bot/handlers/user/besitos.py

SI EXISTE, MODIFICAR el archivo correspondiente

CAMBIOS REQUERIDOS:

1. VISTA DE BALANCE:
   
   Estructura del mensaje:
   ```
   [Comentario de Lucien según cantidad]
   
   💋 <b>Sus Besitos</b>
   
   Balance actual: {total}
   Nivel: {level_name}
   Para siguiente nivel: {needed} más
   
   [Historial reciente si aplica]
   ```

2. COMENTARIOS SEGÚN CANTIDAD:
   
   Agregar a lucien_messages.py si no existen:
   
   ```python
   BESITOS_BALANCE_LOW = (  # 0-10
       "Sus Besitos acumulados: <b>{total}</b>\n\n"
       "Apenas está comenzando. Diana otorga reconocimiento "
       "a quienes demuestran constancia."
   )
   
   BESITOS_BALANCE_GROWING = (  # 11-50
       "Sus Besitos acumulados: <b>{total}</b>\n\n"
       "Va construyendo su mérito. Continúe así y Diana "
       "comenzará a prestar atención."
   )
   
   BESITOS_BALANCE_GOOD = (  # 51-100
       "Sus Besitos acumulados: <b>{total}</b>\n\n"
       "Una cantidad respetable. Tiene opciones en el Gabinete. "
       "¿Los gastará o seguirá acumulando?"
   )
   
   BESITOS_BALANCE_HIGH = (  # 100+
       "Sus Besitos acumulados: <b>{total}</b>\n\n"
       "Impresionante reserva. Diana aprecia a quienes saben "
       "cuándo gastar y cuándo esperar. ¿Cuál es su estrategia?"
   )
   
   BESITOS_BALANCE_HOARDER = (  # 200+ sin gastar
       "Sus Besitos acumulados: <b>{total}</b>\n\n"
       "Acumula sin gastar. Prudente... o quizás indeciso. "
       "El Gabinete tiene objetos dignos de su inversión."
   )
   ```

3. NOTIFICACIÓN AL GANAR BESITOS:
   
   Cuando el usuario gana besitos (reacción, misión, etc.):
   ```
   BESITOS_EARNED = (
       "+{amount} Besitos.\n\n"
       "Diana lo nota."
   )
   
   BESITOS_EARNED_MILESTONE = (  # Al llegar a 50, 100, etc.
       "Ha alcanzado <b>{total}</b> Besitos.\n\n"
       "Un hito. Diana ha sido informada de su progreso."
   )
   ```

4. HISTORIAL RECIENTE (opcional):
   
   Si el servicio permite obtener últimas transacciones:
   ```
   Últimos movimientos:
   • +1.0 - Reacción diaria
   • +3.0 - Encargo completado
   • -10.0 - Adquisición: Llave del Fragmento
   ```

5. BOTONES:
   - "🏛️ Ir al Gabinete" → shop:main
   - "📊 Ver Historial" → besitos:history (si existe)
   - "🔙 Volver" → menú principal
```

---

## 📋 ENTREGABLE F1.7: CENTRALIZAR MENSAJES DE ERROR

### Instrucción para Claude Code

```
TAREA: Reemplazar todos los mensajes de error genéricos por versiones de Lucien

ANTES DE ESCRIBIR CÓDIGO:
1. Busca en TODO el proyecto mensajes que contengan:
   - "❌ Error"
   - "Ha ocurrido un error"
   - "Algo salió mal"
   - "Intente de nuevo"
   - "No disponible"
2. Lee bot/utils/lucien_messages.py sección ERRORS

ARCHIVOS A REVISAR (búsqueda global):
- bot/handlers/**/*.py
- bot/gamification/handlers/**/*.py
- bot/shop/handlers/**/*.py
- bot/narrative/handlers/**/*.py

MENSAJES DE ERROR A USAR:

1. ERROR_GENERIC (error inesperado):
   ```
   ERROR_GENERIC = (
       "Algo ha fallado en el sistema.\n\n"
       "No es culpa suya... probablemente. "
       "Intente nuevamente en unos momentos."
   )
   ```

2. ERROR_NOT_FOUND (recurso no existe):
   ```
   ERROR_NOT_FOUND = (
       "Lo que busca no existe. O ya no existe.\n\n"
       "El Diván tiene sus misterios."
   )
   ```

3. ERROR_PERMISSION (sin permisos):
   ```
   ERROR_PERMISSION = (
       "No tiene autorización para esto.\n\n"
       "Hay puertas que requieren llaves que aún no posee."
   )
   ```

4. ERROR_RATE_LIMITED (demasiadas acciones):
   ```
   ERROR_RATE_LIMITED = (
       "Demasiado rápido.\n\n"
       "La paciencia es una virtud que Diana valora. "
       "Espere un momento antes de continuar."
   )
   ```

5. ERROR_INVALID_INPUT (entrada inválida):
   ```
   ERROR_INVALID_INPUT = (
       "Eso no es lo que esperaba.\n\n"
       "Revise su entrada e intente de nuevo."
   )
   ```

6. ERROR_TIMEOUT (tiempo agotado):
   ```
   ERROR_TIMEOUT = (
       "El tiempo se ha agotado.\n\n"
       "Si desea continuar, deberá comenzar de nuevo."
   )
   ```

7. ERROR_MAINTENANCE (sistema en mantenimiento):
   ```
   ERROR_MAINTENANCE = (
       "El Diván está en mantenimiento.\n\n"
       "Diana está preparando algo. Vuelva pronto."
   )
   ```

PATRÓN DE REEMPLAZO:

ANTES:
```python
await callback.answer("❌ Error al procesar", show_alert=True)
```

DESPUÉS:
```python
from bot.utils.lucien_messages import Lucien
await callback.answer(Lucien.ERROR_GENERIC, show_alert=True)
```

NOTA: Para callback.answer() usar versiones cortas (< 200 chars).
Agregar versiones SHORT si es necesario:
```
ERROR_GENERIC_SHORT = "Algo ha fallado. Intente de nuevo."
```
```

---

## 📋 ENTREGABLE F1.8: CENTRALIZAR CONFIRMACIONES

### Instrucción para Claude Code

```
TAREA: Reemplazar mensajes de confirmación genéricos por versiones de Lucien

ANTES DE ESCRIBIR CÓDIGO:
1. Busca en TODO el proyecto mensajes que contengan:
   - "✅ Éxito"
   - "Completado"
   - "Guardado"
   - "Actualizado"
   - "Listo"
2. Lee bot/utils/lucien_messages.py sección CONFIRMATIONS

MENSAJES DE CONFIRMACIÓN A USAR:

1. CONFIRM_ACTION (acción genérica completada):
   ```
   CONFIRM_ACTION = "Hecho."
   ```

2. CONFIRM_SAVED (datos guardados):
   ```
   CONFIRM_SAVED = "Registrado en los archivos del Diván."
   ```

3. CONFIRM_PURCHASE (compra realizada):
   ```
   CONFIRM_PURCHASE = (
       "Adquisición completada.\n\n"
       "El objeto es suyo. Diana ha sido notificada."
   )
   ```

4. CONFIRM_MISSION_COMPLETE (misión terminada):
   ```
   CONFIRM_MISSION_COMPLETE = (
       "Encargo cumplido.\n\n"
       "Su diligencia ha sido recompensada con {reward} Besitos."
   )
   ```

5. CONFIRM_LEVEL_UP (subida de nivel):
   ```
   CONFIRM_LEVEL_UP = (
       "Ha ascendido a <b>{level_name}</b>.\n\n"
       "{level_comment}"
   )
   ```
   
   Comentarios por nivel:
   - Nivel 2: "Lucien ha comenzado a observarle."
   - Nivel 3: "Ha superado las primeras pruebas."
   - Nivel 4: "Diana sabe que existe."
   - Nivel 5: "Tiene derecho a estar en el Diván."
   - Nivel 6: "Lucien comparte información privilegiada con usted."
   - Nivel 7: "Guardián de Secretos. El círculo más íntimo."

6. CONFIRM_REGISTRATION (registro completado):
   ```
   CONFIRM_REGISTRATION = (
       "Su presencia ha sido registrada.\n\n"
       "Bienvenido al Diván. Todo lo que haga será... observado."
   )
   ```

PATRÓN DE REEMPLAZO:

ANTES:
```python
await message.answer("✅ Guardado exitosamente!")
```

DESPUÉS:
```python
await message.answer(Lucien.CONFIRM_SAVED, parse_mode="HTML")
```
```

---

## 🔄 ORDEN DE IMPLEMENTACIÓN FASE 1

```
1. F1.1: Reescribir /start          → Es el primer contacto, máxima prioridad
         ↓
2. F1.2: Menú dinámico              → Navegación principal
         ↓
3. F1.3: Vista de perfil            → Identidad del usuario
         ↓
4. F1.4: Gabinete (tienda)          → Economía del bot
         ↓
5. F1.5: Encargos (misiones)        → Engagement
         ↓
6. F1.6: Balance de Besitos         → Economía visible
         ↓
7. F1.7: Errores                    → Consistencia en fallos
         ↓
8. F1.8: Confirmaciones             → Consistencia en éxitos
```

---

## ✅ CRITERIOS DE ACEPTACIÓN FASE 1

Antes de pasar a Fase 2, verificar:

### Funcionalidad
- [ ] /start muestra mensajes de Lucien, no genéricos
- [ ] Flujos diferenciados funcionan (nuevo, regresa, inactivo, VIP)
- [ ] Menú principal tiene botones correctos según rol
- [ ] Perfil muestra información con voz de Lucien
- [ ] Gabinete tiene descripciones narrativas
- [ ] Encargos usan terminología correcta
- [ ] Balance de besitos tiene comentarios contextuales

### Consistencia de Voz
- [ ] Ningún mensaje usa "tú" (siempre "usted")
- [ ] Ningún mensaje tiene emojis excesivos en el TEXTO (solo en botones)
- [ ] Tono consistente: formal, elegante, evaluador
- [ ] No hay mensajes genéricos tipo "✅ Éxito!" o "❌ Error!"

### Técnico
- [ ] Todos los imports de LucienMessages funcionan
- [ ] No hay errores de formato (placeholders correctos)
- [ ] parse_mode="HTML" donde se usa formato
- [ ] Callbacks responden correctamente

---

## 📝 NOTAS PARA CLAUDE CODE

1. **Si un mensaje de LucienMessages no existe:**
   - Primero agrégalo a bot/utils/lucien_messages.py
   - Luego úsalo en el handler

2. **Para mensajes con placeholders:**
   - Usar LucienMessages.format("MESSAGE_KEY", variable=valor)
   - O Lucien.MESSAGE_KEY.format(variable=valor)

3. **Priorizar no romper funcionalidad:**
   - Si algo no está claro, mantener la lógica existente
   - Solo cambiar los textos de los mensajes

4. **Testing recomendado:**
   - Probar /start como usuario nuevo
   - Probar navegación completa del menú
   - Verificar que no hay errores de importación

---

## 📁 ARCHIVOS AFECTADOS (RESUMEN)

| Archivo | Cambio |
|---------|--------|
| `bot/utils/lucien_messages.py` | Agregar mensajes faltantes |
| `bot/handlers/user/start.py` | Reescribir completamente |
| `bot/handlers/user/dynamic_menu.py` | Actualizar mensajes |
| `bot/gamification/handlers/user/profile.py` | Actualizar mensajes |
| `bot/shop/handlers/user/shop.py` | Transformar a Gabinete |
| `bot/gamification/handlers/user/missions.py` | Transformar a Encargos |
| Handler de besitos (buscar) | Crear o actualizar |
| Múltiples handlers | Reemplazar errores/confirmaciones |
