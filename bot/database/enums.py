"""
Enums para el sistema.

Define enumeraciones usadas en los modelos.
"""
from enum import Enum


class UserRole(str, Enum):
    """
    Roles de usuario en el sistema.

    Roles:
        FREE: Usuario con acceso al canal Free (default)
        VIP: Usuario con suscripción VIP activa
        ADMIN: Administrador del bot

    Transiciones automáticas:
        - Nuevo usuario → FREE
        - Activar token VIP → VIP
        - Expirar suscripción → FREE
        - Asignación manual → ADMIN
    """

    FREE = "free"
    VIP = "vip"
    ADMIN = "admin"

    def __str__(self) -> str:
        """Retorna valor string del enum."""
        return self.value

    @property
    def display_name(self) -> str:
        """Retorna nombre legible del rol."""
        names = {
            UserRole.FREE: "Usuario Free",
            UserRole.VIP: "Usuario VIP",
            UserRole.ADMIN: "Administrador"
        }
        return names[self]

    @property
    def emoji(self) -> str:
        """Retorna emoji del rol."""
        emojis = {
            UserRole.FREE: "🆓",
            UserRole.VIP: "⭐",
            UserRole.ADMIN: "👑"
        }
        return emojis[self]
