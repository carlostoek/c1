"""
Orquestador de narrativa integrado con gamificación.

Permite crear fragmentos narrativos con recompensas, misiones
y niveles vinculados automáticamente.
"""

from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from bot.narrative.services.fragment import FragmentService
from bot.narrative.database.models import NarrativeFragment, NarrativeChapter

logger = logging.getLogger(__name__)


class NarrativeOrchestrator:
    """Orquestador de narrativa con integración de gamificación."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self._fragment_service = None
        self._reward_orchestrator = None
        self._mission_orchestrator = None

    @property
    def fragment_service(self) -> FragmentService:
        """Lazy load del FragmentService."""
        if self._fragment_service is None:
            self._fragment_service = FragmentService(self.session)
        return self._fragment_service

    @property
    def reward_orchestrator(self):
        """Lazy load del RewardOrchestrator de gamificación."""
        if self._reward_orchestrator is None:
            from bot.gamification.services.orchestrator.reward import RewardOrchestrator
            self._reward_orchestrator = RewardOrchestrator(self.session)
        return self._reward_orchestrator

    @property
    def mission_orchestrator(self):
        """Lazy load del MissionOrchestrator de gamificación."""
        if self._mission_orchestrator is None:
            from bot.gamification.services.orchestrator.mission import MissionOrchestrator
            self._mission_orchestrator = MissionOrchestrator(self.session)
        return self._mission_orchestrator

    async def create_fragment_with_rewards(
        self,
        fragment_data: dict,
        arrival_rewards: Optional[List[dict]] = None,
        decision_rewards: Optional[Dict[str, List[dict]]] = None,
        created_by: int = 0
    ) -> dict:
        """
        Crea fragmento narrativo con recompensas.

        Args:
            fragment_data: Datos del fragmento {
                'chapter_id': int,
                'fragment_key': str,
                'title': str,
                'speaker': str,
                'content': str,
                'visual_hint': Optional[str],
                'order': int,
                'is_entry_point': bool,
                'is_ending': bool
            }
            arrival_rewards: Recompensas otorgadas al llegar al fragmento.
                List[{
                    'name': str,
                    'description': str,
                    'reward_type': RewardType,
                    'metadata': dict
                }]
            decision_rewards: Recompensas por decisión tomada.
                {
                    'decision_key': [reward_data, ...]
                }
            created_by: Admin ID

        Returns:
            {
                'fragment': NarrativeFragment,
                'created_rewards': List[Reward],
                'decision_reward_map': Dict[str, List[Reward]]
            }

        Example:
            >>> result = await orchestrator.create_fragment_with_rewards(
            ...     fragment_data={
            ...         'chapter_id': 1,
            ...         'fragment_key': 'scene_3a',
            ...         'title': 'Respuesta Impulsiva',
            ...         'speaker': 'diana',
            ...         'content': 'Bueno, eso fue... rápido...',
            ...         'order': 3
            ...     },
            ...     arrival_rewards=[
            ...         {
            ...             'name': 'Alma Impulsiva',
            ...             'description': 'Badge por respuesta rápida',
            ...             'reward_type': RewardType.BADGE,
            ...             'metadata': {'icon': '⚡', 'rarity': 'rare'}
            ...         }
            ...     ]
            ... )
        """
        logger.info(f"Creating fragment with rewards: {fragment_data.get('fragment_key')}")

        # 1. Crear fragmento
        fragment = await self.fragment_service.create_fragment(**fragment_data)

        created_rewards = []
        decision_reward_map = {}

        # 2. Crear recompensas por llegada
        if arrival_rewards:
            for reward_data in arrival_rewards:
                try:
                    result = await self.reward_orchestrator.create_reward_with_unlock_condition(
                        reward_data=reward_data,
                        unlock_narrative_fragment=fragment.fragment_key,
                        created_by=created_by
                    )
                    if result.get('reward'):
                        created_rewards.append(result['reward'])
                        logger.info(
                            f"Created arrival reward: {result['reward'].name} "
                            f"for fragment {fragment.fragment_key}"
                        )
                except Exception as e:
                    logger.error(
                        f"Failed to create arrival reward for fragment {fragment.fragment_key}: {e}",
                        exc_info=True
                    )

        # 3. Crear recompensas por decisión
        if decision_rewards:
            for decision_key, rewards in decision_rewards.items():
                decision_reward_map[decision_key] = []
                for reward_data in rewards:
                    try:
                        result = await self.reward_orchestrator.create_reward_with_unlock_condition(
                            reward_data=reward_data,
                            unlock_narrative_decision=decision_key,
                            created_by=created_by
                        )
                        if result.get('reward'):
                            decision_reward_map[decision_key].append(result['reward'])
                            logger.info(
                                f"Created decision reward: {result['reward'].name} "
                                f"for decision {decision_key}"
                            )
                    except Exception as e:
                        logger.error(
                            f"Failed to create decision reward {decision_key}: {e}",
                            exc_info=True
                        )

        logger.info(
            f"Fragment creation completed: {fragment.fragment_key} "
            f"with {len(created_rewards)} arrival rewards and "
            f"{sum(len(r) for r in decision_reward_map.values())} decision rewards"
        )

        return {
            'fragment': fragment,
            'created_rewards': created_rewards,
            'decision_reward_map': decision_reward_map
        }

    async def create_chapter_system(
        self,
        chapter_data: dict,
        fragments: List[dict],
        completion_config: Optional[dict] = None,
        created_by: int = 0
    ) -> dict:
        """
        Crea capítulo completo con sistema de gamificación.

        Args:
            chapter_data: {
                'name': str,
                'slug': str,
                'chapter_type': ChapterType,
                'description': Optional[str]
            }
            fragments: Lista de fragmentos con decisiones
            completion_config: {
                'rewards': List[reward_data],  # Recompensas por completar capítulo
                'unlock_level': dict,  # Nivel a desbloquear
                'grant_besitos': int  # Besitos a otorgar
            }
            created_by: Admin ID

        Returns:
            {
                'chapter': NarrativeChapter,
                'created_fragments': List[NarrativeFragment],
                'completion_rewards': List[Reward],
                'unlocked_level': Optional[Level]
            }

        Example:
            >>> result = await orchestrator.create_chapter_system(
            ...     chapter_data={
            ...         'name': 'Los Kinkys',
            ...         'slug': 'los-kinkys',
            ...         'chapter_type': ChapterType.FREE,
            ...         'description': 'Introducción al mundo de Diana'
            ...     },
            ...     fragments=[...],
            ...     completion_config={
            ...         'rewards': [{
            ...             'name': 'Explorador de Diana',
            ...             'description': 'Completaste Los Kinkys',
            ...             'reward_type': RewardType.BADGE,
            ...             'metadata': {'icon': '🎭', 'rarity': 'epic'}
            ...         }],
            ...         'grant_besitos': 500
            ...     }
            ... )
        """
        from bot.narrative.services.chapter import ChapterService
        from bot.gamification.services.level import LevelService

        logger.info(f"Creating chapter system: {chapter_data.get('name')}")

        chapter_service = ChapterService(self.session)
        level_service = LevelService(self.session)

        # 1. Crear capítulo
        chapter = await chapter_service.create_chapter(**chapter_data)

        # 2. Crear fragmentos
        created_fragments = []
        for fragment_data in fragments:
            fragment_data['chapter_id'] = chapter.id
            fragment = await self.fragment_service.create_fragment(**fragment_data)
            created_fragments.append(fragment)

        logger.info(f"Created {len(created_fragments)} fragments for chapter {chapter.name}")

        completion_rewards = []
        unlocked_level = None

        # 3. Procesar configuración de completado
        if completion_config:
            # Crear recompensas por completar capítulo
            if completion_config.get('rewards'):
                for reward_data in completion_config['rewards']:
                    try:
                        result = await self.reward_orchestrator.create_reward_with_unlock_condition(
                            reward_data=reward_data,
                            unlock_narrative_chapter=chapter.slug,
                            created_by=created_by
                        )
                        if result.get('reward'):
                            completion_rewards.append(result['reward'])
                            logger.info(
                                f"Created completion reward: {result['reward'].name} "
                                f"for chapter {chapter.slug}"
                            )
                    except Exception as e:
                        logger.error(
                            f"Failed to create completion reward for chapter {chapter.slug}: {e}",
                            exc_info=True
                        )

            # Crear nivel desbloqueado al completar
            if completion_config.get('unlock_level'):
                try:
                    level_data = completion_config['unlock_level']
                    unlocked_level = await level_service.create_level(**level_data)
                    logger.info(f"Created unlocked level: {unlocked_level.name}")
                except Exception as e:
                    logger.error(f"Failed to create unlocked level: {e}", exc_info=True)

        logger.info(
            f"Chapter system creation completed: {chapter.name} "
            f"with {len(created_fragments)} fragments, "
            f"{len(completion_rewards)} rewards, "
            f"and {'1 level' if unlocked_level else 'no level'}"
        )

        return {
            'chapter': chapter,
            'created_fragments': created_fragments,
            'completion_rewards': completion_rewards,
            'unlocked_level': unlocked_level
        }

    async def link_existing_reward_to_fragment(
        self,
        reward_id: int,
        fragment_key: str
    ) -> bool:
        """
        Vincula una recompensa existente a un fragmento.

        Actualiza las unlock_conditions de la recompensa para
        requerir llegar al fragmento específico.

        Args:
            reward_id: ID de la recompensa existente
            fragment_key: Key del fragmento

        Returns:
            True si se vinculó correctamente

        Example:
            >>> success = await orchestrator.link_existing_reward_to_fragment(
            ...     reward_id=42,
            ...     fragment_key='scene_5b'
            ... )
        """
        from bot.gamification.services.reward import RewardService
        import json

        reward_service = RewardService(self.session)

        try:
            # Obtener recompensa
            reward = await reward_service.get_reward_by_id(reward_id)
            if not reward:
                logger.error(f"Reward {reward_id} not found")
                return False

            # Actualizar unlock_conditions
            new_condition = {
                'type': 'narrative_fragment',
                'fragment_key': fragment_key
            }

            # Si ya tiene condiciones, crear múltiple
            if reward.unlock_conditions:
                existing = json.loads(reward.unlock_conditions)
                new_condition = {
                    'type': 'multiple',
                    'conditions': [existing, new_condition]
                }

            reward.unlock_conditions = json.dumps(new_condition)
            await self.session.commit()

            logger.info(
                f"Linked reward {reward.name} (ID: {reward_id}) "
                f"to fragment {fragment_key}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to link reward to fragment: {e}", exc_info=True)
            await self.session.rollback()
            return False

    async def create_narrative_mission(
        self,
        mission_data: dict,
        completion_rewards: Optional[List[dict]] = None,
        created_by: int = 0
    ) -> dict:
        """
        Crea misión vinculada a progreso narrativo.

        Args:
            mission_data: {
                'name': str,
                'description': str,
                'mission_type': MissionType,
                'criteria': dict (con datos narrativos),
                'besitos_reward': int
            }
            completion_rewards: Recompensas adicionales al completar
            created_by: Admin ID

        Returns:
            {
                'mission': Mission,
                'created_rewards': List[Reward]
            }

        Example:
            >>> result = await orchestrator.create_narrative_mission(
            ...     mission_data={
            ...         'name': 'Explorador del Diván',
            ...         'description': 'Completa el capítulo El Diván',
            ...         'mission_type': MissionType.ONE_TIME,
            ...         'criteria': {
            ...             'type': 'narrative_chapters',
            ...             'count': 1,
            ...             'specific_chapters': ['el-divan']
            ...         },
            ...         'besitos_reward': 1000
            ...     },
            ...     completion_rewards=[...]
            ... )
        """
        logger.info(f"Creating narrative mission: {mission_data.get('name')}")

        # Delegar a mission_orchestrator
        result = await self.mission_orchestrator.create_mission_with_dependencies(
            mission_data=mission_data,
            rewards_data=completion_rewards,
            created_by=created_by
        )

        logger.info(
            f"Narrative mission created: {result.get('mission').name if result.get('mission') else 'None'}"
        )

        return result
