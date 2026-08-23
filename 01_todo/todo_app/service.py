from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

from .model import Priority, RecurrenceRule, Task, TaskStatus
from .recurrence import next_due_date


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TaskService:
    def __init__(self, repository) -> None:
        self.repository = repository

    def create_task(self, title: str, **metadata) -> Task:
        if not title or not title.strip():
            raise ValueError("title is required")
        active = self.repository.list(TaskStatus.ACTIVE)
        task = Task(
            id=str(uuid4()),
            title=title,
            notes=metadata.get("notes"),
            tags=metadata.get("tags", []),
            due_date=metadata.get("due_date"),
            priority=metadata.get("priority"),
            recurrence=metadata.get("recurrence"),
            manual_order=max((item.manual_order for item in active), default=-1) + 1,
            created_at=_now(),
        )
        return self.repository.create(task)

    def active_tasks(self) -> list[Task]:
        return self.repository.list(TaskStatus.ACTIVE)

    def completed_tasks(self) -> list[Task]:
        return self.repository.list(TaskStatus.COMPLETED)

    def trash(self) -> list[Task]:
        return self.repository.list(TaskStatus.TRASHED)

    def edit_task(self, task_id: str, **changes) -> Task:
        task = self.repository.get(task_id)
        if task.status not in (TaskStatus.ACTIVE, TaskStatus.COMPLETED):
            raise ValueError("only active or completed tasks can be edited")
        allowed = {"title", "notes", "tags", "due_date", "priority", "recurrence"}
        unknown = set(changes) - allowed
        if unknown:
            raise ValueError(f"unsupported fields: {sorted(unknown)}")
        if "title" in changes and (not changes["title"] or not changes["title"].strip()):
            raise ValueError("title is required")
        updated = replace(task, **changes)
        return self.repository.update(updated)

    def move(self, task_id: str, direction: int) -> list[Task]:
        tasks = self.active_tasks()
        index = next((i for i, item in enumerate(tasks) if item.id == task_id), None)
        if index is None:
            raise ValueError("task is not active")
        target = max(0, min(len(tasks) - 1, index + direction))
        if target != index:
            tasks[index], tasks[target] = tasks[target], tasks[index]
            for order, item in enumerate(tasks):
                self.repository.update(replace(item, manual_order=order))
        return tasks

    def move_to_trash(self, task_id: str) -> Task:
        task = self.repository.get(task_id)
        if task.status not in (TaskStatus.ACTIVE, TaskStatus.COMPLETED):
            raise ValueError("only active or completed tasks can be trashed")
        return self.repository.update(replace(task, status=TaskStatus.TRASHED, deleted_at=_now()))

    def restore(self, task_id: str) -> Task:
        task = self.repository.get(task_id)
        if task.status not in (TaskStatus.COMPLETED, TaskStatus.TRASHED):
            raise ValueError("only completed or trashed tasks can be restored")
        return self.repository.update(replace(task, status=TaskStatus.ACTIVE, completed_at=None, deleted_at=None))

    def empty_trash(self, confirmed: bool) -> int:
        if not confirmed:
            return 0
        trashed = self.trash()
        for task in trashed:
            self.repository.delete(task.id)
        return len(trashed)

    def complete(self, task_id: str) -> tuple[Task, Task | None]:
        task = self.repository.get(task_id)
        if task.status != TaskStatus.ACTIVE:
            raise ValueError("only active tasks can be completed")
        if task.recurrence and not task.due_date:
            raise ValueError("recurring tasks require a due date")
        completed = replace(task, status=TaskStatus.COMPLETED, completed_at=_now())
        self.repository.update(completed)
        if not task.recurrence:
            return completed, None
        next_task = self.create_task(
            task.title,
            notes=task.notes,
            tags=task.tags,
            due_date=next_due_date(task.due_date, task.recurrence),
            priority=task.priority,
            recurrence=task.recurrence,
        )
        return completed, next_task
