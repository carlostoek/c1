"""
Tests for ONDA D Services:
- UserLifecycleService
- NotificationPreferencesService
- RiskScoreService
- ReengagementService
"""
import pytest
from unittest.mock import Mock
from datetime import datetime, timedelta

from bot.database.engine import get_session_factory
from bot.database.models import User, UserLifecycle, NotificationPreferences
from bot.database.enums import UserRole
from bot.services.user import UserService
from bot.services.user_lifecycle import UserLifecycleService, LifecycleState
from bot.services.notification_preferences import NotificationPreferencesService

# Common user ID for tests
TEST_USER_ID = 123456789


@pytest.fixture
async def db_session():
    """Fixture to get a clean database session for each test."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session


@pytest.fixture
async def test_user(db_session):
    """Fixture to create a standard test user."""
    user_service = UserService(db_session)
    telegram_user = Mock()
    telegram_user.id = TEST_USER_ID
    telegram_user.username = "lifecycletest"
    telegram_user.first_name = "Lifecycle"
    telegram_user.last_name = "Test"
    
    user = await user_service.get_or_create_user(telegram_user, UserRole.FREE)
    return user


@pytest.mark.asyncio
class TestUserLifecycleService:
    """Tests for the UserLifecycleService."""

    async def test_create_lifecycle_on_first_activity(self, db_session, test_user):
        """Test that a lifecycle record is created on the first update_user_activity call."""
        service = UserLifecycleService(db_session)
        
        # Act
        lifecycle = await service.update_user_activity(test_user.user_id)
        
        # Assert
        assert lifecycle is not None
        assert lifecycle.user_id == test_user.user_id
        assert lifecycle.current_state == LifecycleState.NEW
        assert (datetime.utcnow() - lifecycle.last_activity) < timedelta(seconds=5)

    async def test_update_activity_resets_state_to_active(self, db_session, test_user):
        """Test that user activity resets an at_risk user back to active."""
        service = UserLifecycleService(db_session)
        await service.update_user_activity(test_user.user_id)

        # Arrange: Manually set the user to AT_RISK and make them inactive for 5 days
        lifecycle = await service.get_user_lifecycle(test_user.user_id)
        lifecycle.current_state = LifecycleState.AT_RISK
        lifecycle.last_activity = datetime.utcnow() - timedelta(days=5)
        await db_session.commit()
        
        # Act: Simulate new activity
        updated_lifecycle = await service.update_user_activity(test_user.user_id)

        # Assert
        assert updated_lifecycle.current_state == LifecycleState.ACTIVE
        assert (datetime.utcnow() - updated_lifecycle.last_activity) < timedelta(seconds=5)

    async def test_evaluate_all_users_state_transitions(self, db_session, test_user):
        """Test the state evaluation logic for transitions."""
        service = UserLifecycleService(db_session)
        user = test_user
        
        # 1. NEW to ACTIVE
        user.created_at = datetime.utcnow() - timedelta(days=8)
        await service.update_user_activity(user.user_id)
        await service.evaluate_all_users_state()
        lifecycle = await service.get_user_lifecycle(user.user_id)
        assert lifecycle.current_state == LifecycleState.ACTIVE

        # 2. ACTIVE to AT_RISK
        lifecycle.last_activity = datetime.utcnow() - timedelta(days=5)
        await db_session.commit()
        await service.evaluate_all_users_state()
        lifecycle = await service.get_user_lifecycle(user.user_id)
        assert lifecycle.current_state == LifecycleState.AT_RISK

        # 3. AT_RISK to DORMANT
        lifecycle.last_activity = datetime.utcnow() - timedelta(days=10)
        await db_session.commit()
        await service.evaluate_all_users_state()
        lifecycle = await service.get_user_lifecycle(user.user_id)
        assert lifecycle.current_state == LifecycleState.DORMANT

        # 4. DORMANT to LOST
        lifecycle.last_activity = datetime.utcnow() - timedelta(days=35)
        await db_session.commit()
        await service.evaluate_all_users_state()
        lifecycle = await service.get_user_lifecycle(user.user_id)
        assert lifecycle.current_state == LifecycleState.LOST

    async def test_get_users_by_state(self, db_session, test_user):
        """Test retrieving users by their lifecycle state."""
        service = UserLifecycleService(db_session)
        await service.update_user_activity(test_user.user_id)
        
        # Arrange: Set user to a specific state
        lifecycle = await service.get_user_lifecycle(test_user.user_id)
        lifecycle.current_state = LifecycleState.DORMANT
        await db_session.commit()
        
        # Act
        dormant_users = await service.get_users_by_state(LifecycleState.DORMANT)
        active_users = await service.get_users_by_state(LifecycleState.ACTIVE)
        
        # Assert
        assert len(dormant_users) == 1
        assert dormant_users[0].user_id == test_user.user_id
        assert len(active_users) == 0


@pytest.mark.asyncio
class TestNotificationPreferencesService:
    """Tests for the NotificationPreferencesService."""

    async def test_create_default_preferences(self, db_session, test_user):
        """Test that default preferences are created for a new user."""
        service = NotificationPreferencesService(db_session)
        
        # Act
        prefs = await service.get_preferences(test_user.user_id)
        
        # Assert
        assert prefs is not None
        assert prefs.user_id == test_user.user_id
        assert prefs.content_notifications is True
        assert prefs.reengagement_messages is True
        assert prefs.timezone == "America/Mexico_City"

    async def test_update_preferences(self, db_session, test_user):
        """Test updating user preferences."""
        service = NotificationPreferencesService(db_session)
        
        # Act
        update_data = {
            "content_notifications": False,
            "timezone": "Europe/Madrid"
        }
        await service.update_preferences(test_user.user_id, update_data)
        
        # Assert
        updated_prefs = await service.get_preferences(test_user.user_id)
        assert updated_prefs.content_notifications is False
        assert updated_prefs.streak_reminders is True # Unchanged
        assert updated_prefs.timezone == "Europe/Madrid"

    async def test_is_in_quiet_hours_overnight(self, db_session, test_user):
        """Test quiet hours logic for an overnight period."""
        service = NotificationPreferencesService(db_session)
        await service.update_preferences(test_user.user_id, {
            "quiet_hours_start": 22,
            "quiet_hours_end": 8,
            "timezone": "UTC"
        })
        
        # Mock datetime.now to control the current time
        with pytest.MonkeyPatch.context() as m:
            # Test time inside quiet hours (e.g., 23:00 UTC)
            m.setattr("bot.services.notification_preferences.datetime", Mock(now=lambda tz: datetime(2023, 1, 1, 23, 0, tzinfo=tz)))
            assert await service.is_in_quiet_hours(test_user.user_id) is True
            
            # Test time inside quiet hours (e.g., 04:00 UTC)
            m.setattr("bot.services.notification_preferences.datetime", Mock(now=lambda tz: datetime(2023, 1, 1, 4, 0, tzinfo=tz)))
            assert await service.is_in_quiet_hours(test_user.user_id) is True

            # Test time outside quiet hours (e.g., 15:00 UTC)
            m.setattr("bot.services.notification_preferences.datetime", Mock(now=lambda tz: datetime(2023, 1, 1, 15, 0, tzinfo=tz)))
            assert await service.is_in_quiet_hours(test_user.user_id) is False

    async def test_should_notify(self, db_session, test_user):
        """Test the should_notify logic."""
        service = NotificationPreferencesService(db_session)
        
        # Case 1: Notification type is disabled
        await service.update_preferences(test_user.user_id, {"reengagement_messages": False})
        assert not await service.should_notify(test_user.user_id, "reengagement_messages")
        
        # Case 2: Notification type is enabled, but in quiet hours
        await service.update_preferences(test_user.user_id, {
            "reengagement_messages": True,
            "quiet_hours_start": 0,
            "quiet_hours_end": 23, # All day quiet
            "timezone": "UTC"
        })
        assert not await service.should_notify(test_user.user_id, "reengagement_messages")
        
        # Case 3: All clear
        await service.update_preferences(test_user.user_id, {
            "reengagement_messages": True,
            "quiet_hours_start": 1,
            "quiet_hours_end": 2, # Not quiet now
        })
        assert await service.should_notify(test_user.user_id, "reengagement_messages") is True
