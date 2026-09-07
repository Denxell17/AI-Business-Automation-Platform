# Day 111 Summary — Ordered Workflow Task Storage

## Goal

Model and persist the ordered manual steps that belong to a workflow.

## Completed

- Added the WorkflowTask TypedDict and manual task-type allowlist.
- Added the workflow_tasks table through the existing idempotent initializer.
- Added insert_workflow_task() and load_workflow_tasks() repository functions.
- Retrieval is scoped to one workflow and sorted by sequence_number.
- Followed the existing domain design: title, instructions, task type, required
  flag, and creation/update timestamps accompany each stable task ID.

## Why and Technical Decisions

Tasks are reusable process steps. This storage foundation will support showing
ordered steps on the workflow detail page.

- Sequence numbers are positive integers, unique within each workflow; gaps
  are allowed. The unique constraint also indexes workflow/order lookups.
- Foreign keys reject tasks whose parent workflow does not exist.
- SQLite rejects blank task IDs/titles, unsupported types, invalid required
  flags, and duplicate IDs or sequence numbers.
- Inserts use parameterized SQL and roll back on integrity failures.
- Repository functions are internal persistence helpers, not authorization
  boundaries. Task write services and browser forms remain future work.
- Workflow activation behavior is unchanged. The design's requirement for at
  least one task before activation still needs a later service-layer change.

## How It Works

`WorkflowTask` defines the Python record shape. `initialize_database()` creates
the `workflow_tasks` table idempotently, so existing databases gain the table
without losing data. `insert_workflow_task()` uses parameterized SQL and
`load_workflow_tasks()` selects only one workflow's records ordered by
`sequence_number`.

The parent workflow foreign key prevents orphaned tasks. The combined unique
constraint on workflow ID and sequence number allows different workflows to
reuse position `1` while preventing two tasks from occupying the same position
inside one workflow.

## Files Changed

- Projects/employee_management_system/models.py
- Projects/employee_management_system/database.py
- Projects/employee_management_system/tests/test_workflow_tasks.py
- Notes/day111_summary.md

## Security and Data-Safety Decisions

- Task types are allowlisted; the first release supports only `manual`.
- Task IDs and titles cannot be blank after trimming.
- Sequence numbers must be positive SQLite integers.
- Required flags are stored as constrained `0` or `1` values and loaded as
  Python Booleans.
- Foreign-key enforcement is enabled on every connection.
- Duplicate and invalid records return `False` after rollback.

## Tests

- 6 new task persistence tests passed, covering field/boolean round trips,
  ordering, workflow isolation, empty reads, invalid data, duplicates, and
  repeated initialization preserving records.
- 8 existing workflow service/lifecycle tests passed.
- 45 existing database tests passed.
- git diff --check passed.
- Browser lifecycle tests could not import because the bundled Python runtime
  lacks FastAPI. Full regression was not run. System Python 3.9 also cannot
  evaluate the project's existing union type annotations; successful tests used
  the bundled newer Python runtime.

## Concepts Practiced

- Parent-child database relationships
- Composite uniqueness
- `TypedDict` domain models
- Boolean-to-SQLite conversion
- Ordered repository queries
- Idempotent schema initialization

## Current ABAP Status

Day 110's workflow lifecycle slice now has ordered manual task persistence.
Task management and display have not yet been exposed in the browser.

Day 111 is complete.

## Next Step

Show saved tasks in sequence order on the protected workflow detail page,
including a clear empty state and administrator/viewer read-access tests.
