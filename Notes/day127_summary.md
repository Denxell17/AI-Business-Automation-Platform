# Day 127 Summary — Task Snapshot Creation

## Goal

Connect the Day 126 task-execution records to the established workflow-start
operation. Starting an active workflow should create a complete, durable list
of the tasks that belonged to that specific run.

## What Happens When a Workflow Starts

The existing `start_workflow_execution()` service first validates the live
administrator account and confirms that the workflow is active. It then creates
the parent workflow-execution record. After the parent is saved, the service
loads the workflow’s tasks in sequence order and creates one child
`workflow_task_executions` row per task.

Each new child record:

- Receives a generated `WFTE-...` task-execution ID.
- References the new parent execution.
- Copies the workflow task ID, title, and sequence number.
- Begins with status `running`.
- Uses the same UTC start time as the parent workflow run.
- Starts with the safe summary `Task execution started.`

For example, a workflow with three ordered tasks produces one parent workflow
execution and three child task-execution snapshots when it starts. A later run
of the same workflow produces a new parent and a new set of child records.

## Why This Matters

The application no longer has to reconstruct history from the current workflow
definition. If an administrator edits the workflow after a run starts, the run
still retains the task title and sequence that applied when it began. This is
important for auditability, reporting, retries, and explaining what a past run
actually contained.

It also gives future task-completion actions an exact record to update. A later
feature can target a task-execution ID rather than guessing which task version
or workflow revision the administrator intended.

## Safety Decisions

- Only active workflows can start, so drafts and inactive workflows do not
  create execution history.
- Workflow start continues to require an active, revalidated administrator with
  `workflows.manage`.
- Tasks are loaded in their established sequence order before snapshots are
  created.
- The parent execution is written before its child records, which respects the
  foreign-key relationship.
- The snapshot uses copied values, so later workflow-task maintenance cannot
  rewrite past execution history.

## What This Does Not Do Yet

Creating a `running` task snapshot does not mean the browser or a background
worker performed the task. It establishes an auditable work item. Day 127 does
not provide completion, failure, or task-result controls yet.

## Important Files

- `Projects/employee_management_system/workflow_service.py` adds child snapshot
  creation to the workflow-start service flow.
- `Projects/employee_management_system/database.py` stores the new records.
- `Projects/employee_management_system/tests/test_workflow_executions.py`
  verifies parent execution creation and snapshot behavior.

## Start-Execution Sequence

The following sequence shows the difference between a reusable workflow and a
historical run:

```text
Administrator chooses Start execution
        ↓
Browser verifies signed session and CSRF token
        ↓
Service reloads the saved account and checks workflows.manage
        ↓
Service confirms the workflow exists and is active
        ↓
Repository saves parent WFE workflow-execution record
        ↓
Service loads current tasks in sequence order
        ↓
Repository saves one WFTE task-execution snapshot per task
        ↓
Browser returns to the workflow detail page
```

The shared start timestamp is intentional. It records that the workflow run and
its initial list of work items were created together. A later finish timestamp
belongs to an individual task and records when its outcome was saved.

## Example

Suppose an active workflow has these reusable tasks before it starts:

1. Confirm request
2. Process request
3. Notify requester

Starting the workflow creates a new parent run and three independent task
snapshots. If task 2 is later edited in the definition, all three snapshots
remain unchanged. If task 3 is deleted from the definition, the already-started
run still retains task 3 because it was part of that historical work.

## Failure Cases That Are Rejected

- A blank workflow ID cannot start a run.
- A missing workflow cannot start a run.
- A draft or inactive workflow cannot start a run.
- A viewer cannot start a run because the viewer role lacks `workflows.manage`.
- A session whose user ID does not match the saved account cannot start a run.
- A deactivated or removed saved account cannot start a run.

These checks happen before the application creates child snapshots. They ensure
that the history only records work started through the intended administrator
path.

## Learning Check

**Why load tasks in sequence order?**

The task execution list should reflect the business order that the workflow
used, rather than an accidental database insertion order.

**Why create a new task snapshot for every run?**

The same workflow can run many times. Each run needs its own independent
outcomes, timestamps, and task list.

**Does Day 127 execute the task instructions?**

No. It records that the task belongs to the run and begins in `running` state.

## Next Step

Keep task execution separate from actual instruction processing, then add
controlled task-level outcomes and browser display.
