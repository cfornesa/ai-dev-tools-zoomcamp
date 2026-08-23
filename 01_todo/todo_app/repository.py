from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .model import Task


class InMemoryTaskRepository:
    def __init__(self, tasks: Iterable[Task] = ()) -> None:
        self._tasks: dict[str, Task] = {task.id: task for task in tasks}

    def create(self, task: Task) -> Task:
        if task.id in self._tasks:
            raise ValueError(f"task already exists: {task.id}")
        self._tasks[task.id] = task
        return task

    def get(self, task_id: str) -> Task:
        try:
            return self._tasks[task_id]
        except KeyError as exc:
            raise KeyError(f"unknown task: {task_id}") from exc

    def update(self, task: Task) -> Task:
        if task.id not in self._tasks:
            raise KeyError(f"unknown task: {task.id}")
        self._tasks[task.id] = task
        return task

    def delete(self, task_id: str) -> None:
        self._tasks.pop(task_id, None)

    def list(self, status=None) -> list[Task]:
        tasks = list(self._tasks.values())
        if status is not None:
            tasks = [task for task in tasks if task.status == status]
        return sorted(tasks, key=lambda task: (task.manual_order, task.created_at, task.id))

    def count(self, status=None) -> int:
        return len(self.list(status))


class JsonTaskRepository(InMemoryTaskRepository):
    """A repository that persists the complete collection after every mutation."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        tasks: list[Task] = []
        if self.path.exists() and self.path.stat().st_size:
            try:
                payload = json.loads(self.path.read_text())
                if not isinstance(payload, list):
                    raise ValueError("task store must contain a list")
                tasks = [Task.from_dict(item) for item in payload]
            except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
                tasks = []
        super().__init__(tasks)

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps([task.to_dict() for task in self._tasks.values()], indent=2) + "\n")
        temporary.replace(self.path)

    def create(self, task: Task) -> Task:
        result = super().create(task)
        self._save()
        return result

    def update(self, task: Task) -> Task:
        result = super().update(task)
        self._save()
        return result

    def delete(self, task_id: str) -> None:
        super().delete(task_id)
        self._save()
