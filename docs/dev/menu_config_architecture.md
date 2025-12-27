# Arquitectura: Sistema de Configuración Dinámica de Menús

## 📋 Resumen Ejecutivo

Este documento define la arquitectura para implementar un sistema que permita a los administradores configurar dinámicamente los botones y menús que ven los usuarios (FREE y VIP) desde la interfaz del bot, sin necesidad de modificar código.

---

## 🎯 Objetivos

1. **Permitir a admins configurar menús** desde la interfaz del bot
2. **Diferenciar menús por rol** (FREE vs VIP)
3. **Actualizar labels y contenido** de botones sin código
4. **Mantener compatibilidad** con el sistema actual de roles
5. **Interfaz intuitiva** para administradores

---

## 🏗️ Arquitectura General

```
┌─────────────────────────────────────────────────────────────────┐
│                     FLUJO DE DATOS                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Admin UI   │───▶│ MenuService  │───▶│   Database   │      │
│  │  (Handlers)  │    │              │    │  (MenuItems) │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         │                   ▼                   │               │
│         │         ┌──────────────┐              │               │
│         │         │  KeyboardGen │◀─────────────┘               │
│         │         │  (Dinámico)  │                              │
│         │         └──────────────┘                              │
│         │                   │                                   │
│         ▼                   ▼                                   │
│  ┌──────────────────────────────────────────┐                  │
│  │            USER INTERFACE                 │                  │
│  │  ┌────────────┐      ┌────────────┐      │                  │
│  │  │  FREE Menu │      │  VIP Menu  │      │                  │
│  │  │  (Dinámico)│      │  (Dinámico)│      │                  │
│  │  └────────────┘      └────────────┘      │                  │
│  └──────────────────────────────────────────┘                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Modelos de Base de Datos

### Modelo 1: `MenuItem`

Almacena cada botón/item del menú de forma individual.

```python
# bot/database/models.py (agregar)

class MenuItem(Base):
    """
    Item de menú configurable por administradores.
    
    Representa un botón individual que puede mostrarse
    a usuarios según su rol.
    """
    __tablename__ = "menu_items"
    
    # Identificador único
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Identificador único del botón (ej: "vip_info_1", "free_support")
    item_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    # Rol target: 'vip', 'free', 'all'
    target_role: Mapped[str] = mapped_column(String(20), nullable=False, default='all')
    
    # Texto del botón (label) - lo que ve el usuario
    button_text: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Emoji del botón (opcional)
    button_emoji: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # Tipo de acción: 'info', 'url', 'callback', 'contact'
    action_type: Mapped[str] = mapped_column(String(20), nullable=False, default='info')
    
    # Contenido según tipo:
    # - info: texto informativo a mostrar
    # - url: enlace externo
    # - callback: callback_data para handler interno
    # - contact: información de contacto
    action_content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Orden de aparición en el menú (menor = primero)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Fila en el teclado (para agrupar botones)
    row_number: Mapped[int] = mapped_column(Integer, default=0)
    
    # ¿Está activo?
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    
    # Índices para búsquedas frecuentes
    __table_args__ = (
        Index('ix_menu_items_role_active', 'target_role', 'is_active'),
        Index('ix_menu_items_order', 'display_order', 'row_number'),
    )
    
    def __repr__(self):
        return f"<MenuItem(key={self.item_key}, role={self.target_role}, text={self.button_text})>"
```

### Modelo 2: `MenuConfig`

Configuración global de menús por rol.

```python
class MenuConfig(Base):
    """
    Configuración global del menú para un rol específico.
    
    Almacena configuración como mensaje de bienvenida,
    título del menú, etc.
    """
    __tablename__ = "menu_configs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Rol: 'vip', 'free'
    role: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    
    # Mensaje de bienvenida/cabecera del menú
    welcome_message: Mapped[str] = mapped_column(
        Text, 
        nullable=False,
        default="Bienvenido, selecciona una opción:"
    )
    
    # Footer/mensaje al final del menú (opcional)
    footer_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # ¿Mostrar información de suscripción? (para VIP)
    show_subscription_info: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Variables disponibles en mensajes:
    # {user_name}, {days_remaining}, {subscription_type}
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )
    
    def __repr__(self):
        return f"<MenuConfig(role={self.role})>"
```

---

## 🔧 Servicios

### MenuService

```python
# bot/services/menu_service.py

"""
Menu Service - Gestión de menús dinámicos.

Proporciona operaciones CRUD para MenuItems y MenuConfigs,
así como generación dinámica de keyboards basados en rol.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, UTC

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import MenuItem, MenuConfig
from bot.database.enums import UserRole

logger = logging.getLogger(__name__)


class MenuService:
    """Servicio para gestión de menús configurables."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ═══════════════════════════════════════════════════
    # CRUD MENU ITEMS
    # ═══════════════════════════════════════════════════
    
    async def create_menu_item(
        self,
        item_key: str,
        button_text: str,
        action_type: str,
        action_content: str,
        target_role: str = 'all',
        button_emoji: Optional[str] = None,
        display_order: int = 0,
        row_number: int = 0,
        created_by: Optional[int] = None
    ) -> MenuItem:
        """
        Crea un nuevo item de menú.
        
        Args:
            item_key: Identificador único del botón
            button_text: Texto visible del botón
            action_type: 'info', 'url', 'callback', 'contact'
            action_content: Contenido según el tipo
            target_role: 'vip', 'free', 'all'
            button_emoji: Emoji opcional
            display_order: Orden de aparición
            row_number: Fila en el teclado
            created_by: ID del admin que lo creó
            
        Returns:
            MenuItem creado
        """
        menu_item = MenuItem(
            item_key=item_key,
            target_role=target_role,
            button_text=button_text,
            button_emoji=button_emoji,
            action_type=action_type,
            action_content=action_content,
            display_order=display_order,
            row_number=row_number,
            created_by=created_by
        )
        
        self.session.add(menu_item)
        await self.session.commit()
        await self.session.refresh(menu_item)
        
        logger.info(f"✅ Menu item created: {item_key} for role {target_role}")
        return menu_item
    
    async def get_menu_item(self, item_key: str) -> Optional[MenuItem]:
        """Obtiene un item de menú por su key."""
        result = await self.session.execute(
            select(MenuItem).where(MenuItem.item_key == item_key)
        )
        return result.scalar_one_or_none()
    
    async def get_menu_item_by_id(self, item_id: int) -> Optional[MenuItem]:
        """Obtiene un item de menú por su ID."""
        return await self.session.get(MenuItem, item_id)
    
    async def update_menu_item(
        self,
        item_key: str,
        **kwargs
    ) -> Optional[MenuItem]:
        """
        Actualiza un item de menú.
        
        Args:
            item_key: Key del item a actualizar
            **kwargs: Campos a actualizar (button_text, action_content, etc.)
            
        Returns:
            MenuItem actualizado o None si no existe
        """
        menu_item = await self.get_menu_item(item_key)
        if not menu_item:
            return None
        
        for key, value in kwargs.items():
            if hasattr(menu_item, key):
                setattr(menu_item, key, value)
        
        await self.session.commit()
        await self.session.refresh(menu_item)
        
        logger.info(f"✅ Menu item updated: {item_key}")
        return menu_item
    
    async def delete_menu_item(self, item_key: str) -> bool:
        """Elimina un item de menú."""
        result = await self.session.execute(
            delete(MenuItem).where(MenuItem.item_key == item_key)
        )
        await self.session.commit()
        
        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"🗑️ Menu item deleted: {item_key}")
        return deleted
    
    async def toggle_menu_item(self, item_key: str) -> Optional[bool]:
        """
        Activa/desactiva un item de menú.
        
        Returns:
            Nuevo estado (True/False) o None si no existe
        """
        menu_item = await self.get_menu_item(item_key)
        if not menu_item:
            return None
        
        menu_item.is_active = not menu_item.is_active
        await self.session.commit()
        
        logger.info(f"🔄 Menu item toggled: {item_key} -> {menu_item.is_active}")
        return menu_item.is_active
    
    # ═══════════════════════════════════════════════════
    # QUERIES PARA MENÚS
    # ═══════════════════════════════════════════════════
    
    async def get_menu_items_for_role(
        self,
        role: str,
        only_active: bool = True
    ) -> List[MenuItem]:
        """
        Obtiene todos los items de menú para un rol específico.
        
        Args:
            role: 'vip', 'free'
            only_active: Si solo devolver items activos
            
        Returns:
            Lista de MenuItems ordenados
        """
        query = select(MenuItem).where(
            MenuItem.target_role.in_([role, 'all'])
        )
        
        if only_active:
            query = query.where(MenuItem.is_active == True)
        
        query = query.order_by(
            MenuItem.row_number,
            MenuItem.display_order
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_all_menu_items(
        self,
        only_active: bool = False
    ) -> List[MenuItem]:
        """Obtiene todos los items de menú."""
        query = select(MenuItem)
        
        if only_active:
            query = query.where(MenuItem.is_active == True)
        
        query = query.order_by(
            MenuItem.target_role,
            MenuItem.row_number,
            MenuItem.display_order
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ═══════════════════════════════════════════════════
    # MENU CONFIG
    # ═══════════════════════════════════════════════════
    
    async def get_or_create_menu_config(self, role: str) -> MenuConfig:
        """
        Obtiene o crea la configuración de menú para un rol.
        
        Args:
            role: 'vip' o 'free'
            
        Returns:
            MenuConfig para el rol
        """
        result = await self.session.execute(
            select(MenuConfig).where(MenuConfig.role == role)
        )
        config = result.scalar_one_or_none()
        
        if not config:
            config = MenuConfig(role=role)
            self.session.add(config)
            await self.session.commit()
            await self.session.refresh(config)
            logger.info(f"✅ Menu config created for role: {role}")
        
        return config
    
    async def update_menu_config(
        self,
        role: str,
        **kwargs
    ) -> MenuConfig:
        """
        Actualiza la configuración de menú para un rol.
        
        Args:
            role: 'vip' o 'free'
            **kwargs: Campos a actualizar
            
        Returns:
            MenuConfig actualizado
        """
        config = await self.get_or_create_menu_config(role)
        
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        await self.session.commit()
        await self.session.refresh(config)
        
        logger.info(f"✅ Menu config updated for role: {role}")
        return config
    
    # ═══════════════════════════════════════════════════
    # GENERACIÓN DE KEYBOARDS
    # ═══════════════════════════════════════════════════
    
    async def build_keyboard_for_role(
        self,
        role: str
    ) -> List[List[Dict[str, str]]]:
        """
        Construye la estructura de keyboard para un rol.
        
        Args:
            role: 'vip' o 'free'
            
        Returns:
            Lista de filas, cada fila es lista de botones
            Compatible con create_inline_keyboard()
        """
        items = await self.get_menu_items_for_role(role)
        
        if not items:
            return []
        
        # Agrupar por row_number
        rows: Dict[int, List[MenuItem]] = {}
        for item in items:
            if item.row_number not in rows:
                rows[item.row_number] = []
            rows[item.row_number].append(item)
        
        # Construir estructura de keyboard
        keyboard = []
        for row_num in sorted(rows.keys()):
            row_buttons = []
            for item in sorted(rows[row_num], key=lambda x: x.display_order):
                # Construir texto con emoji
                text = f"{item.button_emoji} {item.button_text}" if item.button_emoji else item.button_text
                
                # Determinar callback o url
                if item.action_type == 'url':
                    row_buttons.append({
                        "text": text,
                        "url": item.action_content
                    })
                else:
                    row_buttons.append({
                        "text": text,
                        "callback_data": f"menu:{item.item_key}"
                    })
            
            keyboard.append(row_buttons)
        
        return keyboard
```

---

## 🎮 Handlers de Administrador

### Estados FSM para Configuración

```python
# bot/states/admin.py (agregar)

class MenuConfigStates(StatesGroup):
    """
    Estados para configuración de menús.
    
    Flujos:
    1. Crear botón nuevo
    2. Editar botón existente
    3. Configurar mensaje de bienvenida
    """
    
    # Crear nuevo botón
    waiting_for_button_text = State()
    waiting_for_button_emoji = State()
    waiting_for_action_type = State()
    waiting_for_action_content = State()
    waiting_for_target_role = State()
    
    # Editar botón
    editing_button_text = State()
    editing_action_content = State()
    
    # Configurar menú
    editing_welcome_message = State()
    editing_footer_message = State()
```

### Handlers para Configuración de Menús

```python
# bot/handlers/admin/menu_config.py

"""
Menu Configuration Handlers - Gestión de menús desde interfaz admin.

Permite a administradores:
- Ver/listar botones configurados
- Crear nuevos botones
- Editar botones existentes
- Activar/desactivar botones
- Configurar mensajes del menú
"""
import logging
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.container import ServiceContainer
from bot.states.admin import MenuConfigStates
from bot.utils.keyboards import create_inline_keyboard

logger = logging.getLogger(__name__)

menu_config_router = Router(name="menu_config")


# ═══════════════════════════════════════════════════════════════
# KEYBOARDS PARA CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════

def menu_management_keyboard():
    """Keyboard principal de gestión de menús."""
    return create_inline_keyboard([
        [{"text": "📋 Ver Botones VIP", "callback_data": "menuconfig:list:vip"}],
        [{"text": "📋 Ver Botones FREE", "callback_data": "menuconfig:list:free"}],
        [{"text": "➕ Crear Nuevo Botón", "callback_data": "menuconfig:create"}],
        [{"text": "⚙️ Configurar Mensaje VIP", "callback_data": "menuconfig:msg:vip"}],
        [{"text": "⚙️ Configurar Mensaje FREE", "callback_data": "menuconfig:msg:free"}],
        [{"text": "🔙 Volver", "callback_data": "admin:main"}]
    ])


def button_actions_keyboard(item_key: str, is_active: bool):
    """Keyboard de acciones para un botón específico."""
    toggle_text = "🔴 Desactivar" if is_active else "🟢 Activar"
    return create_inline_keyboard([
        [{"text": "✏️ Editar Texto", "callback_data": f"menuconfig:edit:text:{item_key}"}],
        [{"text": "📝 Editar Contenido", "callback_data": f"menuconfig:edit:content:{item_key}"}],
        [{"text": toggle_text, "callback_data": f"menuconfig:toggle:{item_key}"}],
        [{"text": "🗑️ Eliminar", "callback_data": f"menuconfig:delete:{item_key}"}],
        [{"text": "🔙 Volver", "callback_data": "menuconfig:main"}]
    ])


def role_selection_keyboard():
    """Keyboard para seleccionar rol target."""
    return create_inline_keyboard([
        [{"text": "⭐ Solo VIP", "callback_data": "menuconfig:role:vip"}],
        [{"text": "🆓 Solo FREE", "callback_data": "menuconfig:role:free"}],
        [{"text": "👥 Ambos", "callback_data": "menuconfig:role:all"}],
        [{"text": "❌ Cancelar", "callback_data": "menuconfig:cancel"}]
    ])


def action_type_keyboard():
    """Keyboard para seleccionar tipo de acción."""
    return create_inline_keyboard([
        [{"text": "ℹ️ Información", "callback_data": "menuconfig:actiontype:info"}],
        [{"text": "🔗 URL Externa", "callback_data": "menuconfig:actiontype:url"}],
        [{"text": "📞 Contacto", "callback_data": "menuconfig:actiontype:contact"}],
        [{"text": "❌ Cancelar", "callback_data": "menuconfig:cancel"}]
    ])


# ═══════════════════════════════════════════════════════════════
# HANDLER PRINCIPAL
# ═══════════════════════════════════════════════════════════════

@menu_config_router.callback_query(F.data == "admin:menu_config")
async def callback_menu_config_main(callback: CallbackQuery, session: AsyncSession):
    """Muestra el menú principal de configuración de menús."""
    logger.debug(f"📋 Admin {callback.from_user.id} abrió config de menús")
    
    await callback.message.edit_text(
        "📋 <b>Configuración de Menús</b>\n\n"
        "Desde aquí puedes configurar los botones que verán\n"
        "los usuarios VIP y FREE.\n\n"
        "Selecciona una opción:",
        reply_markup=menu_management_keyboard(),
        parse_mode="HTML"
    )


# ═══════════════════════════════════════════════════════════════
# LISTAR BOTONES
# ═══════════════════════════════════════════════════════════════

@menu_config_router.callback_query(F.data.startswith("menuconfig:list:"))
async def callback_list_buttons(callback: CallbackQuery, session: AsyncSession):
    """Lista los botones configurados para un rol."""
    role = callback.data.split(":")[-1]
    
    container = ServiceContainer(session, callback.bot)
    items = await container.menu.get_menu_items_for_role(role, only_active=False)
    
    if not items:
        text = f"📋 <b>Botones {role.upper()}</b>\n\n"
        text += "No hay botones configurados para este rol.\n\n"
        text += "Usa 'Crear Nuevo Botón' para agregar uno."
    else:
        text = f"📋 <b>Botones {role.upper()}</b>\n\n"
        for i, item in enumerate(items, 1):
            status = "✅" if item.is_active else "❌"
            emoji = item.button_emoji or ""
            text += f"{i}. {status} {emoji} <b>{item.button_text}</b>\n"
            text += f"   └ Key: <code>{item.item_key}</code>\n"
            text += f"   └ Tipo: {item.action_type}\n\n"
    
    # Crear keyboard con botones para cada item
    buttons = []
    for item in items:
        emoji = "✅" if item.is_active else "❌"
        buttons.append([{
            "text": f"{emoji} {item.button_text}",
            "callback_data": f"menuconfig:item:{item.item_key}"
        }])
    
    buttons.append([{"text": "🔙 Volver", "callback_data": "admin:menu_config"}])
    
    await callback.message.edit_text(
        text,
        reply_markup=create_inline_keyboard(buttons),
        parse_mode="HTML"
    )


# ═══════════════════════════════════════════════════════════════
# VER/EDITAR BOTÓN INDIVIDUAL
# ═══════════════════════════════════════════════════════════════

@menu_config_router.callback_query(F.data.startswith("menuconfig:item:"))
async def callback_view_button(callback: CallbackQuery, session: AsyncSession):
    """Muestra detalles y acciones para un botón específico."""
    item_key = callback.data.split(":")[-1]
    
    container = ServiceContainer(session, callback.bot)
    item = await container.menu.get_menu_item(item_key)
    
    if not item:
        await callback.answer("❌ Botón no encontrado", show_alert=True)
        return
    
    status = "✅ Activo" if item.is_active else "❌ Inactivo"
    emoji = item.button_emoji or "(sin emoji)"
    
    text = (
        f"🔘 <b>Detalles del Botón</b>\n\n"
        f"<b>Key:</b> <code>{item.item_key}</code>\n"
        f"<b>Texto:</b> {item.button_text}\n"
        f"<b>Emoji:</b> {emoji}\n"
        f"<b>Rol:</b> {item.target_role.upper()}\n"
        f"<b>Tipo:</b> {item.action_type}\n"
        f"<b>Estado:</b> {status}\n\n"
        f"<b>Contenido:</b>\n<pre>{item.action_content[:200]}...</pre>"
        if len(item.action_content) > 200 else
        f"<b>Contenido:</b>\n<pre>{item.action_content}</pre>"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=button_actions_keyboard(item_key, item.is_active),
        parse_mode="HTML"
    )


# ═══════════════════════════════════════════════════════════════
# CREAR NUEVO BOTÓN - FLUJO FSM
# ═══════════════════════════════════════════════════════════════

@menu_config_router.callback_query(F.data == "menuconfig:create")
async def callback_create_button_start(
    callback: CallbackQuery, 
    state: FSMContext
):
    """Inicia el flujo de creación de botón."""
    await state.clear()
    await state.set_state(MenuConfigStates.waiting_for_button_text)
    
    await callback.message.edit_text(
        "➕ <b>Crear Nuevo Botón</b>\n\n"
        "Paso 1/5: Escribe el texto que verá el usuario en el botón.\n\n"
        "Ejemplo: <code>Información de Contacto</code>\n\n"
        "Envía /cancel para cancelar.",
        parse_mode="HTML"
    )


@menu_config_router.message(MenuConfigStates.waiting_for_button_text)
async def process_button_text(message: Message, state: FSMContext):
    """Procesa el texto del botón."""
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Creación cancelada.")
        return
    
    button_text = message.text.strip()
    if len(button_text) > 100:
        await message.answer("❌ El texto es muy largo (máx 100 caracteres). Intenta de nuevo.")
        return
    
    await state.update_data(button_text=button_text)
    await state.set_state(MenuConfigStates.waiting_for_button_emoji)
    
    await message.answer(
        "➕ <b>Crear Nuevo Botón</b>\n\n"
        "Paso 2/5: Envía un emoji para el botón (opcional).\n\n"
        "Ejemplo: 📞 o ℹ️\n\n"
        "Envía <code>-</code> para omitir el emoji.",
        parse_mode="HTML"
    )


@menu_config_router.message(MenuConfigStates.waiting_for_button_emoji)
async def process_button_emoji(message: Message, state: FSMContext):
    """Procesa el emoji del botón."""
    emoji = message.text.strip()
    
    if emoji == "-" or emoji == "/cancel":
        emoji = None
    elif len(emoji) > 10:
        await message.answer("❌ Envía solo un emoji. Intenta de nuevo.")
        return
    
    await state.update_data(button_emoji=emoji)
    await state.set_state(MenuConfigStates.waiting_for_action_type)
    
    await message.answer(
        "➕ <b>Crear Nuevo Botón</b>\n\n"
        "Paso 3/5: Selecciona el tipo de acción:",
        reply_markup=action_type_keyboard(),
        parse_mode="HTML"
    )


@menu_config_router.callback_query(
    F.data.startswith("menuconfig:actiontype:"),
    MenuConfigStates.waiting_for_action_type
)
async def process_action_type(callback: CallbackQuery, state: FSMContext):
    """Procesa el tipo de acción."""
    action_type = callback.data.split(":")[-1]
    
    await state.update_data(action_type=action_type)
    await state.set_state(MenuConfigStates.waiting_for_action_content)
    
    if action_type == "info":
        prompt = (
            "➕ <b>Crear Nuevo Botón</b>\n\n"
            "Paso 4/5: Escribe el texto informativo que verá el usuario\n"
            "cuando presione este botón.\n\n"
            "Puedes usar formato HTML básico:\n"
            "• <code>&lt;b&gt;negrita&lt;/b&gt;</code>\n"
            "• <code>&lt;i&gt;itálica&lt;/i&gt;</code>\n"
            "• <code>&lt;code&gt;código&lt;/code&gt;</code>"
        )
    elif action_type == "url":
        prompt = (
            "➕ <b>Crear Nuevo Botón</b>\n\n"
            "Paso 4/5: Envía la URL a la que llevará el botón.\n\n"
            "Ejemplo: <code>https://ejemplo.com/contacto</code>"
        )
    else:  # contact
        prompt = (
            "➕ <b>Crear Nuevo Botón</b>\n\n"
            "Paso 4/5: Escribe la información de contacto.\n\n"
            "Ejemplo:\n"
            "<code>📧 Email: soporte@ejemplo.com\n"
            "📱 WhatsApp: +1234567890</code>"
        )
    
    await callback.message.edit_text(prompt, parse_mode="HTML")


@menu_config_router.message(MenuConfigStates.waiting_for_action_content)
async def process_action_content(message: Message, state: FSMContext):
    """Procesa el contenido de la acción."""
    content = message.text.strip()
    
    data = await state.get_data()
    action_type = data.get("action_type")
    
    # Validar URL si es tipo url
    if action_type == "url" and not content.startswith(("http://", "https://")):
        await message.answer("❌ La URL debe comenzar con http:// o https://")
        return
    
    await state.update_data(action_content=content)
    await state.set_state(MenuConfigStates.waiting_for_target_role)
    
    await message.answer(
        "➕ <b>Crear Nuevo Botón</b>\n\n"
        "Paso 5/5: ¿Para qué usuarios será visible este botón?",
        reply_markup=role_selection_keyboard(),
        parse_mode="HTML"
    )


@menu_config_router.callback_query(
    F.data.startswith("menuconfig:role:"),
    MenuConfigStates.waiting_for_target_role
)
async def process_target_role(
    callback: CallbackQuery, 
    state: FSMContext,
    session: AsyncSession
):
    """Procesa el rol target y crea el botón."""
    target_role = callback.data.split(":")[-1]
    
    data = await state.get_data()
    
    # Generar item_key único
    import secrets
    item_key = f"{target_role}_{secrets.token_hex(4)}"
    
    container = ServiceContainer(session, callback.bot)
    
    # Obtener orden (último + 1)
    existing = await container.menu.get_menu_items_for_role(target_role, only_active=False)
    display_order = len(existing)
    row_number = display_order  # Cada botón en su propia fila por defecto
    
    # Crear el botón
    item = await container.menu.create_menu_item(
        item_key=item_key,
        button_text=data["button_text"],
        button_emoji=data.get("button_emoji"),
        action_type=data["action_type"],
        action_content=data["action_content"],
        target_role=target_role,
        display_order=display_order,
        row_number=row_number,
        created_by=callback.from_user.id
    )
    
    await state.clear()
    
    await callback.message.edit_text(
        f"✅ <b>Botón Creado Exitosamente</b>\n\n"
        f"<b>Key:</b> <code>{item.item_key}</code>\n"
        f"<b>Texto:</b> {item.button_text}\n"
        f"<b>Rol:</b> {item.target_role.upper()}\n"
        f"<b>Tipo:</b> {item.action_type}\n\n"
        f"El botón ya está activo y visible para los usuarios.",
        reply_markup=create_inline_keyboard([
            [{"text": "📋 Ver Todos los Botones", "callback_data": f"menuconfig:list:{target_role}"}],
            [{"text": "➕ Crear Otro", "callback_data": "menuconfig:create"}],
            [{"text": "🔙 Volver", "callback_data": "admin:menu_config"}]
        ]),
        parse_mode="HTML"
    )


# ═══════════════════════════════════════════════════════════════
# EDITAR BOTÓN
# ═══════════════════════════════════════════════════════════════

@menu_config_router.callback_query(F.data.startswith("menuconfig:edit:text:"))
async def callback_edit_button_text(
    callback: CallbackQuery, 
    state: FSMContext
):
    """Inicia edición del texto del botón."""
    item_key = callback.data.split(":")[-1]
    
    await state.set_state(MenuConfigStates.editing_button_text)
    await state.update_data(editing_item_key=item_key)
    
    await callback.message.edit_text(
        "✏️ <b>Editar Texto del Botón</b>\n\n"
        "Envía el nuevo texto para el botón.\n\n"
        "Envía /cancel para cancelar.",
        parse_mode="HTML"
    )


@menu_config_router.message(MenuConfigStates.editing_button_text)
async def process_edit_button_text(
    message: Message, 
    state: FSMContext,
    session: AsyncSession
):
    """Procesa la edición del texto."""
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Edición cancelada.")
        return
    
    new_text = message.text.strip()
    if len(new_text) > 100:
        await message.answer("❌ Texto muy largo (máx 100 caracteres).")
        return
    
    data = await state.get_data()
    item_key = data.get("editing_item_key")
    
    container = ServiceContainer(session, message.bot)
    item = await container.menu.update_menu_item(item_key, button_text=new_text)
    
    await state.clear()
    
    if item:
        await message.answer(
            f"✅ Texto actualizado: <b>{new_text}</b>",
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Error al actualizar.")


# ═══════════════════════════════════════════════════════════════
# TOGGLE Y DELETE
# ═══════════════════════════════════════════════════════════════

@menu_config_router.callback_query(F.data.startswith("menuconfig:toggle:"))
async def callback_toggle_button(callback: CallbackQuery, session: AsyncSession):
    """Activa/desactiva un botón."""
    item_key = callback.data.split(":")[-1]
    
    container = ServiceContainer(session, callback.bot)
    new_state = await container.menu.toggle_menu_item(item_key)
    
    if new_state is not None:
        status = "activado ✅" if new_state else "desactivado ❌"
        await callback.answer(f"Botón {status}", show_alert=True)
        
        # Refrescar vista
        item = await container.menu.get_menu_item(item_key)
        if item:
            await callback.message.edit_reply_markup(
                reply_markup=button_actions_keyboard(item_key, item.is_active)
            )
    else:
        await callback.answer("❌ Botón no encontrado", show_alert=True)


@menu_config_router.callback_query(F.data.startswith("menuconfig:delete:"))
async def callback_delete_button(callback: CallbackQuery, session: AsyncSession):
    """Elimina un botón (con confirmación)."""
    item_key = callback.data.split(":")[-1]
    
    # Mostrar confirmación
    await callback.message.edit_text(
        f"⚠️ <b>¿Eliminar botón?</b>\n\n"
        f"Key: <code>{item_key}</code>\n\n"
        f"Esta acción no se puede deshacer.",
        reply_markup=create_inline_keyboard([
            [
                {"text": "✅ Sí, eliminar", "callback_data": f"menuconfig:confirm_delete:{item_key}"},
                {"text": "❌ Cancelar", "callback_data": f"menuconfig:item:{item_key}"}
            ]
        ]),
        parse_mode="HTML"
    )


@menu_config_router.callback_query(F.data.startswith("menuconfig:confirm_delete:"))
async def callback_confirm_delete(callback: CallbackQuery, session: AsyncSession):
    """Confirma y ejecuta la eliminación."""
    item_key = callback.data.split(":")[-1]
    
    container = ServiceContainer(session, callback.bot)
    deleted = await container.menu.delete_menu_item(item_key)
    
    if deleted:
        await callback.message.edit_text(
            "✅ Botón eliminado correctamente.",
            reply_markup=create_inline_keyboard([
                [{"text": "🔙 Volver", "callback_data": "admin:menu_config"}]
            ])
        )
    else:
        await callback.answer("❌ Error al eliminar", show_alert=True)


# ═══════════════════════════════════════════════════════════════
# CANCELAR
# ═══════════════════════════════════════════════════════════════

@menu_config_router.callback_query(F.data == "menuconfig:cancel")
async def callback_cancel(callback: CallbackQuery, state: FSMContext):
    """Cancela cualquier operación en curso."""
    await state.clear()
    await callback.message.edit_text(
        "❌ Operación cancelada.",
        reply_markup=create_inline_keyboard([
            [{"text": "🔙 Volver", "callback_data": "admin:menu_config"}]
        ])
    )
```

---

## 🔄 Modificación del Sistema de Keyboards Existente

### Actualizar `keyboards.py`

```python
# bot/utils/keyboards.py (modificar función existente o agregar nueva)

async def dynamic_user_menu_keyboard(
    session: AsyncSession,
    role: str
) -> InlineKeyboardMarkup:
    """
    Genera keyboard dinámico para usuarios basado en configuración.
    
    Args:
        session: Sesión de BD
        role: 'vip' o 'free'
        
    Returns:
        InlineKeyboardMarkup con botones configurados
    """
    from bot.services.menu_service import MenuService
    
    menu_service = MenuService(session)
    keyboard_structure = await menu_service.build_keyboard_for_role(role)
    
    if not keyboard_structure:
        # Fallback a menú por defecto si no hay configuración
        if role == 'vip':
            return vip_user_menu_keyboard()  # Existente
        else:
            return free_user_menu_keyboard()  # Existente
    
    return create_inline_keyboard(keyboard_structure)
```

### Handler para Botones Dinámicos

```python
# bot/handlers/user/dynamic_menu.py

"""
Dynamic Menu Handler - Procesa callbacks de menús dinámicos.
"""
from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.container import ServiceContainer

dynamic_menu_router = Router(name="dynamic_menu")


@dynamic_menu_router.callback_query(F.data.startswith("menu:"))
async def callback_dynamic_menu_item(
    callback: CallbackQuery, 
    session: AsyncSession
):
    """
    Procesa clicks en botones de menú dinámico.
    
    Callback format: menu:{item_key}
    """
    item_key = callback.data.replace("menu:", "")
    
    container = ServiceContainer(session, callback.bot)
    item = await container.menu.get_menu_item(item_key)
    
    if not item:
        await callback.answer("❌ Opción no disponible", show_alert=True)
        return
    
    if item.action_type == "info":
        # Mostrar información
        emoji = item.button_emoji or "ℹ️"
        await callback.message.answer(
            f"{emoji} <b>{item.button_text}</b>\n\n"
            f"{item.action_content}",
            parse_mode="HTML"
        )
        await callback.answer()
    
    elif item.action_type == "contact":
        # Mostrar información de contacto
        await callback.message.answer(
            f"📞 <b>Contacto</b>\n\n"
            f"{item.action_content}",
            parse_mode="HTML"
        )
        await callback.answer()
    
    # action_type == "url" se maneja automáticamente por Telegram
    # (el botón tiene url en lugar de callback_data)
```

---

## 📁 Estructura de Archivos Nueva

```
bot/
├── database/
│   ├── models.py              # + MenuItem, MenuConfig
│   └── ...
├── services/
│   ├── menu_service.py        # NUEVO
│   └── container.py           # + menu service
├── handlers/
│   ├── admin/
│   │   ├── menu_config.py     # NUEVO
│   │   └── main.py            # + botón "Configurar Menús"
│   └── user/
│       ├── dynamic_menu.py    # NUEVO
│       └── start.py           # Modificar para usar menús dinámicos
├── states/
│   └── admin.py               # + MenuConfigStates
└── utils/
    └── keyboards.py           # + dynamic_user_menu_keyboard
```

---

## 📝 Migración de Base de Datos

```python
# scripts/migrate_menu_config.py

"""
Migración para agregar tablas de configuración de menús.
"""
import asyncio
from sqlalchemy import text

from bot.database.engine import get_engine, init_db


async def migrate():
    """Ejecuta migración de menús."""
    
    # Inicializar BD (crea tablas nuevas automáticamente)
    await init_db()
    
    engine = get_engine()
    
    async with engine.begin() as conn:
        # Verificar que tablas existen
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='menu_items'")
        )
        if result.scalar():
            print("✅ Tabla menu_items creada")
        
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='menu_configs'")
        )
        if result.scalar():
            print("✅ Tabla menu_configs creada")
    
    print("✅ Migración completada")


if __name__ == "__main__":
    asyncio.run(migrate())
```

---

## 🔐 Integración con Admin Menu

Agregar botón en el menú principal de admin:

```python
# bot/utils/keyboards.py - Modificar admin_main_menu_keyboard()

def admin_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Keyboard del menú principal de admin."""
    return create_inline_keyboard([
        [{"text": "📊 Dashboard", "callback_data": "admin:dashboard"}],
        [
            {"text": "⭐ VIP", "callback_data": "admin:vip"},
            {"text": "🆓 Free", "callback_data": "admin:free"}
        ],
        [{"text": "🎮 Gamificación", "callback_data": "admin:gamification"}],
        [{"text": "📋 Configurar Menús", "callback_data": "admin:menu_config"}],  # NUEVO
        [
            {"text": "📊 Estadísticas", "callback_data": "admin:stats"},
            {"text": "⚙️ Configuración", "callback_data": "admin:config"}
        ],
    ])
```

---

## 📊 Diagrama de Flujo: Crear Botón

```
┌─────────────────┐
│ Admin: /admin   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Menú Principal  │
│ [Config Menús]  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ [Crear Botón]   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Paso 1: Texto   │────▶│ "Info Contacto" │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Paso 2: Emoji   │────▶│      "📞"       │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Paso 3: Tipo    │────▶│ [Información]   │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Paso 4: Content │────▶│ "Email: x@y.c"  │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Paso 5: Rol     │────▶│ [VIP] [FREE]    │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐
│ ✅ Botón Creado │
│ Ya visible para │
│ usuarios        │
└─────────────────┘
```

---

## ✅ Checklist de Implementación

### Fase 1: Base de Datos
- [ ] Agregar modelo `MenuItem` a `models.py`
- [ ] Agregar modelo `MenuConfig` a `models.py`
- [ ] Ejecutar migración
- [ ] Actualizar `__init__.py` del módulo database

### Fase 2: Servicios
- [ ] Crear `menu_service.py`
- [ ] Agregar `menu` al `ServiceContainer`
- [ ] Tests unitarios del servicio

### Fase 3: Handlers Admin
- [ ] Crear `menu_config.py` en handlers/admin
- [ ] Agregar estados FSM en `states/admin.py`
- [ ] Registrar router en `admin/__init__.py`
- [ ] Agregar botón en `admin_main_menu_keyboard()`

### Fase 4: Handlers Usuario
- [ ] Crear `dynamic_menu.py` en handlers/user
- [ ] Modificar `start.py` para usar menús dinámicos
- [ ] Registrar router en `user/__init__.py`

### Fase 5: Testing
- [ ] Tests de creación de botones
- [ ] Tests de edición
- [ ] Tests de menús dinámicos
- [ ] Tests de roles (VIP vs FREE)

---

## 📌 Notas Adicionales

1. **Cache**: Considerar agregar cache para menús (Redis o in-memory) para evitar queries frecuentes.

2. **Validación**: Agregar validación de HTML en `action_content` para prevenir XSS.

3. **Audit Log**: Considerar agregar log de cambios en menús para auditoría.

4. **Backup**: Los menús se pueden exportar/importar como JSON para backup.

5. **Preview**: Agregar función de "preview" para que admin vea cómo quedará el menú antes de publicar.
