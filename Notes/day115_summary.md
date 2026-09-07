# Day 115 Summary — Workflow Task Maintenance Repository

## Goal

Add SQLite repository functions for finding, editing, and reordering workflow
tasks without letting browser routes write SQL directly.

## Completed

- Added `load_workflow_task_by_id()` for stable task-ID lookup.
- Added `update_workflow_task()` for title, instructions, required status, and
  update timestamp changes.
- Preserved task ID, parent workflow, sequence, type, and creation timestamp.
- Added `resequence_workflow_tasks()` for complete-list order changes.
- Required the submitted order to contain every saved task exactly once.
- Saved final positions as positive, contiguous integers starting at `1`.

## How It Works

A normal edit changes task content but cannot move the task or transfer it to
another workflow. Resequencing is a separate operation because several rows
must change together. The repository verifies the complete task list, moves
existing positions temporarily outside the final range, assigns positions
`1` through `n`, and commits once. SQLite rolls back a failed transaction.

## Why ABAP Needs This

Task order affects how a business process will run. Central repository
functions keep SQL consistent and stop an ordinary text edit from silently
changing process order.

## Important Files and Functions

- `Projects/employee_management_system/database.py`
  - `load_workflow_task_by_id()`
  - `update_workflow_task()`
  - `resequence_workflow_tasks()`
- `Projects/employee_management_system/models.py`
  - `WorkflowTask`

## Data-Safety Decisions

- SQL remains parameterized.
- Updates require both task ID and workflow ID to match.
- Resequencing validates the complete saved task set first.
- Sequence changes use one transaction and roll back on failure.
- Final task positions are deterministic and gap-free.

## Tests

Maintenance coverage verifies preserved identity fields, final ordering,
contiguous positions, duplicate rejection, missing-task rejection, and
unchanged records after a rejected order.

## Concepts Practiced

- Repository-layer separation
- Stable record identity
- Partial SQL updates
- Multi-row transactions
- Unique-constraint collision avoidance
- Rollback-safe reordering

## Current ABAP Status

Day 115 is complete. SQLite supports safe task lookup, detail updates, and
complete workflow-task resequencing.

## Next Step

Day 116 adds authorization and validation around these repository operations.
