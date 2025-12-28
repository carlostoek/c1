"""
Modelos de base de datos para el sistema de onboarding narrativo.

El onboarding introduce a los usuarios al sistema de narrativa de forma gradual,
detectando su arquetipo y otorgando recompensas iniciales.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, String, Boolean, Integer, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from bot.database.base import Base


class UserOnboardingProgress(Base):
    """
    Tracking del progreso de onboarding de un usuario.

    El onboarding es un flujo de 5 pasos obligatorio que introduce
    al usuario al sistema narrativo después de ser aprobado en el canal Free.

    Attributes:
        user_id: ID único de Telegram (Primary Key)
        started: Si el usuario inició el onboarding
        completed: Si el usuario completó el onboarding
        current_step: Paso actual (0-5, donde 0 = no iniciado)
        archetype_scores: Puntuaciones por arquetipo (IMPULSIVE, CONTEMPLATIVE, SILENT)
        decisions_made: Lista de decisiones tomadas durante onboarding (JSON)
        besitos_granted: Cantidad de besitos otorgados como bienvenida
        started_at: Fecha/hora de inicio del onboarding
        completed_at: Fecha/hora de completación
        created_at: Fecha de creación del registro
    """

    __tablename__ = "user_onboarding_progress"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # Estado del onboarding
    started: Mapped[bool] = mapped_column(Boolean, default=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    current_step: Mapped[int] = mapped_column(Integer, default=0)

    # Detección de arquetipo durante onboarding
    archetype_scores: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON: {"IMPULSIVE": 5, "CONTEMPLATIVE": 0, "SILENT": 0}

    # Decisiones tomadas (para análisis y personalización)
    decisions_made: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON: [{"step": 1, "choice": 0, "archetype": "IMPULSIVE"}, ...]

    # Recompensas otorgadas
    besitos_granted: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    def __repr__(self) -> str:
        status = "completed" if self.completed else f"step {self.current_step}"
        return f"<UserOnboardingProgress(user_id={self.user_id}, status={status})>"

    @property
    def is_pending(self) -> bool:
        """Verifica si el onboarding está pendiente (iniciado pero no completado)."""
        return self.started and not self.completed

    @property
    def progress_percent(self) -> int:
        """Calcula el porcentaje de progreso (0-100)."""
        if self.completed:
            return 100
        return int((self.current_step / 5) * 100)


class OnboardingFragment(Base):
    """
    Fragmento de contenido para el onboarding.

    Cada fragmento representa un paso del onboarding con su contenido,
    speaker, y opciones de decisión.

    Attributes:
        id: ID único del fragmento
        step: Número de paso (1-5)
        speaker: Quién habla (diana, lucien, narrator)
        content: Contenido HTML del fragmento
        decisions: Opciones de decisión como JSON array
        is_active: Si el fragmento está activo
    """

    __tablename__ = "onboarding_fragments"

    id: Mapped[int] = mapped_column(primary_key=True)
    step: Mapped[int] = mapped_column(Integer, unique=True, index=True)

    # Contenido
    speaker: Mapped[str] = mapped_column(String(50), default="diana")
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)

    # Decisiones como JSON array
    # Format: [{"text": "opción", "archetype_hint": "IMPULSIVE"}, ...]
    decisions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Estado
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<OnboardingFragment(step={self.step}, title='{self.title}')>"
