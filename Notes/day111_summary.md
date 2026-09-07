# Day 111 Summary — Ordered Workflow Task Storage

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

## Files Changed

- Projects/employee_management_system/models.py
- Projects/employee_management_system/database.py
- Projects/employee_management_system/tests/test_workflow_tasks.py
- Notes/day111_summary.md

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

## Current ABAP Status

Day 110's workflow lifecycle slice now has ordered manual task persistence.
Task management and display have not yet been exposed in the browser.

## Next Step

Show saved tasks in sequence order on the protected workflow detail page,
including a clear empty state and administrator/viewer read-access tests.
