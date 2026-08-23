from django import forms
from todo_app.model import Priority, RecurrenceFrequency


class TaskForm(forms.Form):
    title = forms.CharField(max_length=200)
    notes = forms.CharField(required=False, widget=forms.Textarea)
    tags = forms.CharField(required=False, help_text="Comma-separated tags")
    due_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    priority = forms.ChoiceField(required=False, choices=[("", "No priority")] + [(p.value, p.value.title()) for p in Priority])
    recurrence_frequency = forms.ChoiceField(required=False, choices=[("", "Does not repeat")] + [(f.value, f.value.title()) for f in RecurrenceFrequency])
    recurrence_interval = forms.IntegerField(required=False, min_value=1, initial=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "form-control")
        self.fields["priority"].widget.attrs["class"] = "form-select"
        self.fields["recurrence_frequency"].widget.attrs["class"] = "form-select"

    def clean(self):
        data = super().clean()
        if data.get("recurrence_frequency") and not data.get("due_date"):
            self.add_error("due_date", "A due date is required for recurring tasks.")
        if data.get("recurrence_frequency") and not data.get("recurrence_interval"):
            self.add_error("recurrence_interval", "Enter a positive interval.")
        return data

    def metadata(self):
        from todo_app.model import RecurrenceRule
        recurrence = None
        if self.cleaned_data.get("recurrence_frequency"):
            recurrence = RecurrenceRule(self.cleaned_data["recurrence_frequency"], self.cleaned_data["recurrence_interval"])
        return {"notes": self.cleaned_data.get("notes") or None,
                "tags": [tag.strip() for tag in self.cleaned_data.get("tags", "").split(",") if tag.strip()],
                "due_date": self.cleaned_data["due_date"].isoformat() if self.cleaned_data.get("due_date") else None,
                "priority": self.cleaned_data.get("priority") or None, "recurrence": recurrence}
