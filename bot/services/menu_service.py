"""
Menu Service - Gestión de menús dinámicos.

Proporciona operaciones CRUD para MenuItems y MenuConfigs,
así como generación dinámica de keyboards basados en rol.
"""
import logging
from typing import List, Optional, Dict, Any

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import MenuItem, MenuConfig

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
