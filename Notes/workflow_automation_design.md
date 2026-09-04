# Workflow Automation Domain Design

## Purpose

The Workflow Automation module will let authorized ABAP users define reusable
business processes, break them into ordered tasks, optionally schedule them,
and review completed or failed executions.

This design establishes the domain model before SQLite tables, services, or
browser routes are added.

## Scope for the First Workflow Automation Release

The first release will support:

- Creating, viewing, editing, activating, and deactivating workflows
- Adding ordered manual workflow tasks
- Creating enabled or disabled schedules for active workflows
- Starting a workflow execution manually
- Recording execution status and task-level results
- Viewing execution history

The first release will not yet send emails, call external APIs, run AI agents,
or execute background jobs automatically. Those capabilities will be added only
after the reliable workflow foundation exists.

## Core Entities

### Workflow

A workflow is a reusable business process definition.

Examples:

- New employee onboarding
- Weekly customer follow-up review
- Invoice approval process

Each workflow has:

- `workflow_id` — stable public identifier, such as `WF-000001`
- `name` — short human-readable workflow name
- `description` — optional explanation of the business purpose
- `status` — `draft`, `active`, or `inactive`
- `created_by_user_id` — user account that created the workflow
- `created_at` — UTC creation timestamp
- `updated_at` — UTC timestamp of the latest saved workflow change

Rules:

- Workflow names must be required after trimming whitespace.
- Status values must be allowlisted.
- A draft workflow cannot be scheduled.
- An inactive workflow cannot be started or scheduled.
- A workflow may have zero tasks while it is a draft.
- A workflow must have at least one task before it can become active.

### Workflow Task

A workflow task is one ordered step inside a workflow.

Examples:

- Confirm employee documents
- Review customer details
- Approve invoice information

Each task has:

- `task_id` — stable public identifier, such as `WFT-000001`
- `workflow_id` — parent workflow identifier
- `sequence_number` — positive integer determining task order
- `title` — required human-readable task name
- `instructions` — optional guidance for the person or future automation
- `task_type` — initially only `manual`
- `is_required` — whether the task must be completed for a successful run
- `created_at` — UTC creation timestamp
- `updated_at` — UTC timestamp of the latest saved task change

Rules:

- A task belongs to exactly one workflow.
- Sequence numbers are unique within a workflow.
- Task titles must be required after trimming whitespace.
- Task types must be allowlisted.
- The initial release supports only `manual`; later versions may add
  `email`, `webhook`, and `ai_agent`.
- Deleting a task must not silently change task order; remaining tasks must be
  deliberately resequenced in the same database transaction.

### Workflow Schedule

A schedule defines when an active workflow should become eligible to run.

Each schedule has:

- `schedule_id` — stable public identifier, such as `SCH-000001`
- `workflow_id` — workflow to run
- `schedule_type` — initially `daily`, `weekly`, or `manual`
- `scheduled_time` — optional local clock time in `HH:MM` format
- `day_of_week` — optional weekday required for weekly schedules
- `is_enabled` — whether the schedule may run
- `created_by_user_id` — user account that created the schedule
- `created_at` — UTC creation timestamp
- `updated_at` — UTC timestamp of the latest saved schedule change

Rules:

- A schedule belongs to exactly one active workflow.
- `schedule_type` must be allowlisted.
- A daily schedule requires `scheduled_time`.
- A weekly schedule requires both `scheduled_time` and `day_of_week`.
- A manual schedule has no automatic time requirement.
- An inactive workflow must not retain enabled schedules.
- The first release stores schedules but does not yet run a background worker.

### Workflow Execution

An execution is one historical attempt to run a workflow.

Each execution has:

- `execution_id` — stable public identifier, such as `EXE-000001`
- `workflow_id` — workflow definition that was run
- `trigger_type` — `manual` or `schedule`
- `status` — `pending`, `running`, `completed`, `failed`, or `cancelled`
- `started_by_user_id` — optional user who manually started the execution
- `started_at` — UTC start timestamp
- `completed_at` — optional UTC completion timestamp
- `error_message` — optional safe operational failure summary

Rules:

- Trigger and status values must be allowlisted.
- Only active workflows can start new executions.
- A completed, failed, or cancelled execution is final and cannot return to
  `pending` or `running`.
- Failure messages must not expose secrets, database details, or raw exception
  traces.
- Execution history is append-only; it is not edited after creation.

### Task Execution

A task execution records the result of one workflow task during one workflow
execution.

Each task execution has:

- `task_execution_id` — stable public identifier, such as `TEX-000001`
- `execution_id` — parent workflow execution identifier
- `task_id` — source workflow task identifier
- `sequence_number` — task order captured at execution start
- `status` — `pending`, `completed`, `failed`, or `skipped`
- `completed_by_user_id` — optional user who completed a manual task
- `completed_at` — optional UTC completion timestamp
- `result_note` — optional safe completion or failure note

Rules:

- Task executions are created from the workflow task list when an execution
  starts.
- Capturing `sequence_number` preserves historical ordering even when a
  workflow is edited later.
- A required task that fails prevents the workflow execution from being marked
  completed.
- Task execution history is append-only.

## Entity Relationships

```text
User account
    ├── creates → Workflow
    ├── creates → Workflow Schedule
    └── starts or completes → Workflow Execution / Task Execution

Workflow
    ├── contains → Workflow Task
    ├── has → Workflow Schedule
    └── produces → Workflow Execution

Workflow Execution
    └── contains → Task Execution
```

## Initial Authorization Direction

The existing role model remains in effect:

- Administrators will manage workflow definitions, tasks, and schedules.
- Administrators and viewers may later receive separate explicit permissions
  for viewing workflows and execution history.
- New workflow permissions will be defined explicitly and denied by default.
- The first database design will store creator and actor user IDs for audit
  context without exposing password hashes or sensitive account data.

## Implementation Order

1. Define TypedDict models and allowlisted status constants.
2. Add SQLite tables, foreign-key relationships, indexes, and schema tests.
3. Add repository functions for safe workflow CRUD.
4. Add service-layer validation and workflow status transitions.
5. Add protected FastAPI routes and server-rendered workflow pages.
6. Add CSRF-protected administrator forms for state-changing actions.
7. Add execution-history pages and activity logging.
8. Add scheduling and background execution only after the manual workflow
   foundation is verified.

## Security and Data-Safety Decisions

- All state-changing browser routes will use POST and signed-session CSRF
  validation.
- Every submitted status, task type, schedule type, and trigger type will be
  validated against a server-side allowlist.
- SQLite changes that affect task order or workflow activation will use
  transactions.
- Workflow and execution error pages will show safe messages rather than
  internal database details.
- Authorization will be default-deny and based on explicit permissions.
- Activity logging will record successful sensitive workflow actions and
  denied access where appropriate.