from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [migrations.CreateModel(name="TaskRecord", fields=[
        ("id", models.CharField(max_length=36, primary_key=True, serialize=False)),
        ("title", models.CharField(max_length=200)), ("notes", models.TextField(blank=True, null=True)),
        ("tags", models.JSONField(default=list)), ("due_date", models.DateField(blank=True, null=True)),
        ("priority", models.CharField(blank=True, max_length=10, null=True)),
        ("recurrence_frequency", models.CharField(blank=True, max_length=10, null=True)),
        ("recurrence_interval", models.PositiveIntegerField(blank=True, null=True)),
        ("status", models.CharField(default="active", max_length=10)), ("manual_order", models.IntegerField(default=0)),
        ("created_at", models.DateTimeField(auto_now_add=True)), ("completed_at", models.DateTimeField(blank=True, null=True)),
        ("deleted_at", models.DateTimeField(blank=True, null=True)),
    ], options={"ordering": ("manual_order", "created_at", "id")})]
