"""Utilities for monitoring and logging task progress."""
import asyncio

NO_CHANGE_LOG_INTERVAL = 1.0

def should_log_task_stats(monitor_fn, tasks_created: int, tasks_completed: int) -> bool:
    """Check if task stats should be logged based on changes or time elapsed.
    
    Args:
        monitor_fn: The monitoring function to store state on
        tasks_created: Current count of created tasks
        tasks_completed: Current count of completed tasks
        
    Returns:
        bool: True if stats should be logged
    """
    if not hasattr(monitor_fn, '_last_log_time'):
        monitor_fn._last_log_time = 0
        monitor_fn._last_tasks_created = -1
        monitor_fn._last_tasks_completed = -1
    
    current_time = asyncio.get_event_loop().time()
    counts_changed = (tasks_created != monitor_fn._last_tasks_created or 
                     tasks_completed != monitor_fn._last_tasks_completed)
    
    should_log = counts_changed or (current_time - monitor_fn._last_log_time) >= NO_CHANGE_LOG_INTERVAL
    
    if should_log:
        monitor_fn._last_log_time = current_time
        monitor_fn._last_tasks_created = tasks_created
        monitor_fn._last_tasks_completed = tasks_completed
        
    return should_log
