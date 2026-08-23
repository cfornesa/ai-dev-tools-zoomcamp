from django.db import models


class TaskRecord(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    title = models.CharField(max_length=200)
    notes = models.TextField(blank=True, null=True)
    tags = models.JSONField(default=list)
    due_date = models.DateField(blank=True, null=True)
    priority = models.CharField(max_length=10, blank=True, null=True)
    recurrence_frequency = models.CharField(max_length=10, blank=True, null=True)
    recurrence_interval = models.PositiveIntegerField(blank=True, null=True)
    status = models.CharField(max_length=10, default="active")
    manual_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ("manual_order", "created_at", "id")
