# Task Manager — Implementation Plan

## Purpose
Build a task-management application with a Trash workflow and support for recurring tasks.

## Confirmed Product Decisions

### Trash
- Include a dedicated **Trash** area in the MVP.
- Provide an **Empty Trash** action.
- Protect **Empty Trash** with a confirmation dialog because it permanently deletes the affected tasks.
- Restoring a task must preserve all of its original metadata:
  - Notes
  - Tags
  - Due date
  - Priority
  - Recurrence rule
  - Manual ordering

### Recurring Tasks
- Completing a recurring task creates its next occurrence.
- The next occurrence receives:
  - A new task ID.
  - A newly calculated due date based on the recurrence rule.
- The next occurrence retains the completed task’s:
  - Notes
  - Tags
  - Priority
  - Recurrence rule

## Core Behaviors

### Delete and Restore Flow
1. A user deletes a task from an active task list.
2. The task moves to Trash rather than being permanently removed.
3. The user can restore the task from Trash.
4. Restoration returns the task with the same metadata and its prior manual order preserved.
5. The user can choose **Empty Trash**.
6. The application displays a confirmation dialog before permanently deleting all trashed tasks.

### Recurrence Completion Flow
1. A user marks a recurring task as complete.
2. The completed occurrence is recorded as complete.
3. The application calculates the next due date according to the task’s recurrence rule.
4. The application creates a distinct next task occurrence with a new ID.
5. The new occurrence inherits notes, tags, priority, and its recurrence rule.

## Suggested Task Model

```ts
interface Task {
  id: string
  title: string
  notes?: string
  tags: string[]
  dueDate?: string
  priority?: "low" | "medium" | "high"
  recurrence?: RecurrenceRule
  status: "active" | "completed" | "trashed"
  manualOrder: number
  createdAt: string
  completedAt?: string
  deletedAt?: string
}

interface RecurrenceRule {
  frequency: "daily" | "weekly" | "monthly" | "yearly"
  interval: number
}
```

## Acceptance Criteria

### Trash
- [x] A deleted task is visible in Trash and no longer visible in active task views.
- [x] Restoring a task retains its notes, tags, due date, priority, recurrence rule, and manual order.
- [x] **Empty Trash** is available in the Trash interface.
- [x] Clicking **Empty Trash** opens a confirmation dialog.
- [x] Confirming permanently deletes all tasks currently in Trash.
- [x] Cancelling the dialog leaves Trash unchanged.

### Recurring tasks
- [x] Completing a recurring task creates exactly one next occurrence.
- [x] The new occurrence has a different ID from the completed occurrence.
- [x] The new due date is calculated from the recurrence rule.
- [x] The next occurrence preserves notes, tags, priority, and recurrence settings.
- [x] Non-recurring tasks do not create a new occurrence when completed.

## Resolved Decisions
- Recurrence supports daily, weekly, monthly, and yearly frequencies with a positive interval. Monthly and yearly dates clamp to the last valid day of the target month.
- Completed tasks remain stored and are available through the explicit completed view, but are hidden from the default active view.
- Individual permanent deletion is out of scope; users permanently delete trashed tasks through **Empty Trash**.

## Remaining Decisions
- Define storage, authentication, synchronization, and sharing requirements.
- Define the primary task views, filters, sorting rules, and supported platforms.
