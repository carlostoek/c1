"""Filtros para validación de permisos de administrador."""

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from config import Config


class IsAdmin(BaseFilter):
    """
    Filtro para verificar si el usuario es administrador.

    Uso:
        @router.message(Command("admin"), IsAdmin())
        async def admin_command(message: Message):
            ...

    Returns:
        True si el usuario es admin, False en caso contrario
    """

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        """
        Verifica si el usuario del evento es administrador.

        Args:
            event: Message o CallbackQuery a validar

        Returns:
            True si es admin, False en caso contrario
        """
        user = event.from_user
        if user is None:
            return False

        return Config.is_admin(user.id)
