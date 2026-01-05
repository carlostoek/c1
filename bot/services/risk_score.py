"""
Service for calculating user churn risk score (ONDA D).

- Calculates a risk score (0-100) based on multiple factors.
- Identifies users at high risk of churning.
- Provides detailed risk factors for analysis.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.database.models import User, UserLifecycle, VIPSubscriber
# TODO: Import gamification models when they are clear
# from bot.gamification.database.models import UserGamificationStats, MissionAttempt

logger = logging.getLogger(__name__)


@dataclass
class RiskFactor:
    """Represents a single factor contributing to the churn risk score."""
    name: str
    value: int  # The score for this factor (e.g., 15)
    weight: int # The maximum possible score for this factor (e.g., 25)
    details: str


class RiskScoreService:
    """Calculates and manages user churn risk scores."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_risk_factors(self, user_id: int) -> List[RiskFactor]:
        """
        Calculates the individual risk factors for a given user.
        """
        factors = []
        
        lifecycle = await self.session.get(UserLifecycle, user_id, options=[selectinload(UserLifecycle.user)])
        if not lifecycle:
            return []

        # 1. Días inactivo (Weight: 25%)
        days_inactive = (datetime.utcnow() - lifecycle.last_activity).days
        inactive_score = min(int(days_inactive * 2.5), 25)
        factors.append(RiskFactor("Días inactivo", inactive_score, 25, f"{days_inactive} días sin actividad."))

        # 2. Streak roto (Weight: 15%) - Placeholder
        # Depends on Gamification module
        # streak_roto_score = await self._calculate_broken_streak_score(user_id)
        streak_roto_score = 0
        factors.append(RiskFactor("Streak roto", streak_roto_score, 15, "Placeholder: Lógica no implementada."))

        # 3. Misiones abandonadas (Weight: 15%) - Placeholder
        # Depends on Gamification module
        # abandoned_mission_score = await self._calculate_abandoned_mission_score(user_id)
        abandoned_mission_score = 0
        factors.append(RiskFactor("Misiones abandonadas", abandoned_mission_score, 15, "Placeholder: Lógica no implementada."))

        # 4. Declive de actividad (Weight: 15%) - Placeholder
        # Depends on activity tracking over time
        activity_decline_score = 0
        factors.append(RiskFactor("Declive de actividad", activity_decline_score, 15, "Placeholder: Lógica no implementada."))

        # 5. VIP por expirar (Weight: 15%)
        vip_expiring_score, vip_expiring_score_details = await self._calculate_vip_expiring_score(user_id)
        factors.append(RiskFactor("VIP por expirar", vip_expiring_score, 15, vip_expiring_score_details))

        # 6. Onboarding incompleto (Weight: 10%) - Placeholder
        # Depends on Narrative/Gamification progress
        # onboarding_score = await self._calculate_onboarding_score(user_id)
        onboarding_score = 0
        factors.append(RiskFactor("Onboarding incompleto", onboarding_score, 10, "Placeholder: Lógica no implementada."))

        # 7. Sin compras (Weight: 5%) - Placeholder
        # Depends on Shop module
        # no_purchases_score = await self._calculate_no_purchases_score(user_id)
        no_purchases_score = 0
        factors.append(RiskFactor("Sin compras", no_purchases_score, 5, "Placeholder: Lógica no implementada."))

        return factors

    async def _calculate_vip_expiring_score(self, user_id: int) -> tuple[int, str]:
        """Calculates risk score based on VIP subscription expiring soon."""
        subscriber = await self.session.get(VIPSubscriber, user_id)
        if not subscriber or subscriber.status != 'active':
            return 0, "No es un suscriptor VIP activo."
        
        days_left = (subscriber.expiry_date - datetime.utcnow()).days
        if 0 <= days_left <= 5:
            return 15, f"La suscripción VIP expira en {days_left} días."
        
        return 0, f"La suscripción VIP expira en {days_left} días."

    async def calculate_risk_score(self, user_id: int) -> int:
        """
        Calculates the total churn risk score for a user and updates the lifecycle record.
        """
        factors = await self.get_risk_factors(user_id)
        total_score = sum(factor.value for factor in factors)
        
        lifecycle = await self.session.get(UserLifecycle, user_id)
        if lifecycle:
            lifecycle.risk_score = total_score
            await self.session.commit()
            logger.info(f"Calculated risk score for user {user_id}: {total_score}")

        return total_score

    async def get_high_risk_users(self, threshold: int = 70) -> List[User]:
        """
        Retrieves all users with a risk score above a certain threshold.
        """
        stmt = (
            select(User)
            .join(UserLifecycle)
            .where(UserLifecycle.risk_score >= threshold)
            .order_by(UserLifecycle.risk_score.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_all_risk_scores(self) -> int:
        """
        Recalculates the risk score for all active users.
        Intended for a periodic background task.
        Returns the number of users processed.
        """
        logger.info("Starting batch update of all user risk scores...")
        stmt = select(User.user_id).where(User.role != 'admin')
        result = await self.session.execute(stmt)
        user_ids = result.scalars().all()

        for user_id in user_ids:
            await self.calculate_risk_score(user_id)
        
        logger.info(f"Finished updating risk scores for {len(user_ids)} users.")
        return len(user_ids)
