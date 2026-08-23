from __future__ import annotations

import calendar
from datetime import date, timedelta

from .model import RecurrenceRule


def next_due_date(due_date: str, rule: RecurrenceRule) -> str:
    """Return the next ISO date; month/year changes clamp invalid days."""
    current = date.fromisoformat(due_date)
    if rule.frequency.value == "daily":
        result = current + timedelta(days=rule.interval)
    elif rule.frequency.value == "weekly":
        result = current + timedelta(weeks=rule.interval)
    elif rule.frequency.value == "monthly":
        month_index = current.month - 1 + rule.interval
        year, month_zero = divmod(current.year * 12 + month_index, 12)
        month = month_zero + 1
        result = date(year, month, min(current.day, calendar.monthrange(year, month)[1]))
    elif rule.frequency.value == "yearly":
        year = current.year + rule.interval
        result = date(year, current.month, min(current.day, calendar.monthrange(year, current.month)[1]))
    else:  # RecurrenceRule validates this, kept defensive for deserialized data.
        raise ValueError("unsupported recurrence frequency")
    return result.isoformat()
