from datetime import date, datetime

from todo_app.model import RecurrenceFrequency, RecurrenceRule, Task, TaskStatus
from .models import TaskRecord


def _task(record):
    recurrence = None
    if record.recurrence_frequency:
        recurrence = RecurrenceRule(record.recurrence_frequency, record.recurrence_interval)
    return Task(str(record.id), record.title, tags=record.tags or [], notes=record.notes,
                due_date=record.due_date.isoformat() if record.due_date else None,
                priority=record.priority, recurrence=recurrence, status=record.status,
                manual_order=record.manual_order, created_at=record.created_at.isoformat(),
                completed_at=record.completed_at.isoformat() if record.completed_at else None,
                deleted_at=record.deleted_at.isoformat() if record.deleted_at else None)


def _datetime(value):
    return datetime.fromisoformat(value) if value else None


class DjangoTaskRepository:
    def create(self, task):
        TaskRecord.objects.create(**self._fields(task))
        return task

    def get(self, task_id):
        try:
            return _task(TaskRecord.objects.get(pk=task_id))
        except TaskRecord.DoesNotExist as exc:
            raise KeyError(f"unknown task: {task_id}") from exc

    def update(self, task):
        record = TaskRecord.objects.get(pk=task.id)
        for key, value in self._fields(task).items():
            setattr(record, key, value)
        record.save()
        return task

    def delete(self, task_id):
        TaskRecord.objects.filter(pk=task_id).delete()

    def list(self, status=None):
        records = TaskRecord.objects.all()
        if status is not None:
            status = status.value if isinstance(status, TaskStatus) else status
            records = records.filter(status=status)
        return [_task(record) for record in records]

    def count(self, status=None):
        return len(self.list(status))

    @staticmethod
    def _fields(task):
        return {"id": task.id, "title": task.title, "notes": task.notes, "tags": task.tags,
                "due_date": date.fromisoformat(task.due_date) if task.due_date else None,
                "priority": task.priority.value if task.priority else None,
                "recurrence_frequency": task.recurrence.frequency.value if task.recurrence else None,
                "recurrence_interval": task.recurrence.interval if task.recurrence else None,
                "status": task.status.value, "manual_order": task.manual_order,
                "completed_at": _datetime(task.completed_at), "deleted_at": _datetime(task.deleted_at)}
