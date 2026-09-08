# Day 130 Summary — Task Execution Foundation

## Milestone

Days 126 through 130 establish parent-child execution history for Workflow
Automation. An active workflow can now be started by an authorized
administrator, producing one workflow-execution record and one running
task-execution snapshot for every ordered task present at that time.

## What ABAP Can Explain Now

For a past workflow run, the platform can retain:

- The workflow ID and its name at the time the run started.
- The account that started the run and the UTC start time.
- The overall workflow status and result summary.
- Every task that belonged to the run, in the sequence that applied then.
- Each task’s historical title, task ID, status, timestamps, and result summary.

This is stronger than looking up today’s workflow definition after the fact.
The definition might have been edited, resequenced, or deleted, while the
execution history should continue to explain the earlier run accurately.

## Example

If the “New supplier onboarding” workflow contains “Collect tax form,” “Check
bank details,” and “Approve supplier” when an administrator starts it, the run
stores those three task snapshots. If the workflow is later changed to add a
fourth task or rename one of the originals, the earlier run continues to show
the three tasks that actually belonged to that run.

## Architecture

- `models.py` defines the typed `WorkflowTaskExecution` shape.
- `database.py` creates the child table, inserts snapshot records, and enforces
  its relationship to the parent execution.
- `workflow_service.py` validates an active administrator, creates the parent
  run, and creates its ordered task snapshots.
- `web_app.py` retains the administrator-only, CSRF-protected execution-start
  route and safe browser errors.
- `tests/test_workflow_executions.py` validates the execution foundation.

The browser, service, and repository remain separate. The browser handles
session access and CSRF; the service owns business validation and live account
revalidation; the repository owns SQL and transaction handling.

## Security and Data Safety

Workflow execution starts require `workflows.manage`. The browser reloads the
account from SQLite, rejects inactive or mismatched sessions, and requires a
signed-session CSRF token. The service repeats account validation before it
writes. The database uses foreign keys, stable IDs, UTC timestamps, controlled
statuses, and parameterized SQL.

## What an Execution Record Means

It helps to read the historical records as a hierarchy:

```text
Reusable workflow definition: WF-ONBOARD
    ├── Task 1: Collect tax form
    ├── Task 2: Check bank details
    └── Task 3: Approve supplier

Historical workflow execution: WFE-... (started 2026-09-08)
    ├── Task execution: WFTE-... Collect tax form
    ├── Task execution: WFTE-... Check bank details
    └── Task execution: WFTE-... Approve supplier
```

The top part is a template that administrators can maintain. The lower part is
evidence of one particular run. A future second run receives a different
`WFE-...` ID and different `WFTE-...` child IDs, even if it starts from the same
workflow definition.

## Benefits for Future Features

The completed foundation makes later features more straightforward because they
can work with one precise historical record:

- A manual completion screen can update one task execution.
- A failure screen can add a useful reason without overwriting the task title.
- A report can calculate how many task executions completed or failed.
- A scheduler can create a new parent run at the correct time.
- A worker can record one integration or AI result against one task execution.
- A retry design can preserve the failed run while creating a new attempt.

None of those features need to mutate the reusable workflow definition to
describe what happened in the past.

## Questions and Answers

**Why are task snapshots created at workflow start instead of task finish?**

Creating them at start captures the complete plan for that run before the
definition can change. It also lets the application later show which tasks were
still pending if the run stops early.

**Why preserve the workflow name as well as its ID?**

The ID provides a stable technical reference. The name makes historical records
readable and preserves the wording that users saw when the run started.

**Can a viewer start a workflow?**

No. Viewers have read-only workflow access. Starting a run requires the
administrator-only `workflows.manage` permission.

**Can the start action bypass CSRF protection?**

No. The browser route requires the signed-session CSRF token before calling the
service that creates the execution data.

## Scope Boundary

The milestone records work; it does not claim that instructions have been
performed. At the end of Day 130, every task starts as `running`, but there is
no task-level completion or failure control and no task outcomes are displayed
under their parent workflow execution yet.

## Verification

Focused execution tests covered active-workflow starts, snapshot preservation,
ordering and scoping, draft-workflow rejection, viewer rejection, and stale
identity rejection. The full regression suite passed with **428 tests**.

## Next Step

Add administrator-only task completion and failure updates, then show the saved
task outcomes beneath their parent workflow execution.
