# Day 86 Summary — Protected Employee Directory

## Goal

Add a protected, permission-checked, read-only employee directory to the FastAPI web interface.

## Completed Work

### Employee Directory Route

Added `GET /employees` to `Projects/employee_management_system/web_app.py`.

The route:

- Reloads the authenticated account from SQLite
- Redirects unauthenticated visitors to `/login`
- Requires the existing `VIEW_EMPLOYEE` permission
- Denies unauthorized accounts with HTTP status `403`
- Records denied access in the activity log
- Loads employee records through the existing repository
- Returns HTTP status `500` with a safe message when loading fails
- Renders the employee directory after successful loading

### Employee Directory Template

Created `templates/employees.html`.

The page includes:

- Employee directory heading
- Current employee count
- Semantic table caption
- Employee ID, name, department, position, and status columns
- Written employment statuses
- Accessible error message
- Accessible empty-directory state
- Keyboard-focusable horizontal table scrolling

### Authenticated Navigation

Updated `templates/application_base.html`.

The authenticated sidebar now includes an Employees link that:

- Uses FastAPI route generation
- Shows active-page styling
- Uses `aria-current="page"` on the employee directory

### Responsive Styling

Updated `static/styles.css`.

The employee directory includes:

- Warm Charcoal surfaces
- Responsive page heading
- Employee-count badge
- Bordered table container
- Horizontal scrolling on narrow screens
- Clear table headers
- Written status presentation
- Error and empty-state styling
- Existing visible keyboard focus

### Automated Tests

Expanded the FastAPI web suite from 18 to 25 tests.

The seven new tests cover:

- Unauthenticated employee-directory redirects
- Administrator employee-directory access
- Viewer employee-directory access
- Default-deny permission enforcement
- Denied-access activity logging
- Employee-loading failure handling
- Empty-directory presentation
- Active employee navigation

## Verification

Targeted web suite:

- 25 tests passed

Complete automated suite:

- 240 tests passed

Manual browser verification confirmed:

- Real SQLite employee records appear
- The employee count is correct
- The Employees navigation item is active
- The table remains usable at narrow widths
- Logout removes access to `/employees`
- Unauthenticated access redirects to `/login`

## Security Decisions

- The employee directory requires both authentication and `VIEW_EMPLOYEE`.
- Employee records are loaded through the repository instead of direct route-level SQL.
- Authorization denies access by default.
- Denied access is recorded without exposing employee data.
- Repository failures show a safe message instead of database details.
- Tests use a temporary SQLite database and obvious fictional test data.