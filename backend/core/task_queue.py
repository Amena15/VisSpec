"""
Background task queue for async processing.
Handles long-running validation and analysis tasks.
"""
import asyncio
import uuid
from typing import Any, Callable, Dict, Optional
from datetime import datetime, timezone
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Task:
    """Represents a background task."""

    def __init__(self, task_id: str, func: Callable, *args, **kwargs):
        self.task_id = task_id
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.status = TaskStatus.PENDING
        self.result: Optional[Any] = None
        self.error: Optional[str] = None
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


class TaskQueue:
    """Simple in-memory task queue for background processing."""

    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        self._queue: asyncio.Queue = asyncio.Queue()

    async def submit(self, func: Callable, *args, **kwargs) -> str:
        """Submit a task for background execution."""
        task_id = str(uuid.uuid4())
        task = Task(task_id, func, *args, **kwargs)
        self._tasks[task_id] = task
        await self._queue.put(task_id)
        return task_id

    async def process_tasks(self) -> None:
        """Process tasks from the queue."""
        while True:
            task_id = await self._queue.get()
            task = self._tasks.get(task_id)
            if not task:
                continue

            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now(timezone.utc).isoformat()

            try:
                if asyncio.iscoroutinefunction(task.func):
                    result = await task.func(*task.args, **task.kwargs)
                else:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, lambda: task.func(*task.args, **task.kwargs))
                task.result = result
                task.status = TaskStatus.COMPLETED
            except Exception as e:
                task.error = str(e)
                task.status = TaskStatus.FAILED
            finally:
                task.completed_at = datetime.now(timezone.utc).isoformat()
                self._queue.task_done()

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status and result."""
        task = self._tasks.get(task_id)
        return task.to_dict() if task else None

    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get all tasks."""
        return {tid: t.to_dict() for tid, t in self._tasks.items()}


# Global task queue instance
task_queue = TaskQueue()
