"""Status Tracking for Document Processing

Tracks progress across document processing tasks with:
- Real-time progress updates
- Completion estimates
- Error tracking
- Task dependencies

Based on L208 lines 809-826 (Task Coordination Mechanisms - Progress Tracking)
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import time


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskProgress:
    """Progress information for a task

    Based on L208 lines 810-825 (Progress Tracking implementation)
    """
    task_id: str
    status: TaskStatus
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    progress_percent: float = 0.0
    items_total: int = 0
    items_completed: int = 0
    error_message: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

    @property
    def elapsed_time(self) -> Optional[float]:
        """Calculate elapsed time in seconds

        Returns:
            Elapsed time or None if not started
        """
        if not self.started_at:
            return None

        end_time = self.completed_at or time.time()
        return end_time - self.started_at

    @property
    def estimated_remaining(self) -> Optional[float]:
        """Estimate remaining time in seconds

        Returns:
            Estimated remaining time or None if cannot estimate
        """
        if not self.started_at or self.items_completed == 0:
            return None

        elapsed = self.elapsed_time
        if elapsed is None:
            return None

        time_per_item = elapsed / self.items_completed
        remaining_items = self.items_total - self.items_completed
        return time_per_item * remaining_items


class StatusTracker:
    """Tracks status of document processing tasks

    Provides:
    - Progress tracking with completion estimates
    - Hierarchical task tracking (parent/child)
    - Status aggregation across tasks
    - Real-time updates

    Based on L208 lines 809-826 (Progress Tracking)
    """

    def __init__(self):
        """Initialize status tracker"""
        self.tasks: Dict[str, TaskProgress] = {}
        self.task_hierarchy: Dict[str, List[str]] = {}  # parent_id -> [child_ids]

    def create_task(
        self,
        task_id: str,
        total_items: int = 1,
        parent_task_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> TaskProgress:
        """Create a new task for tracking

        Args:
            task_id: Unique task identifier
            total_items: Total number of items to process
            parent_task_id: Parent task ID if this is a child task
            metadata: Additional task metadata

        Returns:
            Created TaskProgress
        """
        progress = TaskProgress(
            task_id=task_id,
            status=TaskStatus.PENDING,
            items_total=total_items,
            metadata=metadata or {}
        )

        self.tasks[task_id] = progress

        # Track hierarchy
        if parent_task_id:
            if parent_task_id not in self.task_hierarchy:
                self.task_hierarchy[parent_task_id] = []
            self.task_hierarchy[parent_task_id].append(task_id)

        return progress

    def start_task(self, task_id: str) -> None:
        """Mark task as started

        Args:
            task_id: Task to start
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = time.time()

    def update_progress(
        self,
        task_id: str,
        items_completed: Optional[int] = None,
        progress_percent: Optional[float] = None
    ) -> None:
        """Update task progress

        Args:
            task_id: Task to update
            items_completed: Number of items completed (optional)
            progress_percent: Progress percentage (optional, calculated if items provided)
        """
        if task_id not in self.tasks:
            return

        task = self.tasks[task_id]

        if items_completed is not None:
            task.items_completed = items_completed

            # Calculate progress percent
            if task.items_total > 0:
                task.progress_percent = (task.items_completed / task.items_total) * 100
        elif progress_percent is not None:
            task.progress_percent = progress_percent

    def complete_task(self, task_id: str, result: Optional[Any] = None) -> None:
        """Mark task as completed

        Args:
            task_id: Task to complete
            result: Optional result data
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()
            task.progress_percent = 100.0
            task.items_completed = task.items_total

            if result is not None:
                task.metadata['result'] = result

    def fail_task(self, task_id: str, error_message: str) -> None:
        """Mark task as failed

        Args:
            task_id: Task that failed
            error_message: Error description
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.FAILED
            task.completed_at = time.time()
            task.error_message = error_message

    def cancel_task(self, task_id: str) -> None:
        """Cancel a task

        Args:
            task_id: Task to cancel
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.CANCELLED
            task.completed_at = time.time()

    def get_task_status(self, task_id: str) -> Optional[TaskProgress]:
        """Get status of a specific task

        Args:
            task_id: Task identifier

        Returns:
            TaskProgress if found, None otherwise
        """
        return self.tasks.get(task_id)

    def get_aggregate_status(self, task_ids: List[str]) -> Dict[str, Any]:
        """Get aggregated status across multiple tasks

        Args:
            task_ids: List of task IDs to aggregate

        Returns:
            Dictionary with aggregate statistics
        """
        tasks = [self.tasks[tid] for tid in task_ids if tid in self.tasks]

        if not tasks:
            return {'error': 'No valid tasks found'}

        total_items = sum(t.items_total for t in tasks)
        completed_items = sum(t.items_completed for t in tasks)

        status_counts = {
            'pending': sum(1 for t in tasks if t.status == TaskStatus.PENDING),
            'in_progress': sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS),
            'completed': sum(1 for t in tasks if t.status == TaskStatus.COMPLETED),
            'failed': sum(1 for t in tasks if t.status == TaskStatus.FAILED),
            'cancelled': sum(1 for t in tasks if t.status == TaskStatus.CANCELLED)
        }

        # Calculate overall progress
        overall_progress = (completed_items / total_items * 100) if total_items > 0 else 0

        # Estimate remaining time (average across in-progress tasks)
        in_progress_tasks = [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
        if in_progress_tasks:
            estimates = [t.estimated_remaining for t in in_progress_tasks if t.estimated_remaining]
            avg_remaining = sum(estimates) / len(estimates) if estimates else None
        else:
            avg_remaining = None

        return {
            'total_tasks': len(tasks),
            'status_counts': status_counts,
            'total_items': total_items,
            'completed_items': completed_items,
            'overall_progress_percent': overall_progress,
            'estimated_remaining_seconds': avg_remaining
        }

    def get_child_tasks(self, parent_task_id: str) -> List[TaskProgress]:
        """Get all child tasks of a parent

        Args:
            parent_task_id: Parent task ID

        Returns:
            List of child TaskProgress objects
        """
        child_ids = self.task_hierarchy.get(parent_task_id, [])
        return [self.tasks[cid] for cid in child_ids if cid in self.tasks]

    def get_task_tree(self, root_task_id: str) -> Dict:
        """Get hierarchical view of task and all descendants

        Args:
            root_task_id: Root task ID

        Returns:
            Dictionary representing task tree
        """
        if root_task_id not in self.tasks:
            return {}

        task = self.tasks[root_task_id]
        children = self.get_child_tasks(root_task_id)

        return {
            'task_id': task.task_id,
            'status': task.status.value,
            'progress_percent': task.progress_percent,
            'elapsed_time': task.elapsed_time,
            'estimated_remaining': task.estimated_remaining,
            'children': [self.get_task_tree(child.task_id) for child in children]
        }

    def clear_completed(self) -> int:
        """Remove completed tasks from tracking

        Returns:
            Number of tasks removed
        """
        completed_ids = [
            tid for tid, task in self.tasks.items()
            if task.status == TaskStatus.COMPLETED
        ]

        for tid in completed_ids:
            del self.tasks[tid]

            # Clean up hierarchy
            for parent_id, children in self.task_hierarchy.items():
                if tid in children:
                    children.remove(tid)

        return len(completed_ids)
