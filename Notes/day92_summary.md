# Day 92 Summary — Protected Browser Employee Search and Filtering

## Completed

Day 92 added protected, read-only employee search and filtering to the
FastAPI employee directory.

The directory now supports:

- Case-insensitive partial-name searches
- Case-insensitive exact department filters
- Inclusive minimum-and-maximum salary filters
- Combined filters requiring every selected condition
- Preserved query values after filtering
- Clear-filter navigation
- Written validation for incomplete salary ranges
- Written validation for non-integer salary values
- Written validation for negative salary values
- Written validation when minimum salary exceeds maximum salary
- A distinct no-match state for valid filters with no results
- Responsive accessible filter controls
- Administrator and viewer access through `VIEW_EMPLOYEE`

The filter form uses read-only GET query parameters:

- `search_text`
- `department`
- `minimum_salary`
- `maximum_salary`

No filter action modifies SQLite data, so CSRF protection is not needed.
Authentication and `VIEW_EMPLOYEE` authorization still run before
employee records are loaded.

## Implementation Decisions

The directory route normalizes all text input with `strip()`.

Salary input is converted from query text to integers only when both
salary bounds are supplied. Invalid ranges display a written error while
leaving the unfiltered employee list available. This avoids presenting a
validation problem as though no employees exist.

Valid filters reuse existing service-layer functions:

- `search_employees_by_name()`
- `filter_employees_by_department()`
- `filter_employees_by_salary_range()`

When several filters are valid, each function receives the previous
result. This creates match-all behavior without duplicating business
rules in the web route.

The directory template preserves submitted filter values, displays Clear
filters only when filters are active, and distinguishes an empty SQLite
directory from a valid search with no matching employees.

## Files Changed

- `Projects/employee_management_system/web_app.py`
  - Added search and filter service imports
  - Added read-only directory query parameters
  - Added normalization and salary-range validation
  - Added service-layer filter composition
  - Added filter template context values
- `Projects/employee_management_system/templates/employees.html`
  - Added the accessible GET filter form
  - Added validation-message rendering
  - Added preserved values and Clear filters navigation
  - Added the no-matching-employees state
- `Projects/employee_management_system/static/styles.css`
  - Added directory filter form, grid, action, and mobile styles
- `Projects/employee_management_system/tests/test_web_app.py`
  - Added 11 directory-filter tests
  - Corrected a viewer test to avoid mutable fixture state
- `README.md`
  - Added Day 92 capability and concepts
  - Updated Project Status
- `Notes/day92_summary.md`
  - Added this continuity record

## Tests

Focused FastAPI web suite:

- **82 tests passed**

Complete Employee Management System suite:

- **299 tests passed**

Day 92 added **11 web tests** covering:

- Filter-form fields and GET submission
- Name searching
- Department filtering
- Salary-range filtering
- Combined filter behavior
- Preserved values and Clear filters navigation
- No-match state
- Incomplete salary ranges
- Non-integer salary values
- Negative salary values
- Reversed salary ranges
- Viewer filtering access

## Current ABAP Status

Day 92 is complete.

The protected web employee directory now supports safe, accessible,
read-only search and filtering for both administrators and viewers.
Browser employee CRUD remains complete, with creation, editing, and
deletion protected by separate permissions and CSRF validation.

SQLite remains the live source of truth. The console application and
legacy migration, verification, backup, and restoration utilities remain
operational.

## Next Step

Day 93 should add protected browser employee sorting to the directory,
reusing `sort_employees_by_name()` and `sort_employees_by_salary()`
while preserving the current search-and-filter query values.