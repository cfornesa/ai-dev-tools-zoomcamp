Task Manager — Implementation Plan
Purpose
Build a task-management application with a Trash workflow and support for recurring tasks.

Confirmed Product Decisions
Trash
Include a dedicated Trash area in the MVP.

Provide an Empty Trash action.

Protect Empty Trash with a confirmation dialog because it permanently deletes the affected tasks.

Restoring a task must preserve all of its original metadata:

Notes

Tags

Due date

Priority

Recurrence rule

Manual ordering

Recurring Tasks
Completing a recurring task creates its next occurrence.

The next occurrence receives:

A new task ID.

A newly calculated due date based on the recurrence rule.

The next occurrence retains the completed task’s:

Notes

Tags

Priority

Recurrence rule

Core Behaviors
Delete and Restore Flow
A user deletes a task from an active task list.

The task moves to Trash rather than being permanently removed.

The user can restore the task from Trash.

Restoration returns the task with the same metadata and its prior manual order preserved.

The user can choose Empty Trash.

The application displays a confirmation dialog before permanently deleting all trashed tasks.

Recurrence Completion Flow
A user marks a recurring task as complete.

The completed occurrence is recorded as complete.

The application calculates the next due date according to the task’s recurrence rule.

The application creates a distinct next task occurrence with a new ID.

The new occurrence inherits notes, tags, priority, and its recurrence rule.

Suggested Task Model
ts
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
Acceptance Criteria
Trash
A deleted task is visible in Trash and no longer visible in active task views.

Restoring a task retains its notes, tags, due date, priority, recurrence rule, and manual order.

Empty Trash is available in the Trash interface.

Clicking Empty Trash opens a confirmation dialog.

Confirming permanently deletes all tasks currently in Trash.

Cancelling the dialog leaves Trash unchanged.

Recurring tasks
Completing a recurring task creates exactly one next occurrence.

The new occurrence has a different ID from the completed occurrence.

The new due date is calculated from the recurrence rule.

The next occurrence preserves notes, tags, priority, and recurrence settings.

Non-recurring tasks do not create a new occurrence when completed.

Remaining Decisions
Define the supported recurrence options and rules for calculating monthly and yearly dates.

Decide whether completed tasks should remain visible, be archived, or be hidden by default.

Decide whether users can permanently delete an individual trashed task in addition to emptying all Trash.

Define storage, authentication, synchronization, and sharing requirements.

Define the primary task views, filters, sorting rules, and supported platforms.