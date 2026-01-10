"""
MenuService - Servicio de gestión de menús dinámicos.

Permite crear y gestionar menús configurables por administradores
sin necesidad de modificar código.
"""
import logging
from typing import List, Dict, Optional, Tuple

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.database.models_menu import MenuItem, MenuConfig

logger = logging.getLogger(__name__)


class MenuService:
    """
    Servicio de gestión de menús dinámicos.

    Responsabilidades:
    - Construir keyboards según rol de usuario
    - CRUD de items de menú
    - Gestión de configuración por rol
    - Manejo de jerarquías (submenús)
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio.

        Args:
            session: Sesión async de SQLAlchemy
        """
        self._session = session

    async def get_menu_for_role(
        self,
        role: str,
        user_completed_onboarding: bool = True,
        parent_key: Optional[str] = None
    ) -> List[MenuItem]:
        """
        Obtiene items de menú para un rol específico.

        Args:
            role: Rol del usuario ('vip', 'free', 'all')
            user_completed_onboarding: Si el usuario completó onboarding
            parent_key: Si se especifica, obtiene solo items de ese submenú

        Returns:
            Lista de MenuItems ordenados por display_order y row_number
        """
        # Construir query base
        stmt = (
            select(MenuItem)
            .where(
                and_(
                    MenuItem.is_active == True,
                    MenuItem.parent_key == parent_key  # None para menú principal
                )
            )
        )

        # Filtrar por rol (incluir 'all' siempre)
        if role == "vip":
            stmt = stmt.where(MenuItem.target_role.in_(["vip", "all"]))
        elif role == "free":
            stmt = stmt.where(MenuItem.target_role.in_(["free", "all"]))
        elif role == "admin":
            stmt = stmt.where(MenuItem.target_role.in_(["admin", "all"]))
        else:
            # Usuario sin rol específico, solo 'all'
            stmt = stmt.where(MenuItem.target_role == "all")

        # NO filtrar por onboarding - todas las opciones visibles
        # La validación se hace cuando el usuario accede a la funcionalidad

        # Ordenar
        stmt = stmt.order_by(MenuItem.display_order, MenuItem.row_number)

        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        logger.debug(
            f"Menu items para role='{role}', onboarding={user_completed_onboarding}, "
            f"parent='{parent_key}': {len(items)} items"
        )

        return items

    async def build_keyboard_for_role(
        self,
        role: str,
        user_id: int,
        completed_onboarding: bool = True,
        parent_key: Optional[str] = None
    ) -> List[List[Dict[str, str]]]:
        """
        Construye estructura de keyboard para create_inline_keyboard().

        Args:
            role: Rol del usuario
            user_id: ID del usuario (para logging)
            completed_onboarding: Si completó onboarding
            parent_key: Si se especifica, construye submenú

        Returns:
            Lista de filas de botones compatible con create_inline_keyboard()

        Example:
            >>> keyboard = await menu_service.build_keyboard_for_role("free", 12345)
            >>> # Retorna:
            >>> [
            >>>     [{"text": "📢 Info", "callback_data": "menu:info"}],
            >>>     [{"text": "🎁 Sets", "callback_data": "menu:sets"}]
            >>> ]
        """
        # Obtener items del menú
        items = await self.get_menu_for_role(
            role=role,
            user_completed_onboarding=completed_onboarding,
            parent_key=parent_key
        )

        if not items:
            logger.warning(
                f"No se encontraron items de menú para role='{role}', "
                f"parent='{parent_key}'"
            )
            return []

        # Agrupar por fila (row_number)
        rows: Dict[int, List[Dict[str, str]]] = {}

        for item in items:
            # Construir botón
            button_text = item.button_text
            if item.button_emoji:
                button_text = f"{item.button_emoji} {button_text}"

            button: Dict[str, str] = {"text": button_text}

            # Determinar tipo de botón según action_type
            if item.action_type == "url":
                button["url"] = item.action_content
            elif item.action_type == "submenu":
                # Submenú: callback con prefijo submenu:
                button["callback_data"] = f"submenu:{item.item_key}"
            elif item.action_type == "blocked":
                # Opción bloqueada (requiere onboarding)
                button["callback_data"] = f"blocked:{item.item_key}"
            else:
                # callback, info, o cualquier otro
                button["callback_data"] = item.action_content

            # Agregar a fila correspondiente
            row_num = item.row_number
            if row_num not in rows:
                rows[row_num] = []
            rows[row_num].append(button)

        # Convertir dict de filas a lista ordenada
        keyboard = [rows[row_num] for row_num in sorted(rows.keys())]

        logger.debug(
            f"Keyboard construido para role='{role}', user={user_id}: "
            f"{len(keyboard)} filas, {sum(len(row) for row in keyboard)} botones"
        )

        return keyboard

    async def create_menu_item(
        self,
        item_key: str,
        button_text: str,
        action_type: str,
        action_content: str,
        target_role: str = "all",
        parent_key: Optional[str] = None,
        button_emoji: Optional[str] = None,
        display_order: int = 0,
        row_number: int = 0,
        requires_onboarding: bool = False,
        created_by: Optional[int] = None
    ) -> MenuItem:
        """
        Crea un nuevo item de menú.

        Args:
            item_key: Clave única del item
            button_text: Texto del botón
            action_type: Tipo de acción ('callback', 'url', 'submenu', 'info', 'blocked')
            action_content: Contenido de la acción (callback_data, URL, etc.)
            target_role: Rol objetivo ('vip', 'free', 'all', 'admin')
            parent_key: Clave del item padre (para submenús)
            button_emoji: Emoji opcional
            display_order: Orden de presentación
            row_number: Número de fila en keyboard
            requires_onboarding: Si requiere onboarding completado
            created_by: ID del admin que crea

        Returns:
            MenuItem creado

        Raises:
            ValueError: Si item_key ya existe o parent_key no existe
        """
        # Verificar si item_key ya existe
        existing = await self.get_menu_item_by_key(item_key)
        if existing:
            raise ValueError(f"Item con key '{item_key}' ya existe")

        # Verificar parent_key si se especifica
        if parent_key:
            parent = await self.get_menu_item_by_key(parent_key)
            if not parent:
                raise ValueError(f"Parent key '{parent_key}' no existe")

        # Crear item
        item = MenuItem(
            item_key=item_key,
            button_text=button_text,
            action_type=action_type,
            action_content=action_content,
            target_role=target_role,
            parent_key=parent_key,
            button_emoji=button_emoji,
            display_order=display_order,
            row_number=row_number,
            requires_onboarding=requires_onboarding,
            is_active=True,
            created_by=created_by
        )

        self._session.add(item)
        await self._session.flush()
        await self._session.refresh(item)

        logger.info(
            f"MenuItem creado: key='{item_key}', role='{target_role}', "
            f"type='{action_type}'"
        )

        return item

    async def get_menu_item_by_key(self, item_key: str) -> Optional[MenuItem]:
        """
        Obtiene un item de menú por su key.

        Args:
            item_key: Clave del item

        Returns:
            MenuItem o None si no existe
        """
        stmt = select(MenuItem).where(MenuItem.item_key == item_key)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_menu_item(
        self,
        item_key: str,
        **kwargs
    ) -> Optional[MenuItem]:
        """
        Actualiza un item de menú existente.

        Args:
            item_key: Clave del item a actualizar
            **kwargs: Campos a actualizar

        Returns:
            MenuItem actualizado o None si no existe
        """
        item = await self.get_menu_item_by_key(item_key)
        if not item:
            logger.warning(f"Item '{item_key}' no existe")
            return None

        # Actualizar campos permitidos
        updatable_fields = {
            "button_text", "button_emoji", "action_type", "action_content",
            "target_role", "parent_key", "display_order", "row_number",
            "requires_onboarding", "is_active"
        }

        for field, value in kwargs.items():
            if field in updatable_fields and hasattr(item, field):
                setattr(item, field, value)

        await self._session.flush()
        await self._session.refresh(item)

        logger.info(f"MenuItem '{item_key}' actualizado: {list(kwargs.keys())}")

        return item

    async def delete_menu_item(self, item_key: str) -> bool:
        """
        Elimina un item de menú (soft delete).

        Args:
            item_key: Clave del item a eliminar

        Returns:
            True si se eliminó, False si no existía
        """
        item = await self.get_menu_item_by_key(item_key)
        if not item:
            logger.warning(f"Item '{item_key}' no existe")
            return False

        item.is_active = False
        await self._session.flush()

        logger.info(f"MenuItem '{item_key}' eliminado (soft delete)")

        return True

    async def get_submenu_items(self, parent_key: str) -> List[MenuItem]:
        """
        Obtiene todos los items de un submenú.

        Args:
            parent_key: Clave del item padre

        Returns:
            Lista de MenuItems hijos
        """
        stmt = (
            select(MenuItem)
            .where(
                and_(
                    MenuItem.parent_key == parent_key,
                    MenuItem.is_active == True
                )
            )
            .order_by(MenuItem.display_order, MenuItem.row_number)
        )

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_or_create_menu_config(
        self,
        role: str,
        welcome_message: str = "",
        footer_message: Optional[str] = None,
        show_subscription_info: bool = False
    ) -> MenuConfig:
        """
        Obtiene o crea configuración de menú para un rol.

        Args:
            role: Rol ('vip', 'free', 'profile')
            welcome_message: Mensaje de bienvenida
            footer_message: Mensaje de footer opcional
            show_subscription_info: Si mostrar info de suscripción

        Returns:
            MenuConfig
        """
        stmt = select(MenuConfig).where(MenuConfig.role == role)
        result = await self._session.execute(stmt)
        config = result.scalar_one_or_none()

        if not config:
            config = MenuConfig(
                role=role,
                welcome_message=welcome_message or f"Menú {role.upper()}",
                footer_message=footer_message,
                show_subscription_info=show_subscription_info
            )
            self._session.add(config)
            await self._session.flush()
            await self._session.refresh(config)

            logger.info(f"MenuConfig creado para role='{role}'")

        return config

    async def update_menu_config(
        self,
        role: str,
        **kwargs
    ) -> Optional[MenuConfig]:
        """
        Actualiza configuración de menú.

        Args:
            role: Rol de la configuración
            **kwargs: Campos a actualizar

        Returns:
            MenuConfig actualizado o None si no existe
        """
        stmt = select(MenuConfig).where(MenuConfig.role == role)
        result = await self._session.execute(stmt)
        config = result.scalar_one_or_none()

        if not config:
            logger.warning(f"MenuConfig para role='{role}' no existe")
            return None

        # Actualizar campos
        for field, value in kwargs.items():
            if hasattr(config, field):
                setattr(config, field, value)

        await self._session.flush()
        await self._session.refresh(config)

        logger.info(f"MenuConfig para role='{role}' actualizado")

        return config
