# Day 128 Summary — Task Execution Boundary

## Goal

Define what “starting an execution” means at this stage of ABAP. This protects
the roadmap from claiming automation that has not been built and keeps the
execution data model ready for future workers, AI calls, and scheduling.

## The Current Meaning of a Running Task

When an administrator starts an active workflow, ABAP creates a workflow run
and one `running` task-execution snapshot for each task in that run. At this
stage, `running` means the task is an active, auditable work item. It does not
mean that the platform has already performed the task’s manual instructions.

For example, a task titled “Approve customer refund” may appear as running
after a workflow starts. The record documents that this task belongs to the
current run. It does not automatically approve a refund, send an email, invoke
an AI model, or call an external system.

## Why the Boundary Is Important

Separating records from task processing prevents a Start execution button from
being mistaken for a background-job system. It gives the platform a reliable
audit trail now without introducing unreviewed side effects such as automated
emails, payments, external API calls, or AI actions.

The separation also makes later additions safer:

- A manual administrator action can record a completed or failed outcome.
- A future worker can claim an eligible task without changing the workflow
  definition itself.
- A future retry can create or manage a new execution record without overwriting
  an earlier outcome.
- Scheduling can decide when a new workflow run becomes eligible without
  changing the history of an existing run.

## Data Model Boundary

ABAP maintains three different concepts:

1. **Workflow definition:** the reusable process template and its editable
   task list.
2. **Workflow execution:** one historical run of that definition.
3. **Task execution:** one historical task snapshot belonging to one run.

This distinction avoids mixing current configuration with past results. It also
means an administrator can understand whether they are editing a reusable task
or recording what occurred during a particular run.

## Security Boundary

The existing protected workflow-start route remains the only way to create
browser-originated executions. It uses the signed session, CSRF validation,
`workflows.manage` authorization, live account revalidation, and the service
and repository layers. Day 128 adds no shortcut around those boundaries.

## What Remains for Later Days

Day 128 does not yet let anyone finish a task or display task outcomes in the
workflow detail page. It also does not establish sequential release rules,
automatic retries, scheduled starts, background processing, AI integration, or
external-system actions.

## Practical Examples

| Situation | What Day 128 records | What Day 128 does not do |
| --- | --- | --- |
| A manager starts a customer-onboarding workflow. | A parent run and one running task record per task. | Create accounts or send messages automatically. |
| A task asks a person to review a contract. | The task is visible in the run’s historical record. | Read, interpret, or approve the contract. |
| A future AI task is added to a workflow. | Its task definition can later be snapshotted into a run. | Call a model or send prompt data anywhere. |
| A schedule becomes due in the future. | The model has a place to store a new run. | Start a scheduler or background worker today. |

This distinction is useful when describing the portfolio project. ABAP has an
execution-history foundation; it does not yet advertise unattended automated
processing. That is an honest and technically precise description of the
current capability.

## Why Separate Outcomes From Instructions

A manual task can fail for a business reason, not a software error. For
example, an administrator may be unable to verify a supplier’s banking details
because the supplier provided incomplete information. The platform needs a safe
way to record that outcome without pretending a database error or automatic
worker failure occurred.

Likewise, a future AI or integration task may need retry logic, approval, rate
limits, error handling, and its own audit metadata. Keeping task executions as
records first gives those later features a stable place to attach their results
without changing how workflow definitions are stored.

## Learning Check

**Does `running` mean a task is actively consuming computer resources?**

No. At this stage it means the historical work item exists and awaits a
controlled outcome.

**Why is this boundary safer?**

It prevents a user from assuming that a button can cause unimplemented or
unreviewed real-world actions, such as payments or emails.

**What would a future worker use?**

It could read eligible task-execution records, perform a narrowly defined task,
and then submit a controlled outcome using the same historical record model.

## Next Step

Review the execution data safety guarantees, then add controlled completion and
failure updates only after the required authorization and browser protections
are in place.
