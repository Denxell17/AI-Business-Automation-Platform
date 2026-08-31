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
│       │   ├── base.html
│       │   ├── employees.html
│       │   ├── home.html
│       │   └── login.html
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

## Project Roadmap

Future versions will introduce:

- Additional filtering and reporting options
- REST APIs
- Expanded responsive web interface and browser workflows
- AI document processing
- AI-generated business reports
- Workflow automation
- Deployment and production configuration


## Project Status

The Employee Management System is an actively developed, security-focused Python application with a complete console interface and a growing authenticated FastAPI web interface.

The backend provides employee CRUD, payroll and workforce analytics, filtering, reporting, CSV export, SQLite-primary storage, JSON migration and verification, database backup and protected restoration, activity logging, secure password hashing, administrator and viewer roles, default-deny authorization, viewer-account administration, and self-service password changes.

The FastAPI interface now provides:

- An application factory, `/health`, and `/docs`
- A protected server-rendered dashboard at `/`
- Accessible browser login at `/login`
- POST-only browser logout at `/logout`
- A protected employee directory at `/employees`
- Signed eight-hour `abap_session` cookies with `HttpOnly` and `SameSite=Lax`
- Live SQLite account revalidation before protected access
- Complete authenticated-session termination during logout
- Repository-backed employee loading
- Existing `VIEW_EMPLOYEE` permission enforcement
- Administrator and viewer employee-directory access
- Default-deny responses and activity logging for missing permissions
- Safe employee-loading failure handling
- Semantic employee tables with captions and scoped headers
- Accessible error and empty-directory states
- Responsive horizontal table scrolling
- Active authenticated navigation
- The accessible Warm Charcoal visual system, visible focus, reduced-motion support, and written status labels

Day 84 established browser login and authenticated sessions. Day 85 completed explicit logout and authenticated-session termination. Day 86 introduced the first protected employee-data workflow through a read-only employee directory.

The employee directory reloads the current account before access, requires `VIEW_EMPLOYEE`, and loads current SQLite records through `load_employee_records()`. Missing permissions return HTTP status `403` and create a denied-access activity entry. Repository failures return HTTP status `500` with a safe written message rather than exposing database details.

The directory displays employee ID, name, department, position, and written employment status. A semantic table, caption, scoped headers, keyboard-focusable scrolling container, employee count, empty state, and responsive layout keep the page usable across desktop and narrow screens.

The automated suite contains **240 passing tests**, including **25 FastAPI web tests**. Day 86 coverage verifies unauthenticated redirects, administrator access, viewer access, default-deny authorization, denied-access logging, repository-failure handling, empty-directory presentation, real temporary SQLite data rendering, and active navigation.

Manual Day 86 verification confirmed that:

- Real SQLite employee records appear at `/employees`
- The employee count is correct
- The Employees navigation item is active
- The table remains contained and horizontally scrollable at narrow widths
- Visible keyboard focus remains available
- Logout removes access to the employee directory
- Unauthenticated access redirects to `/login`

SQLite remains the live source of truth. Legacy JSON utilities remain available for migration, verification, and historical compatibility. The console application remains operational while protected browser workflows continue to grow.

The permanent development plan is stored in `Notes/master_roadmap.md`. Day 100 remains the original Employee Management System milestone, while Day 155 is the target for the full ABAP portfolio MVP.
