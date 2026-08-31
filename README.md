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

The Employee Management System is an actively developed, security-focused Python application with a complete console interface and a growing FastAPI web interface.

The completed backend includes:

- Employee creation, viewing, updating, and deletion
- Payroll calculations and workforce analytics
- Employee filtering, searching, sorting, reporting, and exporting
- SQLite-primary data storage
- JSON migration and storage-verification utilities
- Database backup and protected restoration
- Activity logging
- Secure password hashing and authentication
- Administrator and viewer roles
- Permission-based authorization with default-deny protection
- Administrator-controlled viewer registration
- Viewer activation and deactivation
- Administrator-controlled viewer password resets
- Self-service password changes for authenticated users
- Protected interactive console workflows

The account-management system rejects inactive administrators, unauthorized viewers, missing accounts, protected administrator targets, unchanged statuses, blank passwords, incorrect current passwords, mismatched confirmations, reused passwords, stale inactive accounts, and mismatched session identities. Successful password operations store only protected hashes while preserving account roles and active statuses.

The FastAPI web interface currently includes:

- An application factory
- A JSON health endpoint at `/health`
- Automatic OpenAPI documentation at `/docs`
- A protected server-rendered dashboard at `/`
- A browser login page at `/login`
- Application-relative template and static-file paths
- A reusable global `base.html` template
- A reusable authenticated `application_base.html` layout
- Jinja template inheritance
- A responsive ABAP navigation sidebar
- A responsive mobile navigation drawer
- Keyboard-accessible navigation controls
- A navigation backdrop
- A visible skip link
- Semantic page structure and ARIA attributes
- An accessible Warm Charcoal visual system
- Teal actions and warm off-white text
- Visible keyboard focus
- Reduced-motion support
- Statuses communicated with icons and written text

Day 81 established the FastAPI, Jinja2, health-check, documentation, and home-page foundation. Day 82 added static-file delivery and responsive CSS styling. Day 83 introduced the permanent ABAP master roadmap, reusable navigation layout, accessible mobile navigation behavior, Warm Charcoal interface, and development-resource cards.

Day 84 introduced the tested web-authentication and login-page foundation. The login workflow reuses the existing SQLite account database and `authenticate_user_account()` service instead of duplicating authentication rules. Only active accounts with valid credentials can create an authenticated browser session.

Signed sessions use ItsDangerous through Starlette’s session middleware. The cookie is named `abap_session`, expires after eight hours, uses `HttpOnly`, and uses `SameSite=Lax`. The application stores only the authenticated user’s ID and username in the signed session. Passwords and password hashes are never stored in the browser session.

The new `web_session.py` helper:

- Starts authenticated sessions
- Clears previous session information before login
- Reloads the current account from SQLite
- Rejects missing session data
- Rejects missing database accounts
- Rejects inactive accounts
- Rejects mismatched user identities
- Returns only a currently valid stored account

Unauthenticated dashboard requests receive a `303` redirect to `/login`. Successful login creates the signed session and redirects to the dashboard. Failed login returns HTTP status `401` and displays the uniform message `Username or password is incorrect.` The failure response does not reveal whether the username exists, whether an account is inactive, or which credential was wrong. Submitted passwords are never returned in the rendered HTML.

The login interface includes:

- Visible username and password labels
- Username autocomplete
- Current-password autocomplete
- Hidden password entry
- Required fields
- Visible focus indicators
- A written and icon-supported error message
- A large keyboard- and touch-friendly sign-in button
- Responsive desktop and mobile layouts
- No protected navigation before authentication

Manual Day 84 verification confirmed that:

- Opening `/` without a session redirects to `/login`
- The Warm Charcoal login page renders correctly
- Incorrect credentials display the uniform error message
- The password field remains hidden and clears after failure
- Correct credentials open the protected dashboard
- The responsive authenticated layout remains usable at narrow widths
- Activity logging records generic failures and successful usernames
- Neither passwords nor password hashes appear in the activity log

The automated suite now contains **229 passing tests**, including **14 FastAPI web tests**. Web coverage verifies:

- Login-page HTML and accessible form attributes
- Valid authentication
- Invalid authentication
- Inactive-account rejection
- Signed session-cookie properties
- Unauthenticated dashboard redirects
- Authenticated dashboard access
- Display of the authenticated username and role
- Reusable navigation
- Accessibility foundations
- Static CSS and JavaScript delivery
- Health endpoint
- API documentation

SQLite remains the live source of truth. Legacy JSON utilities remain available for migration, verification, and historical compatibility. The console application remains operational while the protected browser interface continues to grow.

The permanent development plan is stored in `Notes/master_roadmap.md`. Day 100 remains the original Employee Management System milestone, while Day 155 is the target for the full ABAP portfolio MVP.

The next milestone is Day 85: add tested logout and authenticated-session termination.