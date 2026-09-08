# Day 126 Summary — Task Execution Records

Task execution records provide a child audit record for every task in a workflow run. Each row snapshots the task ID, sequence, title, running status, timestamps, and safe result summary. A task execution is linked to its parent workflow execution, so the database can answer both “how did the overall workflow end?” and, later, “what happened to this particular task?”

## Design Decision

The task execution record stores copied task information instead of only a link to the current workflow task. Workflow definitions are editable. A historical run must continue to show the task title and position that were present when it began, even if an administrator later changes the workflow.

## Data Safety

The table uses a stable task-execution ID, allowlisted status values, UTC timestamps, parameterized SQL, and a foreign key to the parent execution. These rules make future reporting and task-level status updates reliable.

## Next Step

Create task snapshots when a workflow execution starts.
