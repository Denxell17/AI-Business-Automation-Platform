# Day 97 Summary — Protected Browser User-Account Directory

## Completed

Day 97 added a protected browser user-account directory at `/users`.

The feature now provides:

- Authentication before user-account data is read
- Administrator-only access through the existing `MANAGE_USER_ACCOUNTS`
  permission
- HTTP `303` redirect to `/login` for unauthenticated requests
- HTTP `403` and denied-access activity logging for unauthorized users
- A safe SQLite query that returns only user ID, username, role, and active
  status
- No password-hash selection, template context exposure, or browser display
- Case-insensitive alphabetical account ordering
- Safe HTTP `500` handling when SQLite user-account data cannot be read
- Administrator-only User accounts navigation
- An accessible account table with written active and inactive statuses
- A responsive horizontal-scroll table for narrow screens
- Empty-state handling when no user accounts exist

## Implementation Decisions

`UserAccountSummary` is separate from `UserAccount`. The original account
type contains `password_hash` because authentication needs it. The new
summary type intentionally excludes the hash, creating a clear safe-data
boundary for web account administration.

The SQLite query selects only the fields the page needs. It does not select
`password_hash`, so that sensitive value cannot accidentally reach the
template through this workflow.

The `/users` route requires `MANAGE_USER_ACCOUNTS`, which remains an
administrator-only permission. The server checks authorization before
calling the SQLite summary query, so denied users cannot trigger account
data loading.

The directory is read-only. Later ABAP-MVP work can add separate,
CSRF-protected account-management actions without combining listing and
state-changing behavior in one feature.

## Files Changed

- `Projects/employee_management_system/models.py`
  - Added the safe `UserAccountSummary` type
- `Projects/employee_management_system/database.py`
  - Added safe, sorted SQLite account-summary loading
  - Added controlled SQLite failure handling
- `Projects/employee_management_system/web_app.py`
  - Added the protected `/users` route
  - Added administrator authorization, denied-access logging, and safe
    loading-failure handling
  - Exposed the account-management permission to Jinja2 templates
- `Projects/employee_management_system/templates/user_accounts.html`
  - Added the accessible account-directory page
- `Projects/employee_management_system/templates/application_base.html`
  - Added permission-aware User accounts navigation
- `Projects/employee_management_system/static/styles.css`
  - Added responsive user-account card, table, status, and empty-state styles
- `Projects/employee_management_system/tests/test_database.py`
  - Added safe account-summary sorting and failure tests
- `Projects/employee_management_system/tests/test_web_app.py`
  - Added protected account-directory route and template tests
- `README.md`
  - Pending Day 97 capability, concept, status, and test-total updates
- `Notes/day97_summary.md`
  - Added this continuity record

## Tests

Focused tests:

- **37 database tests passed**
- **109 FastAPI web tests passed**

Complete Employee Management System suite:

- **332 tests passed**

## Manual Verification

The administrator User accounts page was checked in the browser at both
desktop and narrow widths.

It displayed:

- An active, administrator-only User accounts navigation item
- A correct user-account count
- Username, role, and written access-status columns
- No password hashes
- A readable narrow-screen table with horizontal scrolling

## Current ABAP Status

Day 97 is complete.

ABAP now has a secure browser user-account directory that can become a
shared platform administration module. Its dedicated safe-data model and
administrator-only route provide the foundation for later account creation,
activation, deactivation, and password-reset workflows.

## Quiz — Questions and Answers

1. Why does `UserAccountSummary` exist separately from `UserAccount`?

   `UserAccount` includes `password_hash` for authentication, while
   `UserAccountSummary` excludes it for safe display in the browser.

2. Why should the SQL query avoid selecting `password_hash`?

   A value that is never selected cannot accidentally be included in template
   context or exposed in a browser response.

3. Which permission protects `/users`?

   `MANAGE_USER_ACCOUNTS`.

4. Why does the route check permission before loading account summaries?

   Unauthorized users should not trigger access to sensitive account data.

5. What does `None` from `load_user_account_summaries()` mean?

   The SQLite account data could not be read safely, so the route returns a
   controlled error page.

6. Why is the Day 97 directory read-only?

   Listing accounts and changing accounts have different risks. Future
   state-changing actions need their own CSRF protection and tests.

7. Why does the query use `ORDER BY username COLLATE NOCASE`?

   It gives administrators a predictable alphabetical list without treating
   uppercase and lowercase usernames as separate ordering groups.

8. Why does the table use both a status dot and written text?

   The words “Active” and “Inactive” keep the status understandable without
   relying only on color.