"""Utilities for pagination of long lists of elements.

This module provides reusable pagination tools for handling large lists of elements
in a paginated format, including keyboard navigation and content formatting.
"""
import math
import re
from typing import List, TypeVar, Generic, Callable, Optional
from dataclasses import dataclass

from aiogram.types import InlineKeyboardMarkup
from bot.utils.keyboards import create_inline_keyboard


T = TypeVar('T')  # Generic type for elements


@dataclass
class Page(Generic[T]):
    """Represents a page of elements.

    This class contains information about a specific page including the items on the page,
    page number, total pages, and navigation properties.

    Attributes:
        items: List of elements in this page
        current_page: Current page number (1-indexed)
        total_pages: Total number of available pages
        total_items: Total number of elements across all pages
        has_previous: Whether there is a previous page
        has_next: Whether there is a next page
        page_size: Number of elements per page
    """

    items: List[T]
    current_page: int
    total_pages: int
    total_items: int
    has_previous: bool
    has_next: bool
    page_size: int

    @property
    def is_empty(self) -> bool:
        """Check if the page is empty.

        Returns:
            True if the page has no items, False otherwise.
        """
        return len(self.items) == 0

    @property
    def start_index(self) -> int:
        """Get the index of the first element in the page (1-indexed).

        Returns:
            The 1-indexed position of the first element in the page,
            or 0 if the page is empty.
        """
        if self.is_empty:
            return 0
        return (self.current_page - 1) * self.page_size + 1

    @property
    def end_index(self) -> int:
        """Get the index of the last element in the page (1-indexed).

        Returns:
            The 1-indexed position of the last element in the page,
            or 0 if the page is empty.
        """
        if self.is_empty:
            return 0
        return self.start_index + len(self.items) - 1


class Paginator(Generic[T]):
    """Generic paginator for lists of elements.

    This class provides pagination functionality for any list of elements,
    allowing navigation between pages and checking pagination properties.

    Usage:
        # Create paginator
        paginator = Paginator(items=my_list, page_size=10)

        # Get specific page
        page = paginator.get_page(page_number=2)

        # Check properties
        if page.has_next:
            next_page = paginator.get_page(page.current_page + 1)

    Attributes:
        items: Complete list of elements to paginate
        page_size: Number of elements per page (default: 10)
    """

    def __init__(self, items: List[T], page_size: int = 10):
        """Initialize the paginator.

        Args:
            items: List of elements to paginate
            page_size: Number of elements per page (default: 10)

        Raises:
            ValueError: If page_size < 1
        """
        if page_size < 1:
            raise ValueError("page_size must be >= 1")

        self.items = items
        self.page_size = page_size
        self.total_items = len(items)
        self.total_pages = max(1, math.ceil(self.total_items / self.page_size))

    def get_page(self, page_number: int) -> Page[T]:
        """Get a specific page.

        Args:
            page_number: Page number (1-indexed)

        Returns:
            Page object containing the elements for that page

        Raises:
            ValueError: If page_number < 1 or > total_pages
        """
        if page_number < 1:
            raise ValueError(f"page_number must be >= 1 (received: {page_number})")

        if page_number > self.total_pages:
            raise ValueError(
                f"page_number must be <= {self.total_pages} (received: {page_number})"
            )

        # Calculate offset and limit
        offset = (page_number - 1) * self.page_size
        limit = self.page_size

        # Extract page items
        page_items = self.items[offset:offset + limit]

        # Determine if there are previous/next pages
        has_previous = page_number > 1
        has_next = page_number < self.total_pages

        return Page(
            items=page_items,
            current_page=page_number,
            total_pages=self.total_pages,
            total_items=self.total_items,
            has_previous=has_previous,
            has_next=has_next,
            page_size=self.page_size
        )

    def get_first_page(self) -> Page[T]:
        """Get the first page.

        Returns:
            The first page of the pagination.
        """
        return self.get_page(1)

    def get_last_page(self) -> Page[T]:
        """Get the last page.

        Returns:
            The last page of the pagination.
        """
        return self.get_page(self.total_pages)


def create_pagination_keyboard(
    page: Page,
    callback_pattern: str,
    additional_buttons: Optional[List[List[dict]]] = None,
    back_callback: str = "admin:main"
) -> InlineKeyboardMarkup:
    """Create a pagination keyboard.

    Generates navigation buttons:
    [◀️ Previous] [Page X/Y] [Next ▶️]

    If there are additional buttons, they are added above the pagination.

    Args:
        page: Page object with pagination info
        callback_pattern: Pattern for navigation callbacks.
            Must contain {page} which will be replaced by the number.
            Example: "vip:subscribers:page:{page}"
        additional_buttons: List of rows of additional buttons (optional)
        back_callback: Callback for "Back" button (default: "admin:main")

    Returns:
        InlineKeyboardMarkup with pagination buttons

    Examples:
        >>> page = Page(items=[...], current_page=2, total_pages=5, ...)
        >>> keyboard = create_pagination_keyboard(
        ...     page=page,
        ...     callback_pattern="vip:subscribers:page:{page}"
        ... )
        # Generates:
        # [◀️ Previous] [Page 2/5] [Next ▶️]
        # [🔙 Back]
    """
    buttons = []

    # Add additional buttons if they exist
    if additional_buttons:
        buttons.extend(additional_buttons)

    # Navigation row
    nav_row = []

    # "Previous" button (only if there's a previous page)
    if page.has_previous:
        prev_callback = callback_pattern.format(page=page.current_page - 1)
        nav_row.append({
            "text": "◀️ Anterior",
            "callback_data": prev_callback
        })

    # Page info button (not clickable, but we need callback)
    # Use special callback that the handler can ignore
    nav_row.append({
        "text": f"Página {page.current_page}/{page.total_pages}",
        "callback_data": f"pagination:info:{page.current_page}"
    })

    # "Next" button (only if there's a next page)
    if page.has_next:
        next_callback = callback_pattern.format(page=page.current_page + 1)
        nav_row.append({
            "text": "Siguiente ▶️",
            "callback_data": next_callback
        })

    # Add navigation row only if it's not empty
    if nav_row:
        buttons.append(nav_row)

    # "Back" button
    buttons.append([{"text": "🔙 Volver", "callback_data": back_callback}])

    return create_inline_keyboard(buttons)


def format_page_header(page: Page, title: str) -> str:
    """Format a header for a paginated page.

    Args:
        page: Page object with pagination info
        title: Title of the list

    Returns:
        HTML formatted string with header

    Examples:
        >>> page = Page(items=[...], current_page=2, total_pages=5, total_items=47, ...)
        >>> header = format_page_header(page, "VIP Subscribers")
        # Output:
        # 📋 <b>VIP Subscribers</b>
        #
        # <b>Total:</b> 47 elements
        # <b>Page:</b> 2/5 (showing 11-20)
    """
    if page.is_empty:
        return (
            f"📋 <b>{title}</b>\n\n"
            f"<i>No hay elementos para mostrar.</i>"
        )

    header = f"📋 <b>{title}</b>\n\n"
    header += f"<b>Total:</b> {page.total_items} elementos\n"
    header += f"<b>Página:</b> {page.current_page}/{page.total_pages}"

    # Add range of elements if there are items
    if not page.is_empty:
        header += f" (mostrando {page.start_index}-{page.end_index})"

    return header


def format_items_list(
    items: List[T],
    formatter: Callable[[T, int], str],
    separator: str = "\n"
) -> str:
    """Format a list of elements using a custom formatter.

    Args:
        items: List of elements to format
        formatter: Function that takes (item, index) and returns string
            - item: Element to format
            - index: Index in the page (1-indexed)
        separator: Separator between elements (default: newline)

    Returns:
        String with all formatted elements

    Examples:
        >>> def format_subscriber(sub, idx):
        ...     return f"{idx}. User {sub.user_id} - {sub.days_remaining} days"
        >>>
        >>> formatted = format_items_list(subscribers, format_subscriber)
        # Output:
        # 1. User 123456 - 15 days
        # 2. User 789012 - 8 days
        # ...
    """
    if not items:
        return ""

    formatted_items = []
    for idx, item in enumerate(items, start=1):
        formatted_item = formatter(item, idx)
        formatted_items.append(formatted_item)

    return separator.join(formatted_items)


# ===== COMMON CASE HELPERS =====

def paginate_query_results(
    results: List[T],
    page_number: int,
    page_size: int = 10
) -> Page[T]:
    """Helper to paginate query results.

    Typical usage:
        # Get all results from DB
        all_subscribers = await session.execute(query)
        results = all_subscribers.scalars().all()

        # Paginate
        page = paginate_query_results(results, page_number=2, page_size=10)

    Args:
        results: Complete list of results
        page_number: Desired page number (1-indexed)
        page_size: Elements per page (default: 10)

    Returns:
        Page object with elements for that page
    """
    paginator = Paginator(items=results, page_size=page_size)
    return paginator.get_page(page_number)


def extract_page_from_callback(callback_data: str, pattern: str) -> int:
    """Extract page number from callback data.

    Args:
        callback_data: Callback string (e.g., "vip:subscribers:page:3")
        pattern: Expected pattern with {page} as placeholder
            (e.g., "vip:subscribers:page:{page}")

    Returns:
        Extracted page number (1-indexed)

    Raises:
        ValueError: If page number cannot be extracted

    Examples:
        >>> extract_page_from_callback(
        ...     "vip:subscribers:page:3",
        ...     "vip:subscribers:page:{page}"
        ... )
        3
    """
    # Convert pattern to regex
    # Escape the pattern and then replace {page} with regex
    regex_pattern = re.escape(pattern)
    regex_pattern = regex_pattern.replace(r"\{page\}", r"(\d+)")

    match = re.match(regex_pattern, callback_data)

    if not match:
        raise ValueError(
            f"Callback data '{callback_data}' does not match pattern '{pattern}'"
        )

    page_str = match.group(1)

    try:
        page_number = int(page_str)
        if page_number < 1:
            raise ValueError(f"Invalid page number: {page_number}")
        return page_number
    except ValueError as e:
        raise ValueError(f"Could not parse page number: {e}")
