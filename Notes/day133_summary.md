# Day 133 Summary — Schedule Service Validation

## Goal

Add the business rules that decide who may create or change a schedule and
which combinations of type, time, weekday, enabled state, and workflow status
are valid.

## Administrator and Account Validation

The new `create_workflow_schedule()` and
`set_workflow_schedule_enabled()` services follow the established ABAP security
pattern. They reject an inactive session object immediately, then reload the
username from SQLite and verify:

- The saved account still exists.
- The saved account remains active.
- Its saved user ID matches the session user ID.
- Its current role is `admin`.
- It still has the explicit `workflows.manage` permission.

This live revalidation matters because an eight-hour signed session can outlive
an account change. An administrator who is deactivated or demoted after signing
in cannot use an older session to create or enable schedules.

## Creation Rules

The service normalizes schedule and workflow IDs to uppercase, trims text,
case-normalizes schedule types and weekdays, and requires a real Python Boolean
for the enabled field. It then loads the parent workflow and requires that it
currently be Active.

Each schedule type has a deliberately small rule set:

| Type | Required fields | Stored timing |
| --- | --- | --- |
| Manual | No time or weekday | Both timing fields are stored as empty. |
| Daily | Exact `HH:MM` time | Time is stored; weekday is empty. |
| Weekly | Exact `HH:MM` time and allowlisted weekday | Both normalized values are stored. |

Times must use two-digit 24-hour format. Values such as `09:30` and `23:59`
are valid. Values such as `9:30`, `24:00`, `12:60`, words, or blank input for a
daily or weekly rule are rejected. Weekly weekdays are limited to Monday
through Sunday.

## Why Only Active Workflows Can Receive Schedules

A schedule represents run eligibility. Draft workflows may be incomplete, and
Inactive workflows have been deliberately taken out of service. Allowing either
to receive a schedule would create configuration that looks runnable when the
workflow is not eligible to start.

The service therefore rejects schedule creation for missing, Draft, and
Inactive workflows, even when the requested schedule starts disabled. An
administrator activates the completed workflow first, then adds its schedule.

## Enable and Disable Rules

Schedule state changes are scoped to both `workflow_id` and `schedule_id`.
The service first loads the exact schedule and checks that it belongs to the
workflow in the request. The repository then changes the record only if the
requested state differs from the stored state.

Enabling has one additional database-side condition: the parent workflow must
still be Active at the moment of the update. This closes the gap between the
service read and the write. Disabling does not need an active parent because
turning off eligibility is always the safer direction.

Repeated submissions that request the already-saved state return `False`
instead of rewriting the timestamp. A schedule from another workflow and a
missing schedule ID are also rejected without changes.

## Example Validation Outcomes

- `manual`, blank time, blank weekday: accepted for an Active workflow.
- `manual`, `10:00`, `monday`: accepted but irrelevant timing values are cleared.
- `daily`, `08:15`, blank weekday: accepted.
- `daily`, blank time: rejected.
- `weekly`, `14:30`, `Friday`: accepted and stored as `friday`.
- `weekly`, `14:30`, `holiday`: rejected.
- Valid weekly rule for a Draft workflow: rejected.
- Enable a disabled rule after its workflow becomes Inactive: rejected.

## Files Changed

- `Projects/employee_management_system/workflow_service.py`
- `Projects/employee_management_system/database.py`
- `Projects/employee_management_system/models.py`

## Tests

Focused tests cover normalization, all three schedule types, strict time and
weekday validation, duplicate IDs, wrong parent IDs, missing workflows,
non-Boolean state input, viewer denial, stale identity denial, missing account
denial, demotion, missing permission, repeated status requests, and
active-workflow enforcement.

## Learning Check

**Why validate in the service if SQLite also has constraints?**

The service expresses business rules and can return a controlled failure before
writing. SQLite constraints remain a final integrity boundary if another caller
passes invalid data to the repository.

**Why check workflow state again inside the enable update?**

The workflow might change between an earlier read and the final write. The SQL
condition makes the important rule part of the update itself.

**Why reject an unchanged enabled state?**

No business change occurred. Avoiding a write preserves a meaningful
`updated_at` timestamp and makes repeated submissions easy to detect.

## Current Status and Next Step

Day 133 completes schedule business validation. Day 134 exposes these services
through protected browser pages with CSRF validation, safe errors, accessible
controls, and activity logging.
