from datetime import date

from django.test import TestCase

from todo_app.model import TaskStatus
from .models import TaskRecord


class TodoWebWorkflowTests(TestCase):
    def create(self, title="Buy milk", **extra):
        data = {"title": title, "notes": "remember", "tags": "home, errands", "due_date": "2026-01-31",
                "priority": "high", "recurrence_frequency": "", "recurrence_interval": "1"}
        data.update(extra)
        return self.client.post("/tasks/new/", data)

    def test_create_and_active_view(self):
        response = self.create()
        self.assertRedirects(response, "/")
        record = TaskRecord.objects.get()
        self.assertEqual((record.title, record.status, record.manual_order), ("Buy milk", "active", 0))
        self.assertContains(self.client.get("/"), "Buy milk")

    def test_required_title_and_status_filtering(self):
        self.assertEqual(self.create(title="").status_code, 200)
        self.assertEqual(TaskRecord.objects.count(), 0)
        self.create(title="active")
        TaskRecord.objects.create(id="completed", title="done", status="completed")
        TaskRecord.objects.create(id="trashed", title="gone", status="trashed")
        response = self.client.get("/")
        self.assertContains(response, "active")
        self.assertNotContains(response, "done")
        self.assertNotContains(response, "gone")
        self.assertContains(self.client.get("/completed/"), "done")
        self.assertContains(self.client.get("/trash/"), "gone")

    def test_edit_metadata_and_reorder(self):
        self.create(title="one")
        self.create(title="two")
        first, second = TaskRecord.objects.order_by("manual_order")
        self.client.post(f"/tasks/{second.id}/move/-1/")
        self.assertEqual([r.title for r in TaskRecord.objects.order_by("manual_order")], ["two", "one"])
        response = self.client.post(f"/tasks/{second.id}/edit/", {"title": "updated", "notes": "new notes", "tags": "work, urgent",
            "due_date": "2026-02-01", "priority": "medium", "recurrence_frequency": "weekly", "recurrence_interval": "2"})
        self.assertRedirects(response, "/")
        record = TaskRecord.objects.get(pk=second.id)
        self.assertEqual((record.title, record.notes, record.tags, record.priority, record.due_date.isoformat()),
                         ("updated", "new notes", ["work", "urgent"], "medium", "2026-02-01"))
        self.assertEqual((record.recurrence_frequency, record.recurrence_interval), ("weekly", 2))

    def test_trash_restore_preserves_data_and_empty_trash_requires_confirmation(self):
        self.create()
        record = TaskRecord.objects.get()
        original = (record.notes, record.tags, record.due_date, record.priority, record.recurrence_frequency, record.manual_order)
        self.assertRedirects(self.client.post(f"/tasks/{record.id}/delete/"), "/")
        record.refresh_from_db()
        self.assertEqual(record.status, "trashed")
        self.assertContains(self.client.get("/trash/"), "Buy milk")
        self.assertRedirects(self.client.post("/trash/empty/", {"confirm": "no"}), "/trash/")
        self.assertTrue(TaskRecord.objects.filter(pk=record.id).exists())
        self.assertRedirects(self.client.post(f"/tasks/{record.id}/restore/"), "/")
        record.refresh_from_db()
        self.assertEqual(record.status, "active")
        self.assertIsNone(record.deleted_at)
        self.assertEqual((record.notes, record.tags, record.due_date, record.priority, record.recurrence_frequency, record.manual_order), original)
        self.client.post(f"/tasks/{record.id}/delete/")
        self.client.post("/trash/empty/", {"confirm": "yes"})
        self.assertFalse(TaskRecord.objects.filter(pk=record.id).exists())

    def test_recurring_completion_creates_one_next_occurrence(self):
        self.create(title="Review", notes="memo", tags="work", priority="medium", recurrence_frequency="monthly")
        current = TaskRecord.objects.get()
        response = self.client.post(f"/tasks/{current.id}/complete/")
        self.assertRedirects(response, "/")
        self.assertEqual(TaskRecord.objects.count(), 2)
        current.refresh_from_db()
        next_task = TaskRecord.objects.exclude(pk=current.id).get()
        self.assertEqual(current.status, TaskStatus.COMPLETED.value)
        self.assertIsNotNone(current.completed_at)
        self.assertEqual((next_task.title, next_task.notes, next_task.tags, next_task.priority, next_task.due_date.isoformat()),
                         ("Review", "memo", ["work"], "medium", "2026-02-28"))
        self.assertEqual((next_task.recurrence_frequency, next_task.recurrence_interval), ("monthly", 1))
        self.assertEqual(self.client.post(f"/tasks/{current.id}/complete/").status_code, 404)
        self.assertEqual(TaskRecord.objects.count(), 2)

    def test_completed_task_actions_preserve_metadata_and_do_not_recur(self):
        self.create(title="Completed recurring", notes="keep me", tags="one, two", priority="high",
                    recurrence_frequency="weekly", recurrence_interval="2")
        current = TaskRecord.objects.get()
        original = (current.title, current.notes, current.tags, current.due_date, current.priority,
                    current.recurrence_frequency, current.recurrence_interval, current.manual_order)
        self.assertRedirects(self.client.post(f"/tasks/{current.id}/complete/"), "/")
        current.refresh_from_db()
        completed_at = current.completed_at
        self.assertIsNotNone(completed_at)
        self.assertContains(self.client.get("/completed/"), "Restore")
        self.assertContains(self.client.get("/completed/"), "Edit")
        self.assertContains(self.client.get("/completed/"), "Trash")

        response = self.client.post(f"/tasks/{current.id}/edit/", {
            "title": "Edited completed", "notes": "updated", "tags": "three",
            "due_date": "2026-02-14", "priority": "medium",
            "recurrence_frequency": "monthly", "recurrence_interval": "3",
        })
        self.assertRedirects(response, "/completed/")
        current.refresh_from_db()
        self.assertEqual(current.status, TaskStatus.COMPLETED.value)
        self.assertEqual(current.completed_at, completed_at)
        self.assertEqual((current.title, current.notes, current.tags, current.due_date, current.priority,
                          current.recurrence_frequency, current.recurrence_interval, current.manual_order),
                         ("Edited completed", "updated", ["three"], date(2026, 2, 14), "medium", "monthly", 3, original[-1]))
        self.assertEqual(TaskRecord.objects.count(), 2)

        self.assertRedirects(self.client.post(f"/tasks/{current.id}/delete/"), "/")
        current.refresh_from_db()
        self.assertEqual(current.status, TaskStatus.TRASHED.value)
        self.assertIsNotNone(current.deleted_at)
        self.assertEqual(current.completed_at, completed_at)
        self.assertContains(self.client.get("/trash/"), "Restore")
        self.assertNotContains(self.client.get("/trash/"), f"/tasks/{current.id}/edit/")

        self.assertRedirects(self.client.post(f"/tasks/{current.id}/restore/"), "/")
        current.refresh_from_db()
        self.assertEqual(current.status, TaskStatus.ACTIVE.value)
        self.assertIsNone(current.completed_at)
        self.assertIsNone(current.deleted_at)
        self.assertEqual((current.title, current.notes, current.tags, current.due_date, current.priority,
                          current.recurrence_frequency, current.recurrence_interval, current.manual_order),
                         ("Edited completed", "updated", ["three"], date(2026, 2, 14), "medium", "monthly", 3, original[-1]))

    def test_restore_completed_task_returns_active_without_404(self):
        self.create(title="Restore me", notes="keep", tags="tag", priority="high")
        current = TaskRecord.objects.get()
        self.assertRedirects(self.client.post(f"/tasks/{current.id}/complete/"), "/")
        current.refresh_from_db()
        completed_at = current.completed_at
        self.assertIsNotNone(completed_at)

        response = self.client.post(f"/tasks/{current.id}/restore/")

        self.assertRedirects(response, "/")
        current.refresh_from_db()
        self.assertEqual(current.status, TaskStatus.ACTIVE.value)
        self.assertIsNone(current.completed_at)
        self.assertIsNone(current.deleted_at)
        self.assertEqual((current.title, current.notes, current.tags, current.priority),
                         ("Restore me", "keep", ["tag"], "high"))
