"""
Service for managing the user lifecycle (ONDA D).

- Tracks user activity and state (new, active, at_risk, dormant, lost).
- Updates user state based on inactivity.
- Provides data for re-engagement campaigns.
"""
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.database.models import User, UserLifecycle

logger = logging.getLogger(__name__)


class LifecycleState(str, Enum):
    """Enumeration for user lifecycle states."""
    NEW = "new"            # 0-7 days from registration and active
    ACTIVE = "active"      # Activity in the last 3 days
    AT_RISK = "at_risk"    # 4-7 days of inactivity
    DORMANT = "dormant"    # 8-30 days of inactivity
    LOST = "lost"          # 30+ days of inactivity


class UserLifecycleService:
    """Manages the lifecycle of users."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_lifecycle(self, user_id: int) -> Optional[UserLifecycle]:
        """Retrieves the lifecycle record for a specific user."""
        return await self.session.get(UserLifecycle, user_id)

    async def update_user_activity(self, user_id: int) -> UserLifecycle:
        """
        Updates the last activity timestamp for a user and resets their state to active.
        Creates a lifecycle record if one doesn't exist.
        """
        lifecycle = await self.get_user_lifecycle(user_id)
        now = datetime.utcnow()

        if not lifecycle:
            user = await self.session.get(User, user_id)
            if not user:
                raise ValueError(f"User with id {user_id} not found.")

            lifecycle = UserLifecycle(
                user_id=user_id,
                last_activity=now,
                current_state=LifecycleState.NEW,
                state_changed_at=now,
                risk_score=0,
            )
            self.session.add(lifecycle)
            logger.info(f"Created new lifecycle record for user {user_id}.")
        else:
            # If user was at risk or dormant, their activity makes them active again
            if lifecycle.current_state in [LifecycleState.AT_RISK, LifecycleState.DORMANT, LifecycleState.LOST]:
                logger.info(f"User {user_id} returned from {lifecycle.current_state}. Welcome back!")
                await self.transition_state(user_id, LifecycleState.ACTIVE, lifecycle)
            # If user is new, check if they should transition to active
            elif lifecycle.current_state == LifecycleState.NEW:
                days_since_creation = (now - lifecycle.user.created_at).days
                if days_since_creation > 7:
                    await self.transition_state(user_id, LifecycleState.ACTIVE, lifecycle)
        
        lifecycle.last_activity = now
        await self.session.commit()
        return lifecycle

    async def calculate_days_inactive(self, user_id: int) -> int:
        """Calculates how many days a user has been inactive."""
        lifecycle = await self.get_user_lifecycle(user_id)
        if not lifecycle:
            return 0
        
        delta = datetime.utcnow() - lifecycle.last_activity
        return delta.days

    async def get_user_state(self, user_id: int) -> Optional[LifecycleState]:
        """Gets the current lifecycle state of a user."""
        lifecycle = await self.get_user_lifecycle(user_id)
        if not lifecycle:
            return None
        return LifecycleState(lifecycle.current_state)

    async def transition_state(self, user_id: int, new_state: LifecycleState, lifecycle: Optional[UserLifecycle] = None):
        """Transitions a user to a new lifecycle state."""
        if not lifecycle:
            lifecycle = await self.get_user_lifecycle(user_id)
        
        if not lifecycle:
            logger.warning(f"Cannot transition state for non-existent lifecycle record for user {user_id}.")
            return

        if lifecycle.current_state != new_state.value:
            logger.info(f"Transitioning user {user_id} from {lifecycle.current_state} to {new_state.value}")
            lifecycle.current_state = new_state.value
            lifecycle.state_changed_at = datetime.utcnow()
            # We don't commit here, it will be committed by the calling method.

    async def get_users_by_state(self, state: LifecycleState) -> List[User]:
        """
        Retrieves all users currently in a specific lifecycle state.
        """
        stmt = select(User).join(UserLifecycle).where(UserLifecycle.current_state == state.value)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def evaluate_all_users_state(self) -> int:
        """
        Evaluates and updates the lifecycle state for all users.
        This is intended to be run as a periodic background task.
        Returns the number of users that transitioned.
        """
        logger.info("Starting evaluation of all user lifecycle states...")
        stmt = select(UserLifecycle).options(selectinload(UserLifecycle.user))
        result = await self.session.execute(stmt)
        all_lifecycles = result.scalars().all()
        
        count = 0
        for lifecycle in all_lifecycles:
            days_inactive = (datetime.utcnow() - lifecycle.last_activity).days
            # Eager loaded user object from the initial query
            user_creation_date = lifecycle.user.created_at
            days_since_creation = (datetime.utcnow() - user_creation_date).days
            
            new_state = None
            current_state = LifecycleState(lifecycle.current_state)

            if days_inactive >= 31:
                if current_state != LifecycleState.LOST:
                    new_state = LifecycleState.LOST
            elif 8 <= days_inactive <= 30:
                if current_state != LifecycleState.DORMANT:
                    new_state = LifecycleState.DORMANT
            elif 4 <= days_inactive <= 7:
                if current_state != LifecycleState.AT_RISK:
                    new_state = LifecycleState.AT_RISK
            elif days_inactive <= 3:
                # User is active
                if days_since_creation > 7:
                    if current_state != LifecycleState.ACTIVE:
                        new_state = LifecycleState.ACTIVE
                else: # User is new
                    if current_state != LifecycleState.NEW:
                        new_state = LifecycleState.NEW
            
            if new_state:
                await self.transition_state(lifecycle.user_id, new_state, lifecycle)
                count += 1
        
        if count > 0:
            await self.session.commit()
            
        logger.info(f"Finished evaluating user states. {count} users transitioned.")
        return count
