# Day 122 Summary — Workflow Execution Records

## Goal

Create the first durable record of a workflow run without yet performing its
tasks in the background.

## Completed

- Added a `workflow_executions` SQLite table and typed execution record.
- Each record has a stable execution ID, workflow ID, workflow-name snapshot,
  lifecycle status, starter account, UTC timestamps, and safe result summary.
- Added the constrained execution lifecycle: `running`, `completed`, and
  `failed`.
- Added repository insertion and workflow-scoped newest-first loading.
- Added administrator-only execution starts for active workflows.
- Added a CSRF-protected Start execution action on active workflow pages.
- Added read-only execution history to the protected workflow detail page.
- Logged denied access, invalid CSRF, and successful execution starts.

## Why the Workflow Name Is Saved Again

An execution saves the workflow name as it was when the run began. If an
administrator later renames the workflow, older records still clearly show the
business-process name that applied at the time. This is the beginning of an
audit-friendly execution history.

## Security Decisions

- Starting a run requires an authenticated administrator with
  `workflows.manage`.
- The service reloads the saved account from SQLite and rejects missing,
  deactivated, mismatched, or unauthorized identities.
- Only active workflows can start an execution.
- The browser validates signed-session CSRF before calling the service.
- The repository uses parameterized SQL and foreign keys for workflow and user
  references.
- Browser errors remain safe and do not expose SQLite details.
- Viewers can read execution history but cannot see or submit the start action.

## Scope Boundary

Starting an execution records a `running` state and does not yet perform tasks,
schedule work, invoke AI, or change an execution to `completed` or `failed`.
Those capabilities require the next execution-lifecycle slice.

## Files Changed

- `Projects/employee_management_system/models.py`
- `Projects/employee_management_system/database.py`
- `Projects/employee_management_system/workflow_service.py`
- `Projects/employee_management_system/web_app.py`
- `Projects/employee_management_system/templates/workflow_detail.html`
- `Projects/employee_management_system/tests/test_workflow_executions.py`
- `Projects/employee_management_system/tests/test_workflow_web_lifecycle.py`
- `README.md`
- `Notes/day122_summary.md`

## Tests

Focused coverage verifies execution creation, stored snapshots, workflow-scoped
loading, active-status enforcement, viewer and stale-session denial, CSRF
rejection, administrator browser starts, activity logging, and viewer-safe
display.

## Current ABAP Status

Day 122 establishes durable workflow execution history. Administrators can
start an active workflow and the platform records the start safely for later
completion, failure, and task-result work.

## Next Step

Add controlled execution completion and failure updates, including finished
timestamps and safe result summaries, before introducing individual task
results or background processing.
