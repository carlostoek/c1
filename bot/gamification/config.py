"""
Gamification Config - Configuración de puntos, rangos y recompensas.

Define cuántos Besitos se ganan por cada acción y los requisitos
para cada rango.
"""
from dataclasses import dataclass
from typing import List


@dataclass
class BesitosReward:
    """Recompensa de Besitos por acción."""
    action: str
    amount: int
    description: str


@dataclass
class Rank:
    """Definición de un rango."""
    name: str
    min_besitos: int
    icon: str
    color: str


@dataclass
class BadgeDefinition:
    """Definición de una insignia."""
    id: str
    name: str
    description: str
    icon: str
    requirement_type: str
    requirement_value: int


class GamificationConfig:
    """
    Configuración central de gamificación.

    Define todas las recompensas y requisitos del sistema.
    """

    # ===== RECOMPENSAS DE BESITOS =====

    BESITOS_REWARDS = {
        # Usuario básico
        "user_started": BesitosReward(
            action="user_started",
            amount=10,
            description="Bienvenida al bot"
        ),

        # Canal Free
        "joined_free_channel": BesitosReward(
            action="joined_free_channel",
            amount=25,
            description="Ingreso al canal Free"
        ),

        # VIP
        "joined_vip": BesitosReward(
            action="joined_vip",
            amount=100,
            description="Activación VIP"
        ),

        # Reacciones (botones inline)
        "message_reacted": BesitosReward(
            action="message_reacted",
            amount=5,
            description="Reacción a mensaje"
        ),
        "first_reaction_of_day": BesitosReward(
            action="first_reaction_of_day",
            amount=10,
            description="Primera reacción del día (bonus)"
        ),

        # Daily login
        "daily_login_base": BesitosReward(
            action="daily_login_base",
            amount=20,
            description="Regalo diario base"
        ),
        "daily_login_streak_bonus": BesitosReward(
            action="daily_login_streak_bonus",
            amount=5,
            description="Bonus por racha (5 por día consecutivo)"
        ),

        # Referrals
        "referral_success": BesitosReward(
            action="referral_success",
            amount=50,
            description="Referido exitoso"
        ),

        # Minijuegos (para futuro)
        "minigame_win": BesitosReward(
            action="minigame_win",
            amount=15,
            description="Victoria en minijuego"
        ),
    }

    # ===== RANGOS =====

    RANKS: List[Rank] = [
        Rank(name="Novato", min_besitos=0, icon="🌱", color="#95a5a6"),
        Rank(name="Bronce", min_besitos=500, icon="🥉", color="#cd7f32"),
        Rank(name="Plata", min_besitos=2000, icon="🥈", color="#c0c0c0"),
    ]

    # ===== BADGES (Insignias) =====

    BADGES: List[BadgeDefinition] = [
        # Streaks
        BadgeDefinition(
            id="streak_7",
            name="Constante",
            description="7 días consecutivos de login",
            icon="🔥",
            requirement_type="daily_streak",
            requirement_value=7
        ),
        BadgeDefinition(
            id="streak_30",
            name="Dedicado",
            description="30 días consecutivos de login",
            icon="💪",
            requirement_type="daily_streak",
            requirement_value=30
        ),

        # Reacciones
        BadgeDefinition(
            id="reactions_100",
            name="Reactor",
            description="100 reacciones totales",
            icon="❤️",
            requirement_type="total_reactions",
            requirement_value=100
        ),

        # VIP
        BadgeDefinition(
            id="vip_member",
            name="VIP",
            description="Suscripción VIP activa",
            icon="⭐",
            requirement_type="vip_active",
            requirement_value=1
        ),

        # Besitos acumulados
        BadgeDefinition(
            id="besitos_1000",
            name="Coleccionista",
            description="1000 Besitos acumulados",
            icon="💋",
            requirement_type="total_besitos",
            requirement_value=1000
        ),
    ]

    # ===== LÍMITES DE RATE LIMITING =====

    # Máximo de reacciones que dan Besitos por día
    MAX_REACTIONS_PER_DAY = 50

    # Tiempo mínimo entre reacciones que dan puntos (segundos)
    MIN_SECONDS_BETWEEN_REACTIONS = 5

    @classmethod
    def get_reward(cls, action: str) -> BesitosReward:
        """Obtiene la recompensa para una acción."""
        return cls.BESITOS_REWARDS.get(action)

    @classmethod
    def get_rank_for_besitos(cls, besitos: int) -> Rank:
        """Obtiene el rango correspondiente a una cantidad de Besitos."""
        # Ordenar de mayor a menor
        sorted_ranks = sorted(cls.RANKS, key=lambda r: r.min_besitos, reverse=True)

        for rank in sorted_ranks:
            if besitos >= rank.min_besitos:
                return rank

        # Si no califica para ninguno, retornar el primero (Novato)
        return cls.RANKS[0]

    @classmethod
    def get_badge_definition(cls, badge_id: str) -> BadgeDefinition:
        """Obtiene la definición de una insignia."""
        for badge in cls.BADGES:
            if badge.id == badge_id:
                return badge
        return None
