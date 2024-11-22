import uuid
from typing import Any, Collection, Dict, Optional, Set, Union

from job import JobABC


class Task:
    def __init__(self, data: Dict[str, Any]):
        self._data = data
        self.jobchain_unique_id = str(uuid.uuid4())

    def __getattr__(self, key: str) -> Any:
        return self._data[key]

    def __setattr__(self, key: str, value: Any) -> None:
        if key == '_data' or key == 'jobchain_unique_id':
            super().__setattr__(key, value)
        else:
            self._data[key] = value

    def __repr__(self) -> str:
        return f"Task(data={self._data}, jobchain_unique_id={self.jobchain_unique_id})"
    
    def __eq__(self, other: object) -> bool:
        """
        Define equality based on jobchain_unique_id for proper Set operations.
        Two Tasks are considered equal if they have the same jobchain_unique_id.
        """
        if not isinstance(other, Task):
            return NotImplemented
        return self.jobchain_unique_id == other.jobchain_unique_id

    def __hash__(self) -> int:
        """
        Define hashing based on jobchain_unique_id for proper Set operations.
        This ensures Tasks with the same ID are treated as identical in Sets.
        """
        return hash(self.jobchain_unique_id)


class JobMonitor:
    """
    Monitors the progress of tasks within a job, tracking which tasks are completed
    and which are still pending.
    """
    name: str  # this should be equal to the name of the topmost Job in the Jobs graph.
    tasks_to_do: Set[Task]  # Set of pending tasks
    tasks_done: Set[Task]  # Set of completed tasks

    def __init__(self, job_name: str, tasks_to_do: Optional[Union[Task, Collection[Task]]] = None):
        """
        Initialize the JobMonitor with a job name and optional tasks to monitor.

        Args:
            job_name: Name of the topmost Job in the Jobs graph
            tasks_to_do: Optional single Task or collection of Tasks to monitor. If None, starts with empty set.
        """
        self.name = job_name
        self.tasks_done = set()
        self.tasks_to_do = set()
        
        if tasks_to_do is not None:
            self.add_tasks(tasks_to_do)

    def add_tasks(self, tasks: Union[Task, Collection[Task]]) -> None:
        """
        Add new task(s) to the tasks_to_do set.

        Args:
            tasks: Single Task or collection of Tasks to add to monitoring
        """
        # Convert single task to set for uniform processing
        task_set = {tasks} if isinstance(tasks, Task) else set(tasks)
        self.tasks_to_do |= task_set

    def notify_completed(self, tasks: Union[Task, Collection[Task]]) -> None:
        """
        Mark task(s) as completed and update relevant systems.

        Args:
            tasks: Single Task or collection of Tasks that have been completed

        Raises:
            ValueError: If any task is not found in tasks_to_do set
        """
        # Convert single task to set for uniform processing
        task_set = {tasks} if isinstance(tasks, Task) else set(tasks)
        
        # Verify all tasks exist in tasks_to_do
        missing_tasks = task_set - self.tasks_to_do
        if missing_tasks:
            task_ids = [task.jobchain_unique_id for task in missing_tasks]
            raise ValueError(f"Tasks not found in pending tasks: {task_ids}")
        
        # Update task sets
        self.tasks_to_do -= task_set
        self.tasks_done |= task_set
        
        self.update_datastore()
        self.update_UI()

    def update_datastore(self, job: 'JobABC' = None) -> None:
        """
        Update the persistent storage with current task status.
        To be implemented based on specific storage requirements.

        Args:
            job: Optional Job instance for context
        """
        pass

    def update_UI(self, job: 'JobABC' = None) -> None:
        """
        Update the user interface with current task status.
        To be implemented based on specific UI requirements.

        Args:
            job: Optional Job instance for context
        """
        pass
