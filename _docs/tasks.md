## 1. Initialize the project and test runner
Goal: Create an empty application project with one passing automated test.
Description: Set up the chosen application runtime, package scripts, and test framework with the smallest practical configuration. Add a trivial test and document the command that runs it so contributors can verify the baseline before adding features.

## 2. Define the task domain model
Goal: Establish a typed task model that represents the agreed product data.
Description: Add the task and recurrence-rule types, including status, metadata, manual order, and lifecycle timestamps. Keep the model independent from any UI or storage implementation, and add tests covering valid representative task objects.

## 3. Build an in-memory task repository
Goal: Provide a small data-access layer for saving and retrieving tasks during development.
Description: Implement repository operations to create, read, update, and list tasks using an in-memory collection. Specify and test how results are ordered so later features can rely on stable manual ordering.

## 4. Create a task creation workflow
Goal: Allow a user to add an active task with a title.
Description: Build a form or command interface that validates a required title and saves a new task through the repository. Assign an ID, creation timestamp, active status, and initial manual order, with tests for successful creation and invalid input.

## 5. Display active tasks
Goal: Show active tasks without displaying completed or trashed tasks.
Description: Add an active-task view backed by the repository and render tasks in manual order. Include empty-state handling and tests that prove tasks in other statuses are excluded.

## 6. Edit task metadata
Goal: Allow a user to update a task's title, notes, tags, due date, and priority.
Description: Add an edit workflow for active tasks that validates each supported field and persists the changes. Preserve fields that are not being edited, and test updates to every metadata category.

## 7. Reorder active tasks manually
Goal: Let a user change the manual order of active tasks.
Description: Implement one clear interaction for moving a task within the active-task list and update the affected order values. Add tests for moves in both directions and for preserving the order after a repository reload.

## 8. Move a task to Trash
Goal: Let a user delete an active task without permanently removing it.
Description: Add a delete action that changes a task's status to trashed and records its deletion timestamp. Ensure the task disappears from active views while retaining all task metadata and manual order.

## 9. Create the Trash view
Goal: Give users a dedicated view of tasks currently in Trash.
Description: Build a Trash interface that lists only trashed tasks and presents the available recovery actions. Include a clear empty state and tests confirming active and completed tasks are not shown there.

## 10. Restore a task from Trash
Goal: Return a trashed task to the active list with its original data intact.
Description: Add a restore action that returns the task to active status and clears its deletion timestamp. Test that notes, tags, due date, priority, recurrence rule, and manual order all remain unchanged after restoration.

## 11. Add Empty Trash confirmation
Goal: Require explicit confirmation before permanently removing all trashed tasks.
Description: Add an Empty Trash action that first opens a confirmation dialog with confirm and cancel paths. Test that cancellation changes nothing and confirmation permanently deletes only the tasks currently in Trash.

## 12. Configure recurrence rules on tasks
Goal: Let a user assign a supported recurrence rule to an active task.
Description: Add controls and validation for frequency and interval, using daily, weekly, monthly, and yearly frequencies. Keep recurrence optional, and test that non-recurring tasks remain valid without a rule.

## 13. Define recurrence date calculations
Goal: Implement and document how the next due date is calculated for every recurrence frequency.
Description: Create a date-calculation utility for daily, weekly, monthly, and yearly rules, including the chosen behavior for calendar edge cases such as month-end dates. Add focused tests for each frequency, intervals greater than one, and the documented edge cases.

## 14. Complete a non-recurring task
Goal: Mark a non-recurring active task as completed without creating another task.
Description: Add a completion action that updates status and records a completion timestamp. Test that the completed task leaves active views and that no additional task is created.

## 15. Complete a recurring task and create its next occurrence
Goal: Mark a recurring occurrence complete and create exactly one next active occurrence.
Description: Use the recurrence calculator to create a new task with a different ID and the next due date while recording completion on the original task. Test inheritance of notes, tags, priority, and recurrence settings, along with prevention of duplicate next occurrences.

## 16. Decide and implement completed-task visibility
Goal: Establish one consistent user experience for viewing completed tasks.
Description: Record the product decision on whether completed tasks are shown, archived, or hidden by default, then implement the selected behavior in the task views. Add tests for the chosen visibility and any associated navigation or filtering.

## 17. Add persistent local storage
Goal: Preserve task data across application restarts.
Description: Choose an appropriate local persistence mechanism and connect it behind the repository interface without changing task workflows. Add tests for loading saved tasks and safely handling an empty or malformed initial store.

## 18. Add end-to-end coverage for Trash and recurrence
Goal: Verify the highest-risk user workflows from interface to storage.
Description: Create end-to-end tests for deleting, restoring, and emptying Trash, including the confirmation cancellation path. Add a separate scenario for completing a recurring task and verifying its completed and next occurrences.
