# Day 90 Summary — Protected Web Employee Editing

## Goal

Add a secure, tested browser workflow that lets authorized
administrators update selected employee details stored in SQLite.

## Completed Work

### Protected Edit Routes

Added `GET /employees/{employee_id}/edit` and
`POST /employees/{employee_id}/edit` in
`Projects/employee_management_system/web_app.py`.

Both routes reload the authenticated user, redirect unauthenticated
visitors to `/login`, require `UPDATE_EMPLOYEE`, return HTTP `403` for
missing permission, and record denied access in the activity log.

### Prefilled Edit Form

Created
`Projects/employee_management_system/templates/employee_edit.html`.

The form displays the selected employee's name and employee ID, and
prefills the editable fields:

- Department
- Position
- Email
- Phone number

The employee ID, payroll values, employment status, and other
non-Day-90 fields remain outside this editing workflow.

### CSRF-Protected Updates

The edit form uses the existing session-bound CSRF token.

The submission route checks the token with
`secrets.compare_digest()` before loading or saving employee records.
Invalid tokens return HTTP `403` and do not change employee data.

### Focused Update Services

Added `update_employee_contact_details()` in
`Projects/employee_management_system/employee_service.py`.

It strips email and phone-number input, rejects blank contact values,
and updates both values only when they are valid. The web route reuses
the existing `update_employee_details()` helper for department and
position updates.

### Safe Repository Workflow

The update route loads and saves records through the existing employee
repository.

Missing employees return a written HTTP `404` page. Repository loading
and saving failures return safe written HTTP `500` responses. Successful
updates are logged and redirect with HTTP `303` to the updated employee
profile.

### Permission-Aware Profile Actions

Updated
`Projects/employee_management_system/templates/employee_profile.html`.

Administrators with `UPDATE_EMPLOYEE` see Edit employee. The action is
hidden when the permission is unavailable, while server-side route
authorization remains the actual security boundary.

### Responsive Styling

Updated
`Projects/employee_management_system/static/styles.css`.

The profile now supports paired Edit employee and View payroll actions
with spacing on desktop and full-width stacked actions on narrow
screens. The edit page reuses the existing accessible form-card
patterns.

## Automated Tests

Added and updated tests in:

- `Projects/employee_management_system/tests/test_web_app.py`
- `Projects/employee_management_system/tests/test_employee_system.py`

Day 90 coverage verifies:

- Unauthenticated edit-form redirect
- Prefilled edit values
- Permission-aware Edit employee visibility
- Direct GET and POST permission denial
- CSRF rejection without an update
- Successful department, position, email, and phone updates
- Required-value rejection with preserved form values
- Missing employee handling
- Repository loading and saving failure handling
- Contact-detail service updates
- Blank contact values preserving existing details

## Verification

Focused suites:

- **89 tests passed** in 6.120 seconds

Complete automated suite:

- **278 tests passed** in 16.187 seconds

Manual browser verification confirmed that an administrator can edit an
employee's department, position, email, and phone number, save the
record, and view the updated details on the employee profile.

## Security Decisions

- Employee editing requires authentication and `UPDATE_EMPLOYEE`.
- Permission is checked before employee records are loaded or saved.
- CSRF validation protects every edit submission.
- Server-side required-value checks remain necessary because browser
  validation can be bypassed.
- Repository loading and saving remain behind the repository boundary.
- Missing, denied, invalid, and failed requests do not change employee
  records.
- Successful browser updates are recorded in the activity log.
- Payroll-sensitive fields remain separate from the general employee
  editing workflow.