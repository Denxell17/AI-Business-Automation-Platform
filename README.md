# AI Business Automation Platform

A Python learning and portfolio project focused on building practical business automation software. The long-term goal is to develop an AI-powered platform that automates repetitive office processes.

## Current Module

### Employee Management System

The current Employee Management System can:

- Register, view, update, and delete employee records
- Use SQLite as the configured primary employee storage for
  normal console loading and saving without modifying the
  legacy JSON file during SQLite-primary saves
- Initialize a tested SQLite employee database schema,
  perform complete CRUD operations, synchronize complete
  employee lists, and safely migrate and verify existing
  JSON employee records
- Protect the interactive console with credential authentication
  before employee records are loaded or the menu is displayed,
  and enforce tested role-based authorization that grants administrators
  all mapped console permissions while limiting viewers to read-only
  employee, payroll, and report actions; unknown roles and permissions
  are denied by default, and denied actions are recorded in the
  activity log
- Allow active administrators to create fixed-role viewer accounts
  through a protected console option with hidden password entry,
  password confirmation, required-input validation, duplicate-username
  rejection, success-only activity logging, and default-deny access
  for viewers and inactive administrators
- Allow active administrators to deactivate and reactivate viewer
  accounts through protected console option 15, while rejecting
  missing accounts, administrator targets, unchanged statuses,
  viewers, and inactive administrators; successful changes are
  recorded in the activity log
- Allow active administrators to reset viewer-account passwords
  through protected console option 16 with hidden password entry,
  password confirmation, required-input validation, generic failure
  messages, and success-only activity logging; viewers, inactive
  administrators, missing accounts, administrator targets, blank
  passwords, and reuse of the current password are rejected, while
  successful resets preserve the viewer's role and active status
- Allow active administrators and viewers to change their own
  passwords through console option 17 after verifying the current
  password, using hidden current-password, new-password, and
  confirmation entry, required-input validation, generic failure
  messages, and success-only activity logging; blank input, incorrect
  current passwords, password reuse, inactive sessions, deactivated
  saved accounts, missing accounts, and mismatched session identities
  are rejected, while successful changes preserve the user's role and
  active status; Exit is available through option 18
- Use a tested employee repository throughout the console
  application to separate employee workflows from SQLite
  loading and saving details
- Compare the complete JSON and SQLite employee lists using
  a read-only consistency check that reports missing,
  different, invalid, or matching storage data
- Validate loaded employee records and business rules
- Retain tested legacy JSON loading, atomic saving, backup
  restoration, migration, and verification utilities
- Create, safely refresh, and restore SQLite database backups
  through commands or interactive console options using native
  backup operations, integrity checks, and confirmation prompts
- Calculate payroll, tax, allowances, bonuses, and compensation
- Display workforce summaries, total department count,
  department headcounts, payroll totals, and average salaries,
  largest and smallest departments,
  highest- and lowest-payroll departments,
  highest- and lowest-average-salary departments,
  and compensation range
- Filter employees by department
- Filter employees by an inclusive salary range
- Search employees using all or part of a name
- Sort employees alphabetically or by salary
- Export employee reports to CSV
- Record application activity in a log file
- Run a complete automated test suite
- Run continuously through an interactive menu
- Provide a tested FastAPI web foundation with an application
  factory, JSON health check, automatic OpenAPI documentation,
  and a server-rendered Jinja2 home page while preserving the
  existing console application
- Provide tested browser logout through a POST-only endpoint that
  clears the authenticated session, expires the signed cookie,
  records successful logout activity, and redirects to sign-in
- Provide a protected, permission-checked employee directory that
  loads current SQLite records through the employee repository,
  supports administrator and viewer access, denies missing
  permissions by default, handles loading failures safely, and
  presents responsive employee information with accessible states
- Provide protected, permission-checked employee profiles that
  use normalized employee-ID searches, support administrator and
  viewer access, return safe missing-record and loading-failure
  pages, link from the employee directory, and exclude payroll-
  sensitive fields from the general employee-view permission
- Provide protected employee payroll pages that require the separate
  `VIEW_PAYROLL` permission, reuse the existing payroll calculation
  service, return safe missing-record and loading-failure pages, and
  keep financial information separate from general employee profiles
- Provide an administrator-only browser employee-creation workflow
  with `REGISTER_EMPLOYEE` permission checks, signed-session CSRF
  protection, server-side validation, normalized duplicate-ID
  rejection, repository-backed SQLite saving, activity logging, safe
  failure handling, and redirect-to-profile confirmation
- Provide an administrator-only browser employee-editing workflow
  with `UPDATE_EMPLOYEE` permission checks, signed-session CSRF
  protection, server-side required-field validation, repository-backed
  SQLite saving, activity logging, safe missing-record and repository
  failure handling, prefilled forms, and redirect-to-profile
  confirmation for department, position, email, and phone-number
  updates
- Provide an administrator-only browser employee-deletion workflow
  with a protected confirmation page, `DELETE_EMPLOYEE` permission
  checks, signed-session CSRF protection, repository-backed SQLite
  synchronization, transactional rollback safety, successful-deletion
  activity logging, safe missing-record and storage-failure handling,
  POST-redirect-GET navigation, permission-aware profile actions, and
  accessible destructive-action warnings
- Provide a protected, read-only browser employee-directory search and
  filtering workflow that supports case-insensitive partial-name
  searches, case-insensitive exact department filters, inclusive salary
  ranges, combined match-all filters, server-side salary validation,
  preserved query values, clear-filter navigation, safe SQLite loading
  failures, accessible filter controls, responsive layouts, and
  administrator-and-viewer access through the existing
  `VIEW_EMPLOYEE` permission
- Provide protected, read-only browser employee-directory sorting with
  default-order fallback, alphabetical name sorting, highest-salary-first
  sorting, preserved sorting and filter query values, combined
  filter-then-sort behavior, accessible sorting controls, responsive
  select styling, and administrator-and-viewer access through the
  existing `VIEW_EMPLOYEE` permission
- Provide a protected, read-only browser workforce report that reuses
  existing summary services to show employee and department headcounts,
  largest and smallest departments, safe loading-failure and empty states,
  responsive accessible report tables, and administrator-and-viewer access
  through the existing `VIEW_EMPLOYEE` permission without showing salary
  or payroll values
- Provide a protected browser CSV-download workflow that requires the
  existing `EXPORT_REPORT` permission, reuses the employee CSV service,
  delivers the current SQLite employee report as an in-memory attachment,
  records successful downloads and denied attempts, and exposes salary
  values only to users who hold the explicit export permission
- Provide a protected administrator-only browser activity-log page at
  `/activity-log` that requires the dedicated `VIEW_ACTIVITY_LOG`
  permission, reads only the fixed server-side activity-log file, shows
  the latest 100 entries newest first, safely handles missing and unreadable
  logs, hides the navigation link from unauthorized users, records denied
  access, and uses a dedicated non-propagating application logger so
  framework messages do not pollute audit history
- Provide a protected administrator-only browser user-account directory at
  `/users` that requires `MANAGE_USER_ACCOUNTS`, reads only safe account
  summaries from SQLite, never selects or displays password hashes, sorts
  accounts case-insensitively by username, records denied access, handles
  safe loading failures, provides accessible active and inactive statuses,
  and remains responsive on narrow screens
- Serve a tested static CSS stylesheet through FastAPI, connect it
  to the Jinja2 home page, and provide a responsive navy-and-teal
  business interface with constrained content width, reusable design
  variables, accessible status presentation, and desktop and
  narrow-screen layouts

## Technologies

- Python
- Visual Studio Code
- Git
- GitHub
- SQLite
- FastAPI
- Jinja2
- HTML
- Uvicorn
- CSS
- JavaScript
- ItsDangerous signed sessions

## Project Structure

```text
AI-Business-Automation-Platform/
├── Assets/
├── Lessons/
├── Notes/
├── Projects/
│   └── employee_management_system/
│       ├── archive/
│       │   └── main_original.py
│       ├── data/
│       ├── exports/
│       ├── logs/
│       ├── static/
│       │   ├── navigation.js
│       │   └── styles.css
│       ├── tests/
│       ├── templates/
│       │   ├── application_base.html
│       │   ├── activity_log.html
│       │   ├── base.html
│       │   ├── employee_form.html
│       │   ├── employee_edit.html
│       │   ├── employee_payroll.html
│       │   ├── employee_profile.html
│       │   ├── employees.html
│       │   ├── home.html
│       │   ├── user_accounts.html
│       ├── activity_logger.py
│       ├── admin_setup.py
│       ├── authentication.py
│       ├── authorization.py
│       ├── config.py
│       ├── data_validation.py
│       ├── database.py
│       ├── database_backup.py
│       ├── database_restore.py
│       ├── employee_repository.py
│       ├── employee_service.py
│       ├── exporter.py
│       ├── main.py
│       ├── migration.py
│       ├── models.py
│       ├── payroll.py
│       ├── performance_boundary_demo.py
│       ├── reports.py
│       ├── requirements.txt
│       ├── run_tests.py
│       ├── storage.py
│       ├── storage_verification.py
│       ├── user_account_setup.py
│       ├── user_service.py
│       ├── validators.py
│       ├── web_app.py
│       └── web_session.py
└── README.md
```

## Running the Application

From the main project folder, run:

```powershell
python Projects\employee_management_system\main.py
```

## Running the Web Application

Create and activate a virtual environment, install the Employee
Management System dependencies, and start FastAPI from the main
project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r Projects\employee_management_system\requirements.txt
.\.venv\Scripts\python.exe -m fastapi dev Projects\employee_management_system\web_app.py
```

Open `http://127.0.0.1:8000/` for the HTML home page,
`http://127.0.0.1:8000/health` for the JSON health check, or
`http://127.0.0.1:8000/docs` for the interactive API documentation.


## Creating the Initial Administrator

To create the first SQLite administrator account, run:

```powershell
python Projects\employee_management_system\admin_setup.py
```

Enter a username, then enter and confirm the hidden password.
The setup succeeds only when the SQLite `users` table contains
no existing accounts. Later setup attempts are rejected.

## Running the Performance Test

```powershell
python Projects\employee_management_system\performance_boundary_demo.py
```

## Creating a SQLite Database Backup

From the main project folder, run:

```powershell
python Projects\employee_management_system\database_backup.py
```

## Restoring a SQLite Database Backup

```powershell
python Projects\employee_management_system\database_restore.py
```

Type `RESTORE` when prompted to confirm replacing the primary
SQLite database.

## Verifying JSON and SQLite Consistency

```powershell
python Projects\employee_management_system\storage_verification.py
```

## Running the Automated Tests

```powershell
python Projects\employee_management_system\run_tests.py
```

## Concepts Practiced

- Variables and data types
- User input and validation loops
- Conditions and logical operators
- Functions, parameters, and return values
- Lists, dictionaries, sets, and sorting
- Modules, imports, and separation of responsibilities
- Repository pattern, configurable storage backends,
  console-to-repository integration, default primary-storage
  selection, supported-value checks, and synchronization rules
- Refactoring large functions into focused helper functions
- Type hints and `TypedDict`
- User-account data modeling, SQLite account insertion and
  case-insensitive retrieval, account counting, service-layer
  password protection, duplicate-username rejection, credential
  authentication, inactive-account enforcement, one-time initial
  administrator setup, hidden password entry with `getpass`,
  password confirmation, command-layer separation, process exit
  codes, uniform authentication failure, controlled role and
  active-status constraints, PBKDF2-HMAC-SHA256 password hashing,
  unique random salts, iteration work factors, hexadecimal
  encoding, secure hash comparison, and malformed-hash rejection
- Role-based authorization, named permission constants,
  role-to-permission sets, menu-to-permission mapping,
  default-deny security rules, permission membership checks,
  denied-action logging, `for` loops, and `subTest()` coverage
- Administrator-only viewer-account creation, fixed-role assignment,
  service and command-layer authorization, hidden password confirmation,
  required-input validation, duplicate-account protection, success-only
  audit logging, menu integration, and end-to-end authorization testing
- Administrator-only viewer-account status management, Boolean-to-SQLite
  conversion, affected-row verification, safe activation and deactivation,
  protected administrator accounts, missing-target rejection, unchanged-status
  rejection, command-layer status messages, console action normalization,
  early input validation, success-only audit logging, and end-to-end testing
- Administrator-controlled viewer password resets, password-hash
  replacement, affected-row verification, active-administrator
  authorization, viewer-target protection, blank-password rejection,
  current-password reuse detection, delayed hashing after validation,
  inactive-viewer status preservation, command-layer Boolean-to-message
  conversion, generic failure reporting, hidden password confirmation,
  required-input validation, protected menu routing, exit-option
  renumbering, success-only audit logging, and end-to-end testing
- Self-service password-change business rules, current-password
  verification, role-independent credential ownership, live account
  reloading, session and saved-account active-status checks,
  session-to-record user-ID matching, missing-account rejection,
  password-reuse prevention, delayed hashing, role and status
  preservation, command-layer Boolean-to-message conversion, hidden
  console password entry and confirmation, required-input validation,
  generic failure reporting, success-only activity logging, shared
  administrator-and-viewer menu routing, exit-option renumbering,
  `subTest()` boundary coverage, and end-to-end testing
- JSON storage and runtime data validation
- SQLite CRUD operations, complete-list synchronization,
  transactions, commits, rollbacks, duplicate-safe migrations,
  JSON-to-SQLite verification, file-existence checks,
  main guards, and process exit codes
- SQLite native backup and restoration operations, source and
  destination connections, backup replacement, integrity
  checks, parent-directory creation, and guaranteed connection
  cleanup with `finally`
- Console backup and restoration integration, destructive-action
  confirmation, post-restoration session reload, secondary JSON
  synchronization, and mocked success, cancellation, and failure
  workflow testing
- Read-only cross-storage verification, normalized list
  comparison, missing-file checks, and database-error handling
- Transitional dual-storage saves, startup synchronization,
  `None`-versus-empty-list handling, and mocked dependency testing
- Single-source-of-truth transitions, retirement of dual writes,
  SQLite-only primary saves, legacy-storage compatibility,
  configuration-default testing, and storage-dependency auditing
- CSV report generation
- File and directory paths with `pathlib`
- Exception handling
- Atomic file saving and backups
- Activity logging
- Unit, boundary, and regression testing
- Project-file organization
- FastAPI application factories, HTTP GET routes, JSON and HTML
  responses, automatic OpenAPI documentation, and Uvicorn
  development serving
- Jinja2 template rendering, template context values, semantic
  HTML structure, and reliable template-directory resolution
- FastAPI `TestClient` health-check, documentation, and
  server-rendered home-page testing
- FastAPI static-file mounting, named static routes, stylesheet
  delivery, MIME content-type verification, and HTML-to-CSS
  connection testing
- CSS custom properties, universal box sizing, font stacks,
  constrained responsive widths, `min()`, `calc()`, `clamp()`,
  card surfaces, borders, shadows, status indicators, and
  mobile media queries
- Accessible HTML-to-CSS class mapping, labelled sections,
  decorative-element hiding with `aria-hidden`, desktop visual
  verification, and narrow-screen overflow checking
- POST-only browser logout, authenticated-session clearing,
  signed-cookie expiration, safe unauthenticated logout handling,
  successful logout auditing, and protected-page reauthorization
- Authenticated employee-directory routing, repository-backed web
  data loading, web permission enforcement, default-deny HTTP `403`
  responses, denied-access activity logging, safe repository-failure
  handling, semantic data tables, table captions, scoped row and
  column headers, accessible empty states, responsive horizontal
  scrolling, temporary SQLite web fixtures, and mocked boundary tests
- Dynamic FastAPI path parameters, protected employee-profile
  routing, normalized service-layer record lookup, case-insensitive
  URL identifiers, safe HTTP `404` profile responses, profile-level
  repository-failure handling, semantic description lists, responsive
  detail cards, generated record links, back navigation, long-value
  wrapping, payroll-field separation, and profile boundary testing
- Protected FastAPI form workflows, GET-and-POST route separation,
  `Annotated` form fields, signed-session CSRF tokens, constant-time
  token comparison, server-side form normalization and validation,
  duplicate-record prevention, repository-backed SQLite saves,
  POST-redirect-GET navigation, form-value preservation, written
  validation errors, permission-aware actions, responsive form grids,
  and creation-workflow boundary testing
- Protected web employee editing, separate read and update
  permissions, prefilled edit forms, partial-record service helpers,
  contact-detail validation, atomic contact updates, HTTP `403`,
  `404`, and `500` edit responses, update activity logging,
  permission-aware profile actions, responsive paired actions, and
  service-plus-web regression testing
- Protected web employee deletion, explicit confirmation pages,
  POST-only destructive actions, `DELETE_EMPLOYEE` authorization,
  permission-aware destructive controls, signed-session CSRF
  validation before storage access, case-insensitive employee lookup,
  service-layer list removal, transactional SQLite synchronization,
  rollback-safe persistence failures, success-only deletion logging,
  safe `403`, `404`, and `500` responses, POST-redirect-GET navigation,
  accessible irreversible-action warnings, destructive-button styling,
  and end-to-end deletion boundary testing
- Protected read-only directory search and filtering, GET query
  parameters, query-input normalization, optional filter controls,
  server-side integer conversion, paired salary-range validation,
  negative-value and reversed-range rejection, service-layer filter
  composition, preserved filter values, clear-filter navigation,
  no-match states, accessible search forms, responsive filter grids,
  viewer-access regression coverage, and state-independent web tests
- Protected read-only directory sorting, allowlisted query values,
  default-order fallback, service-layer name and salary sorting,
  filter-then-sort sequencing, preserved sorting controls, accessible
  native select elements, shared input-and-select styling, controlled
  multi-record web fixtures, order assertions, combined-control tests,
  and viewer sorting regression coverage
- Protected read-only browser workforce reporting, service-layer workforce
  summaries, permission-protected aggregate analytics, salary-safe template
  context selection, empty and loading-failure states, semantic report
  tables, responsive metric cards, active navigation, and administrator
  and viewer regression coverage
- Protected browser CSV downloads, permission-aware report actions,
  in-memory CSV generation, UTF-8 BOM spreadsheet compatibility,
  attachment response headers, success-only download activity logging,
  denied-export logging, loading-failure handling, and exporter-plus-web
  regression coverage
- Protected browser activity-log viewing, dedicated administrator-only
  permissions, fixed server-side log paths, bounded newest-first file reads,
  safe missing-file and unreadable-file states, Jinja2 activity-entry
  escaping, permission-aware navigation, named Python loggers, handler
  configuration, logger propagation control, framework-log isolation, and
  activity-log authorization and route regression coverage
- Protected browser user-account directories, safe `TypedDict` view models,
  SQL column minimization, password-hash exclusion, case-insensitive SQLite
  ordering, controlled SQLite loading failures, administrator-only account
  permissions, denied-access audit logging, safe table template contexts,
  written active and inactive statuses, responsive account-table layouts,
  and account-directory regression coverage
- Protected browser viewer-account creation, administrator-only creation
  forms, session-based CSRF validation, required-field and password-match
  validation, blank-value service protection, password-safe error contexts,
  generic registration-failure handling, Post/Redirect/Get completion,
  success-only audit logging, and creation-route regression coverage
- Protected browser viewer-account status management, POST-only
  activation-and-deactivation actions, per-row signed-session CSRF forms,
  Boolean status allowlisting, generic status-failure handling,
  viewer-only controls, administrator-target protection, success-only audit
  logging, Post/Redirect/Get completion, responsive action-table layouts,
  isolated mutable fixtures, and status-route regression coverage

## Project Status

The Employee Management System is an actively developed,
security-focused Python application with a complete console interface
and a growing authenticated FastAPI web interface.

The backend provides employee CRUD, payroll and workforce analytics,
filtering, reporting, CSV export, SQLite-primary storage, JSON migration
and verification, database backup and protected restoration, activity
logging, secure password hashing, administrator and viewer roles,
default-deny authorization, viewer-account administration, and
self-service password changes.

The FastAPI interface now provides:

- An application factory, `/health`, and `/docs`
- A protected server-rendered dashboard at `/`
- Accessible browser login at `/login`
- POST-only browser logout at `/logout`
- A protected employee directory at `/employees`
- Protected employee profiles at `/employees/{employee_id}`
- Protected payroll pages at `/employees/{employee_id}/payroll`
- An administrator-only Add employee page and submission route at
  `/employees/new`
- An administrator-only Edit employee page and submission route at
  `/employees/{employee_id}/edit`
- An administrator-only employee-deletion confirmation page and POST route
  at `/employees/{employee_id}/delete`
- A protected workforce report at `/reports/workforce`
- A protected employee CSV download at `/reports/employees.csv`
- An administrator-only activity-log page at `/activity-log`
- An administrator-only user-account directory at `/users`
- An administrator-only viewer-account creation form and submission route at
  `/users/new`
- An administrator-only viewer-status update route at
  `/users/{username}/status`
- Signed eight-hour `abap_session` cookies with `HttpOnly` and
  `SameSite=Lax`
- Signed-session CSRF protection for employee creation, editing, deletion,
  viewer-account creation, and viewer-status changes
- Live SQLite account revalidation before protected access
- Complete authenticated-session termination during logout
- Repository-backed employee loading and saving
- Separate `VIEW_EMPLOYEE`, `VIEW_PAYROLL`, `REGISTER_EMPLOYEE`,
  `UPDATE_EMPLOYEE`, `DELETE_EMPLOYEE`, `EXPORT_REPORT`,
  `VIEW_ACTIVITY_LOG`, and `MANAGE_USER_ACCOUNTS` permission enforcement
- Permission-aware employee, reporting, activity-log, user-account,
  viewer-account creation, and viewer-status actions
- Default-deny responses and activity logging for missing permissions
- Case-insensitive partial-name directory searches
- Case-insensitive exact department directory filters
- Inclusive minimum-and-maximum salary directory filters
- Combined directory filters that require all selected conditions
- Server-side salary-range validation with preserved query values
- Clear-filter navigation and distinct no-match directory states
- Administrator and viewer directory filtering through `VIEW_EMPLOYEE`
- Protected workforce reports through `VIEW_EMPLOYEE`
- Aggregate employee and department headcounts without salary or payroll
  values
- CSV export downloads through `EXPORT_REPORT`
- In-memory CSV attachments with salary values limited to export-authorized
  users
- Activity-log access through administrator-only `VIEW_ACTIVITY_LOG`
- Fixed server-side activity-log reading with no browser-provided file path
- Bounded activity-log display of the latest 100 entries, newest first
- Safe activity-log empty and loading-failure states
- User-account access through administrator-only `MANAGE_USER_ACCOUNTS`
- Safe account-summary data that excludes password hashes
- Case-insensitive username ordering and safe account-loading failure states
- Administrator-only viewer-account creation with password-safe error pages
- Administrator-only viewer activation and deactivation
- Viewer-only status controls and written administrator unavailable actions
- Boolean status allowlisting before account-status service calls
- Explicit confirmation before permanent employee deletion
- POST-only destructive employee deletion
- CSRF validation before deletion reads or mutates employee storage
- Transactional SQLite synchronization with rollback on failure
- Success-only employee-creation, update, deletion, viewer-account
  registration, viewer-status, and CSV-download activity logging
- Safe employee-loading and saving failure handling
- Safe missing-employee `404` pages
- Case-insensitive employee-ID lookup
- Generated employee-profile, payroll, edit, and delete links
- Post/Redirect/Get navigation after employee creation, editing, deletion,
  viewer-account creation, and viewer-status changes
- Semantic employee tables, profile description lists, payroll summaries,
  labelled employee and viewer-account forms, labelled filter controls,
  activity-log entries, and user-account tables
- Accessible error, warning, confirmation, empty, and no-match states
- Responsive employee tables, profile cards, payroll cards, forms,
  confirmation pages, profile actions, directory filter controls,
  workforce report cards, download actions, activity-log entries, and
  user-account status-action tables
- Written destructive-action labels that do not rely on color alone
- Visible keyboard focus and narrow-screen controls
- Peso currency formatting with two decimal places
- Reuse of existing employee, payroll, report, export, search, filter,
  activity-logging, user-account, and viewer-status services
- Separation of general employee information from payroll-sensitive
  information
- Separation of safe user-account summaries from password-hash data
- Active authenticated navigation
- Administrator-only Activity log and User accounts navigation
- The accessible Warm Charcoal visual system, visible focus,
  reduced-motion support, and written status labels

Day 84 established browser login and authenticated sessions. Day 85
completed explicit logout and authenticated-session termination. Day 86
introduced the protected read-only employee directory. Day 87 added
protected individual employee profiles. Day 88 added protected browser
employee payroll pages. Day 89 added protected browser employee creation.
Day 90 added protected browser employee editing. Day 91 added protected
browser employee deletion. Day 92 added protected browser directory search
and filtering. Day 93 added protected browser directory sorting. Day 94
added protected browser workforce reporting. Day 95 added protected browser
employee CSV downloads. Day 96 added protected administrator-only browser
activity-log viewing. Day 97 added protected administrator-only browser
user-account viewing. Day 98 added protected administrator-only browser
viewer-account creation. Day 99 added protected administrator-only browser
viewer activation and deactivation.

Directory searching, filtering, and sorting require an authenticated user
with `VIEW_EMPLOYEE`. Both administrators and viewers can use the read-only
GET form. Missing permission returns HTTP `403` before employee records are
loaded, while unauthenticated users are redirected to `/login`.

The directory accepts optional `search_text`, `department`,
`minimum_salary`, `maximum_salary`, and `sort_by` query parameters. Text
values are normalized before filtering. The existing service functions
perform case-insensitive partial-name searching, case-insensitive exact
department matching, inclusive salary-range filtering, alphabetical name
sorting, and highest-salary-first sorting.

The workforce report requires `VIEW_EMPLOYEE` and uses the existing
`calculate_workforce_summary()` service. It exposes aggregate employee and
department information without salary or payroll values in template context.
The CSV download requires `EXPORT_REPORT`, generates an in-memory
`employee_report.csv` attachment, includes a UTF-8 BOM for spreadsheet
compatibility, and logs only successful downloads.

The activity-log page requires administrator-only `VIEW_ACTIVITY_LOG`. It
reads only the fixed server-side log file, displays at most the latest 100
entries newest first, safely handles missing and unreadable logs, and records
denied access. A dedicated `abap.activity` logger keeps framework messages
out of the audit trail.

The user-account directory requires administrator-only
`MANAGE_USER_ACCOUNTS`. It loads only user ID, username, role, and active
status from SQLite; password hashes are never selected or displayed.
Accounts are ordered case-insensitively by username. Unauthenticated users
are redirected to `/login`, denied users receive HTTP `403` and an
activity-log entry, and a SQLite loading failure returns a safe error page.

Viewer-account creation at `/users/new` also requires
`MANAGE_USER_ACCOUNTS`. Its form uses a signed-session CSRF token, requires a
username and matching nonblank passwords, and reuses
`register_viewer_account()` for authorization, password hashing, role
assignment, duplicate protection, and SQLite storage. Error pages preserve
only the submitted username. Successful creation logs the action and
redirects with HTTP `303` to `/users`.

Viewer-status changes use POST requests to `/users/{username}/status`. Each
viewer row contains a CSRF-protected form that submits an allowlisted
`true` or `false` status value. The route checks authentication,
authorization, and CSRF before calling
`set_viewer_account_active_status()`. That existing service independently
rejects missing accounts, administrator targets, unchanged statuses, viewer
users, and inactive administrators. The browser shows status controls only
for viewer accounts, returns a generic error on failure, logs only successful
changes, and redirects with HTTP `303` back to `/users`.

Employee deletion remains protected by `DELETE_EMPLOYEE`. Opening the
confirmation page never modifies storage. The deletion POST route checks
authorization and signed-session CSRF protection before loading records,
uses the repository and existing service layer, commits the updated list in
one SQLite transaction, logs only successful deletions, and redirects with
HTTP `303`.

The automated suite contains **347 passing tests**, including
**123 FastAPI web tests**. Day 99 added **7 web tests** covering
unauthenticated redirects, viewer denial and audit logging, invalid CSRF
rejection, invalid status-value rejection, generic service failures,
successful deactivation, successful reactivation, accessible action controls,
and isolated mutable account fixtures.

SQLite remains the live source of truth. Legacy JSON utilities remain
available for migration, verification, and historical compatibility.
The console application remains operational while protected browser
workflows continue to grow.

The permanent development plan is stored in
`Notes/master_roadmap.md`. Day 100 remains the original Employee Management
System milestone, while Day 155 is the target for the full ABAP portfolio
MVP.
