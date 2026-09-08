# Day 124 Summary — Execution Lifecycle Review and Scope Boundary

## Goal

Review the execution-history work before adding more automation. The review
ensures the platform has one clear workflow-level lifecycle rather than mixing
workflow outcomes, individual task outcomes, schedules, and background work in
one unsafe feature.

## Confirmed Lifecycle

Every workflow execution follows this path:

1. An authorized administrator starts an **active** workflow.
2. The platform saves a `running` execution record with workflow and starter
   snapshots plus a UTC start time.
3. An authorized administrator records one terminal outcome: `completed` or
   `failed`.
4. SQLite rejects further terminal changes after the execution leaves
   `running`.

The lifecycle is intentionally small and easy to audit. It answers: “Was this
workflow run started, and how did it end?” It does not yet answer: “Which task
failed?”, “When should it run?”, or “Should the system retry it?”

## Architectural Decision

Workflow executions and task executions must remain separate records.

A workflow execution is the overall business-process run. A future task
execution belongs to one workflow execution and describes one ordered task's
own state, timestamps, and result. Keeping these levels separate prevents a
single failed task from overwriting the workflow-level history and gives future
reporting a clear parent-child structure.

## Security and Data-Safety Review

- Execution actions use the existing `workflows.manage` permission.
- Stored accounts are revalidated before service changes.
- Browser actions require a signed-session CSRF token.
- SQL remains parameterized and references existing workflows and users with
  foreign keys.
- Only `running` records can become terminal, which protects outcome history.
- Viewers remain read-only.
- Safe messages are returned for missing or invalid records instead of raw
  SQLite errors.

## Scope Boundary

The following work remains deliberately out of scope after Day 124:

- Task-execution tables and task-level status transitions.
- Automated processing of manual task instructions.
- Schedules, time zones, queueing, retries, and background workers.
- AI calls, webhooks, notifications, and external-service integration.

These features need their own validation rules, failure behavior, and tests.
Adding them before the execution foundation is clear would make it difficult to
explain which part of the automation actually succeeded or failed.

## Next Step

Day 125 documents the verified milestone. The next implementation milestone is
task-execution records linked to the workflow execution ID, followed by
controlled processing of the existing manual task type.
