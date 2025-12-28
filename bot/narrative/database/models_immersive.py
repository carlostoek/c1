"""
Modelos adicionales para el sistema narrativo inmersivo.

Extiende el sistema base de narrativa con:
- Variantes de fragmentos por contexto
- Tracking de visitas y engagement
- Sistema de cooldowns
- Desafíos interactivos
- Ventanas de disponibilidad temporal
"""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    BigInteger,
    String,
    Text,
    Boolean,
    Integer,
    Float,
    ForeignKey,
    Index,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.database.base import Base
from bot.narrative.database.enums import (
    VariantConditionType,
    ChallengeType,
    CooldownType,
)


class FragmentVariant(Base):
    """
    Variante de contenido para un fragmento.

    Permite que un fragmento tenga múltiples versiones de su contenido
    dependiendo del contexto del usuario (primera visita, retorno,
    si tiene cierta pista, arquetipo, etc.).
    """

    __tablename__ = "fragment_variants"

    id: Mapped[int] = mapped_column(primary_key=True)
    fragment_key: Mapped[str] = mapped_column(
        String(50), ForeignKey("narrative_fragments.fragment_key"), index=True
    )

    # Identificación de la variante
    variant_key: Mapped[str] = mapped_column(String(50))  # "first_visit", "return_with_clue"
    priority: Mapped[int] = mapped_column(default=0)  # Mayor prioridad = evaluar primero

    # Condición para activar esta variante
    condition_type: Mapped[VariantConditionType] = mapped_column()
    condition_value: Mapped[str] = mapped_column(String(100))  # "2" para visit_count >= 2

    # Contenido alternativo (solo los campos que cambian)
    content_override: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    speaker_override: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    visual_hint_override: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    media_file_id_override: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Decisiones adicionales para esta variante (JSON array de decision objects)
    additional_decisions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Estado
    is_active: Mapped[bool] = mapped_column(default=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Índices
    __table_args__ = (
        Index("idx_variant_fragment_priority", "fragment_key", "priority"),
        Index("idx_variant_key", "fragment_key", "variant_key", unique=True),
    )

    def __repr__(self):
        return f"<FragmentVariant(fragment='{self.fragment_key}', variant='{self.variant_key}')>"


class UserFragmentVisit(Base):
    """
    Registro de visitas de usuario a fragmentos.

    Trackea cuántas veces un usuario visitó un fragmento,
    cuánto tiempo pasó en total, y cuándo fue la primera/última visita.
    """

    __tablename__ = "user_fragment_visits"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    fragment_key: Mapped[str] = mapped_column(String(50), index=True)

    # Estadísticas de visitas
    visit_count: Mapped[int] = mapped_column(default=1)
    first_visit: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    last_visit: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Tiempo de engagement (segundos acumulados leyendo el fragmento)
    total_time_seconds: Mapped[int] = mapped_column(default=0)

    # Timestamp de cuando se empezó a leer (para calcular tiempo)
    reading_started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Índices
    __table_args__ = (
        Index("idx_user_fragment_visit", "user_id", "fragment_key", unique=True),
    )

    def __repr__(self):
        return f"<UserFragmentVisit(user={self.user_id}, fragment='{self.fragment_key}', visits={self.visit_count})>"


class NarrativeCooldown(Base):
    """
    Cooldown activo para un usuario.

    Registra cooldowns temporales que impiden acceso a fragmentos,
    capítulos, o acciones específicas hasta que expire.
    """

    __tablename__ = "narrative_cooldowns"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)

    # Tipo y objetivo del cooldown
    cooldown_type: Mapped[CooldownType] = mapped_column()
    target_key: Mapped[str] = mapped_column(String(50))  # fragment_key, chapter_slug, etc.

    # Tiempos
    started_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column()

    # Mensaje narrativo a mostrar mientras está activo
    narrative_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Índices
    __table_args__ = (
        Index("idx_cooldown_user_type", "user_id", "cooldown_type", "target_key"),
        Index("idx_cooldown_expires", "user_id", "expires_at"),
    )

    @property
    def is_expired(self) -> bool:
        """Verifica si el cooldown ya expiró."""
        return datetime.utcnow() > self.expires_at

    @property
    def remaining_seconds(self) -> int:
        """Segundos restantes del cooldown."""
        if self.is_expired:
            return 0
        delta = self.expires_at - datetime.utcnow()
        return int(delta.total_seconds())

    def __repr__(self):
        return f"<NarrativeCooldown(user={self.user_id}, type='{self.cooldown_type.value}', target='{self.target_key}')>"


class FragmentChallenge(Base):
    """
    Desafío/acertijo asociado a un fragmento.

    Define un reto que el usuario debe superar para continuar,
    como escribir una respuesta, recordar un dato, o actuar rápido.
    """

    __tablename__ = "fragment_challenges"

    id: Mapped[int] = mapped_column(primary_key=True)
    fragment_key: Mapped[str] = mapped_column(
        String(50), ForeignKey("narrative_fragments.fragment_key"), index=True
    )

    # Tipo de desafío
    challenge_type: Mapped[ChallengeType] = mapped_column()

    # Pregunta/instrucción del desafío
    question: Mapped[str] = mapped_column(Text)
    question_image_file_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Respuestas correctas (JSON array para múltiples respuestas válidas)
    correct_answers: Mapped[list] = mapped_column(JSON)  # ["7", "siete", "seven"]

    # Pistas progresivas (JSON array ordenado por dificultad)
    hints: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Configuración
    attempts_allowed: Mapped[int] = mapped_column(default=3)  # 0 = infinitos
    timeout_seconds: Mapped[Optional[int]] = mapped_column(nullable=True)  # Para timed

    # Qué pasa si falla
    failure_redirect_key: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    failure_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Qué pasa si tiene éxito
    success_redirect_key: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Recompensa por éxito
    success_clue_slug: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Item slug
    success_besitos: Mapped[int] = mapped_column(default=0)
    success_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Estado
    is_active: Mapped[bool] = mapped_column(default=True)

    def __repr__(self):
        return f"<FragmentChallenge(fragment='{self.fragment_key}', type='{self.challenge_type.value}')>"


class UserChallengeAttempt(Base):
    """
    Intento de desafío por un usuario.

    Registra cada intento del usuario en un desafío,
    incluyendo si tuvo éxito y cuántas pistas usó.
    """

    __tablename__ = "user_challenge_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    challenge_id: Mapped[int] = mapped_column(
        ForeignKey("fragment_challenges.id"), index=True
    )

    # Resultado
    attempt_number: Mapped[int] = mapped_column(default=1)
    answer_given: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_correct: Mapped[bool] = mapped_column(default=False)
    hints_used: Mapped[int] = mapped_column(default=0)

    # Tiempo
    attempted_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    response_time_seconds: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Índices
    __table_args__ = (
        Index("idx_challenge_attempts", "user_id", "challenge_id"),
    )

    def __repr__(self):
        return f"<UserChallengeAttempt(user={self.user_id}, challenge={self.challenge_id}, correct={self.is_correct})>"


class FragmentTimeWindow(Base):
    """
    Ventana de disponibilidad temporal para un fragmento.

    Define cuándo un fragmento está disponible (horarios,
    días de la semana, fechas especiales).
    """

    __tablename__ = "fragment_time_windows"

    id: Mapped[int] = mapped_column(primary_key=True)
    fragment_key: Mapped[str] = mapped_column(
        String(50), ForeignKey("narrative_fragments.fragment_key"), index=True
    )

    # Horas disponibles (JSON array: [20, 21, 22, 23] = 8PM-12AM)
    available_hours: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Días de la semana (JSON array: [0, 1, 2, 3, 4, 5, 6] = Lun-Dom)
    available_days: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Fechas especiales (JSON array: ["2024-02-14", "2024-12-25"])
    special_dates: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Si special_dates está definido, ¿es inclusivo (solo esas fechas) o exclusivo (no esas fechas)?
    special_dates_inclusive: Mapped[bool] = mapped_column(default=True)

    # Mensaje cuando no está disponible
    unavailable_message: Mapped[str] = mapped_column(
        Text,
        default="Este momento de la historia solo está disponible en ciertos horarios..."
    )

    # Estado
    is_active: Mapped[bool] = mapped_column(default=True)

    def __repr__(self):
        return f"<FragmentTimeWindow(fragment='{self.fragment_key}')>"


class ChapterCompletion(Base):
    """
    Registro de capítulos completados por usuario.

    Permite saber qué capítulos ha completado un usuario
    y cuándo los completó.
    """

    __tablename__ = "chapter_completions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    chapter_slug: Mapped[str] = mapped_column(String(50), index=True)

    # Cuándo lo completó
    completed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Estadísticas del recorrido
    fragments_visited: Mapped[int] = mapped_column(default=0)
    decisions_made: Mapped[int] = mapped_column(default=0)
    total_time_seconds: Mapped[int] = mapped_column(default=0)
    clues_found: Mapped[int] = mapped_column(default=0)

    # Arquetipo predominante durante el capítulo
    chapter_archetype: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Índices
    __table_args__ = (
        Index("idx_chapter_completion", "user_id", "chapter_slug", unique=True),
    )

    def __repr__(self):
        return f"<ChapterCompletion(user={self.user_id}, chapter='{self.chapter_slug}')>"


class DailyNarrativeLimit(Base):
    """
    Límites diarios de narrativa por usuario.

    Controla cuántos fragmentos/decisiones puede hacer un usuario
    por día para forzar engagement prolongado.
    """

    __tablename__ = "daily_narrative_limits"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)

    # Fecha del límite actual
    limit_date: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Contadores del día
    fragments_viewed: Mapped[int] = mapped_column(default=0)
    decisions_made: Mapped[int] = mapped_column(default=0)
    challenges_attempted: Mapped[int] = mapped_column(default=0)

    # Límites configurables por usuario (None = usar default global)
    max_fragments_per_day: Mapped[Optional[int]] = mapped_column(nullable=True)
    max_decisions_per_day: Mapped[Optional[int]] = mapped_column(nullable=True)

    def __repr__(self):
        return f"<DailyNarrativeLimit(user={self.user_id}, fragments={self.fragments_viewed})>"
