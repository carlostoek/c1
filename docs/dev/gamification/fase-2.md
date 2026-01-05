# FASE 2: ECONOMÍA DE BESITOS
## Requerimientos para Implementación - Bot "El Mayordomo del Diván"

---

## 🎯 OBJETIVO DE ESTA FASE

Implementar y conectar el sistema de economía definido en Fase 0 (economy.py) con todos los servicios del bot. Asegurar que los valores, niveles y bonificaciones funcionen correctamente.

**Resultado esperado:** Un sistema de besitos coherente donde cada acción tiene un valor definido, las rachas dan bonificaciones, y los usuarios ven su progreso reflejado en niveles narrativos.

---

## ⚠️ REGLA CRÍTICA: INTEGRACIÓN EN MENÚS

**TODOS los comandos o funcionalidades nuevas DEBEN estar accesibles desde un menú.**

Para cada handler nuevo:
1. Identificar si es para ADMIN o USER
2. Agregar botón correspondiente en el menú apropiado
3. Crear callback con prefijo correcto (admin:, user:, etc.)
4. NO dejar comandos "sueltos" solo accesibles por /comando

---

## 📚 ARCHIVOS DE REFERENCIA

| Archivo | Contenido |
|---------|-----------|
| `bot/gamification/config/economy.py` | Valores de economía (Fase 0) |
| `bot/gamification/services/besito_service.py` | Servicio de besitos existente |
| `bot/gamification/services/daily_gift.py` | Sistema de regalo diario |
| `bot/gamification/database/models.py` | Modelos de gamificación |
| `bot/utils/lucien_messages.py` | Mensajes de Lucien (Fase 1) |

---

## 📋 ENTREGABLE F2.1: CONECTAR ECONOMY CONFIG CON SERVICIOS

### Instrucción para Claude Code

```
TAREA: Integrar los valores de economy.py en los servicios existentes

ANTES DE ESCRIBIR CÓDIGO:
1. Lee bot/gamification/config/economy.py completamente
2. Lee bot/gamification/services/besito_service.py - busca valores hardcodeados
3. Lee bot/gamification/services/daily_gift.py - busca valores hardcodeados
4. Lee bot/gamification/services/reaction.py si existe
5. Busca cualquier archivo que use valores numéricos de besitos

OBJETIVO:
Reemplazar TODOS los valores hardcodeados de besitos por referencias a EconomyConfig.
Esto centraliza la configuración y permite ajustar la economía fácilmente.

ARCHIVOS A MODIFICAR:
- bot/gamification/services/besito_service.py
- bot/gamification/services/daily_gift.py
- bot/gamification/services/reaction.py (si existe)
- Cualquier otro servicio que otorgue besitos

CAMBIOS REQUERIDOS:

1. EN CADA SERVICIO, IMPORTAR:
   ```python
   from bot.gamification.config.economy import EconomyConfig
   ```

2. REEMPLAZAR VALORES HARDCODEADOS:

   ANTES:
   ```python
   besitos_amount = 10  # Valor fijo
   ```
   
   DESPUÉS:
   ```python
   besitos_amount = EconomyConfig.DAILY_GIFT_BASE
   ```

3. VALORES A BUSCAR Y REEMPLAZAR:

   | Contexto | Buscar | Reemplazar por |
   |----------|--------|----------------|
   | Reacción a publicación | 1, 0.1, etc. | EconomyConfig.REACTION_REWARD |
   | Primera reacción del día | valores fijos | EconomyConfig.DAILY_FIRST_REACTION |
   | Regalo diario | 10, 15, etc. | EconomyConfig.DAILY_GIFT_BASE |
   | Misión diaria | valores fijos | EconomyConfig.DAILY_MISSION_COMPLETE |
   | Misión semanal | valores fijos | EconomyConfig.WEEKLY_MISSION_COMPLETE |
   | Racha 7 días | valores fijos | EconomyConfig.STREAK_7_DAYS_BONUS |
   | Racha 30 días | valores fijos | EconomyConfig.STREAK_30_DAYS_BONUS |

4. SI HAY VALORES EN BASE DE DATOS (GamificationConfig):
   - Mantener la lógica de BD como override
   - Usar EconomyConfig como fallback/default
   
   Ejemplo:
   ```python
   # Primero intenta BD, si no existe usa config
   db_config = await self._get_config()
   besitos = db_config.daily_gift_besitos if db_config else EconomyConfig.DAILY_GIFT_BASE
   ```

5. VERIFICAR QUE economy.py TIENE ESTOS VALORES:
   
   Si faltan, agregarlos:
   ```python
   class EconomyConfig:
       # Recompensas por acción
       REACTION_REWARD = 0.1
       DAILY_FIRST_REACTION = 0.5
       DAILY_GIFT_BASE = 1.0
       DAILY_MISSION_COMPLETE = 1.0
       WEEKLY_MISSION_COMPLETE = 3.0
       LEVEL_EVALUATION_COMPLETE = 5.0
       
       # Bonificaciones de racha
       STREAK_7_DAYS_BONUS = 2.0
       STREAK_30_DAYS_BONUS = 10.0
       
       # Easter eggs
       EASTER_EGG_FOUND_MIN = 2.0
       EASTER_EGG_FOUND_MAX = 5.0
       
       # Referidos
       REFERRAL_REWARD = 5.0
   ```

PRUEBA:
- Cambiar un valor en economy.py
- Verificar que el cambio se refleja en el comportamiento del bot
- Sin necesidad de modificar otros archivos
```

---

## 📋 ENTREGABLE F2.2: SISTEMA DE NIVELES DEL PROTOCOLO DE ACCESO

### Instrucción para Claude Code

```
TAREA: Implementar los niveles narrativos del "Protocolo de Acceso"

ANTES DE ESCRIBIR CÓDIGO:
1. Lee bot/gamification/config/economy.py - sección LEVELS
2. Lee bot/gamification/database/models.py - modelo Level existente
3. Lee bot/gamification/services/level_service.py si existe
4. Busca cómo se asignan niveles actualmente

OBJETIVO:
Asegurar que los 7 niveles narrativos estén implementados y funcionando:
1. Visitante (0 besitos)
2. Observado (5 besitos)
3. Evaluado (15 besitos)
4. Reconocido (35 besitos)
5. Admitido (70 besitos)
6. Confidente (120 besitos)
7. Guardián de Secretos (200 besitos)

ARCHIVOS A MODIFICAR/CREAR:
- bot/gamification/config/economy.py (verificar LEVELS)
- bot/gamification/services/level_service.py
- Script de seed para crear niveles en BD

CAMBIOS REQUERIDOS:

1. VERIFICAR/AGREGAR EN economy.py:
   ```python
   LEVELS = {
       1: {"name": "Visitante", "threshold": 0, 
           "description": "Recién llegado, bajo observación de Lucien"},
       2: {"name": "Observado", "threshold": 5, 
           "description": "Lucien ha notado su presencia"},
       3: {"name": "Evaluado", "threshold": 15, 
           "description": "Ha pasado las primeras pruebas"},
       4: {"name": "Reconocido", "threshold": 35, 
           "description": "Diana sabe que existe"},
       5: {"name": "Admitido", "threshold": 70, 
           "description": "Tiene derecho a estar en el Diván"},
       6: {"name": "Confidente", "threshold": 120, 
           "description": "Lucien comparte información privilegiada"},
       7: {"name": "Guardián de Secretos", "threshold": 200, 
           "description": "El círculo más íntimo"}
   }
   ```

2. CREAR/ACTUALIZAR LEVEL SERVICE:
   
   Métodos requeridos:
   ```python
   async def get_user_level(self, user_id: int) -> dict:
       """Retorna nivel actual del usuario con info completa."""
       
   async def check_level_up(self, user_id: int, new_besitos: float) -> Optional[dict]:
       """Verifica si usuario subió de nivel. Retorna nuevo nivel o None."""
       
   async def get_progress_to_next_level(self, user_id: int) -> dict:
       """Retorna progreso hacia siguiente nivel."""
       # {current: 42, needed: 70, percentage: 60, next_level_name: "Admitido"}
   ```

3. INTEGRAR LEVEL-UP EN BESITO SERVICE:
   
   Cada vez que se otorgan besitos, verificar level-up:
   ```python
   async def grant_besitos(self, user_id, amount, ...):
       # ... otorgar besitos ...
       
       # Verificar level-up
       level_up = await self.level_service.check_level_up(user_id, new_total)
       if level_up:
           await self._notify_level_up(user_id, level_up)
       
       return granted_amount
   ```

4. NOTIFICACIÓN DE LEVEL-UP:
   
   Usar mensajes de Lucien:
   ```python
   async def _notify_level_up(self, user_id: int, level_info: dict):
       message = Lucien.format(
           f"LEVEL_UP_{level_info['level']}", 
           level_name=level_info['name']
       )
       # Enviar mensaje al usuario
   ```

5. CREAR SCRIPT DE SEED:
   
   `scripts/seed_levels.py`:
   ```python
   async def seed_levels():
       """Crea los 7 niveles en la BD."""
       from bot.gamification.config.economy import EconomyConfig
       
       for level_num, info in EconomyConfig.LEVELS.items():
           # Crear o actualizar Level en BD
           level = Level(
               name=info['name'],
               min_besitos=info['threshold'],
               order=level_num,
               description=info['description'],
               active=True
           )
           # Upsert logic
   ```

INTEGRACIÓN EN MENÚ:
- El nivel se muestra en el perfil (ya implementado en F1.3)
- NO requiere botón adicional, es informativo
```

---

## 📋 ENTREGABLE F2.3: SISTEMA DE RACHAS MEJORADO

### Instrucción para Claude Code

```
TAREA: Mejorar el sistema de rachas con bonificaciones progresivas

ANTES DE ESCRIBIR CÓDIGO:
1. Lee bot/gamification/services/daily_gift.py - lógica de rachas actual
2. Lee bot/gamification/database/models.py - UserStreak o DailyGiftClaim
3. Lee bot/gamification/config/economy.py - bonificaciones de racha
4. Lee bot/utils/lucien_messages.py - mensajes de racha

OBJETIVO:
Implementar un sistema de rachas que:
- Rastree días consecutivos de actividad
- Otorgue bonificaciones en hitos (7 días, 30 días, etc.)
- Notifique al usuario con voz de Lucien
- Se integre con el perfil del usuario

ARCHIVOS A MODIFICAR/CREAR:
- bot/gamification/services/streak_service.py (crear si no existe)
- bot/gamification/services/daily_gift.py (integrar)
- bot/utils/lucien_messages.py (verificar mensajes)

CAMBIOS REQUERIDOS:

1. CREAR STREAK SERVICE (si no existe):
   
   `bot/gamification/services/streak_service.py`:
   ```python
   class StreakService:
       """Gestión de rachas de usuario."""
       
       def __init__(self, session: AsyncSession):
           self.session = session
       
       async def update_streak(self, user_id: int) -> dict:
           """
           Actualiza racha del usuario.
           
           Returns:
               {
                   'current_streak': int,
                   'is_new_day': bool,
                   'milestone_reached': Optional[int],  # 7, 30, etc.
                   'bonus_earned': float
               }
           """
           
       async def get_streak_info(self, user_id: int) -> dict:
           """Obtiene información de racha actual."""
           
       async def check_streak_milestone(self, streak_days: int) -> Optional[float]:
           """Verifica si se alcanzó un hito y retorna bonus."""
   ```

2. HITOS DE RACHA:
   
   Definir en economy.py:
   ```python
   STREAK_MILESTONES = {
       7: {"bonus": 2.0, "message_key": "STREAK_MILESTONE_7"},
       14: {"bonus": 4.0, "message_key": "STREAK_MILESTONE_14"},
       30: {"bonus": 10.0, "message_key": "STREAK_MILESTONE_30"},
       60: {"bonus": 20.0, "message_key": "STREAK_MILESTONE_60"},
       100: {"bonus": 50.0, "message_key": "STREAK_MILESTONE_100"}
   }
   ```

3. MENSAJES DE LUCIEN PARA RACHAS:
   
   Agregar a lucien_messages.py si no existen:
   ```python
   STREAK_MILESTONE_7 = (
       "Siete días consecutivos.\n\n"
       "Una semana de dedicación. Diana ha sido notificada. "
       "Ha ganado {bonus} Besitos adicionales."
   )
   
   STREAK_MILESTONE_14 = (
       "Dos semanas sin fallar.\n\n"
       "Su constancia es... notable. +{bonus} Besitos."
   )
   
   STREAK_MILESTONE_30 = (
       "Un mes. Treinta días consecutivos.\n\n"
       "Debo admitir que estoy impresionado. Muy pocos llegan aquí. "
       "Diana tiene algo especial para usted. +{bonus} Besitos."
   )
   
   STREAK_LOST = (
       "Su racha de {days} días ha terminado.\n\n"
       "El tiempo no espera. Pero puede comenzar de nuevo."
   )
   
   STREAK_CONTINUE = (
       "Día {current} de su racha.\n\n"
       "La consistencia tiene recompensas. Continúe."
   )
   ```

4. INTEGRAR CON DAILY GIFT:
   
   Cuando usuario reclama regalo diario:
   ```python
   async def claim_daily_gift(self, user_id: int):
       # ... lógica existente ...
       
       # Actualizar racha
       streak_result = await self.streak_service.update_streak(user_id)
       
       # Verificar milestone
       if streak_result['milestone_reached']:
           bonus = streak_result['bonus_earned']
           await self._grant_milestone_bonus(user_id, bonus)
           # Notificar con mensaje de Lucien
   ```

5. MOSTRAR RACHA EN PERFIL:
   
   El perfil (F1.3) debe mostrar:
   ```
   🔥 Racha actual: {current_streak} días
   📈 Récord personal: {longest_streak} días
   ```

INTEGRACIÓN EN MENÚ:
- La racha se muestra en el perfil (callback: user:profile)
- El regalo diario tiene su propio botón (callback: user:daily_gift)
- NO crear comando separado para rachas
```

---

## 📋 ENTREGABLE F2.4: NOTIFICACIONES CONTEXTUALES DE BESITOS

### Instrucción para Claude Code

```
TAREA: Implementar notificaciones inteligentes cuando se ganan besitos

ANTES DE ESCRIBIR CÓDIGO:
1. Lee bot/gamification/services/besito_service.py
2. Lee bot/gamification/services/notification_service.py si existe
3. Lee bot/utils/lucien_messages.py - sección BESITOS
4. Revisa cómo se envían mensajes al usuario actualmente

OBJETIVO:
Cuando un usuario gana besitos, mostrar notificación contextual con voz de Lucien.
Las notificaciones deben variar según:
- Cantidad ganada
- Contexto (reacción, misión, regalo, etc.)
- Hitos alcanzados (totales redondos)

ARCHIVOS A MODIFICAR:
- bot/gamification/services/besito_service.py
- bot/gamification/services/notification_service.py (crear si no existe)
- bot/utils/lucien_messages.py (agregar mensajes faltantes)

CAMBIOS REQUERIDOS:

1. CREAR NOTIFICATION SERVICE (si no existe):
   
   `bot/gamification/services/notification_service.py`:
   ```python
   class BesitoNotificationService:
       """Maneja notificaciones de besitos."""
       
       async def notify_besitos_earned(
           self, 
           user_id: int,
           amount: float,
           source: str,  # 'reaction', 'mission', 'daily_gift', 'streak', etc.
           new_total: float
       ) -> str:
           """
           Genera y envía notificación de besitos ganados.
           
           Returns:
               Mensaje formateado para mostrar
           """
           
       async def notify_milestone(
           self,
           user_id: int,
           milestone: int  # 10, 50, 100, etc.
       ) -> str:
           """Notifica cuando se alcanza un total redondo."""
   ```

2. MENSAJES SEGÚN CONTEXTO:
   
   Agregar a lucien_messages.py:
   ```python
   # Por fuente de besitos
   BESITOS_EARNED_REACTION = (
       "+{amount} Besitos por su reacción.\n"
       "Diana aprecia la atención."
   )
   
   BESITOS_EARNED_MISSION = (
       "+{amount} Besitos por completar el encargo.\n"
       "Su diligencia ha sido recompensada."
   )
   
   BESITOS_EARNED_DAILY = (
       "+{amount} Besitos de regalo diario.\n"
       "La constancia tiene sus beneficios."
   )
   
   BESITOS_EARNED_STREAK = (
       "+{amount} Besitos por su racha de {days} días.\n"
       "La persistencia es una virtud que Diana valora."
   )
   
   BESITOS_EARNED_REFERRAL = (
       "+{amount} Besitos por traer a alguien nuevo.\n"
       "Diana aprecia que expanda su círculo."
   )
   
   # Milestones de total
   BESITOS_MILESTONE_10 = "Ha alcanzado 10 Besitos. El camino apenas comienza."
   BESITOS_MILESTONE_50 = "50 Besitos acumulados. Diana comienza a notarlo."
   BESITOS_MILESTONE_100 = "100 Besitos. Una cantidad respetable. El Gabinete tiene opciones para usted."
   BESITOS_MILESTONE_200 = "200 Besitos. Impresionante reserva. ¿Los gastará o seguirá acumulando?"
   ```

3. INTEGRAR EN BESITO SERVICE:
   
   ```python
   async def grant_besitos(self, user_id, amount, transaction_type, ...):
       # ... lógica de otorgar ...
       
       # Determinar fuente para mensaje
       source_map = {
           TransactionType.REACTION: 'reaction',
           TransactionType.MISSION: 'mission',
           TransactionType.DAILY_GIFT: 'daily_gift',
           TransactionType.STREAK_BONUS: 'streak',
           TransactionType.REFERRAL: 'referral'
       }
       source = source_map.get(transaction_type, 'generic')
       
       # Notificar
       message = await self.notification_service.notify_besitos_earned(
           user_id, amount, source, new_total
       )
       
       # Verificar milestones
       await self._check_total_milestones(user_id, new_total)
       
       return granted_amount, message
   ```

4. NO SPAM - REGLAS DE NOTIFICACIÓN:
   
   - Reacciones: notificación silenciosa (solo actualizar UI si visible)
   - Misiones: notificación completa
   - Regalo diario: notificación completa
   - Racha: notificación completa
   - Milestones: siempre notificar
   
   ```python
   SILENT_SOURCES = ['reaction']  # No enviar mensaje push
   FULL_NOTIFY_SOURCES = ['mission', 'daily_gift', 'streak', 'referral']
   ALWAYS_NOTIFY = ['milestone', 'level_up']
   ```

INTEGRACIÓN EN MENÚ:
- Las notificaciones aparecen donde el usuario está interactuando
- NO crear menú separado para notificaciones
- Si usuario está en perfil, actualizar vista
- Si usuario está en otro lugar, enviar mensaje
```

---

## 📋 ENTREGABLE F2.5: HISTORIAL DE TRANSACCIONES

### Instrucción para Claude Code

```
TAREA: Implementar vista de historial de transacciones de besitos

ANTES DE ESCRIBIR CÓDIGO:
1. Lee bot/gamification/database/models.py - BesitoTransaction
2. Lee bot/gamification/services/besito_service.py
3. Lee bot/handlers/user/besitos.py (creado en F1.6)

OBJETIVO:
Permitir al usuario ver su historial de movimientos de besitos.
Accesible desde el menú de besitos.

ARCHIVO A MODIFICAR:
- bot/gamification/handlers/user/besitos.py

CAMBIOS REQUERIDOS:

1. AGREGAR CALLBACK PARA HISTORIAL:
   
   En el menú de besitos, agregar botón:
   ```python
   buttons = [
       [{"text": "📜 Ver Historial", "callback_data": "besitos:history"}],
       [{"text": "🏛️ Ir al Gabinete", "callback_data": "shop:main"}],
       [{"text": "🔙 Volver", "callback_data": "start:main"}]
   ]
   ```

2. HANDLER DE HISTORIAL:
   
   ```python
   @router.callback_query(F.data == "besitos:history")
   async def callback_besitos_history(callback: CallbackQuery, session: AsyncSession):
       """Muestra historial de transacciones de besitos."""
       user_id = callback.from_user.id
       
       # Obtener últimas 10 transacciones
       transactions = await besito_service.get_recent_transactions(user_id, limit=10)
       
       # Formatear con voz de Lucien
       message = Lucien.BESITOS_HISTORY_HEADER
       
       if not transactions:
           message += "\n\n" + Lucien.BESITOS_HISTORY_EMPTY
       else:
           for tx in transactions:
               # Formatear cada transacción
               sign = "+" if tx.amount > 0 else ""
               date = tx.created_at.strftime("%d/%m")
               message += f"\n• {sign}{tx.amount} - {tx.description} ({date})"
       
       # Botón para volver
       keyboard = create_inline_keyboard([
           [{"text": "🔙 Volver a Besitos", "callback_data": "user:besitos"}]
       ])
       
       await callback.message.edit_text(message, reply_markup=keyboard, parse_mode="HTML")
   ```

3. MÉTODO EN BESITO SERVICE:
   
   ```python
   async def get_recent_transactions(
       self, 
       user_id: int, 
       limit: int = 10
   ) -> list[BesitoTransaction]:
       """Obtiene últimas N transacciones del usuario."""
       stmt = (
           select(BesitoTransaction)
           .where(BesitoTransaction.user_id == user_id)
           .order_by(BesitoTransaction.created_at.desc())
           .limit(limit)
       )
       result = await self.session.execute(stmt)
       return result.scalars().all()
   ```

4. MENSAJES DE LUCIEN:
   
   ```python
   BESITOS_HISTORY_HEADER = (
       "📜 <b>Registro de Movimientos</b>\n\n"
       "Sus últimas transacciones en el Diván:"
   )
   
   BESITOS_HISTORY_EMPTY = (
       "No hay movimientos registrados aún.\n\n"
       "Comience a interactuar y verá su historial aquí."
   )
   ```

5. PAGINACIÓN (OPCIONAL):
   
   Si hay muchas transacciones, agregar navegación:
   ```python
   [{"text": "⬅️ Anterior", "callback_data": "besitos:history:0"}]
   [{"text": "➡️ Siguiente", "callback_data": "besitos:history:10"}]
   ```

INTEGRACIÓN EN MENÚ:
- Accesible desde: Menú principal → Mis Besitos → Ver Historial
- Callback path: user:besitos → besitos:history
- Botón de volver regresa a vista de besitos
```

---

## 📋 ENTREGABLE F2.6: PANEL DE ECONOMÍA ADMIN

### Instrucción para Claude Code

```
TAREA: Crear panel de administración para ver y ajustar economía

ANTES DE ESCRIBIR CÓDIGO:
1. Lee bot/handlers/admin/main.py - estructura de menú admin
2. Lee bot/gamification/config/economy.py
3. Lee bot/gamification/database/models.py - GamificationConfig

OBJETIVO:
Permitir a admins ver estadísticas de economía y ajustar parámetros básicos.
Accesible desde el menú de administración.

ARCHIVO A CREAR:
- bot/gamification/handlers/admin/economy_panel.py

CAMBIOS REQUERIDOS:

1. AGREGAR AL MENÚ ADMIN:
   
   En bot/handlers/admin/main.py o donde esté el menú:
   ```python
   # Agregar botón
   [{"text": "💰 Economía", "callback_data": "admin:economy"}]
   ```

2. CREAR HANDLER DE PANEL:
   
   ```python
   @router.callback_query(F.data == "admin:economy")
   async def callback_admin_economy(callback: CallbackQuery, session: AsyncSession):
       """Panel de economía para admins."""
       
       # Obtener estadísticas
       stats = await get_economy_stats(session)
       
       message = (
           "💰 <b>Panel de Economía</b>\n\n"
           
           "📊 <b>Estadísticas Generales</b>\n"
           f"• Total besitos en circulación: {stats['total_besitos']:,.1f}\n"
           f"• Promedio por usuario: {stats['avg_besitos']:,.1f}\n"
           f"• Usuarios activos (7d): {stats['active_users']}\n\n"
           
           "📈 <b>Distribución por Nivel</b>\n"
           f"• Visitantes: {stats['level_1']}\n"
           f"• Observados: {stats['level_2']}\n"
           f"• Evaluados: {stats['level_3']}\n"
           f"• Reconocidos: {stats['level_4']}\n"
           f"• Admitidos: {stats['level_5']}\n"
           f"• Confidentes: {stats['level_6']}\n"
           f"• Guardianes: {stats['level_7']}\n\n"
           
           "⚙️ <b>Configuración Actual</b>\n"
           f"• Regalo diario: {stats['daily_gift']} besitos\n"
           f"• Reacción: {stats['reaction_reward']} besitos\n"
       )
       
       keyboard = create_inline_keyboard([
           [{"text": "📊 Ver Top Usuarios", "callback_data": "admin:economy:top"}],
           [{"text": "⚙️ Ajustar Valores", "callback_data": "admin:economy:config"}],
           [{"text": "🔙 Volver", "callback_data": "admin:main"}]
       ])
       
       await callback.message.edit_text(message, reply_markup=keyboard, parse_mode="HTML")
   ```

3. VER TOP USUARIOS:
   
   ```python
   @router.callback_query(F.data == "admin:economy:top")
   async def callback_economy_top(callback: CallbackQuery, session: AsyncSession):
       """Muestra top 10 usuarios por besitos."""
       
       top_users = await get_top_users(session, limit=10)
       
       message = "🏆 <b>Top 10 Usuarios por Besitos</b>\n\n"
       
       for i, user in enumerate(top_users, 1):
           emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
           message += f"{emoji} {user.username or user.user_id}: {user.total_besitos:,.1f}\n"
       
       keyboard = create_inline_keyboard([
           [{"text": "🔙 Volver a Economía", "callback_data": "admin:economy"}]
       ])
       
       await callback.message.edit_text(message, reply_markup=keyboard, parse_mode="HTML")
   ```

4. AJUSTAR VALORES (BÁSICO):
   
   ```python
   @router.callback_query(F.data == "admin:economy:config")
   async def callback_economy_config(callback: CallbackQuery, session: AsyncSession):
       """Muestra opciones de configuración."""
       
       message = (
           "⚙️ <b>Configuración de Economía</b>\n\n"
           "Seleccione qué desea ajustar:"
       )
       
       keyboard = create_inline_keyboard([
           [{"text": "🎁 Regalo Diario", "callback_data": "admin:economy:set:daily"}],
           [{"text": "👆 Recompensa Reacción", "callback_data": "admin:economy:set:reaction"}],
           [{"text": "🔙 Volver", "callback_data": "admin:economy"}]
       ])
       
       await callback.message.edit_text(message, reply_markup=keyboard, parse_mode="HTML")
   ```

5. FSM PARA AJUSTAR VALORES:
   
   ```python
   class EconomyConfigStates(StatesGroup):
       waiting_daily_gift = State()
       waiting_reaction_reward = State()
   
   @router.callback_query(F.data == "admin:economy:set:daily")
   async def callback_set_daily(callback: CallbackQuery, state: FSMContext):
       """Inicia FSM para ajustar regalo diario."""
       await callback.message.edit_text(
           "🎁 <b>Ajustar Regalo Diario</b>\n\n"
           "Ingrese la nueva cantidad de besitos para el regalo diario:\n"
           "(Valor actual: X besitos)"
       )
       await state.set_state(EconomyConfigStates.waiting_daily_gift)
   ```

INTEGRACIÓN EN MENÚ:
- Accesible desde: /admin → Economía
- Callback path: admin:main → admin:economy
- Solo visible para admins (usar AdminAuthMiddleware)
```

---

## 🔄 ORDEN DE IMPLEMENTACIÓN FASE 2

```
1. F2.1: Conectar Economy Config    → Base para todo
         ↓
2. F2.2: Sistema de Niveles         → Progresión del usuario
         ↓
3. F2.3: Sistema de Rachas          → Engagement diario
         ↓
4. F2.4: Notificaciones             → Feedback al usuario
         ↓
5. F2.5: Historial                  → Transparencia
         ↓
6. F2.6: Panel Admin                → Control para admins
```

---

## ✅ CRITERIOS DE ACEPTACIÓN FASE 2

### Funcionalidad
- [ ] Valores de economy.py se usan en todos los servicios
- [ ] Cambiar un valor en economy.py afecta el comportamiento
- [ ] Los 7 niveles funcionan correctamente
- [ ] Subir de nivel muestra notificación de Lucien
- [ ] Rachas se rastrean y dan bonificaciones
- [ ] Hitos de racha (7, 30 días) dan bonus
- [ ] Notificaciones varían según contexto
- [ ] Historial muestra últimas transacciones
- [ ] Panel admin muestra estadísticas

### Integración en Menús
- [ ] Historial accesible desde menú de besitos
- [ ] Panel economía accesible desde menú admin
- [ ] Todos los botones tienen callbacks correctos
- [ ] Navegación "Volver" funciona en todos los niveles

### Consistencia
- [ ] Todos los mensajes usan voz de Lucien
- [ ] Formato de besitos consistente (1 decimal si aplica)
- [ ] Nombres de niveles consistentes en todo el bot

---

## 📁 ARCHIVOS AFECTADOS (RESUMEN)

| Archivo | Cambio |
|---------|--------|
| `bot/gamification/config/economy.py` | Verificar/completar valores |
| `bot/gamification/services/besito_service.py` | Integrar EconomyConfig |
| `bot/gamification/services/level_service.py` | Crear/actualizar |
| `bot/gamification/services/streak_service.py` | Crear/actualizar |
| `bot/gamification/services/notification_service.py` | Crear |
| `bot/gamification/handlers/user/besitos.py` | Agregar historial |
| `bot/gamification/handlers/admin/economy_panel.py` | Crear |
| `bot/handlers/admin/main.py` | Agregar botón economía |
| `bot/utils/lucien_messages.py` | Agregar mensajes faltantes |
| `scripts/seed_levels.py` | Crear script de seed |
