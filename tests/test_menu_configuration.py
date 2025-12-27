"""
Tests E2E para el sistema de configuración de menús dinámicos.

Tests incluidos:
- Creación de menu items
- Actualización de menu items
- Activación/desactivación de botones
- Generación de keyboards dinámicos
- Configuración de menús por rol
"""
import pytest
from datetime import datetime

from bot.database.models import MenuItem, MenuConfig
from bot.database import get_session
from bot.services.menu_service import MenuService
from sqlalchemy import select


@pytest.mark.asyncio
async def test_create_menu_item():
    """Test crear un menu item básico."""
    async with get_session() as session:
        menu_service = MenuService(session)

        # Crear menu item
        item = await menu_service.create_menu_item(
            item_key="test_info_button",
            button_text="Información de Prueba",
            action_type="info",
            action_content="Este es un mensaje de prueba",
            target_role="all",
            button_emoji="ℹ️",
            created_by=123456
        )

        assert item is not None
        assert item.item_key == "test_info_button"
        assert item.button_text == "Información de Prueba"
        assert item.action_type == "info"
        assert item.is_active is True


@pytest.mark.asyncio
async def test_get_menu_items_for_role():
    """Test obtener menu items filtrados por rol."""
    async with get_session() as session:
        menu_service = MenuService(session)

        # Crear items para diferentes roles
        await menu_service.create_menu_item(
            item_key="vip_only",
            button_text="Solo VIP",
            action_type="info",
            action_content="Contenido VIP",
            target_role="vip"
        )

        await menu_service.create_menu_item(
            item_key="free_only",
            button_text="Solo FREE",
            action_type="info",
            action_content="Contenido FREE",
            target_role="free"
        )

        await menu_service.create_menu_item(
            item_key="all_users",
            button_text="Todos",
            action_type="info",
            action_content="Contenido para todos",
            target_role="all"
        )

        # Obtener items para VIP (debe incluir 'vip' y 'all')
        vip_items = await menu_service.get_menu_items_for_role("vip")
        assert len(vip_items) == 2
        item_keys = [item.item_key for item in vip_items]
        assert "vip_only" in item_keys
        assert "all_users" in item_keys
        assert "free_only" not in item_keys

        # Obtener items para FREE (debe incluir 'free' y 'all')
        free_items = await menu_service.get_menu_items_for_role("free")
        assert len(free_items) == 2
        item_keys = [item.item_key for item in free_items]
        assert "free_only" in item_keys
        assert "all_users" in item_keys
        assert "vip_only" not in item_keys


@pytest.mark.asyncio
async def test_update_menu_item():
    """Test actualizar un menu item."""
    async with get_session() as session:
        menu_service = MenuService(session)

        # Crear item
        item = await menu_service.create_menu_item(
            item_key="update_test",
            button_text="Texto Original",
            action_type="info",
            action_content="Contenido Original"
        )

        # Actualizar
        updated = await menu_service.update_menu_item(
            "update_test",
            button_text="Texto Actualizado",
            action_content="Contenido Actualizado"
        )

        assert updated is not None
        assert updated.button_text == "Texto Actualizado"
        assert updated.action_content == "Contenido Actualizado"


@pytest.mark.asyncio
async def test_toggle_menu_item():
    """Test activar/desactivar un menu item."""
    async with get_session() as session:
        menu_service = MenuService(session)

        # Crear item (activo por defecto)
        await menu_service.create_menu_item(
            item_key="toggle_test",
            button_text="Test",
            action_type="info",
            action_content="Test"
        )

        # Desactivar
        new_state = await menu_service.toggle_menu_item("toggle_test")
        assert new_state is False

        # Activar nuevamente
        new_state = await menu_service.toggle_menu_item("toggle_test")
        assert new_state is True


@pytest.mark.asyncio
async def test_delete_menu_item():
    """Test eliminar un menu item."""
    async with get_session() as session:
        menu_service = MenuService(session)

        # Crear item
        await menu_service.create_menu_item(
            item_key="delete_test",
            button_text="Test",
            action_type="info",
            action_content="Test"
        )

        # Verificar que existe
        item = await menu_service.get_menu_item("delete_test")
        assert item is not None

        # Eliminar
        deleted = await menu_service.delete_menu_item("delete_test")
        assert deleted is True

        # Verificar que no existe
        item = await menu_service.get_menu_item("delete_test")
        assert item is None


@pytest.mark.asyncio
async def test_build_keyboard_for_role():
    """Test generar estructura de keyboard."""
    async with get_session() as session:
        menu_service = MenuService(session)

        # Crear items con diferentes filas
        await menu_service.create_menu_item(
            item_key="row0_btn1",
            button_text="Botón 1",
            action_type="info",
            action_content="Info 1",
            target_role="vip",
            row_number=0,
            display_order=0
        )

        await menu_service.create_menu_item(
            item_key="row0_btn2",
            button_text="Botón 2",
            action_type="url",
            action_content="https://example.com",
            target_role="vip",
            row_number=0,
            display_order=1
        )

        await menu_service.create_menu_item(
            item_key="row1_btn1",
            button_text="Botón 3",
            action_type="info",
            action_content="Info 3",
            target_role="vip",
            row_number=1,
            display_order=0
        )

        # Generar keyboard
        keyboard = await menu_service.build_keyboard_for_role("vip")

        # Verificar estructura
        assert len(keyboard) == 2  # 2 filas
        assert len(keyboard[0]) == 2  # Fila 0: 2 botones
        assert len(keyboard[1]) == 1  # Fila 1: 1 botón

        # Verificar botón con callback_data
        assert keyboard[0][0]["text"] == "Botón 1"
        assert keyboard[0][0]["callback_data"] == "menu:row0_btn1"

        # Verificar botón con URL
        assert keyboard[0][1]["text"] == "Botón 2"
        assert keyboard[0][1]["url"] == "https://example.com"


@pytest.mark.asyncio
async def test_menu_config_get_or_create():
    """Test obtener o crear configuración de menú."""
    async with get_session() as session:
        menu_service = MenuService(session)

        # Primera vez: crear
        config = await menu_service.get_or_create_menu_config("vip")
        assert config is not None
        assert config.role == "vip"
        assert config.welcome_message == "Bienvenido, selecciona una opción:"

        # Segunda vez: obtener existente
        config2 = await menu_service.get_or_create_menu_config("vip")
        assert config.id == config2.id


@pytest.mark.asyncio
async def test_menu_config_update():
    """Test actualizar configuración de menú."""
    async with get_session() as session:
        menu_service = MenuService(session)

        # Crear config
        config = await menu_service.get_or_create_menu_config("free")

        # Actualizar
        updated = await menu_service.update_menu_config(
            "free",
            welcome_message="¡Hola! Elige una opción:",
            footer_message="Gracias por usar nuestro bot",
            show_subscription_info=False
        )

        assert updated.welcome_message == "¡Hola! Elige una opción:"
        assert updated.footer_message == "Gracias por usar nuestro bot"
        assert updated.show_subscription_info is False


@pytest.mark.asyncio
async def test_menu_items_only_active():
    """Test filtrar solo items activos."""
    async with get_session() as session:
        menu_service = MenuService(session)

        # Crear items
        await menu_service.create_menu_item(
            item_key="active_item",
            button_text="Activo",
            action_type="info",
            action_content="Test",
            target_role="vip"
        )

        inactive = await menu_service.create_menu_item(
            item_key="inactive_item",
            button_text="Inactivo",
            action_type="info",
            action_content="Test",
            target_role="vip"
        )

        # Desactivar segundo item
        await menu_service.toggle_menu_item("inactive_item")

        # Obtener solo activos
        active_items = await menu_service.get_menu_items_for_role("vip", only_active=True)
        assert len(active_items) == 1
        assert active_items[0].item_key == "active_item"

        # Obtener todos
        all_items = await menu_service.get_menu_items_for_role("vip", only_active=False)
        assert len(all_items) == 2


@pytest.mark.asyncio
async def test_menu_item_with_emoji():
    """Test menu item con emoji."""
    async with get_session() as session:
        menu_service = MenuService(session)

        item = await menu_service.create_menu_item(
            item_key="emoji_test",
            button_text="Contacto",
            button_emoji="📞",
            action_type="contact",
            action_content="Email: test@example.com",
            target_role="all"
        )

        # Generar keyboard
        keyboard = await menu_service.build_keyboard_for_role("all")

        # Verificar que el emoji se incluye en el texto
        assert len(keyboard) == 1
        assert "📞" in keyboard[0][0]["text"]
        assert "Contacto" in keyboard[0][0]["text"]
