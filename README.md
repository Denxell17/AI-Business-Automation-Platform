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
- PostgreSQL
- Psycopg 3
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
├── .env.example
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
│       ├── migrations/
│       │   └── postgresql/
│       │       └── 001_initial_schema.sql
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
│       ├── database_config.py
│       ├── database_connection.py
│       ├── database_backup.py
│       ├── database_restore.py
│       ├── employee_repository.py
│       ├── employee_service.py
│       ├── exporter.py
│       ├── main.py
│       ├── migration.py
│       ├── postgresql_migrations.py
│       ├── models.py
│       ├── payroll.py
│       ├── performance_boundary_demo.py
│       ├── reports.py
│       ├── requirements.txt
│       ├── run_tests.py
│       ├── schedule_service.py
│       ├── storage.py
│       ├── storage_verification.py
│       ├── user_account_setup.py
│       ├── user_service.py
│       ├── validators.py
│       ├── web_app.py
│       ├── web_session.py
│       └── workflow_service.py
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

### Employee Management System

The Employee Management System is complete and available through both console
and authenticated FastAPI interfaces. It provides secure employee records,
payroll calculations, workforce reporting, account administration, activity
history, data export, backup, and restoration. SQLite remains the working local
source of truth, while legacy JSON tools support migration and verification.

### ABAP Platform Development

ABAP is developing into a secure business automation portfolio platform. The
current application combines Employee Management, Workflow Automation, and
template-based AI-agent management. It includes reusable workflows, ordered
tasks, task outcomes, stored schedules, timezone-aware eligibility, duplicate
occurrence protection, protected Agent Template configuration, and
administrator-only Agent Execution history and detail views.

The shared authenticated dashboard provides access to the available modules,
API documentation, and system-health information through a consistent,
responsive interface.

### Database Portability

- SQLite remains the default local and automated-test database
- PostgreSQL is the selected production database
- Environment-based `DATABASE_BACKEND` selection
- Required and validated `DATABASE_URL` for PostgreSQL
- Psycopg 3 connection support
- Safe `.env.example` configuration without real credentials
- Centralized SQLite and PostgreSQL connection selection
- A shared PostgreSQL compatibility adapter for parameter placeholders,
  SQLite-specific SQL forms, mapping rows, and timestamp normalization
- SQLite foreign-key enforcement preserved
- Configured-backend persistence for user accounts, employees, workflows,
  tasks, executions, schedules, and schedule occurrences
- Case-insensitive username lookup preserved on both supported backends
- PostgreSQL row locking for workflow task resequencing and deletion
- SQLite-only backup and restoration paths kept separate from production
  PostgreSQL connections
- Initial PostgreSQL schema for users, employees, workflows, tasks,
  schedules, occurrences, workflow executions, and task executions
- PostgreSQL foreign keys, indexes, uniqueness rules, and business
  validation constraints
- UTC-aware PostgreSQL timestamps through `TIMESTAMPTZ`
- Ordered migration files using the `001_description.sql` format
- A `schema_migrations` table that records completed migrations
- Repeatable migration execution that skips migrations already applied
- A follow-up schema migration that aligns employee performance scores with
  the application's `0` to `100` validation and prevents duplicate task
  records within one workflow execution
- Mocked PostgreSQL tests that require no live database server
- A Docker Compose environment using PostgreSQL 18.6, persistent storage,
  data checksums, localhost-only port binding, and a readiness health check
- A gated live integration suite covering users, employees, workflows, tasks,
  executions, schedules, occurrence claims, agent-template browser operations,
  Agent Execution service and browser operations, and cleanup

### AI Agent Template Capabilities

- Typed agent-template records with stable IDs, names, descriptions, system
  prompts, model names, creator references, and UTC timestamps
- Draft, active, and inactive lifecycle states
- Administrator-only `agent_templates.manage` authorization
- Read-only `agent_templates.view` authorization for administrators and viewers
- Matching SQLite and PostgreSQL persistence contracts
- Ordered PostgreSQL migration `003_create_agent_templates.sql`
- Parameterized insert, ordered-list, exact-ID, and guarded update repository
  operations
- Live account revalidation before template creation and editing
- Required-field and maximum-length validation
- Draft-only creation so unreviewed prompts cannot become active immediately
- Controlled Draft-to-Active, Active-to-Inactive, and Inactive-to-Active
  lifecycle transitions
- Stored-status checks that reject stale lifecycle submissions
- Protected browser directory and detail pages for administrators and viewers
- Complete system prompts restricted to protected detail pages and excluded from
  general listings
- Allowlisted Draft, Active, and Inactive directory filtering
- Administrator-only browser creation and editing with signed-session CSRF
  protection
- Safe validation and database-error responses with submitted-value preservation
- Permission-controlled actions, sidebar navigation, and activity logging
- Live PostgreSQL browser creation, editing, activation, detail, and cleanup
  verification

### AI Agent Execution Capabilities

- Typed execution records with stable IDs, template and model snapshots, input,
  output, safe errors, requesting users, lifecycle status, and UTC timestamps
- Running, Completed, and Failed states with database-enforced field consistency
- Matching SQLite schema and ordered PostgreSQL migration
  `004_create_agent_executions.sql`
- Foreign keys to Agent Templates and users, plus indexed template and user
  history queries
- Parameterized insertion, exact loading, newest-first template history, and
  one-way completion or failure repository operations
- Administrator-only `agent_templates.execute` authorization
- Live account, identity, activity, and permission revalidation before execution
- Active-template enforcement before any provider call
- Provider-independent `AgentProvider` protocol with keyword-only model, system
  prompt, and input arguments
- OpenAI adapter implemented behind the provider-independent protocol
- Environment-only `OPENAI_API_KEY` loading without a source-code fallback
- Validated `OPENAI_TIMEOUT_SECONDS` configuration restricted to 1 through 120
  seconds
- OpenAI Responses API mapping for template model, system instructions, and
  submitted input with provider response storage disabled
- Predictable single-attempt requests with SDK retries disabled
- Safe `AgentProviderError` translation for SDK failures and unusable provider
  output without exposing provider details
- Deterministic OpenAI adapter tests with an injected in-memory client and no
  network requests or API cost
- Normalized input and output with explicit maximum lengths
- Safe Failed records for provider exceptions and invalid provider responses
  without storing private exception details
- Deterministic service tests that make no network requests and incur no API cost
- Live PostgreSQL execution, finalization, loading, history, and cleanup
  verification
- Administrator-only browser history ordered newest first without exposing
  submitted input, generated output, or error details in the listing
- Protected execution detail pages for Running, Completed, and Failed records
  with escaped input, output, and safe error content
- Template-scoped execution lookup that rejects mismatched execution IDs
- Safe browser handling for missing records and database failures

### Shared Dashboard Capabilities

- Protected dashboard access through the existing signed session
- Shared `ABAP workspace` navigation and top-bar language
- Available Employee Management module with a working directory link
- Available Workflow Automation module with a working directory link
- Written `Available` and `Planned` module statuses
- API documentation and system-health resources
- Semantic dashboard sections and headings
- Responsive module cards for desktop and mobile layouts
- Visible keyboard focus and reduced-motion support
- Warm Charcoal styling consistent with the official ABAP visual direction
- Status information communicated with written labels rather than color alone

### Workflow Automation Capabilities

The Workflow Automation domain defines:

- Workflows as reusable business-process definitions
- Ordered workflow tasks as reusable process steps
- Stored schedules as future run-eligibility rules
- Workflow executions as historical run records
- Task executions as historical task-result records

The tested SQLite workflow foundation provides:

- A `workflows` table with stable public workflow IDs
- Required, non-blank workflow names
- `draft`, `active`, and `inactive` lifecycle states
- Required creator-account references
- Required creation and update timestamps
- SQLite foreign-key enforcement on every database connection
- Safe workflow insertion with parameterized SQL and rollback handling
- Deterministic workflow loading and safe empty-list handling
- A `workflow_tasks` table with stable task IDs and parent-workflow foreign keys
- Unique, positive sequence numbers within each workflow
- Manual task types, required/optional flags, instructions, and UTC timestamps
- Parameterized task insertion and ordered per-workflow retrieval
- Atomic task resequencing that preserves unique positions throughout the update
- Atomic task deletion and contiguous resequencing of remaining tasks
- A `workflow_executions` table with workflow-name snapshots and run status
- A `workflow_task_executions` table with immutable task-name, task-ID, and
  sequence snapshots for each workflow run
- A `workflow_schedules` table with stable IDs, workflow and creator foreign keys,
  allowlisted schedule types, enabled state, creator references, and timestamps
- A `workflow_schedule_occurrences` ledger with schedule and workflow foreign
  keys, UTC occurrence times, and uniqueness per schedule occurrence
- An occurrence-history index for efficient workflow-scoped loading
- Ordered workflow-scoped schedule loading and exact-ID schedule lookup
- Atomic workflow lifecycle updates that disable enabled schedules when a
  workflow leaves Active

The Workflow Automation service layer provides:

- Explicit administrator-only `workflows.manage` authorization
- Live SQLite account revalidation before workflow creation
- Rejection of missing, deactivated, mismatched, or unauthorized accounts
- Normalization of workflow IDs, names, descriptions, and statuses
- Required workflow-ID and workflow-name validation
- Server-side workflow-status allowlisting
- Server-generated UTC creation and update timestamps
- Validated typed workflow records passed to the repository
- Administrator-only task creation with live account revalidation
- Normalized task IDs, workflow IDs, titles, instructions, and task types
- Strict sequence-number and required-flag validation
- Task-detail editing that preserves task IDs, parent workflows, and positions
- Complete-list validation before resequencing task positions
- Administrator-only task deletion with live account revalidation
- Protection against removing the final task from an active workflow
- Administrator-only active-workflow execution starts with live account checks
- Rejection of active workflows that do not contain at least one task
- Administrator-only task-execution completion and failure updates with live
  account revalidation, terminal-state protection, and parent-run scoping
- Administrator-only schedule creation and enable/disable controls with live
  account revalidation
- Manual, daily, and weekly schedule validation with strict `HH:MM` times and
  allowlisted weekdays
- Rejection of schedule creation for Draft, Inactive, or missing workflows
- Rejection of schedule enabling unless the parent workflow is Active
- Pure daily and weekly eligibility evaluated from an explicit timezone-aware
  current time
- `Asia/Shanghai` business-time interpretation with UTC occurrence storage
- A five-minute recovery window that avoids unlimited catch-up after downtime
- Read-only due loading restricted to enabled schedules on Active workflows
- Atomic occurrence claiming that rechecks lifecycle state and prevents
  duplicate claims across repeated scheduler checks

The protected workflow browser experience provides:

- A dedicated `workflows.view` permission for administrators and viewers
- A protected read-only workflow directory
- An administrator-only workflow creation form
- Protected workflow detail pages for administrators and viewers
- Administrator-only workflow editing for name, description, and status
- Ordered task display on protected workflow detail pages
- Administrator-only task creation form linked from workflow details
- Administrator-only task-detail editing and task-order forms
- Administrator-only task-deletion confirmation and POST action
- Administrator-only execution starts and controlled task outcome updates
- Task outcomes displayed beneath their parent workflow execution
- Stored schedules displayed on protected workflow detail pages
- Administrator-only schedule creation forms and enable/disable actions
- Written schedule state and timing descriptions for viewers and administrators
- Readable next-eligible-time display using the shared evaluator and
  browser-local timestamp formatting
- Deliberate contiguous task resequencing with duplicate and missing-task rejection
- Required/optional task labels, empty states, and instruction display
- Signed-session CSRF protection for workflow submissions
- Signed-session CSRF protection for task submissions
- Signed-session CSRF protection for task outcome submissions
- Signed-session CSRF protection for schedule creation and status changes
- Post/Redirect/Get navigation after successful creation
- Post/Redirect/Get navigation after successful updates
- Safe validation errors with submitted-value preservation
- Activity logging for denied access, invalid CSRF, and successful creation
- Activity logging for workflow updates
- Activity logging for denied task access, invalid CSRF, and successful task creation
- Activity logging for task edits and resequencing
- Activity logging for denied, invalid-CSRF, and successful task deletion
- Activity logging for denied, invalid-CSRF, and successful execution starts
- Activity logging for denied, invalid-CSRF, and successful task outcome updates
- Activity logging for denied, invalid-CSRF, successful schedule creation, and
  successful schedule status changes
- Default-deny `403` handling for missing permissions
- Safe SQLite loading-error pages without raw exception details
- Accessible workflow table headings, caption, and scrollable wrapper
- Accessible empty state when no workflow records exist
- Conditional Create workflow action visible only to administrators
- Accessible labels, status selector, error alert, and textarea focus styling
- Allowlisted workflow-directory filtering by status

### Completed Employee Management Capabilities

- Employee CRUD with SQLite-primary storage, synchronization, migration,
  verification, backups, restoration, and rollback-safe handling
- Payroll calculations, compensation summaries, workforce analytics, reports,
  filters, search, sorting, and CSV export
- Console authentication, default-deny role-based authorization, protected
  user-account management, activity logging, and password workflows
- Administrator and viewer roles with inactive-account protection
- Protected browser employee directory, profiles, payroll, creation, editing,
  and confirmed deletion
- Browser directory searching, filtering, and sorting
- Protected workforce reports and CSV downloads
- Administrator-only activity-log and user-account administration
- Accessible responsive layouts, semantic forms and tables, visible focus
  states, and safe empty and error states

### Web Security

The FastAPI interface continues to provide:

- Accessible browser login at `/login` and POST-only logout at `/logout`
- Signed eight-hour `abap_session` cookies with `HttpOnly` and `SameSite=Lax`
- Live configured-database account revalidation before protected access
- Default-deny permission enforcement
- Signed-session CSRF protection for state-changing browser workflows
- POST-only employee deletion and viewer-account mutations
- Server-side input validation and allowlisted values
- Repository-backed and service-backed configured-database operations
- SQLite and PostgreSQL foreign-key enforcement for relational integrity
- Safe missing-record, validation, and storage-failure responses
- Generic error messages for sensitive account-management failures
- Success-only activity logging for completed sensitive actions
- Password hashes excluded from browser account views
- Post/Redirect/Get navigation after successful changes

### Important Browser Routes

- `/` — protected shared ABAP dashboard
- `/agent-templates` — protected Agent Template directory for administrators
  and viewers
- `/agent-templates/new` — administrator-only Agent Template creation form
  and POST submission
- `/agent-templates/{agent_template_id}` — protected Agent Template detail page
  for administrators and viewers
- `/agent-templates/{agent_template_id}/edit` — administrator-only Agent Template
  edit form and POST submission
- `/agent-templates/{agent_template_id}/executions` — administrator-only Agent
  Execution history
- `/agent-templates/{agent_template_id}/executions/{agent_execution_id}` —
  administrator-only Agent Execution detail page
- `/workflows` — protected workflow directory
- `/workflows/new` — administrator-only workflow creation form and POST
  submission
- `/workflows/{workflow_id}` — protected workflow detail page
- `/workflows/{workflow_id}/edit` — administrator-only workflow edit form and
  POST submission
- `/workflows/{workflow_id}/tasks/new` — administrator-only task creation form
  and POST submission
- `/workflows/{workflow_id}/tasks/{task_id}/edit` — administrator-only task
  edit form and POST submission
- `/workflows/{workflow_id}/tasks/resequence` — administrator-only task-order
  form and POST submission
- `/workflows/{workflow_id}/tasks/{task_id}/delete` — administrator-only task
  deletion confirmation and POST submission
- `/workflows/{workflow_id}/executions` — administrator-only execution-start
  POST submission
- `/workflows/{workflow_id}/executions/{execution_id}/tasks/{task_execution_id}/finish`
  — administrator-only task completion or failure POST submission
- `/workflows/{workflow_id}/schedules/new` — administrator-only schedule form
  and creation submission
- `/workflows/{workflow_id}/schedules/{schedule_id}/status` —
  administrator-only schedule enable or disable POST submission
- `/employees` — protected employee directory
- `/employees/{employee_id}` — protected employee profile
- `/employees/{employee_id}/payroll` — protected payroll page
- `/employees/new` — administrator-only employee creation
- `/employees/{employee_id}/edit` — administrator-only employee editing
- `/employees/{employee_id}/delete` — administrator-only deletion
  confirmation and POST submission
- `/reports/workforce` — protected workforce report
- `/reports/employees.csv` — protected CSV download
- `/activity-log` — administrator-only activity log
- `/users` — administrator-only user-account directory
- `/users/new` — administrator-only viewer-account creation
- `/users/{username}/status` — administrator-only viewer activation or
  deactivation
- `/health` — JSON service-health check
- `/docs` — interactive API documentation

### Verification

- **566 automated tests passed**
- **50 dedicated agent-template authorization, schema, migration, repository,
  service, and browser lifecycle tests passed**
- **33 dedicated Agent Execution authorization, schema, migration, repository,
  service, and browser tests passed**
- **3 live PostgreSQL integration tests passed, including Agent Template browser
  plus Agent Execution service and protected browser round trips**
- Stored workflow schedules use typed models, constrained SQLite persistence,
  administrator-only service operations, live account revalidation, signed
  session CSRF protection, safe browser errors, and accessible display
- Schedule lifecycle controls disable schedules when a workflow leaves Active
  and reject enabling while it is Draft or Inactive
- Schedule eligibility covers manual, daily, weekly, disabled, expired, and
  invalid rules with deterministic clock inputs
- Duplicate-run preparation uses a persistent unique UTC occurrence and an
  atomic active/enabled state check
- The initial PostgreSQL migration defines all eight current application tables
- Migration validation rejects missing, empty, and incorrectly named SQL files
- Pending migrations are applied and recorded, while completed migrations are
  skipped
- SQLite remains the working local database and passed the complete regression
  suite
- PostgreSQL configuration rejects missing URLs, invalid backends, and
  unsupported URL formats
- PostgreSQL 18.6 migrations, schema constraints, repository round trips,
  timestamp normalization, and duplicate occurrence protection were verified
  against a live Docker container
- Live verification found and corrected Psycopg bulk insertion so the shared
  adapter now calls `executemany()` through a PostgreSQL cursor
- Real environment credentials remain excluded from Git
- No application data was changed during verification

### Current Development Focus

ABAP supports secure employee management, workflow lifecycle management,
ordered tasks, execution history, controlled task outcomes, stored scheduling
rules, timezone-aware eligibility, and duplicate-safe occurrence claims.

PostgreSQL production-database support now includes backend configuration,
connection selection, ordered schema migrations, migration history, and the
application repository paths used by employee management and workflow
automation. SQLite remains available for local development, backup and
restoration, and automated regression tests. The complete database path is now
verified against a live PostgreSQL 18.6 container.

The template-based AI-agent module now includes template creation, lifecycle
management, durable execution records, protected execution history, and
protected execution details. Active templates can run through a
provider-independent interface with administrator authorization, live account
revalidation, and safe Running-to-Completed-or-Failed persistence.

ABAP now also includes its first external AI-provider adapter. OpenAI
credentials are loaded from the environment, request timeouts are validated,
automatic SDK retries are disabled, Responses API storage is disabled, and
provider failures are translated into safe application errors. Deterministic
tests inject an in-memory client, so automated verification never sends a paid
provider request. The next slice can connect provider construction to a
protected Agent Template execution route while preserving the existing
authorization and safe persistence boundaries.
