# Day 96 Summary — Protected Browser Activity Log

## Completed

Day 96 added a protected browser activity-log page at `/activity-log`.

The feature now provides:

- Authentication before activity entries are read
- A dedicated administrator-only `VIEW_ACTIVITY_LOG` permission
- HTTP `303` redirect to `/login` for unauthenticated requests
- HTTP `403` and denied-access activity logging for users without permission
- A fixed server-side `logs/activity.log` source with no browser-controlled file path
- Bounded reading of the latest 100 entries, displayed newest first
- Safe empty state when the log file does not exist
- Safe HTTP `500` error state when the log cannot be read
- Escaped activity-entry output through Jinja2 template rendering
- A permission-aware Activity log navigation link for administrators only
- A dedicated non-propagating `abap.activity` logger that prevents FastAPI and file-watcher messages from being recorded as application activity

## Implementation Decisions

`VIEW_ACTIVITY_LOG` is separate from employee, payroll, and export permissions. This follows least privilege: activity history can reveal sensitive operational and security information, so only administrators may view it.

The reader always uses the fixed `LOG_FILE` path. A browser request cannot choose a filename or directory, preventing path-traversal and arbitrary-file-read risks.

The page reads only the most recent 100 lines and reverses them for display. This keeps the page responsive as the log file grows while showing the most relevant entries first.

The activity logger now uses a named `abap.activity` logger with `propagate = False`. This prevents framework logging from reaching the audit file, so activity history contains only events intentionally recorded through `log_activity()`.

The successful activity-log page view is not logged. Logging it would add a new entry every time the page refreshes and would make the audit trail noisier without providing useful information.

## Files Changed

- `Projects/employee_management_system/authorization.py`
  - Added the administrator-only `VIEW_ACTIVITY_LOG` permission
- `Projects/employee_management_system/activity_logger.py`
  - Added bounded newest-first activity-log reading
  - Replaced root logging configuration with a dedicated non-propagating application logger
- `Projects/employee_management_system/web_app.py`
  - Added the protected `/activity-log` browser route
  - Added safe authorization, denial logging, empty-state, and loading-failure handling
  - Exposed the permission helper and activity-log permission to templates
- `Projects/employee_management_system/templates/activity_log.html`
  - Added the accessible activity-log page, error state, empty state, and recent-entry list
- `Projects/employee_management_system/templates/application_base.html`
  - Added the administrator-only Activity log navigation link
- `Projects/employee_management_system/static/styles.css`
  - Added responsive activity-log page, status, card, and entry-list styling
- `Projects/employee_management_system/tests/test_authorization.py`
  - Added activity-log permission coverage for administrators, viewers, and unknown roles
- `Projects/employee_management_system/tests/test_activity_logger.py`
  - Added safe log-reader tests
- `Projects/employee_management_system/tests/test_web_app.py`
  - Added protected activity-log route and template tests
- `README.md`
  - Pending Day 96 capability, concept, status, and test-total documentation updates
- `Notes/day96_summary.md`
  - Added this continuity record

## Tests

Focused tests:

- **104 FastAPI web tests passed**
- **7 activity-log and authorization tests passed**
- **3 activity-logger tests passed after the dedicated logger correction**

Complete Employee Management System suite:

- **325 tests passed**

## Manual Verification

The administrator Activity log page was checked in the browser.

It displayed:

- The active administrator-only navigation item
- The newest activity entry first
- A real successful-login event recorded through `log_activity()`
- Older watcher entries only as historical data, with no new watcher messages after the dedicated logger correction

## Current ABAP Status

Day 96 is complete.

Administrators can safely review recent console and browser activity without direct filesystem access. The route enforces authentication and a dedicated permission before reading the fixed log file. The application now keeps audit records separate from framework logging noise.

## Quiz — Questions and Answers

1. Why is `VIEW_ACTIVITY_LOG` separate from `VIEW_EMPLOYEE`?

   Activity records can contain sensitive security and operational information, so they need a more restricted permission.

2. Why must the browser never provide the log filename?

   A user-controlled path could allow path traversal or reading unrelated server files.

3. Why does the reader use `entries[-ACTIVITY_LOG_ENTRY_LIMIT:]`?

   It keeps only the newest bounded group of entries instead of loading and displaying an unlimited log history.

4. Why are the selected entries reversed before rendering?

   Log files append new lines at the end, so reversing the newest entries displays the most recent event first.

5. What does `propagate = False` prevent?

   It prevents activity messages from being passed to the root logger and prevents unrelated framework messages from reaching the activity log.

6. Why is the activity-log page view itself not logged?

   Refreshing the page would constantly create extra audit entries and make meaningful events harder to review.

7. What should happen when the log file does not exist yet?

   The page should show a safe empty state because no activity has been recorded yet.

8. What protects `<script>` text inside an activity entry from running in the browser?

   Jinja2 autoescaping converts special HTML characters into safe text before the entry is rendered.