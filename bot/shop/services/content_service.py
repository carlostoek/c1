"""
Servicio de gestión de Content Sets multimedia.

Responsabilidades:
- CRUD de ContentSets (photos, videos, audio, mixed)
- Envío de contenido multimedia a usuarios vía Telegram
- Tracking de acceso de usuarios a contenido
- Validación de permisos (VIP, tier)
"""

import json
import logging
import asyncio
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, UTC

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot
from aiogram.types import Message

from bot.shop.database.models import ContentSet, UserContentAccess
from bot.shop.database.enums import ContentType, ContentTier
from bot.database.models import User

logger = logging.getLogger(__name__)


def slugify(text: str) -> str:
    """Convierte texto a slug URL-friendly."""
    import re
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text


class ContentService:
    """
    Servicio para gestión de Content Sets multimedia.

    Maneja contenido multimedia (photos, videos, audio) que se entrega
    a usuarios a través de shop, narrativa o gamificación.
    """

    def __init__(self, session: AsyncSession, bot: Bot):
        """
        Inicializa el servicio de contenido.

        Args:
            session: Sesión de base de datos SQLAlchemy
            bot: Instancia del bot de Telegram
        """
        self.session = session
        self.bot = bot

    # ========================================
    # CRUD DE CONTENT SETS
    # ========================================

    async def create_content_set(
        self,
        slug: str,
        name: str,
        content_type: ContentType,
        file_ids: List[str],
        description: Optional[str] = None,
        tier: ContentTier = ContentTier.FREE,
        category: Optional[str] = None,
        file_metadata: Optional[Dict[str, Any]] = None,
        created_by: Optional[int] = None,
        is_active: bool = True,
        requires_vip: bool = False
    ) -> ContentSet:
        """
        Crea un nuevo Content Set.

        Args:
            slug: Identificador único URL-friendly
            name: Nombre del content set
            content_type: Tipo de contenido (PHOTO_SET, VIDEO, AUDIO, MIXED)
            file_ids: Lista de file_ids de Telegram
            description: Descripción opcional
            tier: Nivel de acceso (FREE, VIP, PREMIUM, GIFT)
            category: Categoría de uso (teaser, welcome, milestone, gift)
            file_metadata: Metadata de archivos
            created_by: ID del admin que crea
            is_active: Si está activo
            requires_vip: Si requiere VIP

        Returns:
            ContentSet creado

        Raises:
            ValueError: Si el slug ya existe
        """
        # Verificar slug único
        existing = await self.get_content_set_by_slug(slug)
        if existing:
            raise ValueError(f"Slug '{slug}' ya está en uso")

        # Crear content set
        content_set = ContentSet(
            slug=slug,
            name=name,
            description=description,
            content_type=content_type.value,
            tier=tier.value,
            category=category,
            file_ids_json=json.dumps(file_ids) if file_ids else "[]",  # Convertir a JSON
            file_metadata_json=json.dumps(file_metadata or {}) if file_metadata else "{}",  # Convertir a JSON
            created_by=created_by,
            is_active=is_active,
            requires_vip=requires_vip
        )

        self.session.add(content_set)
        await self.session.flush()

        logger.info(f"ContentSet creado: {content_set.id} - {name}")
        return content_set

    async def get_content_set(
        self,
        set_id: Optional[int] = None,
        slug: Optional[str] = None
    ) -> Optional[ContentSet]:
        """
        Obtiene un Content Set por ID o slug.

        Args:
            set_id: ID del content set
            slug: Slug del content set

        Returns:
            ContentSet o None si no existe
        """
        if set_id:
            stmt = select(ContentSet).where(ContentSet.id == set_id)
        elif slug:
            stmt = select(ContentSet).where(ContentSet.slug == slug)
        else:
            return None

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_content_set_by_slug(self, slug: str) -> Optional[ContentSet]:
        """Obtiene un Content Set por slug."""
        stmt = select(ContentSet).where(ContentSet.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_content_sets(
        self,
        tier: Optional[ContentTier] = None,
        content_type: Optional[ContentType] = None,
        is_active: bool = True,
        limit: int = 100
    ) -> List[ContentSet]:
        """
        Lista content sets con filtros opcionales.

        Args:
            tier: Filtrar por tier
            content_type: Filtrar por tipo de contenido
            is_active: Solo activos
            limit: Límite de resultados

        Returns:
            Lista de ContentSets
        """
        stmt = select(ContentSet)

        if tier:
            stmt = stmt.where(ContentSet.tier == tier.value)
        if content_type:
            stmt = stmt.where(ContentSet.content_type == content_type.value)
        if is_active:
            stmt = stmt.where(ContentSet.is_active == True)

        stmt = stmt.order_by(ContentSet.created_at.desc()).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_content_set(
        self,
        set_id: int,
        **kwargs
    ) -> ContentSet:
        """
        Actualiza un Content Set.

        Args:
            set_id: ID del content set
            **kwargs: Campos a actualizar

        Returns:
            ContentSet actualizado

        Raises:
            ValueError: Si el content set no existe
        """
        content_set = await self.get_content_set(set_id)
        if not content_set:
            raise ValueError(f"ContentSet {set_id} no encontrado")

        for key, value in kwargs.items():
            if hasattr(content_set, key):
                setattr(content_set, key, value)

        content_set.updated_at = datetime.now(UTC)
        await self.session.flush()

        logger.info(f"ContentSet actualizado: {set_id}")
        return content_set

    async def delete_content_set(
        self,
        set_id: int,
        soft_delete: bool = True
    ) -> bool:
        """
        Elimina un Content Set.

        Args:
            set_id: ID del content set
            soft_delete: Si es True, solo marca como inactivo

        Returns:
            True si se eliminó correctamente

        Raises:
            ValueError: Si el content set no existe
        """
        content_set = await self.get_content_set(set_id)
        if not content_set:
            raise ValueError(f"ContentSet {set_id} no encontrado")

        if soft_delete:
            content_set.is_active = False
            content_set.updated_at = datetime.now(UTC)
            logger.info(f"ContentSet desactivado (soft delete): {set_id}")
        else:
            await self.session.delete(content_set)
            logger.info(f"ContentSet eliminado: {set_id}")

        await self.session.flush()
        return True

    # ========================================
    # ENVÍO DE CONTENIDO MULTIMEDIA
    # ========================================

    async def send_content_set(
        self,
        user_id: int,
        content_set_id: int,
        context_message: Optional[str] = None,
        delivery_context: str = "manual",
        trigger_type: str = "manual",
        skip_vip_validation: bool = False
    ) -> Tuple[bool, str]:
        """
        Envía un content set a un usuario vía Telegram.

        Args:
            user_id: ID del usuario de Telegram
            content_set_id: ID del content set
            context_message: Mensaje previo de contexto
            delivery_context: Contexto de entrega (shop_purchase, reward_claim, etc.)
            trigger_type: Tipo de trigger (manual, automatic, achievement)
            skip_vip_validation: Si es True, salta validación VIP (para admin testing)

        Returns:
            Tuple (success, message)
        """
        logger.info(
            f"📤 Enviando content_set_id={content_set_id} a user_id={user_id} "
            f"context={delivery_context} skip_vip={skip_vip_validation}"
        )

        # Obtener content set
        content_set = await self.get_content_set(content_set_id)
        if not content_set:
            logger.error(f"❌ Content set {content_set_id} no encontrado")
            return False, "Content set no encontrado"

        if not content_set.is_active:
            logger.error(f"❌ Content set {content_set_id} no está activo")
            return False, "Content set no está activo"

        logger.info(
            f"✅ Content set encontrado: {content_set.name} "
            f"(type={content_set.content_type}, tier={content_set.tier}, "
            f"files={len(content_set.file_ids)})"
        )

        # Validar permisos VIP (solo si no es modo testing)
        if not skip_vip_validation and (content_set.requires_vip or content_set.tier == ContentTier.VIP.value):
            user = await self.session.get(User, user_id)
            if not user:
                return False, "Usuario no encontrado"

            if not await self._is_vip_user(user) and not await self._has_active_vip_subscription(user_id):
                logger.warning(
                    f"❌ Usuario {user_id} no es VIP y contenido requiere VIP"
                )
                return False, "Este contenido requiere suscripción VIP"

        # Verificar acceso previo
        previous_access = await self.get_user_content_access(user_id, content_set_id)
        if previous_access:
            logger.info(f"Usuario {user_id} ya tenía acceso al content set {content_set_id}")

        # Enviar mensaje de contexto
        if context_message:
            try:
                await self.bot.send_message(
                    user_id,
                    context_message,
                    parse_mode="HTML"
                )
                await asyncio.sleep(0.3)
            except Exception as e:
                logger.error(f"Error enviando mensaje de contexto: {e}")

        # Enviar archivos según tipo
        try:
            success = await self._send_media_by_type(user_id, content_set)
            if not success:
                return False, "Error al enviar contenido multimedia"

            # Trackear acceso
            await self.track_content_access(
                user_id,
                content_set_id,
                delivery_context,
                trigger_type
            )

            logger.info(f"✅ Content set {content_set_id} enviado exitosamente a {user_id}")
            return True, "Contenido enviado exitosamente"

        except Exception as e:
            logger.error(f"Error enviando content set: {e}", exc_info=True)
            return False, f"Error: {str(e)}"

    async def _send_media_by_type(
        self,
        user_id: int,
        content_set: ContentSet
    ) -> bool:
        """
        Envía archivos según el tipo de contenido.

        Args:
            user_id: ID del usuario
            content_set: ContentSet a enviar

        Returns:
            True si se envió correctamente
        """
        content_type = content_set.content_type
        file_ids = content_set.file_ids

        logger.info(
            f"📤 _send_media_by_type: user_id={user_id}, "
            f"content_type={content_type}, num_files={len(file_ids)}"
        )

        if not file_ids:
            logger.warning(f"ContentSet {content_set.id} no tiene archivos")
            return False

        try:
            # Verificar que el bot puede enviar mensajes al usuario
            try:
                await self.bot.send_chat_action(user_id, "upload_photo")
                logger.info(f"✅ Bot puede enviar mensajes a user_id={user_id}")
            except Exception as e:
                logger.error(
                    f"❌ Bot NO puede enviar mensajes a user_id={user_id}: {e}. "
                    f"El usuario puede haber bloqueado al bot o no ha iniciado conversación."
                )
                return False

            if content_type == ContentType.PHOTO_SET.value:
                # Enviar fotos como álbum usando send_media_group
                logger.info(f"📤 Enviando PHOTO_SET con {len(file_ids)} fotos")
                media_group = []
                for file_id in file_ids:
                    media_group.append({'type': 'photo', 'media': file_id})

                # Dividir en grupos de máximo 10 fotos por álbum (Telegram limit)
                for i in range(0, len(media_group), 10):
                    album_batch = media_group[i:i+10]
                    await self.bot.send_media_group(user_id, album_batch)
                    await asyncio.sleep(0.3)  # Anti rate-limit
                logger.info(f"✅ PHOTO_SET enviado correctamente")

            elif content_type == ContentType.VIDEO.value:
                # Enviar video único
                logger.info(f"📤 Enviando VIDEO: {file_ids[0]}")
                await self.bot.send_video(user_id, file_ids[0])
                logger.info(f"✅ VIDEO enviado correctamente")

            elif content_type == ContentType.AUDIO.value:
                # Enviar audio único
                logger.info(f"📤 Enviando AUDIO: {file_ids[0]}")
                await self.bot.send_audio(user_id, file_ids[0])
                logger.info(f"✅ AUDIO enviado correctamente")

            elif content_type == ContentType.MIXED.value:
                # Enviar según metadata o intentar detectar
                logger.info(f"📤 Enviando MIXED content con {len(file_ids)} archivos")
                for idx, file_id in enumerate(file_ids):
                    metadata = content_set.file_metadata.get(file_id, {})
                    file_type = metadata.get('type', 'photo')

                    logger.info(f"📤 Enviando archivo {idx+1}/{len(file_ids)}: type={file_type}")

                    if file_type == 'photo':
                        await self.bot.send_photo(user_id, file_id)
                    elif file_type == 'video':
                        await self.bot.send_video(user_id, file_id)
                    elif file_type == 'audio':
                        await self.bot.send_audio(user_id, file_id)
                    else:
                        # Fallback: intentar como foto
                        await self.bot.send_photo(user_id, file_id)

                    await asyncio.sleep(0.3)
                logger.info(f"✅ MIXED content enviado correctamente")

            return True

        except Exception as e:
            logger.error(f"Error enviando multimedia: {e}", exc_info=True)
            return False

    # ========================================
    # TRACKING DE ACCESO
    # ========================================

    async def track_content_access(
        self,
        user_id: int,
        content_set_id: int,
        delivery_context: str,
        trigger_type: str
    ) -> UserContentAccess:
        """
        Registra acceso de usuario a un content set.

        Args:
            user_id: ID del usuario
            content_set_id: ID del content set
            delivery_context: Contexto de entrega
            trigger_type: Tipo de trigger

        Returns:
            UserContentAccess creado
        """
        access = UserContentAccess(
            user_id=user_id,
            content_set_id=content_set_id,
            delivery_context=delivery_context,
            trigger_type=trigger_type
        )

        self.session.add(access)
        await self.session.flush()

        logger.debug(
            f"Acceso trackeado: user={user_id}, content_set={content_set_id}, "
            f"context={delivery_context}"
        )
        return access

    async def get_user_content_access(
        self,
        user_id: int,
        content_set_id: int
    ) -> Optional[UserContentAccess]:
        """
        Verifica si un usuario ha accedido a un content set.

        Args:
            user_id: ID del usuario
            content_set_id: ID del content set

        Returns:
            UserContentAccess o None
        """
        stmt = select(UserContentAccess).where(
            UserContentAccess.user_id == user_id,
            UserContentAccess.content_set_id == content_set_id
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_content_history(
        self,
        user_id: int,
        limit: int = 50
    ) -> List[UserContentAccess]:
        """
        Obtiene historial de acceso de un usuario.

        Args:
            user_id: ID del usuario
            limit: Límite de resultados

        Returns:
            Lista de UserContentAccess ordenada por fecha
        """
        stmt = select(UserContentAccess).where(
            UserContentAccess.user_id == user_id
        ).order_by(
            UserContentAccess.accessed_at.desc()
        ).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_content_set_stats(
        self,
        content_set_id: int
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas de un content set.

        Args:
            content_set_id: ID del content set

        Returns:
            Dict con stats (total_access, by_context, etc.)
        """
        # Total de accesos
        stmt_total = select(func.count(UserContentAccess.id)).where(
            UserContentAccess.content_set_id == content_set_id
        )
        result_total = await self.session.execute(stmt_total)
        total_access = result_total.scalar() or 0

        # Accesos por contexto
        stmt_context = select(
            UserContentAccess.delivery_context,
            func.count(UserContentAccess.id)
        ).where(
            UserContentAccess.content_set_id == content_set_id
        ).group_by(UserContentAccess.delivery_context)

        result_context = await self.session.execute(stmt_context)
        by_context = {row[0]: row[1] for row in result_context.all()}

        return {
            "total_access": total_access,
            "by_context": by_context,
            "content_set_id": content_set_id
        }

    # ========================================
    # VALIDACIONES
    # ========================================

    async def validate_vip_access(
        self,
        user_id: int,
        content_set_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida si un usuario puede acceder a un content set VIP.

        Args:
            user_id: ID del usuario
            content_set_id: ID del content set

        Returns:
            Tuple (has_access, error_message)
        """
        content_set = await self.get_content_set(content_set_id)
        if not content_set:
            return False, "Content set no encontrado"

        if not content_set.requires_vip and content_set.tier != ContentTier.VIP.value:
            return True, None

        # Verificar si usuario es VIP
        user = await self.session.get(User, user_id)
        if not user:
            return False, "Usuario no encontrado"

        if not await self._is_vip_user(user) and not await self._has_active_vip_subscription(user_id):
            return False, "Este contenido requiere suscripción VIP"

        return True, None

    # ========================================
    # HELPERS
    # ========================================

    async def _is_vip_user(self, user: User) -> bool:
        """Verifica si un usuario es VIP."""
        return user.is_vip

    async def _has_active_vip_subscription(self, user_id: int) -> bool:
        """Verifica si un usuario tiene suscripción VIP activa."""
        from bot.database.models import VIPSubscriber
        from datetime import datetime

        stmt = select(VIPSubscriber).where(
            VIPSubscriber.user_id == user_id,
            VIPSubscriber.expiry_date > datetime.now(UTC)
        )
        result = await self.session.execute(stmt)
        subscription = result.scalar_one_or_none()
        return subscription is not None

    async def add_file_to_content_set(
        self,
        content_set_id: int,
        file_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Agrega un archivo a un content set existente.

        Args:
            content_set_id: ID del content set
            file_id: File ID de Telegram
            metadata: Metadata del archivo

        Returns:
            True si se agregó correctamente
        """
        content_set = await self.get_content_set(content_set_id)
        if not content_set:
            return False

        file_ids = content_set.file_ids
        if file_id in file_ids:
            return False  # Ya existe

        file_ids.append(file_id)

        # Actualizar metadata si se proporciona
        if metadata:
            file_metadata = content_set.file_metadata
            file_metadata[file_id] = metadata
            content_set.file_metadata = file_metadata

        content_set.updated_at = datetime.now(UTC)
        await self.session.flush()

        logger.info(f"Archivo agregado al ContentSet {content_set_id}: {file_id}")
        return True

    async def remove_file_from_content_set(
        self,
        content_set_id: int,
        file_id: str
    ) -> bool:
        """
        Remueve un archivo de un content set.

        Args:
            content_set_id: ID del content set
            file_id: File ID a remover

        Returns:
            True si se removió correctamente
        """
        content_set = await self.get_content_set(content_set_id)
        if not content_set:
            return False

        file_ids = content_set.file_ids
        if file_id not in file_ids:
            return False

        file_ids.remove(file_id)

        # Remover metadata
        file_metadata = content_set.file_metadata
        if file_id in file_metadata:
            del file_metadata[file_id]
            content_set.file_metadata = file_metadata

        content_set.updated_at = datetime.now(UTC)
        await self.session.flush()

        logger.info(f"Archivo removido del ContentSet {content_set_id}: {file_id}")
        return True

    async def get_content_set_shop_items(
        self,
        content_set_id: int
    ) -> List:
        """
        Obtiene los shop items que están asociados a un content set.

        Args:
            content_set_id: ID del content set

        Returns:
            Lista de shop items asociados al content set
        """
        from bot.shop.database.models import ShopItem

        stmt = select(ShopItem).where(
            ShopItem.content_set_id == content_set_id
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())
