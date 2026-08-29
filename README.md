# AI Business Automation Platform

A Python learning and portfolio project focused on building practical business automation software. The long-term goal is to develop an AI-powered platform that automates repetitive office processes.

## Current Module

### Employee Management System

The current console application can:

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
- Provide a tested self-service password-change foundation that
  allows active administrators and viewers to change their own
  passwords only after verifying the current password; blank input,
  password reuse, inactive sessions, deactivated saved accounts,
  missing accounts, and mismatched session identities are rejected,
  while successful changes preserve the user's role and active status
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

## Technologies

- Python
- Visual Studio Code
- Git
- GitHub
- SQLite

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
│       ├── tests/
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
│       ├── run_tests.py
│       ├── storage.py
│       ├── storage_verification.py
│       ├── user_account_setup.py
│       ├── user_service.py
│       └── validators.py
└── README.md
```

## Running the Application

From the main project folder, run:

```powershell
python Projects\employee_management_system\main.py
```

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
  preservation, and `subTest()` boundary coverage
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

## Project Roadmap

Future versions will introduce:

- Additional filtering and reporting options
- REST APIs
- Web interface
- AI document processing
- AI-generated business reports
- Workflow automation
- Deployment and production configuration

## Project Status

The Employee Management System is an actively developed console application. Core employee management, payroll, reporting, backup recovery, logging, filtering, sorting, workforce analytics, legacy validated JSON utilities, and 58 existing automated tests are complete. SQLite integration includes a tested schema, complete CRUD operations, complete-list synchronization, verified migration, read-only cross-storage verification, a configurable employee repository, SQLite-primary console workflows, and SQLite-only normal saving. SQLite backup and restoration are available through tested commands and interactive console options with confirmation protection, integrity checks, post-restoration session reloading, and activity logging. Authentication includes a typed user-account model, protected password storage, case-insensitive account retrieval, credential authentication, inactive-account enforcement, controlled `admin` and `viewer` roles, uniform authentication failure, and required interactive login before employee records are loaded or the menu is displayed. Role-based authorization uses named permission constants, role-to-permission sets, a menu-to-permission mapping, and default-deny protection. Administrators receive every explicitly mapped console permission, while viewers receive read-only employee, payroll, and report permissions. Active administrators can create fixed-role viewer accounts through protected console option 14, manage viewer activation through protected option 15, and reset viewer passwords through protected option 16. Exit is available through option 17. Account-status management rejects viewers, inactive administrators, missing accounts, administrator targets, and unchanged statuses. The administrator-controlled password-reset workflow uses hidden password entry and confirmation, required-input validation, generic failure messages, protected command and service layers, and success-only activity logging. It rejects viewers, inactive administrators, missing accounts, administrator targets, blank passwords, and reuse of the viewer's current password. Successful resets store only a newly protected password hash and preserve the viewer's role and active status. A tested self-service service foundation now allows active administrators and viewers to change their own passwords after proving knowledge of the current password. It reloads the live SQLite account, verifies both session and saved-account active status, matches the session user ID to the saved record, and rejects blank input, incorrect current passwords, password reuse, missing accounts, stale deactivated accounts, and mismatched session identities. Successful self-service changes store a newly protected hash while preserving the account's role and active status. A tested one-time administrator setup command counts existing accounts, rejects repeated setup, hides password entry with `getpass`, confirms matching passwords, validates required input, and reports success or failure through process exit codes. Thirty-five database tests, six administrator-setup command tests, one database-backup command test, two database-restoration command tests, three migration tests, thirty-five console-integration tests, six storage-verification tests, nine repository tests, five authentication tests, thirty-six user-service tests, four authorization-policy tests, and seven viewer-account command tests bring the complete suite to 207 automated tests. During manual verification of administrator-controlled reset, administrator Dennis reset `ReportViewer`'s password, the old password was rejected, the replacement password authenticated successfully, the account remained a viewer, and the viewer was denied access to the protected reset option. The successful reset, failed login, successful login, and denied permission were recorded in the activity log without exposing either password. SQLite remains the live source of truth, while legacy JSON utilities remain available for migration, verification, and historical compatibility. The next account-security milestone is to add the tested command-layer and interactive-console workflow for self-service password changes.