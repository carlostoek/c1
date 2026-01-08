"""
Servicio de Panel de Configuración Central.

Centraliza estadísticas y gestión de objetos cross-module:
- Gamificación (misiones, recompensas, niveles)
- Tienda (categorías, items, ventas)
- Narrativa (capítulos, fragmentos, progreso)

Fase 5 de la integración cross-module.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, UTC, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ConfigurationPanelService:
    """Servicio centralizado de estadísticas cross-module."""

    def __init__(self, session: AsyncSession):
        """
        Inicializa servicio.

        Args:
            session: Sesión async de SQLAlchemy
        """
        self._session = session

    # ========================================
    # ESTADÍSTICAS GAMIFICACIÓN
    # ========================================

    async def get_gamification_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del módulo de gamificación.

        Returns:
            Dict con estadísticas de misiones, recompensas, niveles
        """
        try:
            from bot.gamification.database.models import (
                Mission, Reward, Level, UserGamification
            )

            # Contar misiones activas
            stmt = select(func.count()).select_from(Mission).where(Mission.active == True)
            result = await self._session.execute(stmt)
            missions_count = result.scalar() or 0

            # Contar recompensas activas
            stmt = select(func.count()).select_from(Reward).where(Reward.active == True)
            result = await self._session.execute(stmt)
            rewards_count = result.scalar() or 0

            # Contar niveles
            stmt = select(func.count()).select_from(Level)
            result = await self._session.execute(stmt)
            levels_count = result.scalar() or 0

            # Contar usuarios con perfil de gamificación
            stmt = select(func.count()).select_from(UserGamification)
            result = await self._session.execute(stmt)
            users_count = result.scalar() or 0

            # Total de besitos en circulación
            stmt = select(func.sum(UserGamification.total_besitos)).select_from(UserGamification)
            result = await self._session.execute(stmt)
            total_besitos = result.scalar() or 0

            return {
                "module": "gamification",
                "missions_active": missions_count,
                "rewards_active": rewards_count,
                "levels_count": levels_count,
                "users_with_profile": users_count,
                "total_besitos_circulation": total_besitos,
                "status": "ok"
            }

        except Exception as e:
            logger.error(f"Error getting gamification stats: {e}")
            return {
                "module": "gamification",
                "status": "error",
                "error": str(e)
            }

    # ========================================
    # ESTADÍSTICAS TIENDA
    # ========================================

    async def get_shop_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del módulo de tienda.

        Returns:
            Dict con estadísticas de categorías, items, ventas
        """
        try:
            from bot.shop.database.models import (
                ItemCategory, ShopItem, ItemPurchase, UserInventory
            )
            from bot.shop.database.enums import PurchaseStatus

            # Contar categorías activas
            stmt = select(func.count()).select_from(ItemCategory).where(ItemCategory.is_active == True)
            result = await self._session.execute(stmt)
            categories_count = result.scalar() or 0

            # Contar items activos
            stmt = select(func.count()).select_from(ShopItem).where(ShopItem.is_active == True)
            result = await self._session.execute(stmt)
            items_count = result.scalar() or 0

            # Contar compras completadas
            stmt = select(func.count()).select_from(ItemPurchase).where(
                ItemPurchase.status == PurchaseStatus.COMPLETED.value
            )
            result = await self._session.execute(stmt)
            purchases_count = result.scalar() or 0

            # Revenue total
            stmt = select(func.sum(ItemPurchase.price_paid)).where(
                ItemPurchase.status == PurchaseStatus.COMPLETED.value
            )
            result = await self._session.execute(stmt)
            total_revenue = result.scalar() or 0

            # Usuarios con inventario
            stmt = select(func.count()).select_from(UserInventory)
            result = await self._session.execute(stmt)
            users_with_inventory = result.scalar() or 0

            return {
                "module": "shop",
                "categories_active": categories_count,
                "items_active": items_count,
                "total_purchases": purchases_count,
                "total_revenue": total_revenue,
                "users_with_inventory": users_with_inventory,
                "status": "ok"
            }

        except Exception as e:
            logger.error(f"Error getting shop stats: {e}")
            return {
                "module": "shop",
                "status": "error",
                "error": str(e)
            }

    # ========================================
    # ESTADÍSTICAS NARRATIVA
    # ========================================

    async def get_narrative_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del módulo narrativo.

        Returns:
            Dict con estadísticas de capítulos, fragmentos, progreso
        """
        try:
            from bot.narrative.database import (
                NarrativeChapter, NarrativeFragment, UserNarrativeProgress
            )

            # Contar capítulos activos
            stmt = select(func.count()).select_from(NarrativeChapter).where(
                NarrativeChapter.is_active == True
            )
            result = await self._session.execute(stmt)
            chapters_count = result.scalar() or 0

            # Contar fragmentos activos
            stmt = select(func.count()).select_from(NarrativeFragment).where(
                NarrativeFragment.is_active == True
            )
            result = await self._session.execute(stmt)
            fragments_count = result.scalar() or 0

            # Usuarios con progreso narrativo
            stmt = select(func.count(func.distinct(UserNarrativeProgress.user_id))).select_from(
                UserNarrativeProgress
            )
            result = await self._session.execute(stmt)
            users_with_progress = result.scalar() or 0

            # Capítulos completados (total - suma de todos los usuarios)
            stmt = select(func.sum(UserNarrativeProgress.chapters_completed)).select_from(
                UserNarrativeProgress
            )
            result = await self._session.execute(stmt)
            chapters_completed = result.scalar() or 0

            return {
                "module": "narrative",
                "chapters_active": chapters_count,
                "fragments_active": fragments_count,
                "users_with_progress": users_with_progress,
                "chapters_completed_total": chapters_completed,
                "status": "ok"
            }

        except Exception as e:
            logger.error(f"Error getting narrative stats: {e}")
            return {
                "module": "narrative",
                "status": "error",
                "error": str(e)
            }

    # ========================================
    # RESUMEN GLOBAL
    # ========================================

    async def get_global_summary(self) -> Dict[str, Any]:
        """
        Obtiene resumen global de todos los módulos.

        Returns:
            Dict con estadísticas de todos los módulos
        """
        gamif_stats = await self.get_gamification_stats()
        shop_stats = await self.get_shop_stats()
        narrative_stats = await self.get_narrative_stats()

        # Calcular health general
        modules_ok = sum([
            1 if gamif_stats.get('status') == 'ok' else 0,
            1 if shop_stats.get('status') == 'ok' else 0,
            1 if narrative_stats.get('status') == 'ok' else 0
        ])

        health = "healthy" if modules_ok == 3 else "degraded" if modules_ok > 0 else "unhealthy"

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "health": health,
            "modules_status": {
                "gamification": gamif_stats.get('status', 'unknown'),
                "shop": shop_stats.get('status', 'unknown'),
                "narrative": narrative_stats.get('status', 'unknown')
            },
            "gamification": gamif_stats,
            "shop": shop_stats,
            "narrative": narrative_stats,
            "totals": {
                "missions": gamif_stats.get('missions_active', 0),
                "rewards": gamif_stats.get('rewards_active', 0),
                "levels": gamif_stats.get('levels_count', 0),
                "shop_items": shop_stats.get('items_active', 0),
                "chapters": narrative_stats.get('chapters_active', 0),
                "fragments": narrative_stats.get('fragments_active', 0)
            }
        }

    # ========================================
    # LISTADOS CROSS-MODULE
    # ========================================

    async def get_all_missions(
        self,
        active_only: bool = True,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Lista todas las misiones con información resumida.

        Args:
            active_only: Solo activas
            limit: Límite de resultados
            offset: Desplazamiento

        Returns:
            Lista de misiones con info básica
        """
        try:
            from bot.gamification.database.models import Mission

            stmt = select(Mission).order_by(Mission.created_at.desc())

            if active_only:
                stmt = stmt.where(Mission.active == True)

            stmt = stmt.limit(limit).offset(offset)

            result = await self._session.execute(stmt)
            missions = result.scalars().all()

            return [
                {
                    "id": m.id,
                    "name": m.name,
                    "type": m.mission_type,
                    "besitos_reward": m.besitos_reward,
                    "is_active": m.active,
                    "module": "gamification"
                }
                for m in missions
            ]

        except Exception as e:
            logger.error(f"Error listing missions: {e}")
            return []

    async def get_all_rewards(
        self,
        active_only: bool = True,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Lista todas las recompensas con información resumida.

        Args:
            active_only: Solo activas
            limit: Límite de resultados
            offset: Desplazamiento

        Returns:
            Lista de recompensas con info básica
        """
        try:
            from bot.gamification.database.models import Reward

            stmt = select(Reward).order_by(Reward.created_at.desc())

            if active_only:
                stmt = stmt.where(Reward.active == True)

            stmt = stmt.limit(limit).offset(offset)

            result = await self._session.execute(stmt)
            rewards = result.scalars().all()

            return [
                {
                    "id": r.id,
                    "name": r.name,
                    "type": r.reward_type,
                    "is_active": r.active,
                    "module": "gamification"
                }
                for r in rewards
            ]

        except Exception as e:
            logger.error(f"Error listing rewards: {e}")
            return []

    async def get_all_shop_items(
        self,
        active_only: bool = True,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Lista todos los items de tienda con información resumida.

        Args:
            active_only: Solo activos
            limit: Límite de resultados
            offset: Desplazamiento

        Returns:
            Lista de items con info básica
        """
        try:
            from bot.shop.database.models import ShopItem

            stmt = select(ShopItem).order_by(ShopItem.created_at.desc())

            if active_only:
                stmt = stmt.where(ShopItem.is_active == True)

            stmt = stmt.limit(limit).offset(offset)

            result = await self._session.execute(stmt)
            items = result.scalars().all()

            return [
                {
                    "id": i.id,
                    "name": i.name,
                    "icon": i.icon,
                    "price": i.price_besitos,
                    "is_active": i.is_active,
                    "module": "shop"
                }
                for i in items
            ]

        except Exception as e:
            logger.error(f"Error listing shop items: {e}")
            return []

    async def get_all_chapters(
        self,
        active_only: bool = True,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Lista todos los capítulos narrativos con información resumida.

        Args:
            active_only: Solo activos
            limit: Límite de resultados
            offset: Desplazamiento

        Returns:
            Lista de capítulos con info básica
        """
        try:
            from bot.narrative.database import NarrativeChapter

            stmt = select(NarrativeChapter).order_by(NarrativeChapter.order)

            if active_only:
                stmt = stmt.where(NarrativeChapter.is_active == True)

            stmt = stmt.limit(limit).offset(offset)

            result = await self._session.execute(stmt)
            chapters = result.scalars().all()

            return [
                {
                    "id": c.id,
                    "name": c.name,
                    "slug": c.slug,
                    "type": c.chapter_type.value if hasattr(c.chapter_type, 'value') else str(c.chapter_type),
                    "order": c.order,
                    "is_active": c.is_active,
                    "module": "narrative"
                }
                for c in chapters
            ]

        except Exception as e:
            logger.error(f"Error listing chapters: {e}")
            return []

    # ========================================
    # ACCIONES RÁPIDAS
    # ========================================

    async def toggle_mission_active(self, mission_id: int) -> bool:
        """Alterna estado activo de una misión."""
        try:
            from bot.gamification.database.models import Mission

            mission = await self._session.get(Mission, mission_id)
            if not mission:
                return False

            mission.active = not mission.active
            await self._session.commit()

            logger.info(f"Mission {mission_id} toggled to active={mission.active}")
            return True

        except Exception as e:
            logger.error(f"Error toggling mission: {e}")
            return False

    async def toggle_reward_active(self, reward_id: int) -> bool:
        """Alterna estado activo de una recompensa."""
        try:
            from bot.gamification.database.models import Reward

            reward = await self._session.get(Reward, reward_id)
            if not reward:
                return False

            reward.active = not reward.active
            await self._session.commit()

            logger.info(f"Reward {reward_id} toggled to active={reward.active}")
            return True

        except Exception as e:
            logger.error(f"Error toggling reward: {e}")
            return False

    async def toggle_shop_item_active(self, item_id: int) -> bool:
        """Alterna estado activo de un item de tienda."""
        try:
            from bot.shop.database.models import ShopItem

            item = await self._session.get(ShopItem, item_id)
            if not item:
                return False

            item.is_active = not item.is_active
            await self._session.commit()

            logger.info(f"ShopItem {item_id} toggled to active={item.is_active}")
            return True

        except Exception as e:
            logger.error(f"Error toggling shop item: {e}")
            return False

    async def toggle_chapter_active(self, chapter_id: int) -> bool:
        """Alterna estado activo de un capítulo narrativo."""
        try:
            from bot.narrative.database import NarrativeChapter

            chapter = await self._session.get(NarrativeChapter, chapter_id)
            if not chapter:
                return False

            chapter.is_active = not chapter.is_active
            await self._session.commit()

            logger.info(f"Chapter {chapter_id} toggled to active={chapter.is_active}")
            return True

        except Exception as e:
            logger.error(f"Error toggling chapter: {e}")
            return False

    # ========================================
    # FORMATO PARA TELEGRAM
    # ========================================

    async def get_dashboard_text(self) -> str:
        """
        Genera texto formateado del dashboard para Telegram.

        Returns:
            String HTML con el dashboard
        """
        summary = await self.get_global_summary()

        # Determinar emoji de salud
        health_emoji = {
            "healthy": "🟢",
            "degraded": "🟡",
            "unhealthy": "🔴"
        }.get(summary['health'], "⚪")

        text = f"""📊 <b>Panel de Configuración Central</b>

{health_emoji} <b>Estado del Sistema:</b> {summary['health'].upper()}

━━━━━━━━━━━━━━━━━━━━

🎮 <b>GAMIFICACIÓN</b>
• Misiones activas: {summary['gamification'].get('missions_active', 0)}
• Recompensas: {summary['gamification'].get('rewards_active', 0)}
• Niveles: {summary['gamification'].get('levels_count', 0)}
• Usuarios: {summary['gamification'].get('users_with_profile', 0)}
• Besitos en circulación: {summary['gamification'].get('total_besitos_circulation', 0):,}

━━━━━━━━━━━━━━━━━━━━

🛒 <b>TIENDA</b>
• Categorías: {summary['shop'].get('categories_active', 0)}
• Items activos: {summary['shop'].get('items_active', 0)}
• Compras totales: {summary['shop'].get('total_purchases', 0)}
• Revenue total: {summary['shop'].get('total_revenue', 0):,} besitos

━━━━━━━━━━━━━━━━━━━━

📖 <b>NARRATIVA</b>
• Capítulos: {summary['narrative'].get('chapters_active', 0)}
• Fragmentos: {summary['narrative'].get('fragments_active', 0)}
• Usuarios con progreso: {summary['narrative'].get('users_with_progress', 0)}
• Capítulos completados: {summary['narrative'].get('chapters_completed_total', 0)}

━━━━━━━━━━━━━━━━━━━━

<i>Última actualización: {datetime.now(UTC).strftime('%H:%M:%S UTC')}</i>
"""

        return text
