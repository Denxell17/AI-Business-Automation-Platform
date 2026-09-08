# Day 132 Summary — Workflow Schedule Data Foundation

## Goal

Start the scheduling milestone by defining how ABAP stores a schedule safely.
The first release stores schedule rules only. It does not run a clock, start a
background process, or automatically execute a workflow.

## What Was Added

Day 132 added a typed `WorkflowSchedule` model and the
`workflow_schedules` SQLite table. Each schedule belongs to one workflow and
records:

- `schedule_id` — a stable public ID such as `SCH-WEEKLY-REPORT`.
- `workflow_id` — the active workflow that may become eligible to run.
- `schedule_type` — `manual`, `daily`, or `weekly`.
- `scheduled_time` — an optional local clock time stored as `HH:MM`.
- `day_of_week` — an optional normalized weekday for weekly schedules.
- `is_enabled` — whether the stored eligibility rule is currently enabled.
- `created_by_user_id` — the administrator account that created it.
- `created_at` and `updated_at` — UTC audit timestamps.

The model also defines explicit allowlists for schedule types and weekdays.
These constants give the service and future scheduling code one shared source
of truth instead of scattering accepted strings throughout the application.

## Database Rules

The new table uses a primary key for `schedule_id`, a foreign key to the parent
workflow, and a foreign key to the administrator account that created the
schedule. SQLite checks that schedule types are one of the three supported
values, weekdays are either empty or one of the seven allowlisted names, and
the enabled field is a Boolean-compatible `0` or `1`.

Repository functions now support:

- Inserting one validated schedule with parameterized SQL.
- Loading all schedules for one workflow in stable creation order.
- Loading one schedule by its exact public ID.
- Converting SQLite’s integer enabled value back to a Python Boolean.
- Changing one schedule’s enabled state with workflow and schedule scoping.

## Field Reference

| Field | Example | Purpose |
| --- | --- | --- |
| `schedule_id` | `SCH-PAYROLL-FRIDAY` | Identifies one schedule in routes, logs, and storage. |
| `workflow_id` | `WF-PAYROLL` | Connects the schedule to its workflow definition. |
| `schedule_type` | `weekly` | Tells future eligibility logic how to interpret the timing fields. |
| `scheduled_time` | `17:30` | Stores the requested clock time for daily or weekly rules. |
| `day_of_week` | `friday` | Limits a weekly rule to one allowlisted weekday. |
| `is_enabled` | `True` | Allows a rule to remain stored without being eligible. |
| `created_by_user_id` | `4` | Retains the accountable creator without storing credentials. |
| UTC timestamps | `2026-09-08T...+00:00` | Support auditing and later change tracking. |

## Why Storage Comes Before Automation

A background scheduler needs reliable input. If timing rules, lifecycle rules,
and ownership are unclear, a worker could start the wrong workflow or run a
disabled definition. Day 132 first creates a durable, constrained record that
later eligibility evaluation can read safely.

For example, storing “weekly, Friday, 17:30, enabled” does not mean ABAP has
already run anything. It means the platform has a validated business rule that
a future evaluator can compare with a known clock and time-zone policy.

## Repository Separation

The repository owns SQLite details only. It does not decide whether a daily
schedule needs a time, whether a viewer may create one, or whether the parent
workflow is active. Those are service-layer business rules added on Day 133.
This separation keeps SQL reusable and prevents browser-specific behavior from
entering the database module.

## Data-Safety Decisions

- Public string IDs remain separate from internal SQLite row handling.
- Foreign keys prevent schedules from referencing missing workflows or users.
- Parameterized SQL keeps values separate from SQL instructions.
- Stable ordering makes browser output and tests deterministic.
- Exact-ID loading avoids broad scans when one schedule is updated.
- Failed integrity checks roll back the repository operation and return a
  controlled failure result.

## Files Changed

- `Projects/employee_management_system/models.py`
- `Projects/employee_management_system/database.py`

## Learning Check

**Why does a manual schedule exist if administrators can already start a
workflow manually?**

It gives the schedule domain a valid no-time rule and provides a consistent
stored eligibility record without pretending that automatic timing exists.

**Why store `updated_at` on a schedule?**

Enabling or disabling a rule is a meaningful configuration change. The update
timestamp records when its stored state last changed.

**Why is `day_of_week` nullable?**

Manual and daily rules do not need a weekday. Weekly rules require it through
service validation.

## Current Status and Next Step

Day 132 completes the schedule model and repository foundation. Day 133 adds
administrator authorization, active-workflow checks, normalization, and timing
validation before these repository functions may be used by the application.
