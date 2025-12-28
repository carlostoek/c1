"""
Servicio de gestión de pistas narrativas.

Las pistas son items de tipo NARRATIVE con is_clue=True en su metadata.
Este servicio proporciona una interfaz conveniente para gestionar
pistas sin necesidad de conocer los detalles de la tienda.
"""
import logging
from typing import Optional, List, Dict, Any

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.shop.database.models import ShopItem, UserInventoryItem, UserInventory
from bot.shop.database.enums import ItemType, ObtainedVia

logger = logging.getLogger(__name__)


class ClueService:
    """
    Servicio para gestión de pistas narrativas.

    Las pistas son items de tienda con:
    - item_type = "narrative"
    - item_metadata.is_clue = True

    Este servicio proporciona métodos convenientes para:
    - Otorgar pistas desde fragmentos
    - Verificar posesión de pistas
    - Listar pistas del usuario
    - Obtener información de pistas
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio.

        Args:
            session: Sesión async de SQLAlchemy
        """
        self._session = session

    # ========================================
    # OBTENCIÓN DE PISTAS
    # ========================================

    async def grant_clue(
        self,
        user_id: int,
        clue_slug: str,
        source_fragment_key: Optional[str] = None
    ) -> tuple[bool, str, Optional[UserInventoryItem]]:
        """
        Otorga una pista al usuario.

        Args:
            user_id: ID del usuario
            clue_slug: Slug del item de pista
            source_fragment_key: Fragmento donde se encontró (para contexto)

        Returns:
            Tupla (éxito, mensaje, item_en_inventario)
        """
        # Buscar el item de pista
        clue = await self.get_clue_by_slug(clue_slug)
        if clue is None:
            logger.error(f"Pista no encontrada: {clue_slug}")
            return False, "Pista no encontrada en el sistema", None

        # Verificar si ya tiene la pista
        if await self.has_clue(user_id, clue_slug):
            logger.debug(f"Usuario {user_id} ya tiene la pista {clue_slug}")
            return True, "Ya tienes esta pista", None

        # Obtener o crear inventario del usuario usando el servicio compartido
        from bot.shop.services.inventory import InventoryService
        inventory_service = InventoryService(self._session)
        inventory = await inventory_service.get_or_create_inventory(user_id)

        # Crear item en inventario
        inv_item = UserInventoryItem(
            user_id=user_id,
            item_id=clue.id,
            quantity=1,
            obtained_via=ObtainedVia.DISCOVERY,
            is_equipped=False,
            is_used=False
        )
        self._session.add(inv_item)

        # Actualizar contador de inventario
        inventory.total_items += 1

        await self._session.flush()

        clue_name = clue.name
        clue_icon = clue.icon or "🔍"
        logger.info(f"Pista otorgada: user={user_id}, clue={clue_slug}, source={source_fragment_key}")

        return True, f"{clue_icon} ¡Has encontrado: {clue_name}!", inv_item

    async def grant_clue_from_fragment(
        self,
        user_id: int,
        fragment_key: str,
        clue_slug: str
    ) -> tuple[bool, str, Optional[UserInventoryItem]]:
        """
        Otorga una pista cuando el usuario llega a un fragmento.

        Args:
            user_id: ID del usuario
            fragment_key: Key del fragmento donde se encuentra
            clue_slug: Slug de la pista a otorgar

        Returns:
            Tupla (éxito, mensaje, item_en_inventario)
        """
        return await self.grant_clue(user_id, clue_slug, fragment_key)

    # ========================================
    # VERIFICACIÓN DE POSESIÓN
    # ========================================

    async def has_clue(
        self,
        user_id: int,
        clue_slug: str
    ) -> bool:
        """
        Verifica si el usuario tiene una pista específica.

        Args:
            user_id: ID del usuario
            clue_slug: Slug de la pista

        Returns:
            True si tiene la pista
        """
        clue = await self.get_clue_by_slug(clue_slug)
        if clue is None:
            return False

        stmt = select(UserInventoryItem).where(
            and_(
                UserInventoryItem.user_id == user_id,
                UserInventoryItem.item_id == clue.id,
                UserInventoryItem.quantity > 0
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def has_all_clues(
        self,
        user_id: int,
        clue_slugs: List[str]
    ) -> tuple[bool, List[str]]:
        """
        Verifica si el usuario tiene todas las pistas requeridas.

        Args:
            user_id: ID del usuario
            clue_slugs: Lista de slugs de pistas requeridas

        Returns:
            Tupla (tiene_todas, pistas_faltantes)
        """
        missing = []
        for slug in clue_slugs:
            if not await self.has_clue(user_id, slug):
                missing.append(slug)

        return len(missing) == 0, missing

    # ========================================
    # CONSULTA DE PISTAS
    # ========================================

    async def get_clue_by_slug(
        self,
        slug: str
    ) -> Optional[ShopItem]:
        """
        Obtiene una pista por su slug.

        Args:
            slug: Slug del item de pista

        Returns:
            ShopItem o None
        """
        stmt = select(ShopItem).where(
            and_(
                ShopItem.slug == slug,
                ShopItem.item_type == ItemType.NARRATIVE.value,
                ShopItem.is_active == True
            )
        )
        result = await self._session.execute(stmt)
        item = result.scalar_one_or_none()

        # Verificar que es una pista
        if item and item.item_metadata:
            import json
            try:
                metadata = json.loads(item.item_metadata) if isinstance(item.item_metadata, str) else item.item_metadata
                if metadata.get("is_clue", False):
                    return item
            except (json.JSONDecodeError, TypeError):
                pass

        return None

    async def get_all_clues(
        self,
        active_only: bool = True
    ) -> List[ShopItem]:
        """
        Obtiene todas las pistas del sistema.

        Args:
            active_only: Solo pistas activas

        Returns:
            Lista de items de pista
        """
        stmt = select(ShopItem).where(
            ShopItem.item_type == ItemType.NARRATIVE.value
        )
        if active_only:
            stmt = stmt.where(ShopItem.is_active == True)

        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        # Filtrar solo los que son pistas
        clues = []
        import json
        for item in items:
            if item.item_metadata:
                try:
                    metadata = json.loads(item.item_metadata) if isinstance(item.item_metadata, str) else item.item_metadata
                    if metadata.get("is_clue", False):
                        clues.append(item)
                except (json.JSONDecodeError, TypeError):
                    pass

        return clues

    async def get_user_clues(
        self,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """
        Obtiene todas las pistas que tiene un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Lista de diccionarios con info de cada pista
        """
        # Obtener items de inventario del usuario
        stmt = (
            select(UserInventoryItem)
            .options(selectinload(UserInventoryItem.item))
            .where(
                and_(
                    UserInventoryItem.user_id == user_id,
                    UserInventoryItem.quantity > 0
                )
            )
        )
        result = await self._session.execute(stmt)
        inv_items = list(result.scalars().all())

        clues = []
        import json
        for inv_item in inv_items:
            item = inv_item.item
            if item and item.item_type == ItemType.NARRATIVE.value and item.item_metadata:
                try:
                    metadata = json.loads(item.item_metadata) if isinstance(item.item_metadata, str) else item.item_metadata
                    if metadata.get("is_clue", False):
                        clues.append({
                            "slug": item.slug,
                            "name": item.name,
                            "description": item.description,
                            "icon": metadata.get("clue_icon", item.icon or "🔍"),
                            "category": metadata.get("clue_category", "general"),
                            "hint": metadata.get("clue_hint"),
                            "source_fragment": metadata.get("source_fragment_key"),
                            "required_for": metadata.get("required_for_fragments", []),
                            "obtained_at": inv_item.obtained_at,
                            "lore_text": metadata.get("lore_text"),
                        })
                except (json.JSONDecodeError, TypeError):
                    pass

        return clues

    async def get_clues_for_fragment(
        self,
        fragment_key: str
    ) -> List[ShopItem]:
        """
        Obtiene las pistas que desbloquean un fragmento específico.

        Args:
            fragment_key: Key del fragmento bloqueado

        Returns:
            Lista de pistas que lo desbloquean
        """
        all_clues = await self.get_all_clues()
        matching = []

        import json
        for clue in all_clues:
            if clue.item_metadata:
                try:
                    metadata = json.loads(clue.item_metadata) if isinstance(clue.item_metadata, str) else clue.item_metadata
                    required_for = metadata.get("required_for_fragments", [])
                    if fragment_key in required_for:
                        matching.append(clue)
                except (json.JSONDecodeError, TypeError):
                    pass

        return matching

    # ========================================
    # ESTADÍSTICAS
    # ========================================

    async def get_clue_progress(
        self,
        user_id: int,
        chapter_slug: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtiene progreso de recolección de pistas.

        Args:
            user_id: ID del usuario
            chapter_slug: Filtrar por capítulo (opcional)

        Returns:
            Diccionario con estadísticas de progreso
        """
        all_clues = await self.get_all_clues()
        user_clues = await self.get_user_clues(user_id)
        user_clue_slugs = {c["slug"] for c in user_clues}

        # Agrupar por categoría
        by_category: Dict[str, Dict] = {}
        import json
        for clue in all_clues:
            metadata = {}
            if clue.item_metadata:
                try:
                    metadata = json.loads(clue.item_metadata) if isinstance(clue.item_metadata, str) else clue.item_metadata
                except (json.JSONDecodeError, TypeError):
                    pass

            category = metadata.get("clue_category", "general")
            if category not in by_category:
                by_category[category] = {"total": 0, "found": 0}

            by_category[category]["total"] += 1
            if clue.slug in user_clue_slugs:
                by_category[category]["found"] += 1

        return {
            "total_clues": len(all_clues),
            "found_clues": len(user_clues),
            "completion_percent": round(len(user_clues) / len(all_clues) * 100, 1) if all_clues else 100,
            "by_category": by_category,
            "missing_count": len(all_clues) - len(user_clues),
        }

    # ========================================
    # HELPERS PRIVADOS
    # ========================================
    # (Removed _get_or_create_inventory - now using InventoryService)
