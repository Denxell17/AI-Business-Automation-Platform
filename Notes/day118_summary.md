# Day 118 Summary — Workflow Task Resequencing

## Goal

Let administrators change task order while protecting the workflow from
duplicates, missing tasks, and partial updates.

## Completed

- Added GET and POST routes at
  `/workflows/{workflow_id}/tasks/resequence`.
- Added `workflow_task_resequence_form.html`.
- Added Set task order to workflow detail when tasks exist.
- Rendered one position selector for every saved task.
- Required every saved task to appear exactly once.
- Saved contiguous positions starting at `1`.
- Used one SQLite transaction for the complete order change.
- Redirected success to workflow detail and logged it.
- Returned safe validation, authorization, missing-record, and storage errors.

## How It Works

The GET route displays the current ordered list. Each numbered position has a
selector containing all task IDs and titles. The POST route validates the
session and CSRF token, then sends the order to the service. Duplicate,
missing, extra, or foreign task IDs are rejected. The repository temporarily
moves current positions outside the final range, writes `1` through `n`, and
commits once.

## Why ABAP Needs This

Sequence represents business-process order. A partial update could create
duplicates or an incomplete workflow, so resequencing must succeed or fail as
one unit.

## Important Files and Functions

- `Projects/employee_management_system/web_app.py`
- `Projects/employee_management_system/templates/workflow_task_resequence_form.html`
- `Projects/employee_management_system/workflow_service.py`
  - `resequence_workflow_task_list()`
- `Projects/employee_management_system/database.py`
  - `resequence_workflow_tasks()`

## Data-Safety Decisions

- Viewers cannot open or submit the page.
- The order must describe the complete saved task set.
- Duplicate choices are rejected.
- A failed order leaves original records unchanged.
- Final positions are deterministic and gap-free.

## Tests

Coverage verifies reversed ordering, contiguous positions, duplicate and
missing-task rejection, unchanged records after failure, browser submission,
redirected display, and viewer denial.

## Concepts Practiced

- Multi-value form fields
- Set equality and duplicate detection
- Atomic multi-row updates
- Temporary unique positions
- Transaction rollback

## Current ABAP Status

Day 118 is complete. Administrators can deliberately reorder all tasks without
direct database changes.

## Next Step

Day 119 prevents an empty workflow from becoming active.
