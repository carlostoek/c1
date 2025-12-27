"""
Servicio de importación de contenido narrativo desde JSON.

Responsabilidades:
- Validar estructura JSON
- Detectar conflictos de fragment_key
- Procesar importación (crear/actualizar)
- Manejar media (URLs/file_ids)
"""
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from bot.narrative.database import (
    ChapterType,
    FragmentDecision,
    FragmentRequirement,
    NarrativeChapter,
    NarrativeFragment,
    RequirementType,
)
from bot.narrative.services.chapter import ChapterService
from bot.narrative.services.fragment import FragmentService
from bot.utils.media import download_and_upload_media, is_url

if TYPE_CHECKING:
    from aiogram import Bot

logger = logging.getLogger(__name__)


class ImportType(str, Enum):
    """Tipo de importación."""
    CHAPTER = "chapter"      # Capítulo completo con fragmentos
    FRAGMENTS = "fragments"  # Solo fragmentos para capítulo existente


class ConflictResolution(str, Enum):
    """Resolución de conflicto."""
    UPDATE = "update"  # Actualizar fragmento existente
    SKIP = "skip"      # Omitir fragmento


@dataclass
class ValidationResult:
    """Resultado de validación de JSON."""
    is_valid: bool
    import_type: Optional[ImportType] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    chapter_data: Optional[Dict] = None
    chapter_slug: Optional[str] = None
    fragments: List[Dict] = field(default_factory=list)
    conflicts: List[Dict] = field(default_factory=list)


@dataclass
class ImportResult:
    """Resultado de importación."""
    success: bool
    message: str
    chapters_created: int = 0
    fragments_created: int = 0
    fragments_updated: int = 0
    fragments_skipped: int = 0
    decisions_created: int = 0
    requirements_created: int = 0
    errors: List[str] = field(default_factory=list)
    media_downloaded: int = 0
    media_failed: int = 0


class JsonImportService:
    """Servicio de importación JSON para narrativa."""

    def __init__(self, session: AsyncSession, bot: Optional["Bot"] = None):
        """
        Inicializa servicio.

        Args:
            session: Sesión async de SQLAlchemy
            bot: Instancia del bot (para descargar media)
        """
        self._session = session
        self._bot = bot
        self._chapter_service = ChapterService(session)
        self._fragment_service = FragmentService(session)

    # ========================================
    # VALIDACIÓN
    # ========================================

    async def validate_json(self, json_content: Dict) -> ValidationResult:
        """
        Valida estructura y contenido del JSON.

        Args:
            json_content: Dict parseado del JSON

        Returns:
            ValidationResult con estado de validación y datos extraídos
        """
        errors = []
        warnings = []
        chapter_data = None
        chapter_slug = None
        fragments = []
        conflicts = []

        # 1. Validar campo "type"
        import_type_str = json_content.get("type")
        if import_type_str not in ["chapter", "fragments"]:
            errors.append(
                f"Campo 'type' inválido: '{import_type_str}'. "
                "Debe ser 'chapter' o 'fragments'"
            )
            return ValidationResult(
                is_valid=False,
                import_type=None,
                errors=errors,
                warnings=warnings,
            )

        import_type = ImportType(import_type_str)

        # 2. Validar según tipo
        if import_type == ImportType.CHAPTER:
            chapter_data = json_content.get("chapter")
            if not chapter_data:
                errors.append("Falta campo 'chapter' para type='chapter'")
            else:
                # Validar campos requeridos del capítulo
                required_fields = ["name", "slug", "chapter_type"]
                for fld in required_fields:
                    if fld not in chapter_data:
                        errors.append(f"Falta campo 'chapter.{fld}'")

                # Validar chapter_type
                ch_type = chapter_data.get("chapter_type", "")
                if ch_type.lower() not in ["free", "vip"]:
                    errors.append(
                        "'chapter.chapter_type' debe ser 'free' o 'vip'"
                    )

                chapter_slug = chapter_data.get("slug")

                # Verificar si slug ya existe
                if chapter_slug:
                    existing = await self._chapter_service.get_chapter_by_slug(
                        chapter_slug
                    )
                    if existing:
                        warnings.append(
                            f"El capítulo '{chapter_slug}' ya existe. "
                            "Se actualizarán sus datos."
                        )

        else:  # FRAGMENTS
            chapter_slug = json_content.get("chapter_slug")
            if not chapter_slug:
                errors.append(
                    "Falta campo 'chapter_slug' para type='fragments'"
                )
            else:
                # Verificar que capítulo existe
                existing = await self._chapter_service.get_chapter_by_slug(
                    chapter_slug
                )
                if not existing:
                    errors.append(f"Capítulo '{chapter_slug}' no existe")

        # 3. Validar fragmentos
        fragments_data = json_content.get("fragments", [])
        if not fragments_data:
            errors.append("No hay fragmentos en el JSON")
        else:
            for idx, frag in enumerate(fragments_data):
                frag_errors = self._validate_fragment(frag, idx)
                errors.extend(frag_errors)

                if not frag_errors:
                    fragments.append(frag)

                    # Detectar conflictos
                    frag_key = frag.get("fragment_key")
                    if frag_key:
                        existing_frag = await self._fragment_service.get_fragment(
                            frag_key
                        )
                        if existing_frag:
                            conflicts.append({
                                "fragment_key": frag_key,
                                "existing_title": existing_frag.title,
                                "new_title": frag.get("title"),
                                "index": idx
                            })

        return ValidationResult(
            is_valid=len(errors) == 0,
            import_type=import_type,
            errors=errors,
            warnings=warnings,
            chapter_data=chapter_data,
            chapter_slug=chapter_slug,
            fragments=fragments,
            conflicts=conflicts
        )

    def _validate_fragment(self, fragment: Dict, index: int) -> List[str]:
        """
        Valida un fragmento individual.

        Args:
            fragment: Dict con datos del fragmento
            index: Índice en la lista (para mensajes de error)

        Returns:
            Lista de errores (vacía si válido)
        """
        errors = []
        prefix = f"fragments[{index}]"

        # Campos requeridos
        required = ["fragment_key", "title", "speaker", "content"]
        for fld in required:
            if not fragment.get(fld):
                errors.append(f"{prefix}.{fld} es requerido")

        # Validar speaker
        valid_speakers = ["diana", "lucien", "narrator"]
        speaker = fragment.get("speaker", "").lower()
        if speaker and speaker not in valid_speakers:
            errors.append(
                f"{prefix}.speaker debe ser uno de: {', '.join(valid_speakers)}"
            )

        # Validar decisiones si existen
        decisions = fragment.get("decisions", [])
        for dec_idx, decision in enumerate(decisions):
            dec_prefix = f"{prefix}.decisions[{dec_idx}]"
            if not decision.get("button_text"):
                errors.append(f"{dec_prefix}.button_text es requerido")
            if not decision.get("target_fragment_key"):
                errors.append(f"{dec_prefix}.target_fragment_key es requerido")

        # Validar requirements si existen
        requirements = fragment.get("requirements", [])
        valid_req_types = ["none", "vip", "besitos", "archetype", "decision"]
        for req_idx, req in enumerate(requirements):
            req_prefix = f"{prefix}.requirements[{req_idx}]"
            req_type = req.get("requirement_type", "").lower()
            if req_type and req_type not in valid_req_types:
                errors.append(f"{req_prefix}.requirement_type inválido: {req_type}")

        return errors

    # ========================================
    # IMPORTACIÓN
    # ========================================

    async def import_content(
        self,
        validation_result: ValidationResult,
        conflict_resolutions: Dict[str, ConflictResolution],
        admin_chat_id: Optional[int] = None
    ) -> ImportResult:
        """
        Ejecuta la importación del contenido.

        Args:
            validation_result: Resultado de validate_json()
            conflict_resolutions: Dict {fragment_key: "update"|"skip"}
            admin_chat_id: Chat ID del admin para subir media temporal

        Returns:
            ImportResult con estadísticas
        """
        stats = {
            "chapters_created": 0,
            "fragments_created": 0,
            "fragments_updated": 0,
            "fragments_skipped": 0,
            "decisions_created": 0,
            "requirements_created": 0,
            "media_downloaded": 0,
            "media_failed": 0,
            "errors": []
        }

        try:
            # 1. Procesar capítulo si aplica
            chapter = await self._process_chapter(
                validation_result.import_type,
                validation_result.chapter_data,
                validation_result.chapter_slug,
                stats
            )

            if not chapter:
                return ImportResult(
                    success=False,
                    message="No se pudo obtener/crear el capítulo",
                    **stats
                )

            # 2. Procesar fragmentos
            for fragment_data in validation_result.fragments:
                await self._process_fragment(
                    fragment_data,
                    chapter.id,
                    conflict_resolutions,
                    stats,
                    admin_chat_id
                )

            await self._session.commit()

            return ImportResult(
                success=True,
                message="Importación completada exitosamente",
                **stats
            )

        except Exception as e:
            logger.error(f"Error en importación: {e}", exc_info=True)
            await self._session.rollback()
            stats["errors"].append(str(e))
            return ImportResult(
                success=False,
                message=f"Error durante importación: {str(e)}",
                **stats
            )

    async def _process_chapter(
        self,
        import_type: ImportType,
        chapter_data: Optional[Dict],
        chapter_slug: str,
        stats: Dict
    ) -> Optional[NarrativeChapter]:
        """
        Procesa o recupera el capítulo.

        Returns:
            NarrativeChapter o None si error
        """
        if import_type == ImportType.FRAGMENTS:
            # Solo obtener capítulo existente
            return await self._chapter_service.get_chapter_by_slug(chapter_slug)

        # Crear o actualizar capítulo
        existing = await self._chapter_service.get_chapter_by_slug(chapter_slug)

        if existing:
            # Actualizar
            chapter = await self._chapter_service.update_chapter(
                chapter_id=existing.id,
                name=chapter_data.get("name"),
                description=chapter_data.get("description"),
                order=chapter_data.get("order", existing.order),
                is_active=chapter_data.get("is_active", True)
            )
            logger.info(f"Capítulo actualizado: {chapter.slug}")
        else:
            # Crear
            ch_type_str = chapter_data.get("chapter_type", "free").lower()
            chapter_type = ChapterType(ch_type_str)
            chapter = await self._chapter_service.create_chapter(
                name=chapter_data["name"],
                slug=chapter_data["slug"],
                chapter_type=chapter_type,
                description=chapter_data.get("description"),
                order=chapter_data.get("order", 0)
            )
            stats["chapters_created"] += 1
            logger.info(f"Capítulo creado: {chapter.slug}")

        return chapter

    async def _process_fragment(
        self,
        fragment_data: Dict,
        chapter_id: int,
        conflict_resolutions: Dict[str, ConflictResolution],
        stats: Dict,
        admin_chat_id: Optional[int] = None
    ) -> None:
        """Procesa un fragmento individual."""
        fragment_key = fragment_data["fragment_key"]
        existing = await self._fragment_service.get_fragment(fragment_key)

        if existing:
            # Conflicto - verificar resolución
            resolution = conflict_resolutions.get(
                fragment_key,
                ConflictResolution.SKIP
            )

            if resolution == ConflictResolution.SKIP:
                stats["fragments_skipped"] += 1
                logger.info(f"Fragmento omitido: {fragment_key}")
                return

            # UPDATE: Actualizar fragmento existente
            await self._update_fragment(
                existing, fragment_data, stats, admin_chat_id
            )
            stats["fragments_updated"] += 1
        else:
            # Crear nuevo fragmento
            await self._create_fragment(
                fragment_data, chapter_id, stats, admin_chat_id
            )
            stats["fragments_created"] += 1

    async def _create_fragment(
        self,
        fragment_data: Dict,
        chapter_id: int,
        stats: Dict,
        admin_chat_id: Optional[int] = None
    ) -> NarrativeFragment:
        """Crea un nuevo fragmento con sus relaciones."""

        # Manejar media si existe
        media_file_id = await self._process_media(
            fragment_data.get("media"),
            stats,
            admin_chat_id
        )

        # Crear fragmento
        fragment = await self._fragment_service.create_fragment(
            chapter_id=chapter_id,
            fragment_key=fragment_data["fragment_key"],
            title=fragment_data["title"],
            speaker=fragment_data["speaker"].lower(),
            content=fragment_data["content"],
            order=fragment_data.get("order", 0),
            is_entry_point=fragment_data.get("is_entry_point", False),
            is_ending=fragment_data.get("is_ending", False),
            visual_hint=fragment_data.get("visual_hint"),
            media_file_id=media_file_id
        )

        # Crear decisiones
        for dec_data in fragment_data.get("decisions", []):
            await self._create_decision(fragment.id, dec_data)
            stats["decisions_created"] += 1

        # Crear requisitos
        for req_data in fragment_data.get("requirements", []):
            await self._create_requirement(fragment.id, req_data)
            stats["requirements_created"] += 1

        return fragment

    async def _update_fragment(
        self,
        existing: NarrativeFragment,
        fragment_data: Dict,
        stats: Dict,
        admin_chat_id: Optional[int] = None
    ) -> NarrativeFragment:
        """Actualiza un fragmento existente."""

        # Manejar media si existe
        media_file_id = await self._process_media(
            fragment_data.get("media"),
            stats,
            admin_chat_id
        )

        # Actualizar fragmento
        updates = {
            "title": fragment_data["title"],
            "speaker": fragment_data["speaker"].lower(),
            "content": fragment_data["content"],
            "order": fragment_data.get("order", existing.order),
            "is_entry_point": fragment_data.get(
                "is_entry_point", existing.is_entry_point
            ),
            "is_ending": fragment_data.get("is_ending", existing.is_ending),
            "visual_hint": fragment_data.get("visual_hint", existing.visual_hint),
        }

        if media_file_id:
            updates["media_file_id"] = media_file_id

        updated = await self._fragment_service.update_fragment(
            existing.fragment_key,
            **updates
        )

        return updated

    async def _create_decision(
        self,
        fragment_id: int,
        dec_data: Dict
    ) -> FragmentDecision:
        """Crea una decisión de fragmento."""
        decision = FragmentDecision(
            fragment_id=fragment_id,
            button_text=dec_data["button_text"],
            button_emoji=dec_data.get("button_emoji"),
            order=dec_data.get("order", 0),
            target_fragment_key=dec_data["target_fragment_key"],
            besitos_cost=dec_data.get("besitos_cost", 0),
            grants_besitos=dec_data.get("grants_besitos", 0),
            affects_archetype=dec_data.get("affects_archetype"),
            is_active=True
        )
        self._session.add(decision)
        await self._session.flush()
        return decision

    async def _create_requirement(
        self,
        fragment_id: int,
        req_data: Dict
    ) -> FragmentRequirement:
        """Crea un requisito de fragmento."""
        req_type_str = req_data.get("requirement_type", "none").lower()
        req_type = RequirementType(req_type_str)

        requirement = FragmentRequirement(
            fragment_id=fragment_id,
            requirement_type=req_type,
            value=str(req_data.get("value", "")),
            rejection_message=req_data.get("rejection_message")
        )
        self._session.add(requirement)
        await self._session.flush()
        return requirement

    async def _process_media(
        self,
        media_value: Optional[str],
        stats: Dict,
        admin_chat_id: Optional[int] = None
    ) -> Optional[str]:
        """
        Procesa valor de media.

        Si es URL (http/https): descarga y sube a Telegram para obtener file_id
        Si es file_id (no es URL): retorna directamente
        Si es null/None: retorna None

        Args:
            media_value: URL, file_id o None
            stats: Dict de estadísticas para actualizar
            admin_chat_id: Chat ID para subir media temporal

        Returns:
            file_id o None
        """
        if not media_value:
            return None

        # Detectar si es URL
        if is_url(media_value):
            # Descargar y subir
            try:
                if self._bot and admin_chat_id:
                    file_id = await download_and_upload_media(
                        self._bot,
                        media_value,
                        admin_chat_id
                    )
                    if file_id:
                        stats["media_downloaded"] += 1
                        return file_id
                    else:
                        stats["media_failed"] += 1
                        return None
                else:
                    stats["media_failed"] += 1
                    logger.warning("Bot o chat_id no disponible para descargar media")
                    return None
            except Exception as e:
                stats["media_failed"] += 1
                logger.error(f"Error descargando media: {e}")
                return None
        else:
            # Asumir que es file_id
            return media_value

    # ========================================
    # FORMATEO
    # ========================================

    def format_validation_summary(self, result: ValidationResult) -> str:
        """
        Formatea resumen de validación para mostrar al usuario.

        Args:
            result: ValidationResult de validate_json()

        Returns:
            String HTML formateado
        """
        if not result.is_valid:
            errors_text = "\n".join([f"• {e}" for e in result.errors])
            return (
                f"<b>Validación Fallida</b>\n\n"
                f"<b>Errores:</b>\n<code>{errors_text}</code>"
            )

        import_type_label = (
            "Capítulo completo" if result.import_type == ImportType.CHAPTER
            else "Solo fragmentos"
        )

        summary = (
            f"<b>Validación Exitosa</b>\n\n"
            f"<b>Tipo:</b> {import_type_label}\n"
            f"<b>Capítulo:</b> {result.chapter_slug}\n"
            f"<b>Fragmentos:</b> {len(result.fragments)}\n"
        )

        if result.conflicts:
            summary += f"<b>Conflictos:</b> {len(result.conflicts)}\n"

        if result.warnings:
            warnings_text = "\n".join([f"• {w}" for w in result.warnings])
            summary += f"\n<b>Advertencias:</b>\n<i>{warnings_text}</i>"

        return summary

    def format_import_result(self, result: ImportResult) -> str:
        """
        Formatea resultado de importación para mostrar al usuario.

        Args:
            result: ImportResult de import_content()

        Returns:
            String HTML formateado
        """
        if not result.success:
            errors_text = (
                "\n".join([f"• {e}" for e in result.errors])
                if result.errors else "Error desconocido"
            )
            return (
                f"<b>Importación Fallida</b>\n\n"
                f"{result.message}\n\n"
                f"<b>Errores:</b>\n<code>{errors_text}</code>"
            )

        summary = (
            f"<b>Importación Exitosa</b>\n\n"
            f"<b>Capítulos creados:</b> {result.chapters_created}\n"
            f"<b>Fragmentos creados:</b> {result.fragments_created}\n"
            f"<b>Fragmentos actualizados:</b> {result.fragments_updated}\n"
            f"<b>Fragmentos omitidos:</b> {result.fragments_skipped}\n"
            f"<b>Decisiones creadas:</b> {result.decisions_created}\n"
            f"<b>Requisitos creados:</b> {result.requirements_created}\n"
        )

        if result.media_downloaded > 0 or result.media_failed > 0:
            summary += (
                f"\n<b>Media descargada:</b> {result.media_downloaded}\n"
                f"<b>Media fallida:</b> {result.media_failed}\n"
            )

        return summary
