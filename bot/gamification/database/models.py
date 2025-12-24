"""Modelos de base de datos para el módulo de gamificación.

Define 13 modelos SQLAlchemy 2.0 que representan la estructura
de datos para el sistema de gamificación del bot.
"""

from typing import Optional, List
from datetime import datetime, UTC

from sqlalchemy import (
    BigInteger, String, Integer, Boolean, DateTime, ForeignKey, Index, Text
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# Importar Base del sistema core
try:
    from bot.database.models import Base
except ImportError:
    # Fallback si no existe
    class Base(DeclarativeBase):
        pass


class UserGamification(Base):
    """Perfil de gamificación del usuario.

    Almacena balance de besitos, nivel actual y relaciones
    con misiones y recompensas. Relación 1-to-1 con usuario del sistema core.
    """
    __tablename__ = "user_gamification"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    total_besitos: Mapped[int] = mapped_column(Integer, default=0)
    besitos_earned: Mapped[int] = mapped_column(Integer, default=0)
    besitos_spent: Mapped[int] = mapped_column(Integer, default=0)
    current_level_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("levels.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )

    # Relaciones
    current_level: Mapped[Optional["Level"]] = relationship(
        "Level",
        foreign_keys=[current_level_id],
        back_populates="users"
    )
    user_reactions: Mapped[List["UserReaction"]] = relationship(
        "UserReaction",
        back_populates="user_gamification",
        cascade="all, delete-orphan"
    )
    user_streak: Mapped[Optional["UserStreak"]] = relationship(
        "UserStreak",
        back_populates="user_gamification",
        cascade="all, delete-orphan",
        uselist=False
    )
    user_missions: Mapped[List["UserMission"]] = relationship(
        "UserMission",
        back_populates="user_gamification",
        cascade="all, delete-orphan"
    )
    user_rewards: Mapped[List["UserReward"]] = relationship(
        "UserReward",
        back_populates="user_gamification",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index('ix_user_gamification_total_besitos', 'total_besitos'),
    )


class Reaction(Base):
    """Catálogo de reacciones configuradas en el sistema.

    Almacena emojis disponibles y cuántos besitos otorga cada uno.
    """
    __tablename__ = "reactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    emoji: Mapped[str] = mapped_column(String(10), unique=True)
    besitos_value: Mapped[int] = mapped_column(Integer, default=1)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )

    # Relaciones
    user_reactions: Mapped[List["UserReaction"]] = relationship(
        "UserReaction",
        back_populates="reaction",
        cascade="all, delete-orphan"
    )


class UserReaction(Base):
    """Registro de cada reacción que hace un usuario.

    Almacena historial de reacciones con timestamps para calcular rachas.
    """
    __tablename__ = "user_reactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("user_gamification.user_id")
    )
    reaction_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("reactions.id")
    )
    channel_id: Mapped[int] = mapped_column(BigInteger)
    message_id: Mapped[int] = mapped_column(BigInteger)
    reacted_at: Mapped[datetime] = mapped_column(DateTime)

    # Relaciones
    user_gamification: Mapped["UserGamification"] = relationship(
        "UserGamification",
        back_populates="user_reactions",
        foreign_keys=[user_id]
    )
    reaction: Mapped["Reaction"] = relationship(
        "Reaction",
        back_populates="user_reactions"
    )

    __table_args__ = (
        Index('ix_user_reactions_user_reacted', 'user_id', 'reacted_at'),
        Index('ix_user_reactions_user_channel', 'user_id', 'channel_id'),
    )


class UserStreak(Base):
    """Rachas de reacciones consecutivas por usuario.

    Trackea el streak actual y el récord histórico de reacciones
    consecutivas de cada usuario.
    """
    __tablename__ = "user_streaks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("user_gamification.user_id"), unique=True
    )
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_reaction_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )

    # Relaciones
    user_gamification: Mapped["UserGamification"] = relationship(
        "UserGamification",
        back_populates="user_streak",
        foreign_keys=[user_id]
    )


class Level(Base):
    """Niveles disponibles en el sistema de gamificación.

    Define hitos de progresión con besitos requeridos y beneficios asociados.
    """
    __tablename__ = "levels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    min_besitos: Mapped[int] = mapped_column(Integer)
    order: Mapped[int] = mapped_column(Integer)
    benefits: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )

    # Relaciones
    users: Mapped[List["UserGamification"]] = relationship(
        "UserGamification",
        back_populates="current_level",
        foreign_keys=[UserGamification.current_level_id]
    )
    missions: Mapped[List["Mission"]] = relationship(
        "Mission",
        back_populates="auto_level_up",
        foreign_keys="Mission.auto_level_up_id"
    )

    __table_args__ = (
        Index('ix_levels_min_besitos', 'min_besitos'),
        Index('ix_levels_order', 'order'),
    )


class Mission(Base):
    """Misiones configuradas por administradores.

    Define objetivos con criterios de completación y recompensas asociadas.
    """
    __tablename__ = "missions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(500))
    mission_type: Mapped[str] = mapped_column(String(50))
    criteria: Mapped[str] = mapped_column(String(1000))
    besitos_reward: Mapped[int] = mapped_column(Integer)
    auto_level_up_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("levels.id"), nullable=True
    )
    unlock_rewards: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    repeatable: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )

    # Relaciones
    auto_level_up: Mapped[Optional["Level"]] = relationship(
        "Level",
        back_populates="missions",
        foreign_keys=[auto_level_up_id]
    )
    user_missions: Mapped[List["UserMission"]] = relationship(
        "UserMission",
        back_populates="mission",
        cascade="all, delete-orphan"
    )


class UserMission(Base):
    """Progreso de cada usuario en misiones.

    Trackea el estado de completación y progreso parcial en cada misión.
    """
    __tablename__ = "user_missions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("user_gamification.user_id")
    )
    mission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("missions.id")
    )
    progress: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20))
    started_at: Mapped[datetime] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    claimed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    # Relaciones
    user_gamification: Mapped["UserGamification"] = relationship(
        "UserGamification",
        back_populates="user_missions",
        foreign_keys=[user_id]
    )
    mission: Mapped["Mission"] = relationship(
        "Mission",
        back_populates="user_missions"
    )

    __table_args__ = (
        Index('ix_user_missions_user_mission', 'user_id', 'mission_id'),
        Index('ix_user_missions_user_status', 'user_id', 'status'),
    )


class Reward(Base):
    """Recompensas disponibles en el sistema.

    Define premios que pueden desbloquearse por misiones o comprarse
    con besitos. Clase base para herencia (badges, items, etc).
    """
    __tablename__ = "rewards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(500))
    reward_type: Mapped[str] = mapped_column(String(50))
    cost_besitos: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    unlock_conditions: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True
    )
    reward_metadata: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )

    # Relaciones
    user_rewards: Mapped[List["UserReward"]] = relationship(
        "UserReward",
        back_populates="reward",
        cascade="all, delete-orphan"
    )
    badges: Mapped[List["Badge"]] = relationship(
        "Badge",
        back_populates="reward",
        cascade="all, delete-orphan"
    )


class UserReward(Base):
    """Recompensas obtenidas por usuarios.

    Registra cuándo y cómo un usuario obtuvo una recompensa.
    """
    __tablename__ = "user_rewards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("user_gamification.user_id")
    )
    reward_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("rewards.id")
    )
    obtained_at: Mapped[datetime] = mapped_column(DateTime)
    obtained_via: Mapped[str] = mapped_column(String(50))
    reference_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )

    # Relaciones
    user_gamification: Mapped["UserGamification"] = relationship(
        "UserGamification",
        back_populates="user_rewards",
        foreign_keys=[user_id]
    )
    reward: Mapped["Reward"] = relationship(
        "Reward",
        back_populates="user_rewards"
    )
    user_badges: Mapped[List["UserBadge"]] = relationship(
        "UserBadge",
        back_populates="user_reward",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index('ix_user_rewards_user_reward', 'user_id', 'reward_id'),
    )


class Badge(Base):
    """Tipo especial de recompensa: Badges (logros).

    Extiende Reward usando joined table inheritance.
    Almacena propiedades específicas de badges (icono, rareza).
    """
    __tablename__ = "badges"

    id: Mapped[int] = mapped_column(Integer, ForeignKey("rewards.id"), primary_key=True)
    icon: Mapped[str] = mapped_column(String(10))
    rarity: Mapped[str] = mapped_column(String(20))

    # Relaciones
    reward: Mapped["Reward"] = relationship(
        "Reward",
        back_populates="badges",
        foreign_keys=[id]
    )


class UserBadge(Base):
    """Badges específicos obtenidos por usuarios.

    Extiende UserReward para badges con propiedades adicionales.
    """
    __tablename__ = "user_badges"

    id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user_rewards.id"), primary_key=True
    )
    displayed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relaciones
    user_reward: Mapped["UserReward"] = relationship(
        "UserReward",
        back_populates="user_badges",
        foreign_keys=[id]
    )


class ConfigTemplate(Base):
    """Plantillas predefinidas para configuraciones comunes.

    Permite reutilizar configuraciones de misiones, recompensas, etc.
    """
    __tablename__ = "config_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(500))
    template_data: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50))
    created_by: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )


class GamificationConfig(Base):
    """Configuración global del módulo de gamificación.

    Singleton (id=1) que almacena parámetros globales del sistema.
    """
    __tablename__ = "gamification_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    besitos_per_reaction: Mapped[int] = mapped_column(Integer, default=1)
    max_besitos_per_day: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    streak_reset_hours: Mapped[int] = mapped_column(Integer, default=24)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )
