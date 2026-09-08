# Day 135 Summary — Schedule Lifecycle Milestone

## Goal

Complete the first stored-scheduling milestone by adding administrator-only
Enable and Disable actions and tying schedule eligibility to the parent
workflow lifecycle.

## Enable and Disable Controls

Each stored schedule appears beneath its workflow with a written state. An
authorized administrator receives one action matching the next valid change:

- An Enabled schedule shows **Disable schedule**.
- A Disabled schedule on an Active workflow shows **Enable schedule**.
- A Disabled schedule on a Draft or Inactive workflow shows a disabled control
  and explanatory text telling the administrator to activate the workflow.

The status route is POST-only, requires a current signed-session CSRF token,
strictly accepts only `true` or `false`, calls the service layer, writes a
successful activity entry, and returns to the workflow detail page using a
`303` redirect.

## Parent Workflow Lifecycle Rule

An enabled schedule must never remain eligible when its workflow leaves Active.
The workflow repository now handles this within the same database transaction
as the workflow update. When an administrator changes an Active workflow to
Draft or Inactive, every enabled schedule belonging to that workflow becomes
Disabled and receives the same update timestamp.

This transactional rule avoids a dangerous intermediate state where the
workflow is inactive but one of its schedules still appears eligible. If the
database update fails, the transaction rolls back instead of intentionally
saving only half of the lifecycle change.

Reactivating the workflow does not silently re-enable its schedules. The
administrator must review and enable each rule deliberately. This prevents an
old schedule from resuming after a workflow was intentionally paused.

## Defense-in-Depth Flow

1. The workflow page only renders schedule controls for an administrator with
   `workflows.manage`.
2. The route reloads the session account from SQLite before authorization.
3. The POST must include the current session’s CSRF token.
4. The submitted enabled value must be exactly allowlisted.
5. The service reloads the administrator account and verifies role, active
   status, stable user ID, and permission again.
6. The service confirms that the schedule belongs to the workflow in the URL.
7. The repository changes only a different saved state and requires an Active
   workflow when enabling.

UI visibility is therefore a convenience rather than the security boundary.
Manually posting a hidden action still passes through every route, service, and
database rule.

## What Days 132–135 Deliver Together

```text
Typed schedule and allowlisted constants
        ↓
Constrained SQLite table and scoped repository operations
        ↓
Live-account service authorization and timing validation
        ↓
Accessible browser creation and read-only display
        ↓
Protected Enable/Disable actions and workflow lifecycle enforcement
```

ABAP now stores Manual, Daily, and Weekly workflow eligibility rules. The
records are durable, auditable, scoped to active workflows, visible to permitted
users, and manageable only by revalidated administrators.

## What Is Still Deliberately Out of Scope

Day 135 does not introduce a timer loop, task queue, operating-system scheduler,
background worker, automatic workflow start, time-zone conversion, catch-up
behavior after downtime, duplicate-run prevention, AI calls, emails, or external
API execution.

The phrase “scheduled” currently means that ABAP stores a validated eligibility
rule. A later evaluator must determine whether the current time matches an
enabled rule and whether a new execution may safely be created. Keeping this
boundary explicit avoids overstating the platform’s automation capabilities.

## Files Changed Across Days 132–135

- `Projects/employee_management_system/models.py`
- `Projects/employee_management_system/database.py`
- `Projects/employee_management_system/workflow_service.py`
- `Projects/employee_management_system/web_app.py`
- `Projects/employee_management_system/templates/workflow_schedule_form.html`
- `Projects/employee_management_system/templates/workflow_detail.html`
- `Projects/employee_management_system/templates/home.html`
- `Projects/employee_management_system/tests/test_workflow_schedules.py`
- `README.md`
- `Notes/day132_summary.md` through `Notes/day135_summary.md`

## Verification

The new focused schedule suite contains **10 tests** covering:

- Repository round trips, Boolean conversion, ordering, and workflow scoping.
- Manual, Daily, and Weekly normalization.
- Strict `HH:MM` validation and weekday allowlisting.
- Duplicate IDs and invalid field types.
- Missing, Draft, and Inactive workflow rejection.
- Viewer, stale identity, missing account, demoted account, and missing
  permission rejection.
- Exact parent scoping and unchanged-state protection.
- Automatic schedule disabling during workflow deactivation.
- Administrator browser creation, accessible content, display, logging, and
  Post/Redirect/Get navigation.
- Anonymous, viewer, invalid-CSRF, validation, and safe SQLite error paths.

Verification completed successfully:

- **10 focused schedule tests passed**
- **78 workflow-focused tests passed**
- **448 total automated tests passed**
- No failures or errors remained

## Concepts Practiced

- Typed domain models and shared allowlists
- Relational schema design and foreign keys
- Strict time and weekday validation
- Live account revalidation
- Default-deny authorization
- Signed-session CSRF protection
- Repository/service/browser separation
- Transactional parent-child lifecycle changes
- Idempotent state-change rejection
- Accessible form labels, help text, and written status
- Post/Redirect/Get navigation
- Safe error boundaries and activity logging
- Honest product capability wording

## Learning Check

**Why are schedules disabled automatically when a workflow becomes Inactive?**

An Inactive workflow is not eligible to run. Leaving a rule enabled would make
the stored configuration contradict the workflow lifecycle.

**Why are schedules not automatically re-enabled after reactivation?**

Reactivation may happen after a long pause or business change. Requiring an
explicit review prevents an outdated rule from silently resuming.

**Why does Day 135 stop before creating a background worker?**

Safe automatic execution also needs time-zone policy, due-time evaluation,
duplicate prevention, downtime behavior, and controlled worker ownership. The
stored-rule foundation should be verified before those decisions are added.

## Current ABAP Status

Day 135 is complete. Workflow Automation now supports reusable workflows,
ordered manual tasks, workflow and task execution history, controlled task
outcomes, and protected stored schedules with lifecycle-safe enabled states.

## Next Step

Day 136 should define a read-only schedule-eligibility evaluator. It should
accept an explicit current time for deterministic tests, return which enabled
schedules are due, define time-zone assumptions, and avoid starting executions
until duplicate-run protection is designed.
