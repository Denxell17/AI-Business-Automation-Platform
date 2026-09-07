# Day 114 Summary — Workflow Task Creation Form

## Goal

Let administrators add validated ordered manual tasks from the workflow detail
page.

## Completed

- Added administrator-only task creation GET and POST routes.
- Added a CSRF-protected form for task ID, sequence, title, instructions, and
  required/optional status.
- Added the Add task action to the administrator workflow-detail page.
- Reused the Day 113 creation service and redirected successful submissions to
  the workflow detail page.
- Preserved values and returned a safe 400 form error for validation failures.
- Logged denied access, invalid CSRF attempts, and successful task creation.

## How It Works

The GET route authorizes the administrator, verifies the parent workflow, and
renders a form with a signed-session CSRF token. The POST route repeats the
authorization check, validates CSRF, converts the sequence field, allowlists
the required checkbox, and calls `create_workflow_task()`.

A successful submission redirects to workflow detail, where the new task is
loaded through the ordered repository query. A rejected submission returns
HTTP `400` with the entered task ID, sequence, title, instructions, and required
choice preserved.

## Security Decisions

- Route permission checks happen before task storage is accessed.
- CSRF validation happens before task creation is attempted.
- Required flags are allowlisted as true/false, so malformed values return the
  form error rather than a framework validation response.
- SQLite failures are converted to a generic response without exposing details.
- Viewers are denied before CSRF or service calls.
- Task text is escaped when the form or detail page renders it.
- Post/Redirect/Get prevents refresh from creating the task again.

## Files Changed

- Projects/employee_management_system/web_app.py
- Projects/employee_management_system/templates/workflow_detail.html
- Projects/employee_management_system/templates/workflow_task_form.html
- Projects/employee_management_system/tests/test_workflow_web_lifecycle.py
- Notes/day114_summary.md

## Important Routes and Functions

- `GET /workflows/{workflow_id}/tasks/new`
- `POST /workflows/{workflow_id}/tasks/new`
- `workflow_task_create_form()` and `workflow_task_create()` in `web_app.py`
- `create_workflow_task()` in `workflow_service.py`

## Tests

- 16 focused browser lifecycle tests passed.
- 15 focused task service/storage tests passed.
- Full regression: all 409 automated tests passed.
- git diff --check passed.

Coverage includes administrator success, redirect behavior, saved display,
value preservation, malformed required values, invalid CSRF, viewer denial,
anonymous behavior, and safe database-error responses.

## Concepts Practiced

- Nested creation routes
- CSRF-protected state changes
- HTML checkbox normalization
- Service reuse from browser routes
- Safe form validation errors
- Post/Redirect/Get navigation
- Activity logging

## Current ABAP Status

Administrators can now add ordered manual tasks while administrators and
viewers can review them on the protected workflow detail page.

Day 114 is complete.

## Next Step

Add task editing and deliberate resequencing, so administrators can correct a
task without relying on direct database changes.
