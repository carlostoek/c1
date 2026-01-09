"""
Servicio de gestión de fragmentos narrativos.

Proporciona operaciones CRUD y queries sobre fragmentos narrativos.
"""
import logging
from typing import Optional, List, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.narrative.database import (
    NarrativeChapter,
    NarrativeFragment,
    FragmentDecision,
    FragmentRequirement,
)

logger = logging.getLogger(__name__)


class FragmentService:
    """
    Servicio de fragmentos narrativos.

    Métodos:
    - get_fragment: Obtener fragmento por key
    - get_entry_point: Obtener fragmento de entrada de capítulo
    - get_fragment_with_decisions: Obtener fragmento con decisiones cargadas
    - create_fragment: Crear nuevo fragmento
    - update_fragment: Actualizar fragmento existente
    - delete_fragment: Eliminar fragmento
    - get_fragments_by_chapter: Listar fragmentos de capítulo
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa servicio.

        Args:
            session: Sesión async de SQLAlchemy
        """
        self._session = session

    async def get_fragment(
        self,
        fragment_key: str,
        load_decisions: bool = False,
        load_requirements: bool = False
    ) -> Optional[NarrativeFragment]:
        """
        Obtiene fragmento por key.

        Args:
            fragment_key: Key del fragmento (ej: "scene_1")
            load_decisions: Si cargar decisiones relacionadas
            load_requirements: Si cargar requisitos relacionados

        Returns:
            Fragmento encontrado o None
        """
        stmt = select(NarrativeFragment).where(
            NarrativeFragment.fragment_key == fragment_key
        )

        # Eager loading si se solicita
        if load_decisions:
            stmt = stmt.options(selectinload(NarrativeFragment.decisions))
        if load_requirements:
            stmt = stmt.options(selectinload(NarrativeFragment.requirements))

        result = await self._session.execute(stmt)
        fragment = result.scalar_one_or_none()

        if fragment:
            logger.debug(f"📖 Fragmento encontrado: {fragment_key}")
        else:
            logger.debug(f"❌ Fragmento no encontrado: {fragment_key}")

        return fragment

    async def get_entry_point(
        self,
        chapter_id: int
    ) -> Optional[NarrativeFragment]:
        """
        Obtiene fragmento de entrada de un capítulo.

        Args:
            chapter_id: ID del capítulo

        Returns:
            Fragmento de entrada o None si no existe
        """
        stmt = select(NarrativeFragment).where(
            NarrativeFragment.chapter_id == chapter_id,
            NarrativeFragment.is_entry_point == True
        ).order_by(NarrativeFragment.order)

        result = await self._session.execute(stmt)
        fragment = result.scalar_one_or_none()

        if fragment:
            logger.debug(f"🚪 Entry point encontrado: {fragment.fragment_key}")
        else:
            logger.warning(f"⚠️ No hay entry point para capítulo {chapter_id}")

        return fragment

    async def get_entry_point_by_type(
        self,
        chapter_type: "ChapterType"
    ) -> Optional[NarrativeFragment]:
        """
        Obtiene entry point del primer capítulo activo de un tipo.

        Útil para iniciar la historia desde el primer capítulo FREE o VIP.

        Args:
            chapter_type: Tipo de capítulo (FREE o VIP)

        Returns:
            Fragment entry point del primer capítulo del tipo, o None

        Example:
            >>> entry = await fragment_service.get_entry_point_by_type(ChapterType.FREE)
            >>> # Retorna el entry point del primer capítulo FREE
        """
        from bot.narrative.database import NarrativeChapter

        # Buscar primer capítulo activo del tipo especificado
        stmt = select(NarrativeChapter).where(
            NarrativeChapter.chapter_type == chapter_type,
            NarrativeChapter.is_active == True
        ).order_by(NarrativeChapter.order).limit(1)

        result = await self._session.execute(stmt)
        chapter = result.scalar_one_or_none()

        if not chapter:
            logger.warning(f"⚠️ No hay capítulos activos de tipo {chapter_type.value}")
            return None

        # Obtener entry point del capítulo encontrado
        return await self.get_entry_point(chapter.id)

    async def get_fragment_with_decisions(
        self,
        fragment_key: str
    ) -> Optional[NarrativeFragment]:
        """
        Obtiene fragmento con decisiones y requisitos cargados.

        Args:
            fragment_key: Key del fragmento

        Returns:
            Fragmento con relaciones cargadas o None
        """
        return await self.get_fragment(
            fragment_key,
            load_decisions=True,
            load_requirements=True
        )

    async def create_fragment(
        self,
        chapter_id: int,
        fragment_key: str,
        title: str,
        speaker: str,
        content: str,
        order: int = 0,
        is_entry_point: bool = False,
        is_ending: bool = False,
        visual_hint: Optional[str] = None,
        media_file_id: Optional[str] = None,
        auto_send_content: bool = True,
    ) -> NarrativeFragment:
        """
        Crea nuevo fragmento narrativo.

        Args:
            chapter_id: ID del capítulo al que pertenece
            fragment_key: Key único del fragmento
            title: Título del fragmento
            speaker: Quién habla (diana, lucien, narrator)
            content: Contenido narrativo (HTML)
            order: Orden dentro del capítulo
            is_entry_point: Si es punto de entrada del capítulo
            is_ending: Si es final del capítulo
            visual_hint: Descripción de imagen opcional
            media_file_id: Telegram file_id de media opcional
            auto_send_content: Si se envía automáticamente al cargar (CMS Journey)

        Returns:
            Fragmento creado

        Raises:
            ValueError: Si fragment_key ya existe
        """
        # Verificar que no exista
        existing = await self.get_fragment(fragment_key)
        if existing:
            raise ValueError(f"Fragment key '{fragment_key}' already exists")

        fragment = NarrativeFragment(
            chapter_id=chapter_id,
            fragment_key=fragment_key,
            title=title,
            speaker=speaker,
            content=content,
            order=order,
            is_entry_point=is_entry_point,
            is_ending=is_ending,
            visual_hint=visual_hint,
            media_file_id=media_file_id,
            auto_send_content=auto_send_content,
            is_active=True
        )

        self._session.add(fragment)
        await self._session.flush()
        await self._session.refresh(fragment)

        logger.info(f"✅ Fragmento creado: {fragment_key} (ID: {fragment.id})")

        return fragment

    async def update_fragment(
        self,
        fragment_key: str,
        **updates
    ) -> Optional[NarrativeFragment]:
        """
        Actualiza fragmento existente.

        Args:
            fragment_key: Key del fragmento a actualizar
            **updates: Campos a actualizar

        Returns:
            Fragmento actualizado o None si no existe
        """
        fragment = await self.get_fragment(fragment_key)
        if not fragment:
            logger.warning(f"⚠️ No se puede actualizar fragmento inexistente: {fragment_key}")
            return None

        for key, value in updates.items():
            if hasattr(fragment, key):
                setattr(fragment, key, value)

        await self._session.flush()
        await self._session.refresh(fragment)

        logger.info(f"✅ Fragmento actualizado: {fragment_key}")

        return fragment

    async def delete_fragment(self, fragment_key: str) -> bool:
        """
        Elimina fragmento.

        Args:
            fragment_key: Key del fragmento a eliminar

        Returns:
            True si se eliminó, False si no existía
        """
        fragment = await self.get_fragment(fragment_key)
        if not fragment:
            logger.warning(f"⚠️ No se puede eliminar fragmento inexistente: {fragment_key}")
            return False

        await self._session.delete(fragment)
        await self._session.flush()

        logger.info(f"🗑️ Fragmento eliminado: {fragment_key}")

        return True

    async def get_fragments_by_chapter(
        self,
        chapter_id: int,
        active_only: bool = True
    ) -> List[NarrativeFragment]:
        """
        Obtiene todos los fragmentos de un capítulo.

        Args:
            chapter_id: ID del capítulo
            active_only: Si solo retornar fragmentos activos

        Returns:
            Lista de fragmentos ordenados
        """
        stmt = select(NarrativeFragment).where(
            NarrativeFragment.chapter_id == chapter_id
        )

        if active_only:
            stmt = stmt.where(NarrativeFragment.is_active == True)

        stmt = stmt.order_by(NarrativeFragment.order)

        result = await self._session.execute(stmt)
        fragments = result.scalars().all()

        logger.debug(f"📚 Fragmentos encontrados para capítulo {chapter_id}: {len(fragments)}")

        return list(fragments)

    async def get_chapter_by_slug(self, slug: str) -> Optional[NarrativeChapter]:
        """
        Obtiene capítulo por slug.

        Args:
            slug: Slug del capítulo (ej: "los-kinkys")

        Returns:
            Capítulo encontrado o None
        """
        stmt = select(NarrativeChapter).where(NarrativeChapter.slug == slug)
        result = await self._session.execute(stmt)
        chapter = result.scalar_one_or_none()

        if chapter:
            logger.debug(f"📖 Capítulo encontrado: {slug}")
        else:
            logger.debug(f"❌ Capítulo no encontrado: {slug}")

        return chapter

    async def format_fragment_message(
        self,
        fragment: NarrativeFragment
    ) -> str:
        """
        Formatea fragmento para envío a Telegram.

        Args:
            fragment: Fragmento a formatear

        Returns:
            Mensaje formateado en HTML
        """
        # Emoji según speaker
        speaker_emojis = {
            "diana": "🌸",
            "lucien": "🎩",
            "narrator": "📖"
        }
        emoji = speaker_emojis.get(fragment.speaker, "💬")

        # Construir mensaje
        message = f"{emoji} <b>{fragment.speaker.title()}</b>\n\n"
        message += fragment.content

        # Agregar visual hint si existe
        if fragment.visual_hint:
            message += f"\n\n<i>{fragment.visual_hint}</i>"

        return message

    async def send_fragment_content_set(
        self,
        fragment: NarrativeFragment,
        user_id: int,
        bot
    ) -> Tuple[bool, str]:
        """
        Envía automáticamente el content set asociado a un fragmento narrativo.

        Este método debe llamarse cuando un usuario navega a un fragmento
        que tiene un content_set_id y auto_send_content=True.

        Args:
            fragment: Fragmento narrativo con posible content_set
            user_id: ID del usuario de Telegram
            bot: Instancia del bot de Telegram

        Returns:
            Tuple (success, message)
        """
        if not fragment.content_set_id:
            return False, "Fragmento no tiene content set asociado"

        if not fragment.auto_send_content:
            return False, "Auto-envío desactivado para este fragmento"

        from bot.shop.services.content_service import ContentService

        content_service = ContentService(self._session, bot)
        success, message = await content_service.send_content_set(
            user_id=user_id,
            content_set_id=fragment.content_set_id,
            context_message=None,  # Sin mensaje extra, va junto al fragmento
            delivery_context="narrative",
            trigger_type="automatic"
        )

        if success:
            logger.info(
                f"Content Set {fragment.content_set_id} sent to user {user_id} "
                f"via narrative fragment {fragment.fragment_key}"
            )

        return success, message
