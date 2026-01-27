"""
Message Service Package

Provides centralized message generation with Lucien's voice consistency.

Architecture:
- BaseMessageProvider: Abstract base enforcing stateless interface
- CommonMessages: Shared messages (errors, success, greetings)
- LucienVoiceService: Main service container for all message providers

All providers are stateless: no session/bot stored as instance variables.
All messages use formatters from bot.utils.formatters for dates/numbers.

Usage in handlers:
    from bot.services.container import ServiceContainer

    # Lazy-loaded via ServiceContainer.message property
    msg = container.message.common.error('something failed')
    msg = container.message.common.success('action completed')
"""

from .base import BaseMessageProvider
from .common import CommonMessages

# Direct imports for type hints and external access
from .admin_main import AdminMainMessages
from .admin_vip import AdminVIPMessages
from .admin_free import AdminFreeMessages
from .admin_content import AdminContentMessages
from .user_start import UserStartMessages
from .user_flows import UserFlowMessages
from .user_menu import UserMenuMessages

__all__ = [
    "BaseMessageProvider",
    "CommonMessages",
    "LucienVoiceService",
    "AdminMessages",
    "AdminMainMessages",
    "AdminVIPMessages",
    "AdminFreeMessages",
    "AdminContentMessages",
    "UserMessages",
    "UserStartMessages",
    "UserFlowMessages",
    "UserMenuMessages",
]


class AdminMessages:
    """
    Admin messages namespace for organization.

    Provides access to AdminMainMessages, AdminVIPMessages, AdminFreeMessages, AdminContentMessages.
    Each submenu has its own provider organized by navigation flow.

    Architecture:
        LucienVoiceService
            └─ admin: AdminMessages (this class)
                ├─ main: AdminMainMessages (Phase 2 Plan 03) ✅
                ├─ vip: AdminVIPMessages (Phase 2 Plan 01) ✅
                ├─ free: AdminFreeMessages (Phase 2 Plan 02) ✅
                └─ content: AdminContentMessages (Phase 7 Plan 01) ✅

    Usage:
        container = ServiceContainer(session, bot)

        # Access main menu messages
        text, kb = container.message.admin.main.admin_menu_greeting(is_configured=True)

        # Access VIP messages
        text, kb = container.message.admin.vip.vip_menu(is_configured=True)

        # Access Free messages
        text, kb = container.message.admin.free.free_menu(is_configured=True)

        # Access Content messages
        text, kb = container.message.admin.content.content_menu()

    Stateless Design:
        All sub-providers are lazy-loaded and stateless.
        No session or bot stored as instance variables.
    """

    def __init__(self):
        """
        Initialize admin namespace with lazy-loaded sub-providers.

        Sub-providers created on first access to minimize memory footprint.
        """
        self._main = None
        self._vip = None
        self._free = None
        self._content = None

    @property
    def main(self):
        """
        Main admin menu messages (Phase 2 Plan 03) ✅ COMPLETE.

        Lazy-loaded: creates AdminMainMessages instance on first access.

        Returns:
            AdminMainMessages: Provider for main admin menu messages

        Examples:
            >>> admin = AdminMessages()
            >>> text, kb = admin.main.admin_menu_greeting(is_configured=True)
            >>> '🎩' in text and 'custodio' in text.lower()
            True
        """
        if self._main is None:
            from .admin_main import AdminMainMessages
            self._main = AdminMainMessages()
        return self._main

    @property
    def vip(self):
        """
        VIP admin messages (Phase 2 Plan 01) ✅ COMPLETE.

        Lazy-loaded: creates AdminVIPMessages instance on first access.

        Returns:
            AdminVIPMessages: Provider for VIP management messages

        Examples:
            >>> admin = AdminMessages()
            >>> text, kb = admin.vip.vip_menu(is_configured=True)
            >>> '🎩' in text
            True
        """
        if self._vip is None:
            from .admin_vip import AdminVIPMessages
            self._vip = AdminVIPMessages()
        return self._vip

    @property
    def free(self):
        """
        Free admin messages (Phase 2 Plan 02) ✅ COMPLETE.

        Lazy-loaded: creates AdminFreeMessages instance on first access.

        Returns:
            AdminFreeMessages: Provider for Free channel management messages

        Examples:
            >>> admin = AdminMessages()
            >>> text, kb = admin.free.free_menu(is_configured=True)
            >>> '🎩' in text
            True
        """
        if self._free is None:
            from .admin_free import AdminFreeMessages
            self._free = AdminFreeMessages()
        return self._free

    @property
    def content(self):
        """
        Admin content management messages (Phase 7 Plan 01) ✅ COMPLETE.

        Lazy-loaded: creates AdminContentMessages instance on first access.

        Returns:
            AdminContentMessages: Provider for content management messages

        Examples:
            >>> admin = AdminMessages()
            >>> text, kb = admin.content.content_menu()
            >>> '🎩' in text and 'paquete' in text.lower() or 'contenido' in text.lower()
            True
        """
        if self._content is None:
            from .admin_content import AdminContentMessages
            self._content = AdminContentMessages()
        return self._content


class UserMessages:
    """
    User messages namespace for organization.

    Provides access to UserStartMessages, UserFlowMessages, and UserMenuMessages.
    Each provider organized by user interaction flow.

    Architecture:
        LucienVoiceService
            └─ user: UserMessages (this class)
                ├─ start: UserStartMessages (Phase 3 Plan 01) ✅
                ├─ flows: UserFlowMessages (Phase 3 Plan 02) ✅
                └─ menu: UserMenuMessages (Phase 6 Plan 01) ✅ NEW

    Usage:
        container = ServiceContainer(session, bot)

        # Access /start messages
        text, kb = container.message.user.start.greeting("Juan", is_vip=True, vip_days_remaining=15)

        # Access Free flow messages
        text = container.message.user.flows.free_request_success(wait_time_minutes=30)

        # Access user menu messages
        text, kb = container.message.user.menu.vip_menu_greeting("Juan", vip_expires_at=expiry_date)

    Stateless Design:
        All sub-providers are lazy-loaded and stateless.
        No session or bot stored as instance variables.
    """

    def __init__(self):
        """
        Initialize user namespace with lazy-loaded sub-providers.

        Sub-providers created on first access to minimize memory footprint.
        """
        self._start = None
        self._flows = None
        self._menu = None  # NEW

    @property
    def start(self):
        """
        User start messages (Phase 3 Plan 01) ✅ COMPLETE.

        Lazy-loaded: creates UserStartMessages instance on first access.
        Provides /start greetings with time-of-day variations and role adaptation.

        Returns:
            UserStartMessages: Provider for /start command messages

        Examples:
            >>> user = UserMessages()
            >>> text, kb = user.start.greeting("María", is_vip=True, vip_days_remaining=15)
            >>> '🎩' in text and 'María' in text
            True
        """
        if self._start is None:
            from .user_start import UserStartMessages
            self._start = UserStartMessages()
        return self._start

    @property
    def flows(self):
        """
        User flow messages (Phase 3 Plan 02) ✅ COMPLETE.

        Lazy-loaded: creates UserFlowMessages instance on first access.
        Provides Free channel request flow messages with reassuring tone.

        Returns:
            UserFlowMessages: Provider for user flow messages

        Examples:
            >>> user = UserMessages()
            >>> text = user.flows.free_request_success(30)
            >>> '30 minutos' in text
            True
        """
        if self._flows is None:
            from .user_flows import UserFlowMessages
            self._flows = UserFlowMessages()
        return self._flows

    @property
    def menu(self):
        """
        User menu messages (Phase 6 Plan 01) ✅ NEW.

        Lazy-loaded: creates UserMenuMessages instance on first access.
        Provides VIP and Free user menu messages with Lucien's voice consistency.

        Returns:
            UserMenuMessages: Provider for user menu messages

        Examples:
            >>> user = UserMessages()
            >>> text, kb = user.menu.vip_menu_greeting("Juan", vip_expires_at=datetime.now())
            >>> '🎩' in text and 'círculo exclusivo' in text.lower()
            True
            >>> text, kb = user.menu.free_menu_greeting("Ana", free_queue_position=5)
            >>> 'jardín público' in text.lower()
            True
        """
        if self._menu is None:
            from .user_menu import UserMenuMessages
            self._menu = UserMenuMessages()
        return self._menu


class LucienVoiceService:
    """
    Main message service providing access to all message providers.

    This service is stateless and integrated into ServiceContainer with lazy loading.
    Organizes message providers by navigation flow (admin/, user/) for discoverability.

    Architecture:
        ServiceContainer
            └─ LucienVoiceService (this class)
                ├─ common: CommonMessages ✅
                ├─ admin: AdminMessages ✅ PHASE 2 COMPLETE, PHASE 7 IN PROGRESS
                │   ├─ main: AdminMainMessages ✅
                │   ├─ vip: AdminVIPMessages ✅
                │   ├─ free: AdminFreeMessages ✅
                │   └─ content: AdminContentMessages ✅ NEW (Plan 01)
                └─ user: UserMessages ✅ PHASE 3 COMPLETE, PHASE 6 COMPLETE
                    ├─ start: UserStartMessages ✅ (Plan 01)
                    ├─ flows: UserFlowMessages ✅ (Plan 02)
                    └─ menu: UserMenuMessages ✅ (Plan 01)

    Voice Consistency:
        All providers inherit from BaseMessageProvider which enforces Lucien's voice.
        See docs/guia-estilo.md for complete voice guidelines.

    Stateless Design:
        This service does NOT store session or bot as instance variables.
        All context passed to message methods via parameters.
        Prevents memory leaks and database session leaks.

    Usage:
        container = ServiceContainer(session, bot)

        # Common messages
        error_msg = container.message.common.error('context')

        # Admin main menu
        text, kb = container.message.admin.main.admin_menu_greeting(is_configured=True)

        # Admin VIP messages
        text, kb = container.message.admin.vip.vip_menu(is_configured=True)

        # Admin Free messages
        text, kb = container.message.admin.free.free_menu(is_configured=True)

        # User start messages
        text, kb = container.message.user.start.greeting("Juan", is_vip=True, vip_days_remaining=15)

        # User flow messages
        text = container.message.user.flows.free_request_success(wait_time_minutes=30)

        # User menu messages
        text, kb = container.message.user.menu.vip_menu_greeting(
            user_name="Juan",
            vip_expires_at=expiry_date,
            user_id=user.id,
            session_history=session_ctx
        )
        text, kb = container.message.user.menu.free_menu_greeting(
            user_name="Ana",
            free_queue_position=5,
            user_id=user.id,
            session_history=session_ctx
        )

        # Session-aware messages (prevents repetition)
        session_history = container.message.get_session_context(container)
        text, kb = container.message.user.start.greeting(
            user_name="Juan",
            user_id=user.id,  # Required for session tracking
            session_history=session_history  # Enables context-aware selection
        )
    """

    def __init__(self):
        """
        Initialize message service with lazy-loaded providers.

        Providers are created on first access to minimize memory footprint.
        """
        self._common = None
        self._admin = None
        self._user = None

    @property
    def common(self) -> CommonMessages:
        """
        Common messages provider (errors, success, not_found).

        Lazy-loaded: creates CommonMessages instance on first access.

        Returns:
            CommonMessages: Provider for shared messages
        """
        if self._common is None:
            self._common = CommonMessages()
        return self._common

    @property
    def admin(self) -> AdminMessages:
        """
        Admin messages namespace.

        Lazy-loaded: creates AdminMessages namespace on first access.
        Provides access to admin.main, admin.vip, admin.free sub-providers.

        Returns:
            AdminMessages: Namespace for admin message providers

        Examples:
            >>> service = LucienVoiceService()
            >>> text, kb = service.admin.vip.vip_menu(is_configured=True)
            >>> '🎩' in text
            True
        """
        if self._admin is None:
            self._admin = AdminMessages()
        return self._admin

    @property
    def user(self) -> UserMessages:
        """
        User messages namespace.

        Lazy-loaded: creates UserMessages namespace on first access.
        Provides access to user.start and user.flows sub-providers.

        Returns:
            UserMessages: Namespace for user message providers

        Examples:
            >>> service = LucienVoiceService()
            >>> text, kb = service.user.start.greeting("María", is_vip=True, vip_days_remaining=15)
            >>> '🎩' in text and 'María' in text
            True
            >>> text = service.user.flows.free_request_success(30)
            >>> '30 minutos' in text
            True
        """
        if self._user is None:
            self._user = UserMessages()
        return self._user

    def get_session_context(self, container: "ServiceContainer"):
        """
        Get session history instance from container for passing to providers.

        This is a convenience method for handlers to obtain session history
        and pass it to message provider methods.

        Args:
            container: ServiceContainer instance (has session_history property)

        Returns:
            SessionMessageHistory: Session history service instance

        Usage:
            # In handler
            from bot.services.container import ServiceContainer
            session_ctx = container.message.get_session_context(container)
            text, kb = container.message.user.start.greeting(
                user_name="Juan",
                user_id=user.id,
                session_history=session_ctx
            )
        """
        return container.session_history
