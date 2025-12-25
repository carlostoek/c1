# Sistema de Reacciones Personalizadas con Gamificación

Documento técnico que describe el sistema de reacciones personalizadas implementado para el bot VIP/Free, permitiendo gamificación de publicaciones en canales VIP y Free.

## Resumen

El sistema de reacciones personalizadas permite a los administradores:
- Enviar publicaciones con botones de reacción personalizados
- Rastrear quién reacciona a cada publicación
- Otorgar besitos por reaccionar (gamificación)
- Generar estadísticas de engagement
- Proteger contenido (anti-forward)

## Componentes del Sistema

### 1. Modelos de Base de Datos

#### BroadcastMessage
Modelo para registrar mensajes de broadcasting con gamificación:

```python
class BroadcastMessage(Base):
    __tablename__ = "broadcast_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(BigInteger, nullable=False)  # ID del mensaje en Telegram
    chat_id = Column(BigInteger, nullable=False)      # ID del canal donde se envió
    content_type = Column(String(20), nullable=False)  # "text", "photo", "video"
    content_text = Column(String(4096), nullable=True)  # Texto del mensaje
    media_file_id = Column(String(200), nullable=True)  # File ID de Telegram (si es media)
    sent_by = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)  # Admin que envió
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    gamification_enabled = Column(Boolean, default=False, nullable=False)
    reaction_buttons = Column(JSON, default=list)  # Lista de configs de reacciones
    content_protected = Column(Boolean, default=False, nullable=False)  # Protección anti-forward
    total_reactions = Column(Integer, default=0, nullable=False)  # Cache de estadísticas
    unique_reactors = Column(Integer, default=0, nullable=False)  # Cache de estadísticas
```

#### CustomReaction
Modelo para registrar reacciones personalizadas de usuarios:

```python
class CustomReaction(Base):
    __tablename__ = "custom_reactions"

    id = Column(Integer, primary_key=True)
    broadcast_message_id = Column(Integer, nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    reaction_type_id = Column(Integer, ForeignKey("reactions.id"), nullable=False)
    emoji = Column(String(10), nullable=False)
    besitos_earned = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    # Relaciones
    reaction_type = relationship("Reaction", foreign_keys=[reaction_type_id])

    # Índices
    __table_args__ = (
        Index('idx_unique_reaction', 'broadcast_message_id', 'user_id', 'reaction_type_id', unique=True),
        Index('idx_user_created', 'user_id', 'created_at'),
        Index('idx_broadcast_message', 'broadcast_message_id'),
    )
```

#### Actualización de Reaction
Modelo Reaction actualizado con campos de UI:

```python
class Reaction(Base):
    # ... campos existentes ...
    
    # Campos de UI para botones personalizados
    button_emoji = Column(String(10), nullable=True)    # Emoji para el botón
    button_label = Column(String(50), nullable=True)    # Etiqueta para el botón
    sort_order = Column(Integer, default=0)             # Orden de visualización
```

### 2. Servicios

#### CustomReactionService
Servicio para manejar reacciones personalizadas:

```python
class CustomReactionService:
    def __init__(self, session: AsyncSession, besito_service: BesitoService):
        self.session = session
        self.besito_service = besito_service

    async def register_custom_reaction(
        self, 
        broadcast_message_id: int, 
        user_id: int, 
        reaction_type_id: int
    ) -> Dict[str, Any]:
        """
        Registra una reacción personalizada de un usuario a un mensaje de broadcasting.
        
        Args:
            broadcast_message_id: ID del mensaje de broadcasting
            user_id: ID del usuario que reacciona
            reaction_type_id: ID del tipo de reacción
            
        Returns:
            Dict con resultado: {success, besitos_earned, already_reacted, message}
        """
        # Verificar si el usuario ya reaccionó con este emoji
        existing_reaction = await self._check_existing_reaction(
            broadcast_message_id, user_id, reaction_type_id
        )
        
        if existing_reaction:
            return {
                "success": False,
                "already_reacted": True,
                "besitos_earned": 0,
                "message": "Ya reaccionaste con este emoji a esta publicación"
            }

        # Obtener información de la reacción
        reaction_type = await self.session.get(Reaction, reaction_type_id)
        if not reaction_type:
            return {
                "success": False,
                "already_reacted": False,
                "besitos_earned": 0,
                "message": "Tipo de reacción no encontrado"
            }

        # Calcular besitos ganados
        besitos_earned = reaction_type.besitos_value
        
        # Aplicar multiplicadores si existen
        current_balance = await self.besito_service.get_user_balance(user_id)
        besitos_earned = await self._apply_multipliers(besitos_earned, user_id)

        # Crear registro de reacción
        custom_reaction = CustomReaction(
            broadcast_message_id=broadcast_message_id,
            user_id=user_id,
            reaction_type_id=reaction_type_id,
            emoji=reaction_type.emoji,
            besitos_earned=besitos_earned
        )
        
        self.session.add(custom_reaction)
        await self.session.flush()  # Para obtener el ID

        # Otorgar besitos al usuario
        await self.besito_service.add_besitos(
            user_id=user_id,
            amount=besitos_earned,
            reason=f"Reacción '{reaction_type.emoji}' al broadcast {broadcast_message_id}"
        )

        # Actualizar estadísticas del mensaje
        await self._update_message_stats(broadcast_message_id)

        return {
            "success": True,
            "already_reacted": False,
            "besitos_earned": besitos_earned,
            "message": f"¡Reacción registrada! Ganaste {besitos_earned} besitos"
        }

    async def get_user_reactions_for_message(
        self, 
        broadcast_message_id: int, 
        user_id: int
    ) -> List[int]:
        """
        Obtiene los IDs de reacciones que un usuario ya usó para un mensaje específico.
        
        Args:
            broadcast_message_id: ID del mensaje
            user_id: ID del usuario
            
        Returns:
            Lista de reaction_type_ids que ya usó el usuario
        """
        result = await self.session.execute(
            select(CustomReaction.reaction_type_id)
            .where(CustomReaction.broadcast_message_id == broadcast_message_id)
            .where(CustomReaction.user_id == user_id)
        )
        return [row[0] for row in result.fetchall()]

    async def get_message_reaction_stats(
        self, 
        broadcast_message_id: int
    ) -> Dict[str, int]:
        """
        Obtiene estadísticas de reacciones para un mensaje específico.
        
        Args:
            broadcast_message_id: ID del mensaje
            
        Returns:
            Dict con conteo por emoji: {"👍": 45, "❤️": 32}
        """
        result = await self.session.execute(
            select(CustomReaction.emoji, func.count(CustomReaction.id))
            .where(CustomReaction.broadcast_message_id == broadcast_message_id)
            .group_by(CustomReaction.emoji)
        )
        return dict(result.fetchall())

    async def _check_existing_reaction(
        self,
        broadcast_message_id: int,
        user_id: int,
        reaction_type_id: int
    ) -> bool:
        """Verifica si el usuario ya reaccionó con este tipo de reacción."""
        result = await self.session.execute(
            select(func.count(CustomReaction.id))
            .where(CustomReaction.broadcast_message_id == broadcast_message_id)
            .where(CustomReaction.user_id == user_id)
            .where(CustomReaction.reaction_type_id == reaction_type_id)
        )
        return result.scalar() > 0

    async def _update_message_stats(self, broadcast_message_id: int):
        """Actualiza las estadísticas cacheadas del mensaje."""
        # Contar total de reacciones
        total_reactions_result = await self.session.execute(
            select(func.count(CustomReaction.id))
            .where(CustomReaction.broadcast_message_id == broadcast_message_id)
        )
        total_reactions = total_reactions_result.scalar()

        # Contar usuarios únicos
        unique_reactors_result = await self.session.execute(
            select(func.count(func.distinct(CustomReaction.user_id)))
            .where(CustomReaction.broadcast_message_id == broadcast_message_id)
        )
        unique_reactors = unique_reactors_result.scalar()

        # Actualizar el mensaje
        await self.session.execute(
            update(BroadcastMessage)
            .where(BroadcastMessage.id == broadcast_message_id)
            .values(
                total_reactions=total_reactions,
                unique_reactors=unique_reactors
            )
        )
        await self.session.commit()
```

#### BroadcastService
Servicio para enviar mensajes con gamificación:

```python
class BroadcastService:
    def __init__(self, session: AsyncSession, channel_service: ChannelService, config_service: ConfigService):
        self.session = session
        self.channel_service = channel_service
        self.config_service = config_service

    async def send_broadcast_with_gamification(
        self,
        target: str,  # "vip", "free", "both"
        content_type: str,  # "text", "photo", "video"
        content_text: str,
        media_file_id: str,
        sent_by: int,
        gamification_config: Dict[str, Any],
        content_protected: bool = False
    ) -> Dict[str, Any]:
        """
        Envía un mensaje de broadcasting con opciones de gamificación.
        
        Args:
            target: Canal(es) destino ("vip", "free", "both")
            content_type: Tipo de contenido
            content_text: Texto del mensaje
            media_file_id: File ID si es media
            sent_by: ID del usuario que envía
            gamification_config: Configuración de gamificación
            content_protected: Si el contenido debe estar protegido
        
        Returns:
            Dict con resultados de envío
        """
        # Determinar canales destino
        target_channels = await self._get_target_channels(target)
        
        if not target_channels:
            return {"success": False, "message": "No hay canales configurados"}

        # Preparar reacciones si están habilitadas
        reaction_buttons = []
        if gamification_config.get("enabled", False):
            reaction_buttons = await self._build_reaction_config(gamification_config["reactions"])

        # Enviar a cada canal
        results = {}
        for channel_name, channel_id in target_channels:
            # Construir teclado con reacciones si aplica
            reply_markup = None
            if reaction_buttons:
                reply_markup = await self._build_reaction_keyboard(reaction_buttons)

            # Enviar mensaje
            if content_type == "photo":
                success, message, sent_msg = await self.channel_service.send_to_channel(
                    channel_id=channel_id,
                    text=content_text,
                    photo=media_file_id,
                    protect_content=content_protected,
                    reply_markup=reply_markup
                )
            elif content_type == "video":
                success, message, sent_msg = await self.channel_service.send_to_channel(
                    channel_id=channel_id,
                    text=content_text,
                    video=media_file_id,
                    protect_content=content_protected,
                    reply_markup=reply_markup
                )
            else:  # text
                success, message, sent_msg = await self.channel_service.send_to_channel(
                    channel_id=channel_id,
                    text=content_text,
                    protect_content=content_protected,
                    reply_markup=reply_markup
                )

            results[channel_name] = {
                "success": success,
                "message": message,
                "message_id": sent_msg.message_id if success else None
            }

            # Registrar en BD si éxito y gamificación habilitada
            if success and reaction_buttons:
                broadcast_msg = BroadcastMessage(
                    message_id=sent_msg.message_id,
                    chat_id=channel_id,
                    content_type=content_type,
                    content_text=content_text,
                    media_file_id=media_file_id,
                    sent_by=sent_by,
                    gamification_enabled=True,
                    reaction_buttons=reaction_buttons,
                    content_protected=content_protected
                )
                self.session.add(broadcast_msg)

        await self.session.commit()

        return {
            "success": any(r["success"] for r in results.values()),
            "results": results,
            "reactions_enabled": bool(reaction_buttons)
        }

    async def _get_target_channels(self, target: str) -> List[Tuple[str, str]]:
        """Obtiene los canales destino según el objetivo."""
        channels = []
        
        if target in ["vip", "both"]:
            vip_channel = await self.config_service.get_vip_channel_id()
            if vip_channel:
                channels.append(("VIP", vip_channel))
        
        if target in ["free", "both"]:
            free_channel = await self.config_service.get_free_channel_id()
            if free_channel:
                channels.append(("Free", free_channel))
        
        return channels

    async def _build_reaction_config(self, reaction_ids: List[int]) -> List[Dict]:
        """Construye la configuración de reacciones basada en IDs."""
        reactions = await self.session.execute(
            select(Reaction).where(Reaction.id.in_(reaction_ids))
        )
        
        return [
            {
                "emoji": reaction.emoji,
                "label": reaction.button_label or reaction.emoji,
                "reaction_type_id": reaction.id,
                "besitos": reaction.besitos_value,
                "sort_order": reaction.sort_order
            }
            for reaction in reactions.scalars().all()
        ]

    async def _build_reaction_keyboard(self, reaction_config: List[Dict]) -> InlineKeyboardMarkup:
        """Construye un teclado con botones de reacción."""
        # Ordenar por sort_order
        sorted_reactions = sorted(reaction_config, key=lambda x: x["sort_order"])

        buttons = []
        current_row = []
        
        for i, reaction in enumerate(sorted_reactions):
            # Crear botón con emoji y etiqueta
            button_text = f"{reaction['emoji']} {reaction['label']}"
            callback_data = f"react:{reaction['reaction_type_id']}"
            
            current_row.append(InlineKeyboardButton(
                text=button_text,
                callback_data=callback_data
            ))
            
            # Cada 3 botones o al final, crear nueva fila
            if len(current_row) == 3 or i == len(sorted_reactions) - 1:
                buttons.append(current_row)
                current_row = []

        return InlineKeyboardMarkup(inline_keyboard=buttons)
```

### 3. Handlers

#### Handler de Reacciones de Usuario
Handler para procesar reacciones de usuarios:

```python
from aiogram import Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.engine import get_session
from bot.gamification.services.custom_reaction import CustomReactionService
from bot.services.container import ServiceContainer

router = Router()

@router.callback_query(lambda c: c.data.startswith("react:"))
async def handle_reaction_button(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Handler para botones de reacción personalizados.
    
    Callback data: "react:{reaction_type_id}"
    """
    # Extraer reaction_type_id del callback
    reaction_type_id = int(callback.data.split(":")[1])
    
    user_id = callback.from_user.id
    message_id = callback.message.message_id
    chat_id = callback.message.chat.id
    
    # Validar que el mensaje es un broadcast registrado
    broadcast_result = await session.execute(
        select(BroadcastMessage)
        .where(BroadcastMessage.message_id == message_id)
        .where(BroadcastMessage.chat_id == chat_id)
    )
    broadcast_msg = broadcast_result.scalar_one_or_none()
    
    if not broadcast_msg:
        await callback.answer(
            text="❌ Esta publicación no tiene gamificación activa",
            show_alert=True
        )
        return

    # Obtener el servicio de reacciones personalizadas
    container = ServiceContainer(session, callback.bot)
    custom_reaction_service = container.custom_reaction
    
    # Registrar la reacción
    result = await custom_reaction_service.register_custom_reaction(
        broadcast_message_id=broadcast_msg.id,
        user_id=user_id,
        reaction_type_id=reaction_type_id
    )
    
    if result["success"]:
        # Actualizar teclado con marca personal
        updated_keyboard = await _build_reaction_keyboard_with_marks(
            session, broadcast_msg.id, user_id, broadcast_msg.reaction_buttons
        )
        
        try:
            await callback.message.edit_reply_markup(
                reply_markup=updated_keyboard
            )
        except Exception:
            # No se puede editar el teclado, continuar sin error
            pass
        
        # Enviar alerta con besitos ganados
        await callback.answer(
            text=f"🎉 ¡Reacción registrada! Ganaste {result['besitos_earned']} besitos",
            show_alert=False  # Mostrar como toast, no alerta
        )
    else:
        if result["already_reacted"]:
            await callback.answer(
                text="Ya reaccionaste con este emoji a esta publicación",
                show_alert=False
            )
        else:
            await callback.answer(
                text="Error al registrar reacción",
                show_alert=True
            )

async def _build_reaction_keyboard_with_marks(
    session: AsyncSession,
    broadcast_message_id: int,
    current_user_id: int,
    reaction_config: List[Dict]
) -> InlineKeyboardMarkup:
    """
    Construye un teclado con marcas de reacciones ya realizadas por el usuario.
    """
    # Obtener estadísticas de reacciones
    reaction_stats = await get_reaction_counts(session, broadcast_message_id)
    
    # Obtener reacciones del usuario actual
    user_reactions = await get_user_reactions_for_message(
        session, broadcast_message_id, current_user_id
    )
    
    # Ordenar reacciones por sort_order
    sorted_reactions = sorted(
        reaction_config, 
        key=lambda x: x.get("sort_order", 0)
    )

    buttons = []
    current_row = []
    
    for i, reaction in enumerate(sorted_reactions):
        emoji = reaction["emoji"]
        label = reaction.get("label", emoji)
        reaction_type_id = reaction["reaction_type_id"]
        
        # Obtener conteo para este emoji
        count = reaction_stats.get(emoji, 0)
        
        # Determinar si el usuario actual ya reaccionó con este tipo
        is_reacted = reaction_type_id in user_reactions
        
        if is_reacted:
            # Añadir checkmark personal
            button_text = f"{emoji} {count} ✓"
        else:
            button_text = f"{emoji} {count}"
        
        callback_data = f"react:{reaction_type_id}"
        
        current_row.append(InlineKeyboardButton(
            text=button_text,
            callback_data=callback_data
        ))
        
        # Cada 3 botones o al final, crear nueva fila
        if len(current_row) == 3 or i == len(sorted_reactions) - 1:
            buttons.append(current_row)
            current_row = []

    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def get_reaction_counts(
    session: AsyncSession,
    broadcast_message_id: int
) -> Dict[str, int]:
    """
    Obtiene el conteo de reacciones por emoji para un mensaje.
    """
    result = await session.execute(
        select(CustomReaction.emoji, func.count(CustomReaction.id))
        .where(CustomReaction.broadcast_message_id == broadcast_message_id)
        .group_by(CustomReaction.emoji)
    )
    return dict(result.fetchall())

async def get_user_reactions_for_message(
    session: AsyncSession,
    broadcast_message_id: int,
    user_id: int
) -> List[int]:
    """
    Obtiene los IDs de reacciones ya realizadas por un usuario en un mensaje.
    """
    result = await session.execute(
        select(CustomReaction.reaction_type_id)
        .where(CustomReaction.broadcast_message_id == broadcast_message_id)
        .where(CustomReaction.user_id == user_id)
    )
    return [row[0] for row in result.fetchall()]
```

#### Extensión del Handler de Broadcasting
Actualización del handler de broadcasting para incluir opciones de gamificación:

```python
from aiogram.fsm.state import State
from aiogram.fsm.context import FSMContext

# Estados extendidos para broadcasting con gamificación
class BroadcastStates(StatesGroup):
    waiting_for_content = State()
    configuring_options = State()  # Nuevo estado
    selecting_reactions = State()  # Existente
    waiting_for_confirmation = State()

@router.message(BroadcastStates.waiting_for_content)
async def process_broadcast_content(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """
    Procesa el contenido enviado para broadcasting y pasa a opciones de configuración.
    """
    # ... código existente para procesar contenido ...
    
    # Actualizar FSM para incluir configuración de gamificación
    await state.update_data({
        # ... datos existentes ...
        "gamification_enabled": False,  # Por defecto deshabilitado
        "content_protected": False,     # Por defecto sin protección
        "selected_reactions": []        # Reacciones seleccionadas
    })
    
    # Cambiar al nuevo estado de configuración
    await state.set_state(BroadcastStates.configuring_options)
    
    # Mostrar opciones de configuración
    await show_broadcast_options(message, state)

async def show_broadcast_options(message: Message, state: FSMContext):
    """
    Muestra las opciones de configuración para el broadcast (gamificación, protección).
    """
    data = await state.get_data()
    gamification_enabled = data.get("gamification_enabled", False)
    content_protected = data.get("content_protected", False)
    
    text = (
        "<b>⚙️ Opciones de Broadcasting</b>\n\n"
        f"🎮 Gamificación: {'✅ Activada' if gamification_enabled else '❌ Desactivada'}\n"
        f"🔒 Contenido protegido: {'✅ Sí' if content_protected else '❌ No'}\n\n"
        "Selecciona las opciones que deseas aplicar:"
    )
    
    # Crear teclado con opciones
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎮 Configurar Reacciones" if not gamification_enabled else "🎮 Editar Reacciones",
                callback_data="broadcast:config:reactions"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Desactivar Gamificación" if gamification_enabled else "✅ Activar Gamificación",
                callback_data="broadcast:config:gamification_toggle"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔒 Activar Protección" if not content_protected else "🔓 Desactivar Protección",
                callback_data="broadcast:config:protection_toggle"
            )
        ],
        [
            InlineKeyboardButton(
                text="✅ Continuar",
                callback_data="broadcast:continue"
            ),
            InlineKeyboardButton(
                text="❌ Cancelar",
                callback_data="broadcast:cancel"
            )
        ]
    ])
    
    await message.answer(text=text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("broadcast:config:"))
async def handle_broadcast_config_callback(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """
    Maneja callbacks de configuración de broadcasting.
    """
    data = callback.data.split(":")
    
    if data[2] == "reactions":
        # Mostrar selección de reacciones
        await show_reaction_selection(callback, state, session)
    elif data[2] == "gamification_toggle":
        # Alternar gamificación
        current_data = await state.get_data()
        new_state = not current_data.get("gamification_enabled", False)
        await state.update_data({"gamification_enabled": new_state})
        
        # Actualizar mensaje
        await show_broadcast_options(callback.message, state)
        await callback.answer()
    elif data[2] == "protection_toggle":
        # Alternar protección
        current_data = await state.get_data()
        new_state = not current_data.get("content_protected", False)
        await state.update_data({"content_protected": new_state})
        
        # Actualizar mensaje
        await show_broadcast_options(callback.message, state)
        await callback.answer()
    elif data[2] == "continue":
        # Confirmar broadcasting
        await callback_broadcast_confirm(callback, state, session)
    elif data[2] == "cancel":
        # Cancelar
        await callback.message.edit_text("❌ Envío cancelado.")
        await state.clear()

async def show_reaction_selection(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """
    Muestra la selección de reacciones para el broadcast.
    """
    # Obtener todas las reacciones disponibles
    all_reactions_result = await session.execute(
        select(Reaction)
        .where(Reaction.active == True)
        .order_by(Reaction.sort_order)
    )
    all_reactions = all_reactions_result.scalars().all()
    
    current_data = await state.get_data()
    selected_reactions = current_data.get("selected_reactions", [])
    
    # Crear teclado con todas las reacciones y checkboxes
    keyboard_rows = []
    current_row = []
    
    for i, reaction in enumerate(all_reactions):
        # Determinar si está seleccionado
        is_selected = reaction.id in selected_reactions
        
        # Texto del botón con checkbox
        checkbox = "✅ " if is_selected else "☐ "
        button_text = f"{checkbox}{reaction.emoji} {reaction.button_label or reaction.emoji}"
        
        # Callback para alternar selección
        callback_data = f"broadcast:react:toggle:{reaction.id}"
        
        current_row.append(InlineKeyboardButton(
            text=button_text,
            callback_data=callback_data
        ))
        
        # Cada 2 botones o al final, crear nueva fila
        if len(current_row) == 2 or i == len(all_reactions) - 1:
            keyboard_rows.append(current_row)
            current_row = []
    
    # Añadir botones de confirmación
    keyboard_rows.append([
        InlineKeyboardButton(
            text="✅ Confirmar Reacciones",
            callback_data="broadcast:react:confirm"
        )
    ])
    keyboard_rows.append([
        InlineKeyboardButton(
            text="❌ Volver",
            callback_data="broadcast:back_to_options"
        )
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
    
    await callback.message.edit_text(
        text="<b>🎮 Selecciona Reacciones para el Broadcast</b>\n\n"
             "Elige los emojis que se mostrarán como botones en la publicación:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("broadcast:react:toggle:"))
async def toggle_reaction_selection(
    callback: CallbackQuery,
    state: FSMContext
):
    """
    Alterna la selección de una reacción específica.
    """
    reaction_id = int(callback.data.split(":")[3])
    
    current_data = await state.get_data()
    selected_reactions = current_data.get("selected_reactions", [])
    
    # Alternar selección
    if reaction_id in selected_reactions:
        selected_reactions.remove(reaction_id)
    else:
        selected_reactions.append(reaction_id)
    
    # Actualizar FSM data
    await state.update_data({"selected_reactions": selected_reactions})
    
    # Actualizar mensaje con selección actualizada
    await show_reaction_selection(callback, state, callback.bot.session)
    await callback.answer()

@router.callback_query(F.data == "broadcast:react:confirm")
async def confirm_reaction_selection(
    callback: CallbackQuery,
    state: FSMContext
):
    """
    Confirma la selección de reacciones.
    """
    current_data = await state.get_data()
    selected_reactions = current_data.get("selected_reactions", [])
    
    if not selected_reactions:
        await callback.answer("❌ Debes seleccionar al menos una reacción", show_alert=True)
        return
    
    # Activar gamificación
    await state.update_data({
        "gamification_enabled": True,
        "selected_reactions": selected_reactions
    })
    
    # Volver a opciones
    await show_broadcast_options(callback.message, state)
    await callback.answer("✅ Reacciones seleccionadas")
```

### 4. Estadísticas de Broadcasting

Servicio para obtener estadísticas de reacciones en broadcasts:

```python
from sqlalchemy import func, desc
from typing import List, Dict, Any

class BroadcastStatsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_broadcast_reaction_stats(
        self, 
        broadcast_id: int
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas de reacciones para una publicación específica.
        
        Args:
            broadcast_id: ID de la publicación de broadcasting
            
        Returns:
            Dict con estadísticas detalladas
        """
        # Obtener el mensaje de broadcasting
        broadcast = await self.session.get(BroadcastMessage, broadcast_id)
        if not broadcast:
            return {"error": "Broadcast no encontrado"}

        # Contar reacciones totales
        total_reactions_result = await self.session.execute(
            select(func.count(CustomReaction.id))
            .where(CustomReaction.broadcast_message_id == broadcast_id)
        )
        total_reactions = total_reactions_result.scalar()

        # Contar usuarios únicos
        unique_users_result = await self.session.execute(
            select(func.count(func.distinct(CustomReaction.user_id)))
            .where(CustomReaction.broadcast_message_id == broadcast_id)
        )
        unique_users = unique_users_result.scalar()

        # Contar por emoji
        breakdown_result = await self.session.execute(
            select(
                CustomReaction.emoji,
                func.count(CustomReaction.id)
            )
            .where(CustomReaction.broadcast_message_id == broadcast_id)
            .group_by(CustomReaction.emoji)
        )
        breakdown = dict(breakdown_result.fetchall())

        # Sumar besitos distribuidos
        besitos_result = await self.session.execute(
            select(func.sum(CustomReaction.besitos_earned))
            .where(CustomReaction.broadcast_message_id == broadcast_id)
        )
        besitos_distributed = besitos_result.scalar() or 0

        # Obtener top 5 reaccionadores
        top_reactors_result = await self.session.execute(
            select(
                CustomReaction.user_id,
                func.count(CustomReaction.id).label('reaction_count')
            )
            .where(CustomReaction.broadcast_message_id == broadcast_id)
            .group_by(CustomReaction.user_id)
            .order_by(desc('reaction_count'))
            .limit(5)
        )
        top_reactors = [
            {"user_id": row[0], "reactions": row[1]}
            for row in top_reactors_result.fetchall()
        ]

        return {
            "broadcast_id": broadcast_id,
            "total_reactions": total_reactions,
            "unique_users": unique_users,
            "breakdown_by_emoji": breakdown,
            "besitos_distributed": besitos_distributed,
            "top_reactors": top_reactors,
            "content_type": broadcast.content_type,
            "sent_at": broadcast.sent_at,
            "content_protected": broadcast.content_protected
        }

    async def get_top_performing_broadcasts(
        self,
        limit: int = 10,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Obtiene los broadcasts mejor desempeñados según reacciones.
        
        Args:
            limit: Número máximo de resultados
            days_back: Días hacia atrás para filtrar
            
        Returns:
            Lista de broadcasts ordenados por reacciones
        """
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        query = (
            select(
                BroadcastMessage.id,
                BroadcastMessage.message_id,
                BroadcastMessage.chat_id,
                BroadcastMessage.content_text,
                BroadcastMessage.sent_at,
                func.count(CustomReaction.id).label('reaction_count'),
                func.count(func.distinct(CustomReaction.user_id)).label('unique_reactors')
            )
            .select_from(BroadcastMessage)
            .outerjoin(CustomReaction, CustomReaction.broadcast_message_id == BroadcastMessage.id)
            .where(BroadcastMessage.sent_at >= cutoff_date)
            .where(BroadcastMessage.gamification_enabled == True)
            .group_by(BroadcastMessage.id)
            .order_by(desc('reaction_count'))
            .limit(limit)
        )

        result = await self.session.execute(query)
        broadcasts = []
        
        for row in result.fetchall():
            broadcasts.append({
                "broadcast_id": row[0],
                "message_id": row[1],
                "chat_id": row[2],
                "content_preview": row[2][:50] + "..." if row[2] and len(row[2]) > 50 else row[2],
                "sent_at": row[5],
                "total_reactions": row[6],
                "unique_reactors": row[7]
            })

        return broadcasts
```

### 5. Ejecución de Migración

La migración ya está implementada en `alembic/versions/005_add_custom_reactions_system.py`:

```python
"""
Add custom reactions system for broadcasting

Revision ID: 005
Revises: 004
Create Date: 2025-12-24 00:00:00.000000

Changes:
- Add broadcast_messages table for tracking broadcasts with gamification
- Add custom_reactions table for tracking user reactions via buttons
- Add UI fields to reactions table (button_emoji, button_label, sort_order)
"""

def upgrade() -> None:
    # 1. Crear tabla broadcast_messages
    op.create_table(
        'broadcast_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.BigInteger(), nullable=False),
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        # ... otros campos como se mostró anteriormente
    )

    # 2. Modificar tabla reactions - Agregar campos de UI
    op.add_column('reactions', sa.Column('button_emoji', sa.String(10), nullable=True))
    op.add_column('reactions', sa.Column('button_label', sa.String(50), nullable=True))
    op.add_column('reactions', sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'))

    # 3. Crear tabla custom_reactions
    op.create_table(
        'custom_reactions',
        sa.Column('id', sa.Integer(), nullable=False),
        # ... otros campos como se mostró anteriormente
    )

    # Crear índices
    # ... como se mostró anteriormente

def downgrade() -> None:
    # Revertir cambios
    # ... como se mostró anteriormente
```

### 6. Script de Seed

Script para crear reacciones predeterminadas:

```python
#!/usr/bin/env python3
"""
Script para inicializar datos de reacciones predeterminadas.
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

# Añadir el directorio raíz al path
sys.path.append('/data/data/com.termux/files/home/repos/c1')

from bot.database.models import Base, Reaction
from config import Config

async def seed_reactions():
    """Crea reacciones predeterminadas en la base de datos."""
    engine = create_async_engine(Config.DATABASE_URL)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:
        # Definir reacciones predeterminadas
        default_reactions = [
            {
                "emoji": "👍",
                "besitos_value": 10,
                "button_emoji": "👍",
                "button_label": "Me Gusta",
                "sort_order": 1,
                "active": True
            },
            {
                "emoji": "❤️",
                "besitos_value": 15,
                "button_emoji": "❤️",
                "button_label": "Me Encanta",
                "sort_order": 2,
                "active": True
            },
            {
                "emoji": "🔥",
                "besitos_value": 20,
                "button_emoji": "🔥",
                "button_label": "Increíble",
                "sort_order": 3,
                "active": True
            },
            {
                "emoji": "😂",
                "besitos_value": 10,
                "button_emoji": "😂",
                "button_label": "Divertido",
                "sort_order": 4,
                "active": True
            },
            {
                "emoji": "😮",
                "besitos_value": 15,
                "button_emoji": "😮",
                "button_label": "Sorprendente",
                "sort_order": 5,
                "active": True
            }
        ]
        
        for reaction_data in default_reactions:
            # Verificar si ya existe
            existing = await session.execute(
                select(Reaction)
                .where(Reaction.emoji == reaction_data["emoji"])
            )
            if existing.scalar_one_or_none():
                print(f"⚠️  Reacción {reaction_data['emoji']} ya existe, omitiendo...")
                continue
            
            # Crear nueva reacción
            reaction = Reaction(**reaction_data)
            session.add(reaction)
            print(f"✅ Reacción {reaction_data['emoji']} añadida")
        
        await session.commit()
        print("🎉 Reacciones predeterminadas añadidas exitosamente")

if __name__ == "__main__":
    asyncio.run(seed_reactions())
```

## Flujo de Operación

### 1. Configuración de Reacciones
```
Admin: /admin → "Enviar Broadcast"
   ↓
Bot: Mostrar opciones de gamificación
   ↓
Admin: "Configurar Reacciones"
   ↓
Bot: Mostrar reacciones disponibles con checkboxes
   ↓
Admin: Seleccionar reacciones deseadas
   ↓
Bot: Confirmar selección y volver a opciones
   ↓
Admin: "Enviar Publicación"
```

### 2. Envío de Broadcast con Gamificación
```
Admin: Enviar contenido
   ↓
Bot: Guardar en BD como BroadcastMessage
   ↓
Bot: Enviar con botones de reacción personalizados
   ↓
Bot: Registrar en BD como mensaje gamificado
```

### 3. Reacción de Usuario
```
Usuario: Hace click en botón de reacción
   ↓
Bot: Verifica mensaje es gamificado
   ↓
Bot: Registra CustomReaction en BD
   ↓
Bot: Otorga besitos al usuario
   ↓
Bot: Actualiza teclado con marca personal
   ↓
Bot: Muestra notificación de besitos ganados
```

### 4. Estadísticas
```
Admin: Accede a estadísticas de broadcast
   ↓
Bot: Consulta BD por CustomReaction
   ↓
Bot: Calcula métricas (reacciones totales, usuarios únicos, etc.)
   ↓
Bot: Muestra reporte detallado
```

## Consideraciones de Seguridad

1. **Prevención de Spam:** Índice único previene múltiples reacciones idénticas
2. **Validación de Datos:** Verificación de existencia de mensajes y reacciones
3. **Protección de Contenido:** Opción de `protect_content` para evitar forward/copiar
4. **Control de Acceso:** Validación de permisos para enviar broadcasts

## Consideraciones de Rendimiento

1. **Caching de Estadísticas:** Campos cacheados en `BroadcastMessage` para evitar queries complejas
2. **Índices Adequados:** Índices en tablas para queries eficientes
3. **Lazy Loading:** Carga perezosa de relaciones en modelos
4. **Batch Processing:** Posibilidad de procesar reacciones en batch para análisis

## API de Servicios

### CustomReactionService
- `register_custom_reaction()` - Registrar reacción de usuario
- `get_user_reactions_for_message()` - Obtener reacciones ya hechas por usuario
- `get_message_reaction_stats()` - Obtener estadísticas de reacciones

### BroadcastService
- `send_broadcast_with_gamification()` - Enviar broadcast con opciones
- `_build_reaction_keyboard()` - Construir teclado de reacciones
- `_get_target_channels()` - Obtener canales destino

### BroadcastStatsService
- `get_broadcast_reaction_stats()` - Estadísticas de un broadcast
- `get_top_performing_broadcasts()` - Top broadcasts por engagement

## Integración con Otros Sistemas

1. **Gamificación:** Integrado con sistema de besitos para otorgamiento
2. **Servicios de Canal:** Usa ChannelService para envío de mensajes
3. **Configuración:** Usa ConfigService para obtener IDs de canales
4. **Usuarios:** Relación con modelo User para tracking de reacciones
5. **Middleware:** Usa DatabaseMiddleware para inyección de sesión

## Pruebas E2E

El sistema incluye pruebas end-to-end que verifican:

1. **Flujo Completo de Broadcast:** Creación, envío y registro de mensaje
2. **Reacciones de Usuarios:** Registro correcto y otorgamiento de besitos
3. **Prevención de Duplicados:** No permite múltiples reacciones idénticas
4. **Estadísticas Precisas:** Conteos correctos por emoji y usuarios únicos
5. **Backward Compatibility:** Broadcasting sin gamificación sigue funcionando

---

**Fecha de Documentación:** 2025-12-25
**Versión del Sistema:** 1.0.0