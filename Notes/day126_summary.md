# Day 126 Summary — Task Execution Records

## Goal

Begin the execution-history milestone by defining a durable database record for
each task that belongs to a workflow run. Before this work, ABAP could retain a
workflow execution, but it could not answer which individual tasks were part of
that run or later attach a result to each task.

## What Was Added

Day 126 introduced the `workflow_task_executions` data model. A task-execution
record is a child of one workflow execution and represents one historical task
within that run. It contains:

- A stable public ID such as `WFTE-...`.
- The parent workflow execution ID.
- The original workflow task ID, sequence number, and title.
- A task status, start time, optional finish time, and result summary.

The table has a foreign key to `workflow_executions`. This protects the parent
and child relationship: a task-execution record cannot point to an execution
that does not exist. The database also uses the established connection setup,
including foreign-key enforcement, for every operation.

## Why Task Data Is Snapshotted

Workflow definitions are reusable and editable. An administrator might rename a
task, change its instructions, resequence it, or remove it after a run starts.
Historical execution data should still describe the work that actually existed
at that moment.

For that reason, the task-execution record stores copied task identity and
display information rather than relying only on the current `workflow_tasks`
row. For example, if task 2 was called “Review invoice” when a run began and is
later renamed “Review supplier invoice,” the earlier run can still show the
original title and original position.

## Security and Data Safety

- Task executions use generated stable IDs instead of exposing SQLite row IDs.
- Status values are designed to be controlled by the application rather than
  accepted as arbitrary text.
- Timestamps use UTC, so execution history stays consistent across time zones.
- Database writes use parameterized SQL, which keeps submitted values separate
  from SQL commands.
- The parent foreign key prevents orphaned execution-history records.
- The design preserves a clear separation between workflow definitions,
  workflow executions, and task executions.

## What This Does Not Do Yet

Day 126 creates the storage foundation only. It does not start task snapshots,
run task instructions, show task outcomes in the browser, or permit updates.
Those functions are deliberately separate so later work can add authorization,
auditing, and browser controls without weakening the data model.

## Important Files

- `Projects/employee_management_system/models.py` defines the typed
  `WorkflowTaskExecution` record shape.
- `Projects/employee_management_system/database.py` creates and persists the
  task-execution table.

## Field-by-Field Reference

| Field | Meaning | Why it is retained |
| --- | --- | --- |
| `task_execution_id` | The unique public ID for this one historical task run. | Lets later routes and audit entries point to the exact record. |
| `execution_id` | The parent workflow run. | Groups all task outcomes belonging to one workflow run. |
| `task_id` | The workflow-definition task that was copied. | Keeps a connection to the original reusable task. |
| `sequence_number` | The task’s position when the workflow started. | Preserves the original order even if the definition is resequenced. |
| `task_title` | The task name when the run started. | Makes history readable even after a later rename. |
| `status` | `running`, `completed`, or `failed`. | Describes the state of this task within this run. |
| `started_at` / `finished_at` | UTC timestamps. | Makes duration and timeline reporting possible later. |
| `result_summary` | A short human-readable outcome. | Explains the result without needing to read logs. |

## Example History

Imagine the reusable workflow `WF-ONBOARD` has two tasks: “Create user
account” at position 1 and “Send welcome email” at position 2. An administrator
starts it at 09:00 UTC. The future execution history can contain records like
this:

| Parent execution | Task execution | Task title | Position | Status |
| --- | --- | --- | --- | --- |
| `WFE-...A1` | `WFTE-...B1` | Create user account | 1 | Running |
| `WFE-...A1` | `WFTE-...B2` | Send welcome email | 2 | Running |

If the workflow is edited at 10:00 UTC so “Send welcome email” becomes
“Send welcome email and handbook,” the two rows above still retain the wording
that was present at 09:00 UTC. A new execution would get a new snapshot with
the changed title.

## Learning Check

**Why is a task execution not the same thing as a workflow task?**

A workflow task is the editable reusable template. A task execution is the
historical record of one copy of that task in one particular workflow run.

**Why copy the sequence number?**

The current task order can change later. Copying the position means a past run
keeps the order that was actually used.

**Why does `finished_at` allow an empty value?**

New task executions begin running, so they have a start time but no finish time
until a later controlled completion or failure update occurs.

## Next Step

Create one running task snapshot for every ordered task when an administrator
starts an active workflow execution.
