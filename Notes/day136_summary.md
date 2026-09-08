# Day 136 Summary — Read-Only Schedule Eligibility

## Objective

Turn the schedule records created during Days 132–135 into rules that ABAP can
evaluate safely. Day 136 deliberately separates the question “Is this schedule
due?” from the action “Start this workflow.” This makes the time calculation
easy to test and prevents an unfinished scheduler from changing application
data.

## What Was Implemented

A new `schedule_service.py` module now contains the schedule clock logic. Its
main function, `evaluate_workflow_schedule()`, accepts a stored
`WorkflowSchedule` and a timezone-aware `datetime` supplied by its caller. It
returns the schedule and workflow IDs, whether the schedule is due, the UTC
occurrence time, the next eligible UTC time, and the business timezone used.

Because the current time is explicit, tests do not depend on the computer
clock. A test can ask what happens at exactly 09:30, four minutes afterward, or
one second after the recovery window ends.

## Eligibility Rules

| Schedule type | Eligibility behavior |
|---|---|
| `manual` | Never becomes clock-due. It remains available for a person-controlled start. |
| `daily` | Becomes due at its configured local `HH:MM` time each day. |
| `weekly` | Becomes due only when its configured weekday and local time match. |

A disabled schedule is never due and has no next eligible time. Database-backed
due-list loading also excludes schedules whose parent workflow is no longer
Active.

## Important Concept: Pure Evaluation

A pure evaluator calculates and returns an answer without writing to SQLite,
starting tasks, or logging an execution. ABAP needs this separation because a
background runner may evaluate schedules repeatedly. Reading the same schedule
multiple times must not create multiple workflow runs.

The boundary also lets a FastAPI route, command-line scheduler, n8n connection,
or future worker reuse one interpretation instead of creating separate rules.

## Validation and Failure Behavior

- The supplied current time must include timezone information.
- The grace period must be a positive integer.
- Invalid timezone names are rejected with a controlled `ValueError`.
- Manual schedules ignore clock fields.
- A malformed stored clock cannot become due.
- Disabled schedules do not expose a future eligible timestamp.

## Files Added or Changed

- `Projects/employee_management_system/schedule_service.py`
- `Projects/employee_management_system/models.py`
- `Projects/employee_management_system/tests/test_workflow_schedule_eligibility.py`

## Verification and Result

Focused tests cover daily eligibility before, during, and after its allowed
window; manual and disabled behavior; explicit-time validation; and invalid
configuration. Day 136 gives ABAP a deterministic answer to “Which schedule is
due now?” without starting an execution. Day 137 defines the timezone and
missed-time policy that determines what “now” means.
