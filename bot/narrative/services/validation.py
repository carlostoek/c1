"""
Servicio de validación de integridad narrativa.

Detecta problemas en la estructura narrativa:
- Dead ends: Fragmentos sin decisiones no marcados como ending
- Broken references: Decisiones con target_fragment_key inexistente
- Unreachable: Fragmentos sin camino de acceso
- Missing entry: Capítulos sin entry_point
"""
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Set

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.narrative.database import (
    NarrativeChapter,
    NarrativeFragment,
    FragmentDecision,
)

logger = logging.getLogger(__name__)


class ValidationIssueType(str, Enum):
    """Tipo de problema de validación."""
    DEAD_END = "dead_end"              # Fragmento sin decisiones ni ending
    BROKEN_REFERENCE = "broken_ref"    # target_fragment_key no existe
    UNREACHABLE = "unreachable"        # Fragmento sin camino de acceso
    MISSING_ENTRY = "missing_entry"    # Capítulo sin entry_point


class IssueSeverity(str, Enum):
    """Severidad del problema."""
    ERROR = "error"
    WARNING = "warning"


@dataclass
class ValidationIssue:
    """Problema de validación encontrado."""
    issue_type: ValidationIssueType
    severity: IssueSeverity
    chapter_id: int
    chapter_name: str
    fragment_key: str
    detail: str
    decision_id: int = None  # Solo para broken_reference


@dataclass
class ValidationResult:
    """Resultado de validación."""
    is_valid: bool
    total_issues: int
    errors: int
    warnings: int
    issues: List[ValidationIssue] = field(default_factory=list)


class NarrativeValidationService:
    """Servicio de validación de integridad narrativa."""

    def __init__(self, session: AsyncSession):
        """
        Inicializa servicio.

        Args:
            session: Sesión async de SQLAlchemy
        """
        self._session = session

    async def validate_all(self) -> ValidationResult:
        """
        Ejecuta todas las validaciones.

        Returns:
            ValidationResult con todos los problemas encontrados
        """
        issues = []

        # Ejecutar todas las validaciones
        dead_ends = await self.find_dead_ends()
        broken_refs = await self.find_broken_references()
        unreachable = await self.find_unreachable_fragments()
        missing_entries = await self.find_missing_entry_points()

        issues.extend(dead_ends)
        issues.extend(broken_refs)
        issues.extend(unreachable)
        issues.extend(missing_entries)

        # Contar por severidad
        errors = sum(1 for i in issues if i.severity == IssueSeverity.ERROR)
        warnings = sum(1 for i in issues if i.severity == IssueSeverity.WARNING)

        result = ValidationResult(
            is_valid=errors == 0,
            total_issues=len(issues),
            errors=errors,
            warnings=warnings,
            issues=issues
        )

        logger.info(
            f"🔍 Validación completada: {errors} errores, {warnings} warnings"
        )

        return result

    async def validate_chapter(self, chapter_id: int) -> ValidationResult:
        """
        Valida un capítulo específico.

        Args:
            chapter_id: ID del capítulo a validar

        Returns:
            ValidationResult para ese capítulo
        """
        issues = []

        # Obtener capítulo con fragmentos
        stmt = select(NarrativeChapter).where(
            NarrativeChapter.id == chapter_id
        ).options(selectinload(NarrativeChapter.fragments))

        result = await self._session.execute(stmt)
        chapter = result.scalar_one_or_none()

        if not chapter:
            return ValidationResult(
                is_valid=True,
                total_issues=0,
                errors=0,
                warnings=0,
                issues=[]
            )

        # Filtrar a este capítulo
        all_dead_ends = await self.find_dead_ends()
        all_broken = await self.find_broken_references()
        all_unreachable = await self.find_unreachable_fragments()
        all_missing = await self.find_missing_entry_points()

        for issue in all_dead_ends + all_broken + all_unreachable + all_missing:
            if issue.chapter_id == chapter_id:
                issues.append(issue)

        errors = sum(1 for i in issues if i.severity == IssueSeverity.ERROR)
        warnings = sum(1 for i in issues if i.severity == IssueSeverity.WARNING)

        return ValidationResult(
            is_valid=errors == 0,
            total_issues=len(issues),
            errors=errors,
            warnings=warnings,
            issues=issues
        )

    async def find_dead_ends(self) -> List[ValidationIssue]:
        """
        Encuentra fragmentos sin decisiones no marcados como ending.

        Un dead end es:
        - Fragmento activo
        - Sin decisiones activas
        - is_ending = False

        Returns:
            Lista de issues tipo DEAD_END
        """
        issues = []

        # Obtener todos los fragmentos activos con sus decisiones
        stmt = select(NarrativeFragment).where(
            and_(
                NarrativeFragment.is_active == True,
                NarrativeFragment.is_ending == False
            )
        ).options(
            selectinload(NarrativeFragment.decisions),
            selectinload(NarrativeFragment.chapter)
        )

        result = await self._session.execute(stmt)
        fragments = result.scalars().all()

        for fragment in fragments:
            # Contar decisiones activas
            active_decisions = [d for d in fragment.decisions if d.is_active]

            if len(active_decisions) == 0:
                issues.append(ValidationIssue(
                    issue_type=ValidationIssueType.DEAD_END,
                    severity=IssueSeverity.ERROR,
                    chapter_id=fragment.chapter_id,
                    chapter_name=fragment.chapter.name if fragment.chapter else "?",
                    fragment_key=fragment.fragment_key,
                    detail=(
                        f"Sin decisiones y no marcado como ending. "
                        f"Título: '{fragment.title}'"
                    )
                ))

        logger.debug(f"🔴 Dead ends encontrados: {len(issues)}")
        return issues

    async def find_broken_references(self) -> List[ValidationIssue]:
        """
        Encuentra decisiones con target_fragment_key inexistente.

        Una referencia rota es:
        - Decisión activa
        - target_fragment_key no corresponde a ningún fragmento activo

        Returns:
            Lista de issues tipo BROKEN_REFERENCE
        """
        issues = []

        # Obtener todos los fragment_keys activos
        stmt = select(NarrativeFragment.fragment_key).where(
            NarrativeFragment.is_active == True
        )
        result = await self._session.execute(stmt)
        valid_keys: Set[str] = set(result.scalars().all())

        # Obtener todas las decisiones activas con sus fragmentos
        stmt = select(FragmentDecision).where(
            FragmentDecision.is_active == True
        ).options(
            selectinload(FragmentDecision.fragment).selectinload(
                NarrativeFragment.chapter
            )
        )

        result = await self._session.execute(stmt)
        decisions = result.scalars().all()

        for decision in decisions:
            if decision.target_fragment_key not in valid_keys:
                fragment = decision.fragment
                issues.append(ValidationIssue(
                    issue_type=ValidationIssueType.BROKEN_REFERENCE,
                    severity=IssueSeverity.ERROR,
                    chapter_id=fragment.chapter_id if fragment else 0,
                    chapter_name=fragment.chapter.name if fragment and fragment.chapter else "?",
                    fragment_key=fragment.fragment_key if fragment else "?",
                    detail=(
                        f"Decisión '{decision.button_text}' apunta a "
                        f"'{decision.target_fragment_key}' que no existe"
                    ),
                    decision_id=decision.id
                ))

        logger.debug(f"🔴 Referencias rotas encontradas: {len(issues)}")
        return issues

    async def find_unreachable_fragments(self) -> List[ValidationIssue]:
        """
        Encuentra fragmentos que no pueden ser alcanzados.

        Un fragmento inalcanzable es:
        - Fragmento activo
        - is_entry_point = False
        - Ninguna decisión activa apunta a él

        Returns:
            Lista de issues tipo UNREACHABLE
        """
        issues = []

        # Obtener todos los target_fragment_key de decisiones activas
        stmt = select(FragmentDecision.target_fragment_key).where(
            FragmentDecision.is_active == True
        )
        result = await self._session.execute(stmt)
        reachable_keys: Set[str] = set(result.scalars().all())

        # Obtener fragmentos activos que no son entry_point
        stmt = select(NarrativeFragment).where(
            and_(
                NarrativeFragment.is_active == True,
                NarrativeFragment.is_entry_point == False
            )
        ).options(selectinload(NarrativeFragment.chapter))

        result = await self._session.execute(stmt)
        fragments = result.scalars().all()

        for fragment in fragments:
            if fragment.fragment_key not in reachable_keys:
                issues.append(ValidationIssue(
                    issue_type=ValidationIssueType.UNREACHABLE,
                    severity=IssueSeverity.WARNING,
                    chapter_id=fragment.chapter_id,
                    chapter_name=fragment.chapter.name if fragment.chapter else "?",
                    fragment_key=fragment.fragment_key,
                    detail=(
                        f"Ninguna decisión lleva a este fragmento. "
                        f"Título: '{fragment.title}'"
                    )
                ))

        logger.debug(f"🟡 Fragmentos inalcanzables: {len(issues)}")
        return issues

    async def find_missing_entry_points(self) -> List[ValidationIssue]:
        """
        Encuentra capítulos sin entry_point definido.

        Returns:
            Lista de issues tipo MISSING_ENTRY
        """
        issues = []

        # Obtener capítulos activos
        stmt = select(NarrativeChapter).where(
            NarrativeChapter.is_active == True
        ).options(selectinload(NarrativeChapter.fragments))

        result = await self._session.execute(stmt)
        chapters = result.scalars().all()

        for chapter in chapters:
            # Buscar fragmentos activos que sean entry_point
            entry_points = [
                f for f in chapter.fragments
                if f.is_active and f.is_entry_point
            ]

            if len(entry_points) == 0:
                # Verificar si tiene fragmentos activos
                active_fragments = [f for f in chapter.fragments if f.is_active]

                if len(active_fragments) > 0:
                    issues.append(ValidationIssue(
                        issue_type=ValidationIssueType.MISSING_ENTRY,
                        severity=IssueSeverity.WARNING,
                        chapter_id=chapter.id,
                        chapter_name=chapter.name,
                        fragment_key="",
                        detail=(
                            f"Capítulo con {len(active_fragments)} fragmentos "
                            f"pero ningún entry_point definido"
                        )
                    ))

        logger.debug(f"🟡 Capítulos sin entry_point: {len(issues)}")
        return issues

    def format_validation_report(self, result: ValidationResult) -> str:
        """
        Formatea reporte de validación para Telegram (HTML).

        Args:
            result: Resultado de validación

        Returns:
            String HTML formateado
        """
        if result.total_issues == 0:
            return (
                "✅ <b>Validación Exitosa</b>\n\n"
                "No se encontraron problemas en la narrativa."
            )

        # Header con resumen
        status_emoji = "❌" if result.errors > 0 else "⚠️"
        text = (
            f"{status_emoji} <b>Reporte de Validación</b>\n\n"
            f"<b>Errores:</b> {result.errors}\n"
            f"<b>Warnings:</b> {result.warnings}\n"
        )

        # Agrupar por tipo
        by_type = {}
        for issue in result.issues:
            if issue.issue_type not in by_type:
                by_type[issue.issue_type] = []
            by_type[issue.issue_type].append(issue)

        # Formatear cada tipo
        type_labels = {
            ValidationIssueType.DEAD_END: "🔴 Dead Ends",
            ValidationIssueType.BROKEN_REFERENCE: "🔴 Referencias Rotas",
            ValidationIssueType.UNREACHABLE: "🟡 Inalcanzables",
            ValidationIssueType.MISSING_ENTRY: "🟡 Sin Entry Point",
        }

        for issue_type, label in type_labels.items():
            if issue_type in by_type:
                issues = by_type[issue_type]
                text += f"\n<b>{label} ({len(issues)})</b>\n"

                # Mostrar máximo 5 por tipo
                for issue in issues[:5]:
                    if issue.fragment_key:
                        text += f"• <code>{issue.fragment_key}</code>\n"
                        text += f"  └ {issue.detail[:50]}...\n" if len(issue.detail) > 50 else f"  └ {issue.detail}\n"
                    else:
                        text += f"• {issue.chapter_name}: {issue.detail}\n"

                if len(issues) > 5:
                    text += f"  <i>... y {len(issues) - 5} más</i>\n"

        return text
