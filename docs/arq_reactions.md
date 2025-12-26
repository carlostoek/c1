╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
 Plan de Implementación: Sistema de Reacciones
 Personalizadas + Broadcasting

 Fecha: 2025-12-24
 Estado: En Revisión
 Rama: dev

 ---
 📋 ANÁLISIS DEL REQUERIMIENTO

 Objetivo

 Transformar el sistema de reacciones de "Telegram
 nativas" (que NO funcionan en canales) a "Botones de
 Reacción Personalizados" que SÍ trackean quién
 reacciona, permitiendo:
 - Gamificación de publicaciones en canales VIP/Free
 - Otorgar besitos por reaccionar
 - Estadísticas de engagement
 - Protección de contenido opcional

 Problema Identificado

 Sistema Actual:
 - reaction_hook.py procesa MessageReactionUpdated
 (eventos nativos de Telegram)
 - ❌ NO funciona en canales: Los canales NO emiten
 user_id en eventos de reacción
 - Resultado: Sistema de gamificación no aplicable a
 publicaciones de broadcasting

 Solución Propuesta:
 - Cambio de paradigma: Reacciones Nativas → Botones
 Inline
 - Usuario presiona botón → Callback con user_id → ✅
 Trackeable

 ---
 🔍 DISCREPANCIAS ENTRE DISEÑO Y SISTEMA ACTUAL

 1. Modelos de BD

 Propuesto en arq_reactions.md:
 - BroadcastMessage (NUEVO): Registra cada publicación
 enviada
 - CustomReaction (NUEVO): Trackea clicks en botones
 - ReactionType (MODIFICADO): Agregar button_emoji,
 button_label, sort_order

 Estado Actual:
 - ❌ BroadcastMessage NO existe
 - ❌ CustomReaction NO existe
 - ⚠️ ReactionType existe en gamificación pero SIN
 campos de UI (button_emoji, button_label, sort_order)
 - ✅ Existe Reaction y UserReaction en gamificación
 (pero para reacciones nativas)

 Acción Requerida:
 - Crear BroadcastMessage en bot/database/models.py
 - Crear CustomReaction en
 bot/gamification/database/models.py
 - Modificar modelo Reaction (renombrar o extender) en
 gamificación
 - Migración de BD

 ---
 2. Estados FSM

 Propuesto:
 class BroadcastStates(StatesGroup):
     waiting_for_content = State()
     waiting_for_confirmation = State()  # ← Ya NO es
 final
     configuring_options = State()       # ⭐ NUEVO
     selecting_reactions = State()       # ⭐ NUEVO

 Estado Actual:
 class BroadcastStates(StatesGroup):
     waiting_for_content = State()
     waiting_for_confirmation = State()  # ← ES final
     selecting_reactions = State()       # ✅ Existe
 pero NO usado

 Acción Requerida:
 - Agregar configuring_options State
 - Modificar flujo para insertar paso de configuración
 ANTES de waiting_for_confirmation

 ---
 3. Servicios

 Propuesto:
 - CustomReactionService (NUEVO): Gestiona reacciones
 por botones
   - register_custom_reaction()
   - get_user_reactions_for_message()
   - get_message_reaction_stats()
 - BroadcastService.send_broadcast_with_gamification()
 (MODIFICADO)

 Estado Actual:
 - ❌ CustomReactionService NO existe
 - ⚠️ BroadcastService NO existe como servicio (solo
 handlers en broadcast.py)
 - ✅ ChannelService existe con send_to_channel()
 - ✅ ReactionService existe en gamificación (pero para
  reacciones nativas)

 Acción Requerida:
 - Crear CustomReactionService en
 bot/gamification/services/
 - Crear BroadcastService en bot/services/ o extender
 ChannelService
 - Integrar con BesitoService para otorgar puntos

 ---
 4. Handlers

 Propuesto:
 - Modificar broadcast.py: Agregar paso
 configuring_options
 - Nuevo reactions.py: Handler de callbacks
 react:{reaction_type_id}

 Estado Actual:
 - ✅ bot/handlers/admin/broadcast.py existe
 - Flujo actual: waiting_for_content →
 waiting_for_confirmation (2 pasos)
 - ❌ NO hay paso de configuración de reacciones
 - ❌ NO existe handler para callbacks de reacciones de
  usuario

 Acción Requerida:
 - Extender broadcast.py con nuevos handlers
 - Crear bot/gamification/handlers/user/reactions.py

 ---
 🎯 PLAN DE IMPLEMENTACIÓN (11 TAREAS)

 FASE 1: Fundamentos de BD y Servicios (No rompe nada
 existente)

 T1: Modelos de Base de Datos

 Archivo: bot/database/models.py,
 bot/gamification/database/models.py

 Subtareas:
 1. Crear modelo BroadcastMessage en
 bot/database/models.py:
 class BroadcastMessage(Base):
     __tablename__ = "broadcast_messages"

     id = Column(Integer, primary_key=True)
     message_id = Column(BigInteger, nullable=False)
     chat_id = Column(BigInteger, nullable=False)
     content_type = Column(String(20), nullable=False)
  # "text", "photo", "video"
     content_text = Column(Text, nullable=True)
     media_file_id = Column(String(200), nullable=True)
     sent_by = Column(BigInteger,
 ForeignKey("users.user_id"), nullable=False)
     sent_at = Column(DateTime,
 default=datetime.utcnow, nullable=False)

     # Gamification
     gamification_enabled = Column(Boolean,
 default=False)
     reaction_buttons = Column(JSON, default=list)  #
 Lista de configs
     content_protected = Column(Boolean, default=False)

     # Stats cache
     total_reactions = Column(Integer, default=0)
     unique_reactors = Column(Integer, default=0)

     # Índices
     __table_args__ = (
         Index('idx_chat_message', 'chat_id',
 'message_id', unique=True),
         Index('idx_sent_at', 'sent_at'),
     )
 2. Crear modelo CustomReaction en
 bot/gamification/database/models.py:
 class CustomReaction(Base):
     __tablename__ = "custom_reactions"

     id = Column(Integer, primary_key=True)
     broadcast_message_id = Column(Integer,
 ForeignKey("broadcast_messages.id"), nullable=False)
     user_id = Column(BigInteger,
 ForeignKey("users.user_id"), nullable=False)
     reaction_type_id = Column(Integer,
 ForeignKey("reactions.id"), nullable=False)
     emoji = Column(String(10), nullable=False)
     besitos_earned = Column(Integer, nullable=False,
 default=0)
     created_at = Column(DateTime,
 default=datetime.utcnow, nullable=False)

     # Relaciones
     broadcast_message =
 relationship("BroadcastMessage",
 back_populates="reactions")
     user = relationship("User")
     reaction_type = relationship("Reaction")

     # Índices
     __table_args__ = (
         Index('idx_unique_reaction',
 'broadcast_message_id', 'user_id', 'reaction_type_id',
  unique=True),
         Index('idx_user_created', 'user_id',
 'created_at'),
     )
 3. Modificar modelo Reaction en
 bot/gamification/database/models.py:
   - Agregar campos:
       - button_emoji = Column(String(10),
 nullable=True)
     - button_label = Column(String(50), nullable=True)
     - sort_order = Column(Integer, default=0)
 4. Crear migración Alembic:
 alembic revision -m "Add BroadcastMessage and
 CustomReaction models"

 Tests:
 - Validar creación de modelos
 - Validar índices
 - Validar relaciones

 ---
 T2: CustomReactionService

 Archivo: bot/gamification/services/custom_reaction.py
 (NUEVO)

 Implementar métodos:
 class CustomReactionService:
     async def register_custom_reaction(
         self,
         broadcast_message_id: int,
         user_id: int,
         reaction_type_id: int,
         emoji: str
     ) -> dict:
         """
         Registra reacción cuando usuario presiona
 botón.

         Returns:
             {
                 "success": True,
                 "besitos_earned": 10,
                 "total_besitos": 1245,
                 "already_reacted": False,
                 "multiplier_applied": 1.5  # Si hay
 multiplicador
             }
         """
         # 1. Verificar si ya reaccionó con este emoji
         # 2. Obtener ReactionType para saber besitos
         # 3. Calcular besitos (con multiplicador si
 aplica)
         # 4. Crear CustomReaction
         # 5. Otorgar besitos via BesitoService
         # 6. Actualizar stats del mensaje
         # 7. Emitir evento
         # 8. Retornar resultado

     async def get_user_reactions_for_message(
         self,
         broadcast_message_id: int,
         user_id: int
     ) -> list[int]:
         """
         Retorna IDs de reaction_types que el usuario
 ya usó.
         Para marcar botones como "ya reaccionado".
         """

     async def get_message_reaction_stats(
         self,
         broadcast_message_id: int
     ) -> dict:
         """
         Stats de reacciones de un mensaje.

         Returns:
             {
                 "👍": 45,
                 "❤️": 32,
                 "🔥": 28
             }
         """

     async def _update_message_stats(
         self,
         broadcast_message_id: int
     ):
         """
         Actualiza cache de stats en BroadcastMessage.
         """

 Integración:
 - Agregar al GamificationContainer
 - Inyectar BesitoService para otorgar puntos

 Tests:
 - Test: Registrar reacción válida
 - Test: Prevenir reacciones duplicadas
 - Test: Calcular besitos correctamente
 - Test: Aplicar multiplicadores

 ---
 T3: BroadcastService

 Archivo: bot/services/broadcast.py (NUEVO)

 Implementar métodos:
 class BroadcastService:
     async def send_broadcast_with_gamification(
         self,
         target: str,  # "vip", "free", "both"
         content_type: str,
         content_text: str,
         media_file_id: Optional[str] = None,
         sent_by: int = None,
         gamification_config: Optional[dict] = None,
         content_protected: bool = False
     ) -> dict:
         """
         Envía broadcast con configuración de
 gamificación.

         gamification_config = {
             "enabled": True,
             "reaction_types": [1, 2, 3]  # IDs de
 Reaction
         }
         """
         # 1. Determinar canales destino
         # 2. Construir inline keyboard si gamification
  habilitado
         # 3. Enviar mensaje a cada canal
         # 4. Registrar en BroadcastMessage si
 gamification habilitado
         # 5. Retornar resultados

     async def _build_reaction_keyboard(
         self,
         reaction_type_ids: list[int]
     ) -> InlineKeyboardMarkup:
         """
         Construye teclado de botones de reacción.
         Máximo 3 botones por fila.
         """

     async def _build_reaction_config(
         self,
         reaction_type_ids: list[int]
     ) -> list[dict]:
         """
         Construye JSON de configuración de reacciones.

         Returns:
             [
                 {"emoji": "👍", "label": "Me Gusta",
 "reaction_type_id": 1, "besitos": 10},
                 ...
             ]
         """

     def _get_target_channels(self, target: str) ->
 list[str]:
         """
         Obtiene IDs de canales según target.
         """

 Integración:
 - Agregar al ServiceContainer
 - Usar ChannelService para envío real
 - Usar ConfigService para obtener IDs de canales

 Tests:
 - Test: Envío con gamificación habilitada
 - Test: Envío sin gamificación (backward compatible)
 - Test: Construcción de keyboard correcta
 - Test: Protección de contenido aplicada

 ---
 FASE 2: Extensión de Broadcasting

 T4: Extender Estados FSM

 Archivo: bot/states/admin.py

 Modificaciones:
 class BroadcastStates(StatesGroup):
     """
     Flujo completo (4 pasos):
     1. Admin envía contenido
     2. Bot muestra preview del contenido
     3. ⭐ NUEVO: Configurar opciones (reacciones +
 protección)
     4. Preview final + Confirmar
     5. Enviar con configuración
     """
     waiting_for_content = State()
     configuring_options = State()       # ⭐ NUEVO
     selecting_reactions = State()       # ✅ Ya existe
     waiting_for_confirmation = State()  # ← Ya no es
 el segundo paso

 Documentación:
 - Actualizar docstring del flujo completo
 - Ejemplos de transiciones

 ---
 T5: Modificar broadcast.py - Paso de Configuración

 Archivo: bot/handlers/admin/broadcast.py

 Modificaciones principales:

 1. Modificar process_broadcast_content():
   - Cambiar: await state.set_state(BroadcastStates.wai
 ting_for_confirmation)
   - Por: await
 state.set_state(BroadcastStates.configuring_options)
   - Llamar a show_broadcast_options()
 2. Nuevo handler: show_broadcast_options()
 async def show_broadcast_options(message: Message,
 state: FSMContext):
     """
     Muestra opciones de gamificación y protección.
     """
     data = await state.get_data()
     gamif_enabled = data.get("gamification_enabled",
 False)
     protected = data.get("content_protected", False)
     selected_reactions =
 data.get("selected_reactions", [])

     # Construir texto con status
     # Construir keyboard dinámico
     # Enviar mensaje
 3. Nuevo handler: show_reaction_selection()
 @admin_router.callback_query(
     F.data == "broadcast:config:reactions",
     BroadcastStates.configuring_options
 )
 async def show_reaction_selection(callback:
 CallbackQuery, state: FSMContext):
     """
     Muestra selector de reacciones.
     """
     await
 state.set_state(BroadcastStates.selecting_reactions)

     # Obtener todas las reacciones disponibles
     # Construir keyboard con checkboxes
     # Enviar mensaje
 4. Nuevo handler: toggle_reaction()
 @admin_router.callback_query(
     F.data.startswith("broadcast:react:toggle:"),
     BroadcastStates.selecting_reactions
 )
 async def toggle_reaction(callback: CallbackQuery,
 state: FSMContext):
     """
     Toggle selección de reacción.
     """
     reaction_type_id =
 int(callback.data.split(":")[-1])

     # Agregar/quitar de selected_reactions en FSM
     # Refrescar display
 5. Nuevo handler: confirm_reactions()
 @admin_router.callback_query(
     F.data == "broadcast:react:confirm",
     BroadcastStates.selecting_reactions
 )
 async def confirm_reactions(callback: CallbackQuery,
 state: FSMContext):
     """
     Confirma selección de reacciones.
     """
     # Validar que hay al menos una seleccionada
     # Marcar gamification_enabled=True
     # Volver a configuring_options
 6. Nuevo handler: toggle_protection()
 @admin_router.callback_query(
     F.data.startswith("broadcast:config:protection_"),
     BroadcastStates.configuring_options
 )
 async def toggle_protection(callback: CallbackQuery,
 state: FSMContext):
     """
     Toggle protección de contenido.
     """
     action = callback.data.split("_")[-1]  # "on" o
 "off"
     await state.update_data(content_protected=(action
 == "on"))
     # Refrescar opciones
 7. Modificar callback_broadcast_confirm():
   - Obtener gamification_config de FSM
   - Usar
 BroadcastService.send_broadcast_with_gamification() en
  lugar de ChannelService.send_to_channel()

 Callbacks nuevos:
 - broadcast:config:reactions - Activar/configurar
 reacciones
 - broadcast:config:gamif_off - Desactivar gamificación
 - broadcast:config:protection_on - Activar protección
 - broadcast:config:protection_off - Desactivar
 protección
 - broadcast:react:toggle:{id} - Toggle reacción
 - broadcast:react:confirm - Confirmar selección
 - broadcast:react:cancel - Cancelar selección

 Tests:
 - Test: Flujo completo con reacciones
 - Test: Flujo sin reacciones (backward compatible)
 - Test: Toggle protección
 - Test: Validación de al menos 1 reacción

 ---
 FASE 3: Handler de Reacciones de Usuario

 T6: Handler de Callbacks de Reacciones

 Archivo: bot/gamification/handlers/user/reactions.py
 (NUEVO)

 Implementar:
 from aiogram import Router, F
 from aiogram.types import CallbackQuery
 from sqlalchemy.ext.asyncio import AsyncSession

 from bot.gamification.services.container import
 GamificationContainer
 from bot.database.models import BroadcastMessage

 router = Router(name="gamification_reactions")

 @router.callback_query(F.data.startswith("react:"))
 async def handle_reaction_button(
     callback: CallbackQuery,
     session: AsyncSession
 ):
     """
     Maneja cuando usuario presiona botón de reacción.

     Callback data format: "react:{reaction_type_id}"
     """
     # 1. Extraer reaction_type_id
     reaction_type_id =
 int(callback.data.split(":")[1])

     # 2. Obtener info del mensaje
     message_id = callback.message.message_id
     chat_id = callback.message.chat.id
     user_id = callback.from_user.id

     # 3. Buscar BroadcastMessage
     broadcast_msg = await session.execute(
         select(BroadcastMessage).where(
             BroadcastMessage.message_id == message_id,
             BroadcastMessage.chat_id == chat_id
         )
     )
     broadcast_msg = broadcast_msg.scalar_one_or_none()

     if not broadcast_msg:
         await callback.answer("⚠️ Mensaje no
 encontrado", show_alert=True)
         return

     # 4. Registrar reacción
     container = GamificationContainer(session,
 callback.bot)
     result = await
 container.custom_reaction.register_custom_reaction(
         broadcast_message_id=broadcast_msg.id,
         user_id=user_id,
         reaction_type_id=reaction_type_id,
         emoji=await
 get_emoji_for_reaction_type(reaction_type_id)
     )

     # 5. Respuesta al usuario
     if not result["success"]:
         if result.get("already_reacted"):
             await callback.answer("Ya reaccionaste con
  este emoji 😊")
         else:
             await callback.answer("⚠️ Error al
 registrar reacción", show_alert=True)
         return

     besitos = result["besitos_earned"]
     total = result["total_besitos"]
     response = f"¡+{besitos} besitos! 🎉\nTotal:
 {total:,} besitos"

     if result.get("multiplier_applied"):
         mult = result["multiplier_applied"]
         response += f"\n✨ Multiplicador x{mult}
 aplicado"

     await callback.answer(response, show_alert=False)

     # 6. Actualizar botones para marcar como
 reaccionado
     user_reactions = await container.custom_reaction.g
 et_user_reactions_for_message(
         broadcast_msg.id, user_id
     )
     updated_keyboard = await
 build_reaction_keyboard_with_marks(
         broadcast_msg.reaction_buttons,
         user_reactions
     )

     try:
         await callback.message.edit_reply_markup(reply
 _markup=updated_keyboard)
     except:
         pass  # Si falla editar, no pasa nada


 async def build_reaction_keyboard_with_marks(
     reaction_config: list[dict],
     user_reacted_ids: list[int],
     session: AsyncSession,
     broadcast_message_id: int
 ) -> InlineKeyboardMarkup:
     """
     Construye keyboard con contadores públicos y
 checkmark personal.

     Formato:
     - Usuario NO ha reaccionado: "❤️ 33"
     - Usuario SÍ ha reaccionado: "❤️ 33 ✓"
     """
     # Obtener stats de reacciones
     stats = await get_reaction_counts(session,
 broadcast_message_id)

     buttons = []
     for config in reaction_config:
         rt_id = config["reaction_type_id"]
         emoji = config["emoji"]

         # Obtener contador público
         count = stats.get(rt_id, 0)

         # Formato: "❤️ 33" o "❤️ 33 ✓"
         if rt_id in user_reacted_ids:
             text = f"{emoji} {count} ✓"
         else:
             text = f"{emoji} {count}"

         buttons.append(
             InlineKeyboardButton(
                 text=text,
                 callback_data=f"react:{rt_id}"
             )
         )

     # 3 botones por fila
     keyboard = []
     for i in range(0, len(buttons), 3):
         keyboard.append(buttons[i:i+3])

     return
 InlineKeyboardMarkup(inline_keyboard=keyboard)


 async def get_reaction_counts(
     session: AsyncSession,
     broadcast_message_id: int
 ) -> dict[int, int]:
     """
     Obtiene contadores de reacciones por
 reaction_type_id.

     Returns:
         {1: 45, 2: 33, 3: 28}  # reaction_type_id →
 count
     """
     result = await session.execute(
         select(
             CustomReaction.reaction_type_id,

 func.count(CustomReaction.id).label("count")
         ).where(
             CustomReaction.broadcast_message_id ==
 broadcast_message_id
         ).group_by(CustomReaction.reaction_type_id)
     )

     return {row.reaction_type_id: row.count for row in
  result.all()}

 Integración:
 - Registrar router en main.py
 - Aplicar DatabaseMiddleware

 Tests:
 - Test: Usuario reacciona y gana besitos
 - Test: Prevenir duplicados
 - Test: Marcar botón como presionado
 - Test: Aplicar multiplicadores

 ---
 FASE 4: Features Adicionales

 T7: Protección de Contenido

 Archivos: broadcast.py, BroadcastService

 Implementar:
 - Ya implementado en T5 y T3
 - Validar que protect_content=True se pasa
 correctamente a Telegram API

 Tests:
 - Test: Mensaje con protección activada
 - Test: Mensaje sin protección (default)

 ---
 T8: Estadísticas de Broadcasting

 Archivo: bot/gamification/services/stats.py
 (MODIFICAR)

 Agregar métodos:
 class GamificationStatsService:
     async def get_broadcast_reaction_stats(
         self,
         broadcast_message_id: int
     ) -> dict:
         """
         Stats de reacciones de una publicación.

         Returns:
             {
                 "total_reactions": 1234,
                 "unique_users": 567,
                 "breakdown": {
                     "👍": 456,
                     "❤️": 345,
                     "🔥": 433
                 },
                 "besitos_distributed": 12340,
                 "top_reactors": [
                     {"user_id": 123, "username":
 "user1", "reactions": 3},
                     ...
                 ]
             }
         """

     async def get_top_performing_broadcasts(
         self,
         limit: int = 10
     ) -> list:
         """
         Publicaciones con más engagement.

         Returns:
             [
                 {
                     "broadcast_id": 1,
                     "sent_at": datetime,
                     "channel": "VIP",
                     "total_reactions": 1234,
                     "unique_reactors": 567
                 },
                 ...
             ]
         """

 Tests:
 - Test: Stats de publicación sin reacciones
 - Test: Stats de publicación con reacciones
 - Test: Top broadcasts ordenados correctamente

 ---
 FASE 5: Testing y Refinamiento

 T9: Seed de Datos Iniciales

 Archivo: scripts/seed_reactions.py (NUEVO)

 Crear reacciones predeterminadas:
 reactions = [
     {"emoji": "👍", "label": "Me Gusta", "besitos":
 10, "sort_order": 1},
     {"emoji": "❤️", "label": "Me Encanta", "besitos":
 15, "sort_order": 2},
     {"emoji": "🔥", "label": "Increíble", "besitos":
 20, "sort_order": 3},
     {"emoji": "😂", "label": "Divertido", "besitos":
 10, "sort_order": 4},
     {"emoji": "😮", "label": "Sorprendente",
 "besitos": 15, "sort_order": 5},
 ]

 Ejecutar:
 python scripts/seed_reactions.py

 ---
 T10: Tests E2E

 Archivo: tests/test_custom_reactions_e2e.py (NUEVO)

 Tests a implementar:
 1. test_broadcast_with_reactions_full_flow(): Flujo
 completo
 2. test_user_reacts_and_earns_besitos(): Usuario
 reacciona
 3. test_prevent_duplicate_reactions(): Prevenir
 duplicados
 4. test_reaction_stats_accurate(): Estadísticas
 correctas
 5. test_broadcast_without_reactions(): Backward
 compatible

 ---
 T11: Migración y Documentación

 Archivos: alembic/versions/, docs/

 Migración:
 alembic revision -m "Add custom reactions and
 broadcast message tracking"
 alembic upgrade head

 Documentación:
 - Actualizar docs/ARCHITECTURE.md con nuevo sistema
 - Crear docs/gamification/CUSTOM_REACTIONS.md con
 detalles técnicos
 - Actualizar docs/HANDLERS.md con nuevos handlers

 ---
 📁 ARCHIVOS CRÍTICOS

 Nuevos

 - bot/database/models.py - Agregar BroadcastMessage
 - bot/gamification/database/models.py - Agregar
 CustomReaction
 - bot/gamification/services/custom_reaction.py - NUEVO
 - bot/services/broadcast.py - NUEVO
 - bot/gamification/handlers/user/reactions.py - NUEVO
 - tests/test_custom_reactions_e2e.py - NUEVO
 - scripts/seed_reactions.py - NUEVO

 Modificados

 - bot/states/admin.py - Agregar configuring_options
 - bot/handlers/admin/broadcast.py - Extender flujo
 - bot/gamification/database/models.py - Modificar
 Reaction
 - bot/gamification/services/stats.py - Agregar métodos
  de stats
 - bot/services/container.py - Agregar BroadcastService
 - bot/gamification/services/container.py - Agregar
 CustomReactionService

 ---
 ⚠️ CONSIDERACIONES IMPORTANTES

 1. Backward Compatibility

 - Broadcasting sin gamificación DEBE seguir
 funcionando
 - reaction_hook.py (reacciones nativas) NO se elimina
 - CustomReaction y UserReaction son complementarios

 2. Performance

 - Índice único en (broadcast_message_id, user_id,
 reaction_type_id) previene duplicados
 - Cache de stats en BroadcastMessage reduce queries
 - Lazy loading de servicios optimiza memoria

 3. UX (Decisiones Confirmadas)

 - Preview visual antes de enviar (ya existe)
 - Contadores públicos: Formato "❤️ 33" (emoji +
 número, sin paréntesis)
 - Checkmark personal: Si usuario ya reaccionó: "❤️ 33
 ✓"
 - Reacciones ilimitadas: Usuario puede presionar todos
  los botones
 - No cambio de reacción: Una vez presionado, no se
 puede deshacer
 - Feedback inmediato con besitos ganados
 - Máximo 3 botones por fila

 4. Seguridad

 - Validar que broadcast_message_id existe
 - Validar que reaction_type_id existe y está activo
 - Prevenir spam con índice único

 ---
 🎯 ORDEN DE EJECUCIÓN RECOMENDADO

 1. T1: Modelos de BD (base)
 2. T9: Seed de reacciones (datos iniciales)
 3. T2: CustomReactionService
 4. T3: BroadcastService
 5. T4: Extender Estados FSM
 6. T5: Modificar broadcast.py
 7. T6: Handler de reacciones de usuario
 8. T7: Protección de contenido (validación)
 9. T8: Estadísticas
 10. T10: Tests E2E
 11. T11: Documentación final

 ---
 ✅ CRITERIOS DE ÉXITO

 - Usuario puede enviar publicación con botones de
 reacción
 - Usuario presiona botón y gana besitos
 - Botones se marcan como presionados
 - No se permiten reacciones duplicadas
 - Estadísticas de engagement correctas
 - Broadcasting sin reacciones sigue funcionando
 - Todos los tests E2E pasan
 - Documentación actualizada

 ---
 Notas Finales:
 - Este plan es incremental y no rompe funcionalidad
 existente
 - Cada tarea es independiente y testeable
 - Se mantiene compatibilidad con sistema de reacciones
  nativas existente
