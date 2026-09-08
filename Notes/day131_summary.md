# Day 131 Summary — Task Execution Outcomes

## Goal

Add controlled browser updates for task-execution records so an authorized
administrator can mark a running task as completed or failed and record a
result summary under its parent workflow execution.

## Completed

- Added repository functions to load task-execution snapshots by parent
  execution and atomically update one running task record.
- Added a service-layer task-outcome operation that validates input, reloads
  the signed-in account from SQLite, requires an active administrator with
  `workflows.manage`, and writes a server-generated UTC completion timestamp.
- Limited terminal outcomes to `completed` and `failed`; a saved terminal task
  cannot be changed again.
- Scoped updates to the supplied workflow ID, workflow-execution ID, and
  task-execution ID in a single SQL statement.
- Prevented task updates after the parent workflow execution reaches a terminal
  state.
- Added a protected, POST-only browser route for task outcome submissions.
- Added signed-session CSRF validation before the service layer is called.
- Added safe `400`, `403`, and `500` browser responses without database details.
- Added successful, denied-access, and invalid-CSRF activity logging.
- Rendered each execution's task snapshots under that execution, including its
  stored title, sequence, status, timestamps, and result summary.
- Added accessible, labelled per-task forms for running tasks. Forms are visible
  only to administrators who can manage workflows, while execution history
  remains readable to permitted viewers.

## How an Administrator Uses It

1. The administrator opens a workflow detail page and starts an active
   workflow. The platform creates a parent workflow execution and a running
   snapshot for each ordered task.
2. Under the matching execution in Execution history, the administrator sees a
   Task outcomes section. Each task shows its historical title, task ID,
   sequence position, current status, start time, finish time, and result
   summary.
3. For a running task in a running parent execution, the administrator enters a
   short required result summary and chooses **Mark task completed** or
   **Mark task failed**.
4. The browser sends a POST request with the signed-session CSRF token. If all
   checks pass, the application records the terminal status and a UTC finish
   timestamp, writes an activity-log entry, and redirects back to the workflow
   detail page.
5. The saved outcome appears beneath the same parent execution. Its update
   form disappears because terminal task outcomes cannot be changed.

For example, an administrator could start “New supplier onboarding,” complete
the “Collect tax form” task with “Completed: signed form received,” and fail
the “Check bank details” task with “Failed: bank account could not be
verified.” Both outcomes stay with that one historical workflow run even if the
workflow is edited later.

## What the System Checks Before Saving

The update is intentionally protected at more than one layer:

- The route requires a valid signed-in session. If the account was removed,
  deactivated, or its stored identity no longer matches the session, the user
  is redirected to sign-in before an update is attempted.
- The route requires an administrator with `workflows.manage`; viewer accounts
  can read execution history but never receive a task-outcome form.
- The submitted CSRF token must match the current signed session. Forged,
  missing, invalid, or old-session tokens are rejected before calling the
  service layer.
- The service reloads the account from SQLite and confirms its ID, active state,
  administrator role, and permission again immediately before saving.
- The repository updates only the supplied task execution when it belongs to
  the supplied parent execution and workflow, both the task and parent are
  still running, and the requested status is `completed` or `failed`.

This means a browser URL copied from another workflow run, a task ID from a
different execution, a repeated form submission, or an outdated administrator
session cannot rewrite the wrong historical record.

## Files Changed

- `Projects/employee_management_system/database.py`
- `Projects/employee_management_system/workflow_service.py`
- `Projects/employee_management_system/web_app.py`
- `Projects/employee_management_system/templates/workflow_detail.html`
- `Projects/employee_management_system/tests/test_workflow_task_executions.py`
- `README.md`

## Important Decisions

- Task records remain historical snapshots. The browser displays the stored
  task title and sequence rather than reloading the live task definition.
- The task update does not automatically finish its workflow execution. A
  workflow run remains a separate parent-level decision, matching the existing
  Day 130 workflow-execution completion behavior.
- The database checks the parent workflow and execution together as part of the
  update. A task ID from a different run or a mismatched workflow route cannot
  be changed.
- `load_authenticated_session_user()` revalidates the browser session before
  authorization, and the service repeats the database account validation before
  writing. A removed, deactivated, demoted, or identity-mismatched account is
  rejected even if it held an earlier signed session.
- The result summary is required, normalized at the service boundary, stored as
  data, and escaped by the template when displayed.

## Relationship to the Parent Workflow Outcome

Task outcomes and the overall workflow outcome are deliberately separate. A
task failure does not silently mark the parent workflow as failed, and a task
completion does not silently mark it completed. This keeps the parent decision
explicit: an administrator may need to investigate a failed optional task,
finish remaining work, or record a different overall conclusion. The existing
parent-execution completion and failure control remains responsible for that
separate decision.

## Resulting Execution Timeline

The full Days 126–131 flow now looks like this:

```text
Workflow definition and ordered tasks exist
        ↓
Authorized administrator starts an active workflow
        ↓
One WFE parent run and one WFTE snapshot per task are stored as running
        ↓
Administrator records completed or failed results for individual running tasks
        ↓
Each outcome remains under its original parent execution
        ↓
Administrator can separately decide the overall parent execution outcome
```

This timeline is designed to preserve history. It never reuses the current task
definition to overwrite an earlier run, and it never lets an already-terminal
task transition back to running or to a different terminal result.

## Safe Browser Responses

The user-facing route distinguishes the main safe cases without exposing SQLite
or implementation details:

| Situation | Browser response | Reason |
| --- | --- | --- |
| No valid authenticated session | Redirect to sign-in | The request has no current user context. |
| Viewer or account without permission | `403 Access denied.` | The user cannot update workflow execution history. |
| Missing, invalid, or old CSRF token | `403 Your form could not be verified.` | The state-changing request may be forged or stale. |
| Invalid status, blank result, wrong parent IDs, or a terminal record | `400 Task execution could not be finished.` | The request cannot safely change history. |
| SQLite operational error | `500 Task execution could not be saved.` | The user receives a safe message without database details. |
| Valid request | `303` redirect to the workflow detail page | Post/Redirect/Get avoids accidental resubmission on refresh. |

## Learning Check

**Why does the SQL update check the parent execution status?**

It prevents a late request from updating a task after the overall workflow run
has already been marked completed or failed.

**Why does the update check all three IDs: workflow, execution, and task
execution?**

It keeps the route hierarchy meaningful. A task execution from one run cannot
be updated through a URL for another run or another workflow.

**Why does the form disappear after success?**

The saved task is no longer `running`. Hiding the controls communicates the
one-time terminal-state rule, while the repository independently enforces it.

**Why are viewer accounts still allowed to see outcomes?**

`workflows.view` remains a read-only permission. It lets viewers understand
workflow history without giving them authority to alter it.

**Why keep the activity log if the database already stores an outcome?**

The task-execution record describes what happened to the work item. The audit
log describes the security-relevant browser event, including who performed a
successful update or attempted a denied or invalid-CSRF action.

## Tests

Focused Day 131 coverage verifies:

- Ordered, execution-scoped task snapshot loading.
- Successful completion and failure updates with UTC completion timestamps.
- Immutable saved snapshot fields and one-time terminal transitions.
- Rejection of blank input, unknown status, missing records, and mismatched
  workflow/execution/task parent relationships.
- Rejection after a parent execution is already completed or failed.
- Service-layer rejection of viewer, inactive, missing, demoted, and
  identity-mismatched accounts.
- Browser success, redirect behavior, escaped output, accessible labels, and
  hidden update controls for viewers.
- Anonymous, viewer, missing-permission, missing-CSRF, invalid-CSRF, and
  session-rotation rejection before service calls.
- Revoked browser account rejection, safe loading and storage errors, and
  repository rollback after a failed write.

Verification completed successfully:

- **10 focused Day 131 tests passed**
- **438 total automated tests passed**
- No failures or errors remained

## Concepts Practiced

- Parent-child database scoping
- Atomic conditional updates
- Terminal-state transitions
- Defense-in-depth session revalidation
- Signed-session CSRF protection
- Post/Redirect/Get navigation
- Historical execution snapshots
- Accessible form labels and fieldsets
- Safe browser error boundaries
- Activity audit logging

## Current ABAP Status

Day 131 is complete. Workflow Automation now records running task snapshots
when a workflow run starts and lets authorized administrators record a single
completed or failed outcome for each task while the parent execution is still
running.

## Next Step

Choose the next workflow capability from the roadmap: scheduling workflows or
adding more controlled task-processing rules, such as sequential task release
or parent-execution outcome validation.
