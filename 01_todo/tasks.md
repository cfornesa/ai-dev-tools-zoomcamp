## 1. Initialize the Django project and test runner
Goal: Create an empty Django application with one passing automated test.
Description: Set up a Django project and a dedicated task-management app, including settings, URL routing, templates, and the Django test runner. Add a trivial Django test and document the command that runs it so contributors can verify the baseline before adding features. The application must start with `python manage.py runserver` from `01_todo`.

## 2. Define the task domain and Django models
Goal: Establish Django-backed task models that represent the agreed product data.
Description: Add the task and recurrence-rule types/models, including status, metadata, manual order, and lifecycle timestamps. Keep business rules testable outside templates and views, expose the model through Django's app configuration, and add tests covering valid representative task objects.

## 3. Build an in-memory task repository
Goal: Provide a small data-access layer for saving and retrieving tasks during development.
Description: Implement repository operations to create, read, update, and list tasks using an in-memory collection. Specify and test how results are ordered so later features can rely on stable manual ordering.

## 4. Create a task creation workflow
Goal: Allow a user to add an active task with a title.
Description: Build a Django form, URL, view, and template that validate a required title and save a new task through the repository. Assign an ID, creation timestamp, active status, and initial manual order, with Django test-client coverage for successful creation and invalid input.

## 5. Display active tasks
Goal: Show active tasks without displaying completed or trashed tasks.
Description: Add a Django URL/view/template for active tasks backed by the repository and render tasks in manual order. Include empty-state handling and Django test-client coverage that proves tasks in other statuses are excluded.

## 6. Edit task metadata
Goal: Allow a user to update a task's title, notes, tags, due date, and priority.
Description: Add a Django form, URL, view, and template for editing active tasks. Validate each supported field and persist the changes. Preserve fields that are not being edited, and test updates to every metadata category through the Django test client.

## 7. Reorder active tasks manually
Goal: Let a user change the manual order of active tasks.
Description: Implement one clear Django POST interaction for moving a task within the active-task list and update the affected order values. Add tests for moves in both directions and for preserving the order after a repository reload.

## 8. Move a task to Trash
Goal: Let a user delete an active task without permanently removing it.
Description: Add a Django POST delete action that changes a task's status to trashed and records its deletion timestamp. Ensure the task disappears from active views while retaining all task metadata and manual order.

## 9. Create the Trash view
Goal: Give users a dedicated view of tasks currently in Trash.
Description: Build a Django Trash URL/view/template that lists only trashed tasks and presents the available recovery actions. Include a clear empty state and Django test-client coverage confirming active and completed tasks are not shown there.

## 10. Restore a task from Trash
Goal: Return a trashed task to the active list with its original data intact.
Description: Add a Django POST restore action that returns the task to active status and clears its deletion timestamp. Test that notes, tags, due date, priority, recurrence rule, and manual order all remain unchanged after restoration.

## 11. Add Empty Trash confirmation
Goal: Require explicit confirmation before permanently removing all trashed tasks.
Description: Add a Django Empty Trash action that first renders a confirmation page/dialog with confirm and cancel POST paths. Test that cancellation changes nothing and confirmation permanently deletes only the tasks currently in Trash.

## 12. Configure recurrence rules on tasks
Goal: Let a user assign a supported recurrence rule to an active task.
Description: Add Django form controls and validation for frequency and interval, using daily, weekly, monthly, and yearly frequencies. Keep recurrence optional, and test that non-recurring tasks remain valid without a rule.

## 13. Define recurrence date calculations
Goal: Implement and document how the next due date is calculated for every recurrence frequency.
Description: Create a domain date-calculation utility used by Django workflows for daily, weekly, monthly, and yearly rules, including the chosen behavior for calendar edge cases such as month-end dates. Add focused tests for each frequency, intervals greater than one, and the documented edge cases.

## 14. Complete a non-recurring task
Goal: Mark a non-recurring active task as completed without creating another task.
Description: Add a Django POST completion action that updates status and records a completion timestamp. Test that the completed task leaves active views and that no additional task is created.

## 15. Complete a recurring task and create its next occurrence
Goal: Mark a recurring occurrence complete and create exactly one next active occurrence.
Description: Use the recurrence calculator from a Django POST completion workflow to create a new task with a different ID and the next due date while recording completion on the original task. Test inheritance of notes, tags, priority, and recurrence settings, along with prevention of duplicate next occurrences.

## 16. Decide and implement completed-task visibility
Goal: Establish one consistent user experience for viewing completed tasks.
Description: Record the product decision on whether completed tasks are shown, archived, or hidden by default, then implement the selected behavior in Django views, templates, and navigation. Add tests for the chosen visibility and any associated navigation or filtering.

## 17. Add persistent local storage
Goal: Preserve task data across application restarts.
Description: Use Django's ORM with SQLite as the default local persistence mechanism and connect it behind the repository interface without changing task workflows. Add tests for loading saved tasks and safely handling an empty or malformed initial database state.

## 18. Add end-to-end coverage for Trash and recurrence
Goal: Verify the highest-risk user workflows from interface to storage.
Description: Create Django test-client end-to-end tests for deleting, restoring, and emptying Trash, including the confirmation cancellation path. Add a separate scenario for completing a recurring task and verifying its completed and next occurrences through URLs, views, and persistence.

## 19. Replace the CLI prototype with the required Django application
Goal: Remove the CLI-only implementation gap and deliver the backlog through Django web workflows.
Description: Migrate or replace the current command-line prototype with the Django project established in issue 1. Preserve the tested domain behaviors, but expose them through Django URLs, forms, templates, and POST actions. Add a migration/compatibility note if any prototype-only interface is removed.
