# Day 134 Summary — Protected Schedule Browser Experience

## Goal

Make stored schedules understandable and manageable from the existing Workflow
Automation browser interface while preserving the browser, service, and
repository boundaries.

## Workflow Detail Display

The protected workflow detail page now loads schedules belonging to the current
workflow and displays them in stable order. Administrators and viewers with
`workflows.view` can read:

- The schedule’s stable ID.
- Its Manual, Daily, or Weekly type.
- A written Enabled or Disabled state.
- A human-readable timing description.
- Its creation timestamp.

The timing text translates stored fields into useful language. Manual rules say
“Manual eligibility only,” Daily rules show “Daily at HH:MM,” and Weekly rules
show the weekday and time. The page also clearly states that schedules store
future run-eligibility rules and do not start background work yet.

When no schedules exist, the page displays an explicit empty state rather than
an empty list. Viewers can understand the configuration but never receive Add,
Enable, or Disable controls.

## Administrator Schedule Form

An Active workflow shows an **Add schedule** link to administrators. The new
form includes:

- A required schedule ID.
- An allowlisted Manual, Daily, or Weekly type selector.
- A browser time field with help text explaining Daily and Weekly requirements.
- A weekday selector with all seven valid values.
- An enabled checkbox.
- A clear note that automatic background execution is not active.
- Cancel navigation back to the parent workflow.
- A `role="alert"` validation message that preserves submitted values.

The form uses semantic labels and help-text connections so keyboard and
assistive-technology users can understand the fields. Native time and select
controls reuse the project’s existing form styling and visible focus behavior.

## Browser Request Flow

```text
GET schedule form
    → reload authenticated account
    → require administrator and workflows.manage
    → load exact workflow
    → require Active workflow
    → render form with signed-session CSRF token

POST schedule form
    → reload authenticated account
    → require administrator and workflows.manage
    → verify current CSRF token
    → load exact workflow
    → parse enabled value using a strict allowlist
    → call create_workflow_schedule()
    → log successful creation
    → redirect to workflow detail with HTTP 303
```

The `303` redirect implements Post/Redirect/Get. Refreshing the detail page does
not resubmit the schedule creation form.

## Safe Errors

- Missing sessions redirect to sign-in.
- Viewers and accounts without permission receive a safe `403 Access denied.`
- Missing or invalid CSRF tokens receive a safe `403` verification message.
- Missing workflows return a safe `404` response.
- Inactive workflow form access returns a safe `400` explanation.
- Invalid schedule combinations return the form with a safe `400` message and
  preserved values.
- SQLite errors return a generic `500` message without paths, SQL, tracebacks,
  or database exception text.

## Activity Logging

The browser logs denied schedule-creation access, invalid-CSRF submissions, and
successful schedule creation. Successful entries include the normalized
schedule ID, parent workflow ID, and administrator username. Submitted timing
details are not copied into the activity message, keeping the log concise.

## Dashboard Wording

The shared dashboard now describes Workflow Automation accurately: workflows,
ordered tasks, stored schedules, and execution history are available, while
automatic background processing remains planned.

## Files Changed

- `Projects/employee_management_system/web_app.py`
- `Projects/employee_management_system/templates/workflow_schedule_form.html`
- `Projects/employee_management_system/templates/workflow_detail.html`
- `Projects/employee_management_system/templates/home.html`
- `Projects/employee_management_system/tests/test_workflow_schedules.py`

## Tests

Browser tests verify anonymous redirects, administrator form access, viewer
denial, CSRF rejection before service calls, successful Weekly schedule
creation, redirect behavior, activity logging, schedule display, written state,
help text, validation errors, submitted-value preservation, and safe storage
failure responses.

## Learning Check

**Why can viewers read schedules?**

They already have `workflows.view`, which is a read-only permission. Reading an
eligibility rule does not grant authority to create or change one.

**Why hide Add schedule on Draft and Inactive workflows?**

The service will reject creation for those states. Hiding the link makes the UI
explain the same lifecycle rule, while the server still enforces it.

**Why keep validation in the service instead of the HTML fields alone?**

Browser controls can be bypassed or manually altered. Server validation applies
the same rules to every caller.

## Current Status and Next Step

Day 134 completes schedule creation and read-only schedule display in the
browser. Day 135 adds protected lifecycle controls and ensures enabled schedules
cannot remain active when their workflow leaves Active.
