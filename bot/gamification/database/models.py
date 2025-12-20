"""
Database models for the gamification module.

This module contains all SQLAlchemy models for the gamification system,
including user profiles, reactions, missions, rewards, and configurations.
"""

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import (
    BigInteger, String, DateTime, Boolean, ForeignKey, Integer, Float,
    Index, UniqueConstraint, CheckConstraint
)
from datetime import datetime, UTC
from typing import Optional, List


# Using the same base as the main application
from bot.database.models import Base


class UserGamification(Base):
    """
    Perfil de gamificación del usuario.

    Almacena balance de besitos, nivel actual y relaciones
    con misiones/recompensas.
    """
    __tablename__ = "user_gamification"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"), primary_key=True)
    total_besitos: Mapped[int] = mapped_column(Integer, default=0)
    besitos_earned: Mapped[int] = mapped_column(Integer, default=0)
    besitos_spent: Mapped[int] = mapped_column(Integer, default=0)
    current_level_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("levels.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    user = relationship("bot.database.models.User", primaryjoin="UserGamification.user_id == bot.database.models.User.user_id", lazy="select")
    current_level: Mapped[Optional["Level"]] = relationship(
        "Level",
        foreign_keys=[current_level_id],
        back_populates="users"
    )
    user_streak: Mapped[Optional["UserStreak"]] = relationship(
        "UserStreak",
        back_populates="user_gamification",
        uselist=False
    )
    missions: Mapped[List["UserMission"]] = relationship(
        "UserMission",
        back_populates="user_gamification"
    )
    rewards: Mapped[List["UserReward"]] = relationship(
        "UserReward",
        back_populates="user_gamification"
    )
    reactions: Mapped[List["UserReaction"]] = relationship(
        "UserReaction",
        back_populates="user_gamification"
    )
    transactions: Mapped[List["BesitoTransaction"]] = relationship(
        "BesitoTransaction",
        back_populates="user_gamification"
    )

    # Indexes
    __table_args__ = (
        Index('ix_user_gamification_total_besitos', 'total_besitos'),
    )


class Reaction(Base):
    """
    Catálogo de reacciones configuradas (emojis).

    Define qué emojis están disponibles para reaccionar
    y cuántos besitos otorgan.
    """
    __tablename__ = "reactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    emoji: Mapped[str] = mapped_column(String(10), unique=True)
    besitos_value: Mapped[int] = mapped_column(Integer, default=1)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    # Relationships
    user_reactions: Mapped[List["UserReaction"]] = relationship(
        "UserReaction",
        back_populates="reaction"
    )

    # Indexes
    __table_args__ = (
        Index('ix_reactions_emoji', 'emoji'),
    )


class UserReaction(Base):
    """
    Registro de cada reacción que hace un usuario.

    Almacena información sobre cada reacción realizada
    por un usuario en un mensaje de un canal específico.
    """
    __tablename__ = "user_reactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user_gamification.user_id"))
    reaction_id: Mapped[int] = mapped_column(Integer, ForeignKey("reactions.id"))
    channel_id: Mapped[int] = mapped_column(BigInteger)
    message_id: Mapped[int] = mapped_column(BigInteger)
    reacted_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    # Relationships
    user_gamification: Mapped["UserGamification"] = relationship(
        "UserGamification",
        back_populates="reactions"
    )
    reaction: Mapped["Reaction"] = relationship(
        "Reaction",
        back_populates="user_reactions"
    )

    # Indexes
    __table_args__ = (
        Index('ix_user_reactions_user_reacted_at', 'user_id', 'reacted_at'),
        Index('ix_user_reactions_user_channel', 'user_id', 'channel_id'),
    )


class UserStreak(Base):
    """
    Rachas de reacciones consecutivas por usuario.

    Mantiene el historial de días seguidos reaccionando
    y la racha más larga conseguida por cada usuario.
    """
    __tablename__ = "user_streaks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user_gamification.user_id"), unique=True)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_reaction_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    user_gamification: Mapped["UserGamification"] = relationship(
        "UserGamification",
        back_populates="user_streak"
    )

    # Indexes
    __table_args__ = (
        Index('ix_user_streaks_user_id', 'user_id'),
    )


class Level(Base):
    """
    Niveles disponibles en el sistema.

    Define los diferentes niveles que un usuario puede alcanzar
    basados en sus besitos acumulados.
    """
    __tablename__ = "levels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    min_besitos: Mapped[int] = mapped_column(Integer)
    order: Mapped[int] = mapped_column(Integer)
    benefits: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # JSON string
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    # Relationships
    users: Mapped[List["UserGamification"]] = relationship(
        "UserGamification",
        back_populates="current_level"
    )
    missions: Mapped[List["Mission"]] = relationship(
        "Mission",
        back_populates="auto_level_up"
    )

    # Indexes
    __table_args__ = (
        Index('ix_levels_min_besitos', 'min_besitos'),
        Index('ix_levels_order', 'order'),
    )


class Mission(Base):
    """
    Misiones configuradas por admins.

    Define objetivos que los usuarios pueden completar
    para obtener besitos y recompensas.
    """
    __tablename__ = "missions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(500))
    mission_type: Mapped[str] = mapped_column(String(50))  # "one_time", "daily", "weekly", "streak"
    criteria: Mapped[str] = mapped_column(String(1000))  # JSON string
    besitos_reward: Mapped[int] = mapped_column(Integer)
    auto_level_up_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("levels.id"), nullable=True)
    unlock_rewards: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # JSON array string
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    repeatable: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    # Relationships
    auto_level_up: Mapped[Optional["Level"]] = relationship(
        "Level",
        back_populates="missions"
    )
    user_missions: Mapped[List["UserMission"]] = relationship(
        "UserMission",
        back_populates="mission"
    )

    # Indexes
    __table_args__ = (
        Index('ix_missions_active', 'active'),
        Index('ix_missions_created_by', 'created_by'),
    )


class UserMission(Base):
    """
    Progreso de cada usuario en misiones.

    Registra el estado actual de las misiones
    en las que está participando cada usuario.
    """
    __tablename__ = "user_missions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user_gamification.user_id"))
    mission_id: Mapped[int] = mapped_column(Integer, ForeignKey("missions.id"))
    progress: Mapped[str] = mapped_column(String(500))  # JSON string with progress data
    status: Mapped[str] = mapped_column(String(20))  # "in_progress", "completed", "claimed"
    started_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    claimed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user_gamification: Mapped["UserGamification"] = relationship(
        "UserGamification",
        back_populates="missions"
    )
    mission: Mapped["Mission"] = relationship(
        "Mission",
        back_populates="user_missions"
    )

    # Indexes
    __table_args__ = (
        Index('ix_user_missions_user_status', 'user_id', 'status'),
        UniqueConstraint('user_id', 'mission_id', name='uc_user_mission'),
    )


class Reward(Base):
    """
    Recompensas disponibles en el sistema.

    Define los premios que los usuarios pueden obtener
    por completar misiones o gastar besitos.
    """
    __tablename__ = "rewards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(500))
    reward_type: Mapped[str] = mapped_column(String(50))  # "badge", "item", "permission"
    cost_besitos: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    unlock_conditions: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)  # JSON string
    reward_metadata: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)  # JSON string
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    # Relationships
    user_rewards: Mapped[List["UserReward"]] = relationship(
        "UserReward",
        back_populates="reward"
    )
    badge: Mapped[Optional["Badge"]] = relationship("Badge", back_populates="reward", uselist=False)

    # Indexes
    __table_args__ = (
        Index('ix_rewards_active', 'active'),
        Index('ix_rewards_reward_type', 'reward_type'),
    )


class UserReward(Base):
    """
    Recompensas obtenidas por usuarios.

    Registra qué recompensas específicas ha obtenido
    cada usuario y cómo las obtuvo.
    """
    __tablename__ = "user_rewards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user_gamification.user_id"))
    reward_id: Mapped[int] = mapped_column(Integer, ForeignKey("rewards.id"))
    obtained_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    obtained_via: Mapped[str] = mapped_column(String(50))  # "mission", "purchase", "admin_grant"
    reference_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # ID of related mission/transaction

    # Relationships
    user_gamification: Mapped["UserGamification"] = relationship(
        "UserGamification",
        back_populates="rewards"
    )
    reward: Mapped["Reward"] = relationship(
        "Reward",
        back_populates="user_rewards"
    )
    user_badge: Mapped[Optional["UserBadge"]] = relationship("UserBadge", back_populates="user_reward", uselist=False)

    # Indexes
    __table_args__ = (
        UniqueConstraint('user_id', 'reward_id', name='uc_user_reward'),
        Index('ix_user_rewards_user_id', 'user_id'),
        Index('ix_user_rewards_obtained_via', 'obtained_via'),
    )


class Badge(Base):
    """
    Tipo especial de recompensa (badges/logros).

    Extensión de Reward con características específicas
    para insignias y logros.
    """
    __tablename__ = "badges"

    id: Mapped[int] = mapped_column(Integer, ForeignKey("rewards.id"), primary_key=True)  # FK to rewards.id
    icon: Mapped[str] = mapped_column(String(10))  # Emoji del badge
    rarity: Mapped[str] = mapped_column(String(20))  # "common", "rare", "epic", "legendary"

    # Relationships
    reward: Mapped["Reward"] = relationship("Reward", back_populates="badge")

    # Indexes
    __table_args__ = (
        Index('ix_badges_rarity', 'rarity'),
    )


class UserBadge(Base):
    """
    Badges específicos obtenidos por usuarios.

    Especialización de UserReward para el caso de badges,
    con opciones adicionales de visualización.
    """
    __tablename__ = "user_badges"

    id: Mapped[int] = mapped_column(Integer, ForeignKey("user_rewards.id"), primary_key=True)  # FK to user_rewards.id
    displayed: Mapped[bool] = mapped_column(Boolean, default=False)  # Si se muestra en perfil

    # Relationships
    user_reward: Mapped["UserReward"] = relationship("UserReward", back_populates="user_badge")

    # Indexes
    __table_args__ = (
        Index('ix_user_badges_displayed', 'displayed'),
    )


class ConfigTemplate(Base):
    """
    Plantillas predefinidas para configuraciones comunes.

    Almacena configuraciones recurrentes para misiones,
    recompensas o sistemas de nivel que pueden reutilizarse.
    """
    __tablename__ = "config_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(500))
    template_data: Mapped[str] = mapped_column(String(5000))  # JSON string with full configuration
    category: Mapped[str] = mapped_column(String(50))  # "mission", "reward", "level_progression"
    created_by: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    # Indexes
    __table_args__ = (
        Index('ix_config_templates_category', 'category'),
        Index('ix_config_templates_created_by', 'created_by'),
    )


class BesitoTransaction(Base):
    """
    Registro de transacciones de besitos.

    Almacena todas las operaciones de besitos (otorgamientos, gastos, etc.)
    para auditoría y seguimiento.
    """
    __tablename__ = "besito_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user_gamification.user_id"))
    amount: Mapped[int] = mapped_column(Integer)  # Puede ser negativo para gastos
    transaction_type: Mapped[str] = mapped_column(String(50))  # TransactionType enum
    description: Mapped[str] = mapped_column(String(500))
    reference_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # ID de origen (mission_id, reward_id, etc)
    balance_after: Mapped[int] = mapped_column(Integer)  # Balance después de esta transacción
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    # Relationships
    user_gamification: Mapped["UserGamification"] = relationship(
        "UserGamification",
        back_populates="transactions"
    )

    # Indexes
    __table_args__ = (
        Index('ix_besito_transactions_user_created', 'user_id', 'created_at'),
        Index('ix_besito_transactions_user_type', 'user_id', 'transaction_type'),
        Index('ix_besito_transactions_ref_type', 'reference_id', 'transaction_type'),
        Index('ix_besito_transactions_created_at', 'created_at'),
    )


class GamificationConfig(Base):
    """
    Configuración global del módulo.

    Singleton que almacena los parámetros de configuración
    globales para el sistema de gamificación.
    """
    __tablename__ = "gamification_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)  # Single row (singleton)
    besitos_per_reaction: Mapped[int] = mapped_column(Integer, default=1)
    max_besitos_per_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Daily limit (anti-spam)
    streak_reset_hours: Mapped[int] = mapped_column(Integer, default=24)  # Hours to break streak
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Constraints
    __table_args__ = (
        CheckConstraint(besitos_per_reaction >= 0, name='ck_besitos_positive'),
        CheckConstraint(streak_reset_hours > 0, name='ck_streak_reset_positive'),
    )