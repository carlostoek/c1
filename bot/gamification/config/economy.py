"""
Configuración de Economía de Besitos - Sistema de Gamificación

Este archivo centraliza TODOS los valores de la economía del bot.
Cualquier cambio aquí afecta el comportamiento de todo el sistema.

Author: Sistema de Gamificación
Version: 1.0
"""

from typing import Dict, List, Any, Optional


class EconomyConfig:
    """
    Configuración central de economía de besitos.

    TODOS los valores de recompensas, costos y umbrales se definen aquí.
    """

    # =========================================================================
    # 1. RECOMPENSAS POR ACCIÓN
    # =========================================================================

    # Reacciones a publicaciones
    REACTION_REWARD = 0.1  # Besitos por cada reacción
    DAILY_FIRST_REACTION = 0.5  # Bonus por primera reacción del día

    # Regalo diario
    DAILY_GIFT_BASE = 1.0  # Besitos base del regalo diario
    DAILY_GIFT_VIP_BONUS = 1.5  # Multiplicador para usuarios VIP

    # Misiones/Encargos
    DAILY_MISSION_COMPLETE = 1.0  # Besitos por misión diaria
    WEEKLY_MISSION_COMPLETE = 3.0  # Besitos por misión semanal
    MONTHLY_MISSION_COMPLETE = 10.0  # Besitos por misión mensual
    LEVEL_EVALUATION_COMPLETE = 5.0  # Besitos por completar evaluación de nivel

    # ============================================================================
    # 2. BONIFICACIONES DE RACHA (STREAK BONUSES)
    # ============================================================================

    # Bonos por hitos de días consecutivos
    STREAK_7_DAYS_BONUS = 2.0
    STREAK_14_DAYS_BONUS = 4.0
    STREAK_30_DAYS_BONUS = 10.0
    STREAK_60_DAYS_BONUS = 20.0
    STREAK_100_DAYS_BONUS = 50.0

    # Multiplicador de regalo diario según racha
    STREAK_MULTIPLIER_7 = 1.2  # 20% más de regalo
    STREAK_MULTIPLIER_14 = 1.5  # 50% más de regalo
    STREAK_MULTIPLIER_30 = 2.0  # 100% más de regalo

    # =========================================================================
    # 3. NIVELES DEL PROTOCOLO DE ACCESO
    # =========================================================================

    LEVELS: Dict[int, Dict[str, Any]] = {
        1: {
            "name": "Visitante",
            "threshold": 0,
            "description": "Recién llegado, bajo observación de Lucien"
        },
        2: {
            "name": "Observado",
            "threshold": 5,
            "description": "Lucien ha notado su presencia"
        },
        3: {
            "name": "Evaluado",
            "threshold": 15,
            "description": "Ha pasado las primeras pruebas"
        },
        4: {
            "name": "Reconocido",
            "threshold": 35,
            "description": "Diana sabe que existe"
        },
        5: {
            "name": "Admitido",
            "threshold": 70,
            "description": "Tiene derecho a estar en el Diván"
        },
        6: {
            "name": "Confidente",
            "threshold": 120,
            "description": "Lucien comparte información privilegiada"
        },
        7: {
            "name": "Guardián de Secretos",
            "threshold": 200,
            "description": "El círculo más íntimo"
        }
    }

    # =========================================================================
    # 4. HITOS DE RACHA (MILESTONES)
    # =========================================================================

    STREAK_MILESTONES: Dict[int, Dict[str, Any]] = {
        7: {
            "bonus": 2.0,
            "message_key": "STREAK_MILESTONE_7",
            "description": "Una semana de dedicación"
        },
        14: {
            "bonus": 4.0,
            "message_key": "STREAK_MILESTONE_14",
            "description": "Dos semanas sin fallar"
        },
        30: {
            "bonus": 10.0,
            "message_key": "STREAK_MILESTONE_30",
            "description": "Un mes de constancia"
        },
        60: {
            "bonus": 20.0,
            "message_key": "STREAK_MILESTONE_60",
            "description": "Dos meses de dedicación"
        },
        100: {
            "bonus": 50.0,
            "message_key": "STREAK_MILESTONE_100",
            "description": "100 días - Maestría de la persistencia"
        }
    }

    # =========================================================================
    # 5. MILESTONES DE BESITOS TOTALES
    # =========================================================================

    BESITOS_MILESTONES: List[int] = [
        10, 25, 50, 75, 100, 150, 200, 300, 500, 750,
        1000, 1500, 2000, 3000, 5000, 10000
    ]

    # =========================================================================
    # 6. EASTER EGGS
    # =========================================================================

    EASTER_EGG_FOUND_MIN = 2.0
    EASTER_EGG_FOUND_MAX = 5.0

    # =========================================================================
    # 7. REFERIDOS
    # =========================================================================

    REFERRAL_REWARD = 5.0  # Besitos por traer un nuevo usuario
    REFERRAL_CONVERTED_BONUS = 10.0  # Bonus extra si el referido se mantiene activo

    # =========================================================================
    # 8. COSTOS DEL GABINETE (SHOP)
    # =========================================================================

    # Costos mínimos y máximos de artículos
    SHOP_MIN_COST = 1.0
    SHOP_MAX_COST = 1000.0

    # =========================================================================
    # 9. LÍMITES Y RESTRICCIONES
    # =========================================================================

    # Máximo de besitos que se pueden ganar por día (anti-abuso)
    MAX_DAILY_EARNINGS = 100.0

    # Máximo de reacciones que dan recompensa por día
    MAX_REACTIONS_PER_DAY = 50

    # Penalización por inactividad (días sin actividad)
    INACTIVITY_PENALTY_DAYS = 30
    INACTIVITY_PENALTY_PERCENTAGE = 0.1  # 10% de reducción

    # =========================================================================
    # 10. HELPERS
    # =========================================================================

    @classmethod
    def get_level_for_besitos(cls, besitos: float) -> Dict[str, Any]:
        """
        Obtiene el nivel correspondiente a una cantidad de besitos.

        Args:
            besitos: Cantidad total de besitos del usuario

        Returns:
            Diccionario con info del nivel {level, name, threshold, description}
        """
        current_level = cls.LEVELS[1]  # Default: Visitante

        for level_num, level_info in sorted(cls.LEVELS.items()):
            if besitos >= level_info["threshold"]:
                current_level = {
                    "level": level_num,
                    **level_info
                }
            else:
                break

        return current_level

    @classmethod
    def get_next_level(cls, besitos: float) -> Optional[Dict[str, Any]]:
        """
        Obtiene el siguiente nivel a alcanzar.

        Args:
            besitos: Cantidad total de besitos del usuario

        Returns:
            Diccionario con info del siguiente nivel o None si ya es máximo
        """
        for level_num, level_info in sorted(cls.LEVELS.items()):
            if besitos < level_info["threshold"]:
                return {
                    "level": level_num,
                    **level_info
                }
        return None  # Ya está en el nivel máximo

    @classmethod
    def get_streak_bonus(cls, streak_days: int) -> float:
        """
        Obtiene el bono correspondiente a una racha de días.

        Args:
            streak_days: Días consecutivos de actividad

        Returns:
            Bono de besitos por la racha
        """
        bonus = 0.0
        for milestone, info in sorted(cls.STREAK_MILESTONES.items()):
            if streak_days >= milestone:
                bonus = info["bonus"]
        return bonus

    @classmethod
    def get_daily_multiplier(cls, streak_days: int) -> float:
        """
        Obtiene el multiplicador del regalo diario según racha.

        Args:
            streak_days: Días consecutivos de actividad

        Returns:
            Multiplicador a aplicar al regalo diario
        """
        if streak_days >= 30:
            return cls.STREAK_MULTIPLIER_30
        elif streak_days >= 14:
            return cls.STREAK_MULTIPLIER_14
        elif streak_days >= 7:
            return cls.STREAK_MULTIPLIER_7
        return 1.0

    @classmethod
    def is_milestone(cls, besitos: float) -> bool:
        """
        Verifica si una cantidad de besitos es un hito.

        Args:
            besitos: Cantidad total de besitos

        Returns:
            True si es un hito (número redondo significativo)
        """
        return int(besitos) in cls.BESITOS_MILESTONES


# =============================================================================
# CONSTANTS PARA COMPATIBILIDAD CON CÓDIGO EXISTENTE
# =============================================================================

# Valores por defecto si no hay config en BD
DEFAULT_DAILY_GIFT_BESITOS = EconomyConfig.DAILY_GIFT_BASE
DEFAULT_REACTION_REWARD = EconomyConfig.REACTION_REWARD

# Umbrales de nivel para queries rápidas
LEVEL_THRESHOLDS = [info["threshold"] for info in EconomyConfig.LEVELS.values()]
