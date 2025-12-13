"""
Background Tasks - Module for automatic scheduled tasks.

Exports functions to start and stop the scheduler.
"""
from bot.background.tasks import (
    start_background_tasks,
    stop_background_tasks,
    get_scheduler_status
)

__all__ = [
    "start_background_tasks",
    "stop_background_tasks",
    "get_scheduler_status"
]
