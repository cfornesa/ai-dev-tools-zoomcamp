import io
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout
from unittest.mock import patch

from todo_app import InMemoryTaskRepository, JsonTaskRepository, RecurrenceRule, TaskService
from todo_app.cli import main
from todo_app.model import Priority, RecurrenceFrequency, Task, TaskStatus
from todo_app.recurrence import next_due_date


class TodoTests(unittest.TestCase):
    def service(self, tasks=()):
        return TaskService(InMemoryTaskRepository(tasks))

    def test_baseline_and_domain_model(self):
        task = Task("1", "Ship", tags=["work"], notes="notes", priority=Priority.HIGH,
                    recurrence=RecurrenceRule(RecurrenceFrequency.WEEKLY, 2), created_at="now")
        self.assertEqual(task.to_dict()["status"], "active")
        self.assertEqual(Task.from_dict(task.to_dict()).recurrence.interval, 2)

    def test_repository_crud_and_manual_order(self):
        repo = InMemoryTaskRepository()
        first = Task("1", "first", manual_order=1, created_at="1")
        second = Task("2", "second", manual_order=0, created_at="2")
        repo.create(first); repo.create(second)
        self.assertEqual([t.id for t in repo.list()], ["2", "1"])
        repo.update(Task("2", "changed", manual_order=2, created_at="2"))
        self.assertEqual(repo.get("2").title, "changed")
        repo.delete("2")
        self.assertEqual(repo.count(), 1)

    def test_create_validates_title_and_assigns_metadata(self):
        service = self.service()
        with self.assertRaises(ValueError): service.create_task("  ")
        task = service.create_task("  Buy milk ", notes="2%", tags=["home"], priority="low")
        self.assertEqual(task.title, "Buy milk")
        self.assertEqual(task.manual_order, 0)
        self.assertEqual(task.status, TaskStatus.ACTIVE)

    def test_active_and_trash_views_filter_status(self):
        service = self.service()
        active = service.create_task("active")
        service.repository.create(Task("done", "done", status=TaskStatus.COMPLETED, created_at="x"))
        service.repository.create(Task("trash", "trash", status=TaskStatus.TRASHED, created_at="x"))
        self.assertEqual([t.id for t in service.active_tasks()], [active.id])
        self.assertEqual([t.id for t in service.completed_tasks()], ["done"])
        self.assertEqual([t.id for t in service.trash()], ["trash"])

    def test_edit_preserves_unedited_fields(self):
        service = self.service()
        task = service.create_task("old", notes="keep", tags=["a"], due_date="2026-01-01", priority="high")
        edited = service.edit_task(task.id, title="new", tags=["b"])
        self.assertEqual((edited.title, edited.tags, edited.notes, edited.due_date, edited.priority),
                         ("new", ["b"], "keep", "2026-01-01", Priority.HIGH))

    def test_reorder_both_directions(self):
        service = self.service()
        one = service.create_task("one"); two = service.create_task("two"); three = service.create_task("three")
        service.move(three.id, -1)
        self.assertEqual([t.title for t in service.active_tasks()], ["one", "three", "two"])
        service.move(one.id, 1)
        self.assertEqual([t.title for t in service.active_tasks()], ["three", "one", "two"])

    def test_trash_restore_and_empty_confirmation(self):
        service = self.service()
        task = service.create_task("keep", notes="n", tags=["x"], due_date="2026-01-01", priority="high",
                                   recurrence=RecurrenceRule(RecurrenceFrequency.MONTHLY, 2))
        original = task.to_dict()
        service.move_to_trash(task.id)
        self.assertEqual(service.active_tasks(), [])
        self.assertEqual(service.empty_trash(False), 0)
        restored = service.restore(task.id)
        self.assertEqual(restored.to_dict()["notes"], original["notes"])
        self.assertEqual(restored.to_dict()["manual_order"], original["manual_order"])
        service.move_to_trash(task.id)
        self.assertEqual(service.empty_trash(True), 1)
        with self.assertRaises(KeyError): service.repository.get(task.id)

    def test_recurrence_dates(self):
        cases = [
            ("2026-01-01", RecurrenceFrequency.DAILY, 2, "2026-01-03"),
            ("2026-01-01", RecurrenceFrequency.WEEKLY, 2, "2026-01-15"),
            ("2026-01-31", RecurrenceFrequency.MONTHLY, 1, "2026-02-28"),
            ("2024-02-29", RecurrenceFrequency.YEARLY, 1, "2025-02-28"),
        ]
        for current, frequency, interval, expected in cases:
            self.assertEqual(next_due_date(current, RecurrenceRule(frequency, interval)), expected)

    def test_complete_non_recurring(self):
        service = self.service(); task = service.create_task("done")
        completed, next_task = service.complete(task.id)
        self.assertEqual(completed.status, TaskStatus.COMPLETED)
        self.assertIsNone(next_task)
        self.assertEqual(service.active_tasks(), [])

    def test_complete_recurring_inherits_metadata_once(self):
        service = self.service()
        task = service.create_task("pay", notes="memo", tags=["finance"], due_date="2026-01-31", priority="medium",
                                   recurrence=RecurrenceRule(RecurrenceFrequency.MONTHLY, 1))
        completed, next_task = service.complete(task.id)
        self.assertNotEqual(completed.id, next_task.id)
        self.assertEqual(next_task.due_date, "2026-02-28")
        self.assertEqual((next_task.notes, next_task.tags, next_task.priority, next_task.recurrence),
                         ("memo", ["finance"], Priority.MEDIUM, task.recurrence))
        with self.assertRaises(ValueError): service.complete(task.id)
        self.assertEqual(len(service.active_tasks()), 1)

    def test_json_storage_round_trip_and_malformed_store(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tasks.json"
            repo = JsonTaskRepository(path)
            task = Task("1", "saved", tags=["x"], created_at="now")
            repo.create(task)
            loaded = JsonTaskRepository(path)
            self.assertEqual(loaded.get("1").to_dict(), task.to_dict())
            path.write_text("not json")
            self.assertEqual(JsonTaskRepository(path).list(), [])

    def test_cli_end_to_end_trash_restore_and_recurring_completion(self):
        with tempfile.TemporaryDirectory() as directory:
            store = str(Path(directory) / "tasks.json")
            output = io.StringIO()
            with redirect_stdout(output):
                main(["--store", store, "add", "weekly review", "--due-date", "2026-01-31",
                      "--frequency", "monthly", "--notes", "memo", "--tag", "work"])
            task_id = output.getvalue().strip()
            with patch("sys.stdout"):
                main(["--store", store, "delete", task_id])
                main(["--store", store, "restore", task_id])
                main(["--store", store, "complete", task_id])
            loaded = JsonTaskRepository(store)
            self.assertEqual(len(loaded.list(TaskStatus.COMPLETED)), 1)
            next_tasks = loaded.list(TaskStatus.ACTIVE)
            self.assertEqual(len(next_tasks), 1)
            self.assertEqual(next_tasks[0].due_date, "2026-02-28")
            self.assertEqual(next_tasks[0].notes, "memo")

    def test_cli_without_command_prints_help(self):
        with patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(main([]), 0)
        self.assertIn("Manage tasks", output.getvalue())


if __name__ == "__main__":
    unittest.main()
