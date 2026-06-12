"""
Background task queue for async processing.
Handles long-running validation and analysis tasks.
"""
import asyncio
import uuid
from typing import Any, Callable, Dict, Optional
from datetime import datetime, timezone
from enum import Enum
import logging

logger = logging.getLogger(__name__)


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
    """In‑memory async task queue with background processor and graceful shutdown."""

    def __init__(self, max_task_age_seconds: int = 3600):
        """
        Args:
            max_task_age_seconds: Completed/failed tasks older than this are removed.
                                  Set to 0 to disable automatic cleanup.
        """
        self._tasks: Dict[str, Task] = {}
        self._queue: asyncio.Queue = asyncio.Queue()
        self._stop_event = asyncio.Event()
        self._processor_task: Optional[asyncio.Task] = None
        self._max_task_age = max_task_age_seconds

    async def start_processor(self) -> None:
        """Launch the background task processor (call during FastAPI startup)."""
        if self._processor_task is None or self._processor_task.done():
            self._stop_event.clear()
            self._processor_task = asyncio.create_task(self._process_tasks())
            logger.info("Task queue processor started")

    async def stop_processor(self, timeout: float = 5.0) -> None:
        """
        Gracefully stop the task processor.
        Waits for currently running tasks to finish, then cancels the loop.
        """
        if self._processor_task and not self._processor_task.done():
            self._stop_event.set()
            try:
                await asyncio.wait_for(self._processor_task, timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning("Task processor did not stop in time, cancelling")
                self._processor_task.cancel()
            except Exception as e:
                logger.error(f"Error stopping task processor: {e}")
        logger.info("Task queue processor stopped")

    async def submit(self, func: Callable, *args, **kwargs) -> str:
        """Submit a task for background execution. Returns task_id."""
        task_id = str(uuid.uuid4())
        task = Task(task_id, func, *args, **kwargs)
        self._tasks[task_id] = task
        await self._queue.put(task_id)
        logger.debug(f"Task {task_id} submitted")
        return task_id

    async def _process_tasks(self) -> None:
        """Main processor loop – runs until stop_event is set."""
        while not self._stop_event.is_set():
            try:
                task_id = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                self._cleanup_old_tasks()
                continue
            except asyncio.CancelledError:
                break

            task = self._tasks.get(task_id)
            if not task:
                self._queue.task_done()
                continue

            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now(timezone.utc).isoformat()
            logger.info(f"Processing task {task_id}")

            try:
                if asyncio.iscoroutinefunction(task.func):
                    result = await task.func(*task.args, **task.kwargs)
                else:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None, lambda: task.func(*task.args, **task.kwargs)
                    )
                task.result = result
                task.status = TaskStatus.COMPLETED
                logger.info(f"Task {task_id} completed successfully")
            except Exception as e:
                task.error = str(e)
                task.status = TaskStatus.FAILED
                logger.error(f"Task {task_id} failed: {e}")
            finally:
                task.completed_at = datetime.now(timezone.utc).isoformat()
                self._queue.task_done()
                self._cleanup_old_tasks()

    def _cleanup_old_tasks(self) -> None:
        """Remove tasks that are completed/failed and older than max_task_age."""
        if self._max_task_age <= 0:
            return
        now = datetime.now(timezone.utc)
        to_delete = []
        for task_id, task in self._tasks.items():
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                completed_at = datetime.fromisoformat(task.completed_at)
                age = (now - completed_at).total_seconds()
                if age > self._max_task_age:
                    to_delete.append(task_id)
        for task_id in to_delete:
            del self._tasks[task_id]
        if to_delete:
            logger.debug(f"Cleaned up {len(to_delete)} old tasks")

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status and result."""
        task = self._tasks.get(task_id)
        return task.to_dict() if task else None

    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get all tasks (including cleaned ones may be missing)."""
        return {tid: t.to_dict() for tid, t in self._tasks.items()}


# Global task queue instance – keep old tasks for 1 hour
task_queue = TaskQueue(max_task_age_seconds=3600)