"""Modelos de base de datos para el módulo de gamificación.

Define 13 modelos SQLAlchemy 2.0 que representan la estructura
de datos para el sistema de gamificación del bot.
"""

from typing import Optional, List
from datetime import datetime, UTC

from sqlalchemy import (
    BigInteger, String, Integer, Boolean, DateTime, ForeignKey, Index, Text, Float
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
    total_besitos: Mapped[float] = mapped_column(Float, default=0.0)
    besitos_earned: Mapped[float] = mapped_column(Float, default=0.0)
    besitos_spent: Mapped[float] = mapped_column(Float, default=0.0)
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
    Incluye campos de UI para botones de reacción personalizados.
    """
    __tablename__ = "reactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    emoji: Mapped[str] = mapped_column(String(10), unique=True)
    name: Mapped[str] = mapped_column(String(50))
    besitos_value: Mapped[int] = mapped_column(Integer, default=1)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )

    # Campos de UI para botones personalizados
    button_emoji: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True
    )
    button_label: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

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
    progress: Mapped[float] = mapped_column(Float, default=0.0)
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
    Incluye configuración de economía de Favores.
    """
    __tablename__ = "gamification_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    besitos_per_reaction: Mapped[int] = mapped_column(Integer, default=1)
    max_besitos_per_day: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    streak_reset_hours: Mapped[int] = mapped_column(Integer, default=24)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Configuración de regalo diario
    daily_gift_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    daily_gift_besitos: Mapped[int] = mapped_column(Integer, default=10)

    # ============================================================
    # ECONOMÍA DE FAVORES (Valores configurables)
    # ============================================================
    # Valores por defecto alineados con FAVOR_REWARDS en formatters.py

    # Reacciones a publicaciones
    earn_reaction_base: Mapped[float] = mapped_column(Float, default=0.1)
    earn_first_reaction_day: Mapped[float] = mapped_column(Float, default=0.5)
    limit_reactions_per_day: Mapped[int] = mapped_column(Integer, default=10)

    # Misiones
    earn_mission_daily: Mapped[float] = mapped_column(Float, default=1.0)
    earn_mission_weekly: Mapped[float] = mapped_column(Float, default=3.0)
    earn_level_evaluation: Mapped[float] = mapped_column(Float, default=5.0)

    # Rachas
    earn_streak_7_days: Mapped[float] = mapped_column(Float, default=2.0)
    earn_streak_30_days: Mapped[float] = mapped_column(Float, default=10.0)

    # Easter eggs
    earn_easter_egg_min: Mapped[float] = mapped_column(Float, default=2.0)
    earn_easter_egg_max: Mapped[float] = mapped_column(Float, default=5.0)

    # Referidos
    earn_referral_active: Mapped[float] = mapped_column(Float, default=5.0)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )


class CustomReaction(Base):
    """Registro de reacciones personalizadas en mensajes de broadcasting.

    Almacena cada vez que un usuario presiona un botón de reacción
    en un mensaje de broadcasting con gamificación habilitada.

    Attributes:
        id: ID único del registro
        broadcast_message_id: ID del mensaje de broadcasting
        user_id: ID del usuario que reaccionó
        reaction_type_id: ID del tipo de reacción (Reaction)
        emoji: Emoji de la reacción
        besitos_earned: Cantidad de besitos ganados con esta reacción
        created_at: Timestamp de cuando se realizó la reacción

    Relaciones:
        user: Usuario que reaccionó (via users table)
        reaction_type: Tipo de reacción seleccionada
    """
    __tablename__ = "custom_reactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    broadcast_message_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("broadcast_messages.id"),
        nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id"),
        nullable=False
    )
    reaction_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("reactions.id"),
        nullable=False
    )
    emoji: Mapped[str] = mapped_column(String(10), nullable=False)
    besitos_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False
    )

    # Relaciones
    reaction_type: Mapped["Reaction"] = relationship(
        "Reaction",
        foreign_keys=[reaction_type_id]
    )

    # Índices para optimización
    __table_args__ = (
        Index(
            'idx_unique_reaction',
            'broadcast_message_id', 'user_id', 'reaction_type_id',
            unique=True
        ),
        Index('idx_user_created', 'user_id', 'created_at'),
        Index('idx_broadcast_message', 'broadcast_message_id'),
    )


class BesitoTransaction(Base):
    """Registro de auditoría de transacciones de besitos.

    Registra TODA operación de besitos para trazabilidad completa.
    Incluye balance_after para detectar inconsistencias.

    Attributes:
        id: ID único de la transacción
        user_id: ID del usuario que realizó la transacción
        amount: Cantidad de besitos (positivo=ganancia, negativo=gasto)
        transaction_type: Tipo de transacción (TransactionType enum)
        description: Descripción de la transacción
        reference_id: ID del origen (UserReaction.id, UserMission.id, etc)
        balance_after: Balance del usuario después de esta transacción
        created_at: Timestamp de la transacción (UTC)

    Relaciones:
        user: Usuario que realizó la transacción (via users table)

    Índices:
        - (user_id, created_at DESC): Para historial de usuario
        - (user_id, transaction_type): Para filtros por tipo
        - (reference_id, transaction_type): Para rastrear origen
    """
    __tablename__ = "besito_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    reference_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    balance_after: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False
    )

    # Índices compuestos para optimización
    __table_args__ = (
        Index('idx_user_transactions_history', 'user_id', 'created_at'),
        Index('idx_user_transaction_type', 'user_id', 'transaction_type'),
        Index('idx_reference_transaction', 'reference_id', 'transaction_type'),
    )


class DailyGiftClaim(Base):
    """Registro de reclamaciones de regalo diario.

    Trackea cuando cada usuario reclama su regalo diario,
    manteniendo la racha de días consecutivos.

    Attributes:
        user_id: ID del usuario (PK, 1-to-1 con users)
        last_claim_date: Última fecha de reclamación (solo fecha, sin hora)
        current_streak: Racha actual de días consecutivos
        longest_streak: Récord histórico de racha más larga
        total_claims: Total de regalos reclamados desde el inicio
        created_at: Fecha de creación del registro
        updated_at: Fecha de última actualización

    Relaciones:
        user: Usuario del sistema core (via users table)
    """
    __tablename__ = "daily_gift_claims"

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True
    )
    last_claim_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    total_claims: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False
    )

    # Índices para optimización
    __table_args__ = (
        Index('idx_daily_gift_last_claim', 'last_claim_date'),
        Index('idx_daily_gift_streak', 'current_streak'),
    )


class UserBehaviorSignals(Base):
    """Señales de comportamiento del usuario para detección de arquetipos.

    Almacena métricas derivadas de las interacciones del usuario que
    son utilizadas por el algoritmo de clasificación de arquetipos.
    Lucien observa estas señales para entender el comportamiento.

    Categorías de métricas:
        - Exploración: Curiosidad, cobertura de contenido
        - Velocidad/Directness: Eficiencia, rapidez de decisión
        - Emocionales: Conexión, expresividad
        - Análisis: Precisión, estructuración
        - Persistencia: Tenacidad, retornos
        - Paciencia: Constancia, calma

    Attributes:
        user_id: ID del usuario (PK, 1-to-1 con users)

        # Métricas de exploración (EXPLORER)
        content_sections_visited: Secciones únicas visitadas
        content_completion_rate: % de contenido disponible visto (0.0-1.0)
        easter_eggs_found: Easter eggs encontrados
        avg_time_on_content: Segundos promedio en contenido
        revisits_old_content: Veces que revisó contenido antiguo

        # Métricas de velocidad/directness (DIRECT)
        avg_response_time: Segundos promedio para responder
        avg_response_length: Palabras promedio por respuesta
        button_vs_text_ratio: % de interacciones via botón vs texto (0.0-1.0)
        avg_decision_time: Segundos para tomar decisiones
        actions_per_session: Acciones promedio por sesión

        # Métricas emocionales (ROMANTIC)
        emotional_words_count: Veces que usó palabras emocionales
        question_count: Preguntas hechas al bot
        long_responses_count: Respuestas >50 palabras
        personal_questions_about_diana: Preguntas sobre Diana como persona

        # Métricas de análisis (ANALYTICAL)
        quiz_avg_score: Promedio en evaluaciones (0.0-100.0)
        structured_responses: Respuestas con estructura (listas, puntos)
        error_reports: Veces que reportó errores/inconsistencias

        # Métricas de persistencia (PERSISTENT)
        return_after_inactivity: Veces que volvió después de 3+ días
        retry_failed_actions: Reintentos de acciones fallidas
        incomplete_flows_completed: Flujos abandonados y luego completados

        # Métricas de paciencia (PATIENT)
        skip_actions_used: Veces que usó "saltar" o similar
        current_streak: Racha actual (vinculado a F2.3)
        best_streak: Mejor racha histórica
        avg_session_duration: Duración promedio de sesión en segundos

        # Metadata
        total_interactions: Total de interacciones registradas
        first_interaction_at: Primera interacción
        last_updated_at: Última actualización de métricas
    """
    __tablename__ = "user_behavior_signals"

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True
    )

    # ========================================
    # MÉTRICAS DE EXPLORACIÓN (EXPLORER)
    # ========================================
    content_sections_visited: Mapped[int] = mapped_column(Integer, default=0)
    content_completion_rate: Mapped[float] = mapped_column(Float, default=0.0)
    easter_eggs_found: Mapped[int] = mapped_column(Integer, default=0)
    avg_time_on_content: Mapped[float] = mapped_column(Float, default=0.0)
    revisits_old_content: Mapped[int] = mapped_column(Integer, default=0)

    # ========================================
    # MÉTRICAS DE VELOCIDAD/DIRECTNESS (DIRECT)
    # ========================================
    avg_response_time: Mapped[float] = mapped_column(Float, default=0.0)
    avg_response_length: Mapped[float] = mapped_column(Float, default=0.0)
    button_vs_text_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    avg_decision_time: Mapped[float] = mapped_column(Float, default=0.0)
    actions_per_session: Mapped[float] = mapped_column(Float, default=0.0)

    # ========================================
    # MÉTRICAS EMOCIONALES (ROMANTIC)
    # ========================================
    emotional_words_count: Mapped[int] = mapped_column(Integer, default=0)
    question_count: Mapped[int] = mapped_column(Integer, default=0)
    long_responses_count: Mapped[int] = mapped_column(Integer, default=0)
    personal_questions_about_diana: Mapped[int] = mapped_column(Integer, default=0)

    # ========================================
    # MÉTRICAS DE ANÁLISIS (ANALYTICAL)
    # ========================================
    quiz_avg_score: Mapped[float] = mapped_column(Float, default=0.0)
    structured_responses: Mapped[int] = mapped_column(Integer, default=0)
    error_reports: Mapped[int] = mapped_column(Integer, default=0)

    # ========================================
    # MÉTRICAS DE PERSISTENCIA (PERSISTENT)
    # ========================================
    return_after_inactivity: Mapped[int] = mapped_column(Integer, default=0)
    retry_failed_actions: Mapped[int] = mapped_column(Integer, default=0)
    incomplete_flows_completed: Mapped[int] = mapped_column(Integer, default=0)

    # ========================================
    # MÉTRICAS DE PACIENCIA (PATIENT)
    # ========================================
    skip_actions_used: Mapped[int] = mapped_column(Integer, default=0)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    best_streak: Mapped[int] = mapped_column(Integer, default=0)
    avg_session_duration: Mapped[float] = mapped_column(Float, default=0.0)

    # ========================================
    # METADATA
    # ========================================
    total_interactions: Mapped[int] = mapped_column(Integer, default=0)
    first_interaction_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False
    )

    # Índices para optimización
    __table_args__ = (
        Index('idx_behavior_total_interactions', 'total_interactions'),
        Index('idx_behavior_last_updated', 'last_updated_at'),
    )


class BehaviorInteraction(Base):
    """Registro individual de interacción para tracking de comportamiento.

    Almacena cada interacción del usuario con datos específicos
    para análisis posterior y cálculo de métricas.

    Attributes:
        id: ID único de la interacción
        user_id: ID del usuario
        interaction_type: Tipo de interacción (InteractionType enum)
        interaction_data: JSON con datos específicos del tipo de interacción
        created_at: Timestamp de la interacción

    Interaction data por tipo de interacción:
        BUTTON_CLICK:
            button_id: str, context: str, time_to_click: float

        TEXT_RESPONSE:
            word_count: int, has_emotional_words: bool, has_questions: bool,
            is_structured: bool, response_time: float

        CONTENT_VIEW:
            content_id: str, content_type: str, time_spent: float,
            is_revisit: bool, completion: float

        QUIZ_ANSWER:
            quiz_id: str, question_id: str, is_correct: bool,
            time_to_answer: float

        DECISION_MADE:
            fragment_id: str, decision_id: str, time_to_decide: float,
            options_available: int
    """
    __tablename__ = "behavior_interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    interaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    interaction_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False
    )

    # Índices para optimización
    __table_args__ = (
        Index('idx_behavior_user_type', 'user_id', 'interaction_type'),
        Index('idx_behavior_user_created', 'user_id', 'created_at'),
        Index('idx_behavior_type_created', 'interaction_type', 'created_at'),
    )
