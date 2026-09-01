# Day 89 Summary — Protected Web Employee Creation

## Goal

Add a secure, tested browser workflow that lets authorized administrators create employee records in the SQLite database.

## Completed Work

### Protected Add Employee Page

Added `GET /employees/new` in `Projects/employee_management_system/web_app.py`.

The route reloads the authenticated user, redirects unauthenticated visitors to `/login`, requires `REGISTER_EMPLOYEE`, records denied access, generates or reuses a CSRF token, and renders the accessible Add employee form.

### CSRF Protection

Added session-bound CSRF token helpers.

The workflow creates a random token with `secrets.token_urlsafe(32)`, stores it in the signed session, places it in a hidden form field, and uses `secrets.compare_digest()` to validate submitted tokens. Invalid submissions return HTTP `403` and do not create employee records.

### Server-Side Form Validation

Added `build_employee_from_form()`.

The helper:

- Strips submitted text and normalizes employee IDs to uppercase
- Safely converts salary, years of experience, and performance score to integers
- Reuses `get_employee_record_errors()`
- Requires salary greater than zero
- Enforces experience from `0` through `60`
- Enforces performance score from `0` through `100`
- Preserves non-sensitive submitted values when validation fails
- Returns a written error instead of allowing malformed input to crash the route

### Protected Employee Creation

Added `POST /employees/new`.

The route:

- Reloads the authenticated user
- Requires `REGISTER_EMPLOYEE`
- Checks the CSRF token before loading or saving employee records
- Validates submitted employee fields
- Loads records through `load_employee_records()`
- Rejects duplicate employee IDs with normalized lookup
- Saves through `save_employee_records()`
- Returns safe `500` errors for repository loading or saving failures
- Logs successful browser employee registration
- Redirects successful submissions to the new employee profile with HTTP `303`

### Accessible Employee Form

Created `Projects/employee_management_system/templates/employee_form.html`.

The form includes identity, employment, contact, and payroll-basis sections; labels for every input; browser-required fields; numeric ranges; a hidden CSRF token; written errors; Cancel; and Create employee actions.

### Permission-Aware Directory Action

Updated the employee directory route and template.

Administrators see Add employee only when they have `REGISTER_EMPLOYEE`. Viewers do not see the action, but direct route authorization remains the actual security boundary.

### Responsive Styling

Updated `Projects/employee_management_system/static/styles.css`.

The interface now has responsive directory actions, raised form cards, responsive field grids, visible input focus, a registration-status badge, and full-width mobile actions.

## Automated Tests

Expanded the FastAPI web suite from **41** to **51** tests.

The ten Day 89 tests cover:

- Unauthenticated Add employee redirects
- Administrator form access
- Administrator-only directory-action visibility
- Direct permission denial and activity logging
- Successful CSRF-protected employee creation
- Redirect to the new employee profile
- Invalid form values and preserved entries
- Invalid CSRF rejection without employee creation
- Duplicate employee-ID rejection
- Repository loading and saving failures

## Verification

Targeted web suite:

- **51 tests passed** in 6.352 seconds

Complete automated suite:

- **266 tests passed** in 18.744 seconds

Manual browser verification confirmed:

- Administrators see Add employee
- The responsive form loads correctly
- A manually entered employee was saved successfully
- The new profile opens after creation
- The employee appears in the directory
- Viewers can view the directory but do not see Add employee

## Security Decisions

- Employee creation requires authentication and `REGISTER_EMPLOYEE`.
- Permission is checked before form display, loading, or saving.
- CSRF validation protects every data-changing submission.
- Server-side validation is required because browser validation can be bypassed.
- Employee IDs are normalized before duplicate checks.
- Repository loading and saving remain behind the repository boundary.
- Invalid, duplicate, denied, and failed requests do not create records.
- Successful employee creation is recorded in the activity log.