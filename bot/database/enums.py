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


class TransactionType(str, Enum):
    """
    Tipos de transacciones de puntos en el sistema de gamificación.

    Tipos:
        REACTION: Puntos ganados por reaccionar en publicaciones
        DAILY_GIFT: Puntos del regalo diario
        SHOP_PURCHASE: Puntos gastados en compras de tienda
        ADMIN_GRANT: Puntos otorgados manualmente por admin
        MISSION_REWARD: Puntos ganados por completar misión
    """
    REACTION = "reaction"
    DAILY_GIFT = "daily_gift"
    SHOP_PURCHASE = "shop_purchase"
    ADMIN_GRANT = "admin_grant"
    MISSION_REWARD = "mission_reward"

    def __str__(self) -> str:
        return self.value


class BadgeRarity(str, Enum):
    """
    Rareza de badges en el sistema de gamificación.

    Rareza:
        COMMON: Badge común (fácil de conseguir)
        RARE: Badge raro (requiere esfuerzo)
        EPIC: Badge épico (difícil de conseguir)
        LEGENDARY: Badge legendario (muy difícil)
    """
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"

    def __str__(self) -> str:
        return self.value

    @property
    def emoji(self) -> str:
        """Retorna emoji de rareza."""
        emojis = {
            BadgeRarity.COMMON: "⚪",
            BadgeRarity.RARE: "🔵",
            BadgeRarity.EPIC: "🟣",
            BadgeRarity.LEGENDARY: "🟡"
        }
        return emojis[self]

    @property
    def display_name(self) -> str:
        """Retorna nombre legible de la rareza."""
        names = {
            BadgeRarity.COMMON: "Común",
            BadgeRarity.RARE: "Raro",
            BadgeRarity.EPIC: "Épico",
            BadgeRarity.LEGENDARY: "Legendario"
        }
        return names[self]


class ChannelType(str, Enum):
    """
    Tipos de canales para publicaciones.

    Tipos:
        VIP: Canal VIP (solo suscriptores)
        FREE: Canal Free (acceso público con espera)
    """
    VIP = "vip"
    FREE = "free"

    def __str__(self) -> str:
        return self.value


class MediaType(str, Enum):
    """
    Tipos de media en sets multimedia.

    Tipos:
        PHOTO: Imagen/foto
        VIDEO: Video
        DOCUMENT: Documento/archivo
        AUDIO: Audio/música
    """
    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"

    def __str__(self) -> str:
        return self.value


class ShopItemType(str, Enum):
    """
    Tipos de items en la tienda.

    Tipos:
        BADGE: Badge/insignia
        LEVEL: Nivel de usuario
        VIP_DAYS: Días de acceso VIP
        MEDIA_SET: Set de contenido multimedia
    """
    BADGE = "badge"
    LEVEL = "level"
    VIP_DAYS = "vip_days"
    MEDIA_SET = "media_set"

    def __str__(self) -> str:
        return self.value


class MissionType(str, Enum):
    """
    Tipos de misiones en el sistema de gamificación.

    Tipos:
        REACT_N_TIMES: Reaccionar N veces
        REACH_STREAK: Alcanzar racha de N
        CLAIM_DAILY: Reclamar regalo diario N veces
    """
    REACT_N_TIMES = "react_n_times"
    REACH_STREAK = "reach_streak"
    CLAIM_DAILY = "claim_daily"

    def __str__(self) -> str:
        return self.value

    @property
    def display_name(self) -> str:
        """Retorna nombre legible del tipo de misión."""
        names = {
            MissionType.REACT_N_TIMES: "Reaccionar N veces",
            MissionType.REACH_STREAK: "Alcanzar racha",
            MissionType.CLAIM_DAILY: "Reclamar regalo diario"
        }
        return names[self]


class RewardType(str, Enum):
    """
    Tipos de recompensas para misiones.

    Tipos:
        POINTS: Puntos (besitos)
        BADGE: Badge/insignia
        MEDIA_SET: Set de contenido multimedia
    """
    POINTS = "points"
    BADGE = "badge"
    MEDIA_SET = "media_set"

    def __str__(self) -> str:
        return self.value
