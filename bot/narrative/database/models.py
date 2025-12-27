"""
Modelos de base de datos para el módulo de narrativa.

Sistema de fragmentos narrativos con decisiones, requisitos y progreso de usuario.
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
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.database.base import Base
from bot.narrative.database.enums import ChapterType, RequirementType, ArchetypeType


class NarrativeChapter(Base):
    """
    Capítulo narrativo (contenedor de fragmentos).

    Un capítulo es un conjunto de fragmentos relacionados que forman
    una unidad narrativa (ej: "Los Kinkys", "El Diván").
    """

    __tablename__ = "narrative_chapters"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))  # "Los Kinkys"
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)  # "los-kinkys"
    chapter_type: Mapped[ChapterType] = mapped_column(default=ChapterType.FREE)
    order: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    fragments: Mapped[List["NarrativeFragment"]] = relationship(
        back_populates="chapter",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<NarrativeChapter(id={self.id}, name='{self.name}', slug='{self.slug}')>"


class NarrativeFragment(Base):
    """
    Fragmento narrativo (unidad mínima de historia).

    Un fragmento es una escena individual con contenido de Diana/Lucien,
    posibles decisiones del usuario, y requisitos para acceder.
    """

    __tablename__ = "narrative_fragments"

    id: Mapped[int] = mapped_column(primary_key=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("narrative_chapters.id"))

    # Identificación
    fragment_key: Mapped[str] = mapped_column(
        String(50), unique=True, index=True
    )  # "scene_1", "scene_2a"
    title: Mapped[str] = mapped_column(String(200))  # "Bienvenida de Diana"

    # Contenido
    speaker: Mapped[str] = mapped_column(String(50))  # "diana", "lucien", "narrator"
    content: Mapped[str] = mapped_column(Text)  # Texto narrativo con formato HTML
    visual_hint: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )  # Descripción imagen
    media_file_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # Telegram file_id

    # Navegación
    order: Mapped[int] = mapped_column(default=0)
    is_entry_point: Mapped[bool] = mapped_column(default=False)  # Inicio de capítulo
    is_ending: Mapped[bool] = mapped_column(default=False)  # Fin de capítulo

    # Estado
    is_active: Mapped[bool] = mapped_column(default=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    chapter: Mapped["NarrativeChapter"] = relationship(back_populates="fragments")
    decisions: Mapped[List["FragmentDecision"]] = relationship(
        back_populates="fragment",
        cascade="all, delete-orphan"
    )
    requirements: Mapped[List["FragmentRequirement"]] = relationship(
        back_populates="fragment",
        cascade="all, delete-orphan"
    )

    # Índices
    __table_args__ = (
        Index("idx_chapter_order", "chapter_id", "order"),
        Index("idx_entry_points", "chapter_id", "is_entry_point"),
    )

    def __repr__(self):
        return f"<NarrativeFragment(id={self.id}, key='{self.fragment_key}', speaker='{self.speaker}')>"


class FragmentDecision(Base):
    """
    Decisión/botón dentro de un fragmento.

    Representa una opción que el usuario puede elegir para avanzar
    en la narrativa.
    """

    __tablename__ = "fragment_decisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    fragment_id: Mapped[int] = mapped_column(ForeignKey("narrative_fragments.id"))

    # Botón
    button_text: Mapped[str] = mapped_column(String(100))  # "🚪 Descubrir más"
    button_emoji: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    order: Mapped[int] = mapped_column(default=0)

    # Destino
    target_fragment_key: Mapped[str] = mapped_column(String(50))  # "scene_2"

    # Costo opcional (en besitos)
    besitos_cost: Mapped[int] = mapped_column(default=0)

    # Efectos
    grants_besitos: Mapped[int] = mapped_column(default=0)
    affects_archetype: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # "impulsive"

    # Estado
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationship
    fragment: Mapped["NarrativeFragment"] = relationship(back_populates="decisions")

    # Índice
    __table_args__ = (Index("idx_fragment_order", "fragment_id", "order"),)

    def __repr__(self):
        return f"<FragmentDecision(id={self.id}, text='{self.button_text}', target='{self.target_fragment_key}')>"


class FragmentRequirement(Base):
    """
    Requisito para acceder a un fragmento.

    Define condiciones que el usuario debe cumplir para poder
    acceder a un fragmento específico.
    """

    __tablename__ = "fragment_requirements"

    id: Mapped[int] = mapped_column(primary_key=True)
    fragment_id: Mapped[int] = mapped_column(ForeignKey("narrative_fragments.id"))

    requirement_type: Mapped[RequirementType] = mapped_column()
    value: Mapped[str] = mapped_column(
        String(100)
    )  # "100" para besitos, "impulsive" para arquetipo

    # Mensaje si no cumple
    rejection_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationship
    fragment: Mapped["NarrativeFragment"] = relationship(back_populates="requirements")

    # Índice
    __table_args__ = (Index("idx_fragment_requirements", "fragment_id"),)

    def __repr__(self):
        return f"<FragmentRequirement(id={self.id}, type='{self.requirement_type.value}', value='{self.value}')>"


class UserNarrativeProgress(Base):
    """
    Progreso del usuario en la narrativa.

    Rastrea la posición actual del usuario, arquetipo detectado
    y estadísticas generales.
    """

    __tablename__ = "user_narrative_progress"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)

    # Posición actual
    current_chapter_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("narrative_chapters.id"), nullable=True
    )
    current_fragment_key: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )

    # Arquetipo detectado
    detected_archetype: Mapped[ArchetypeType] = mapped_column(
        default=ArchetypeType.UNKNOWN
    )
    archetype_confidence: Mapped[float] = mapped_column(default=0.0)  # 0.0 - 1.0

    # Estadísticas
    total_decisions: Mapped[int] = mapped_column(default=0)
    chapters_completed: Mapped[int] = mapped_column(default=0)

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    last_interaction: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Índice único por usuario
    __table_args__ = (Index("idx_user_narrative", "user_id", unique=True),)

    def __repr__(self):
        return f"<UserNarrativeProgress(user_id={self.user_id}, archetype='{self.detected_archetype.value}', decisions={self.total_decisions})>"


class UserDecisionHistory(Base):
    """
    Historial de decisiones del usuario.

    Registra cada decisión tomada por el usuario para análisis
    de arquetipos y tracking de progreso.
    """

    __tablename__ = "user_decision_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)

    # Qué decidió
    fragment_key: Mapped[str] = mapped_column(String(50))
    decision_id: Mapped[int] = mapped_column(ForeignKey("fragment_decisions.id"))

    # Cuándo
    decided_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Tiempo de respuesta (para arquetipo)
    response_time_seconds: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Índice
    __table_args__ = (Index("idx_user_decisions", "user_id", "fragment_key"),)

    def __repr__(self):
        return f"<UserDecisionHistory(user_id={self.user_id}, fragment='{self.fragment_key}', decided_at={self.decided_at})>"
