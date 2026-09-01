# Day 87 Summary — Protected Employee Profiles

## Goal

Add protected, permission-checked, read-only employee profile pages to the FastAPI web interface.

## Completed Work

### Employee Profile Route

Added `GET /employees/{employee_id}` to `Projects/employee_management_system/web_app.py`.

The route:

- Reloads the authenticated account from SQLite
- Redirects unauthenticated visitors to `/login`
- Requires the existing `VIEW_EMPLOYEE` permission
- Denies missing permissions with HTTP status `403`
- Records denied profile access in the activity log
- Loads employee records through the existing repository
- Uses `find_employee_by_id()` for normalized employee searches
- Accepts employee IDs without case sensitivity
- Returns a safe HTTP `404` page for missing employees
- Returns a safe HTTP `500` page when loading fails
- Renders the matched employee profile

### Employee Profile Template

Created `templates/employee_profile.html`.

The page includes:

- Back-to-directory navigation
- Employee name and ID
- Written employment status
- Employment details
- Contact details
- Semantic description lists
- Accessible error presentation
- Responsive profile cards

The profile deliberately excludes salary, payroll calculations, and performance score because the route requires `VIEW_EMPLOYEE`, while payroll information uses a separate permission.

### Employee Directory Links

Updated `templates/employees.html`.

Employee names now link to their individual profile routes using FastAPI `url_for()` route generation.

### Responsive Styling

Updated `static/styles.css`.

The profile interface includes:

- Warm Charcoal raised surfaces
- Visible employee-name links
- Keyboard-accessible back navigation
- Responsive profile headers
- Written status badges
- Responsive detail cards
- Long-value wrapping
- Mobile detail stacking
- Accessible error styling

### Automated Tests

Expanded the FastAPI web suite from 25 to 33 tests.

The eight new tests cover:

- Employee-directory profile links
- Unauthenticated profile redirects
- Administrator profile access
- Viewer profile access
- Case-insensitive employee IDs
- Missing-employee `404` responses
- Repository-failure `500` responses
- Default-deny permission enforcement
- Denied-access activity logging
- Exclusion of salary and performance information

## Verification

Targeted web suite:

- 33 tests passed

Complete automated suite:

- 248 tests passed

Manual browser verification confirmed:

- Employee names open the correct profile
- Real SQLite employee details appear
- Salary, payroll, and performance score remain hidden
- Back navigation returns to the directory
- Profile cards stack at narrow widths
- Missing employee IDs show a safe written error
- Logout removes profile access
- Unauthenticated profile requests redirect to `/login`

## Security Decisions

- Employee profiles require both authentication and `VIEW_EMPLOYEE`.
- Current accounts are revalidated before every profile request.
- Employee records are loaded through the repository.
- Existing normalized service logic performs employee lookup.
- Missing IDs do not expose internal details.
- Repository failures return a safe written message.
- Denied access is recorded without exposing employee data.
- Payroll-sensitive fields are excluded from the employee-view page.