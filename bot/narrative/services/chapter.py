"""
Servicio de gestión de capítulos narrativos.

Responsabilidades:
- CRUD de capítulos
- Validación de estructura
- Consultas y listados
"""

import logging
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.narrative.database import NarrativeChapter, ChapterType

logger = logging.getLogger(__name__)


class ChapterService:
    """Servicio de gestión de capítulos narrativos."""

    def __init__(self, session: AsyncSession):
        """
        Inicializa servicio.

        Args:
            session: Sesión async de SQLAlchemy
        """
        self._session = session

    async def create_chapter(
        self,
        name: str,
        slug: str,
        chapter_type: ChapterType,
        description: Optional[str] = None,
        order: int = 0
    ) -> NarrativeChapter:
        """
        Crea nuevo capítulo narrativo.

        Args:
            name: Nombre del capítulo (ej: "Los Kinkys")
            slug: Slug único (ej: "los-kinkys")
            chapter_type: FREE o VIP
            description: Descripción opcional
            order: Orden de aparición (default: 0)

        Returns:
            Capítulo creado

        Raises:
            ValueError: Si slug ya existe
        """
        # Verificar que slug no exista
        existing = await self.get_chapter_by_slug(slug)
        if existing:
            raise ValueError(f"Chapter with slug '{slug}' already exists")

        chapter = NarrativeChapter(
            name=name,
            slug=slug,
            chapter_type=chapter_type,
            description=description,
            order=order,
            is_active=True
        )

        self._session.add(chapter)
        await self._session.flush()
        await self._session.refresh(chapter)

        logger.info(f"✅ Capítulo creado: {name} (slug: {slug}, tipo: {chapter_type.value})")

        return chapter

    async def get_chapter_by_id(
        self,
        chapter_id: int
    ) -> Optional[NarrativeChapter]:
        """
        Obtiene capítulo por ID.

        Args:
            chapter_id: ID del capítulo

        Returns:
            Capítulo o None si no existe
        """
        return await self._session.get(NarrativeChapter, chapter_id)

    async def get_chapter_by_slug(
        self,
        slug: str
    ) -> Optional[NarrativeChapter]:
        """
        Obtiene capítulo por slug.

        Args:
            slug: Slug del capítulo

        Returns:
            Capítulo o None si no existe
        """
        stmt = select(NarrativeChapter).where(NarrativeChapter.slug == slug)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_chapters(
        self,
        active_only: bool = True,
        chapter_type: Optional[ChapterType] = None
    ) -> List[NarrativeChapter]:
        """
        Obtiene todos los capítulos con filtros opcionales.

        Args:
            active_only: Si True, solo retorna capítulos activos
            chapter_type: Filtrar por tipo (FREE o VIP)

        Returns:
            Lista de capítulos ordenados por 'order'
        """
        stmt = select(NarrativeChapter).order_by(NarrativeChapter.order)

        if active_only:
            stmt = stmt.where(NarrativeChapter.is_active == True)

        if chapter_type:
            stmt = stmt.where(NarrativeChapter.chapter_type == chapter_type)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_chapter(
        self,
        chapter_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        order: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> NarrativeChapter:
        """
        Actualiza capítulo existente.

        Args:
            chapter_id: ID del capítulo
            name: Nuevo nombre (opcional)
            description: Nueva descripción (opcional)
            order: Nuevo orden (opcional)
            is_active: Nuevo estado activo (opcional)

        Returns:
            Capítulo actualizado

        Raises:
            ValueError: Si capítulo no existe
        """
        chapter = await self.get_chapter_by_id(chapter_id)
        if not chapter:
            raise ValueError(f"Chapter {chapter_id} not found")

        if name is not None:
            chapter.name = name
        if description is not None:
            chapter.description = description
        if order is not None:
            chapter.order = order
        if is_active is not None:
            chapter.is_active = is_active

        await self._session.flush()
        await self._session.refresh(chapter)

        logger.info(f"✏️ Capítulo actualizado: {chapter.name} (ID: {chapter_id})")

        return chapter

    async def delete_chapter(
        self,
        chapter_id: int
    ) -> bool:
        """
        Soft-delete de capítulo (is_active=False).

        Args:
            chapter_id: ID del capítulo

        Returns:
            True si se eliminó correctamente
        """
        chapter = await self.get_chapter_by_id(chapter_id)
        if not chapter:
            return False

        chapter.is_active = False
        await self._session.flush()

        logger.info(f"🗑️ Capítulo desactivado: {chapter.name} (ID: {chapter_id})")

        return True

    async def get_chapter_fragments_count(
        self,
        chapter_id: int
    ) -> int:
        """
        Obtiene la cantidad de fragmentos de un capítulo.

        Args:
            chapter_id: ID del capítulo

        Returns:
            Cantidad de fragmentos
        """
        from bot.narrative.database import NarrativeFragment
        from sqlalchemy import func

        stmt = select(func.count()).select_from(NarrativeFragment).where(
            NarrativeFragment.chapter_id == chapter_id,
            NarrativeFragment.is_active == True
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()
