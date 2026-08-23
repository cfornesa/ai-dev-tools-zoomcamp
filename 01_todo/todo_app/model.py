from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    TRASHED = "trashed"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RecurrenceFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


@dataclass(frozen=True)
class RecurrenceRule:
    frequency: RecurrenceFrequency
    interval: int = 1

    def __post_init__(self) -> None:
        frequency = self.frequency
        if not isinstance(frequency, RecurrenceFrequency):
            try:
                frequency = RecurrenceFrequency(frequency)
            except ValueError as exc:
                raise ValueError("unsupported recurrence frequency") from exc
            object.__setattr__(self, "frequency", frequency)
        if not isinstance(self.interval, int) or isinstance(self.interval, bool) or self.interval < 1:
            raise ValueError("recurrence interval must be a positive integer")


@dataclass
class Task:
    id: str
    title: str
    tags: list[str] = field(default_factory=list)
    notes: str | None = None
    due_date: str | None = None
    priority: Priority | None = None
    recurrence: RecurrenceRule | None = None
    status: TaskStatus = TaskStatus.ACTIVE
    manual_order: int = 0
    created_at: str = ""
    completed_at: str | None = None
    deleted_at: str | None = None

    def __post_init__(self) -> None:
        if not self.title or not self.title.strip():
            raise ValueError("title is required")
        self.title = self.title.strip()
        if not isinstance(self.status, TaskStatus):
            self.status = TaskStatus(self.status)
        if self.priority is not None and not isinstance(self.priority, Priority):
            self.priority = Priority(self.priority)
        if self.recurrence is not None and not isinstance(self.recurrence, RecurrenceRule):
            self.recurrence = RecurrenceRule(
                RecurrenceFrequency(self.recurrence["frequency"]), self.recurrence["interval"]
            )
        self.tags = list(self.tags)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        value["priority"] = self.priority.value if self.priority else None
        if self.recurrence:
            value["recurrence"] = {
                "frequency": self.recurrence.frequency.value,
                "interval": self.recurrence.interval,
            }
        return value

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Task":
        recurrence = value.get("recurrence")
        if recurrence:
            recurrence = RecurrenceRule(
                RecurrenceFrequency(recurrence["frequency"]), recurrence["interval"]
            )
        return cls(
            id=value["id"],
            title=value["title"],
            tags=value.get("tags", []),
            notes=value.get("notes"),
            due_date=value.get("due_date"),
            priority=Priority(value["priority"]) if value.get("priority") else None,
            recurrence=recurrence,
            status=TaskStatus(value.get("status", TaskStatus.ACTIVE.value)),
            manual_order=value.get("manual_order", 0),
            created_at=value.get("created_at", ""),
            completed_at=value.get("completed_at"),
            deleted_at=value.get("deleted_at"),
        )
