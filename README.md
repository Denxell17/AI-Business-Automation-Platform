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
- Provide a tested authentication foundation with SQLite user
  accounts, case-insensitive unique usernames, controlled
  account roles, active-status rules, salted password hashing,
  and secure password verification
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
│       └── validators.py
└── README.md
```

## Running the Application

From the main project folder, run:

```powershell
python Projects\employee_management_system\main.py
```

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
- User-account data modeling, case-insensitive unique usernames,
  controlled role and active-status constraints, PBKDF2-HMAC-SHA256
  password hashing, unique random salts, iteration work factors,
  hexadecimal encoding, secure hash comparison, and malformed-hash
  rejection
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
- User authentication and access control
- REST APIs
- Web interface
- AI document processing
- AI-generated business reports
- Workflow automation
- Deployment and production configuration

## Project Status

The Employee Management System is an actively developed console application. Core employee management, payroll, reporting, backup recovery, logging, filtering, sorting, workforce analytics, legacy validated JSON utilities, and 58 existing automated tests are complete. SQLite integration includes a tested schema, complete CRUD operations, complete-list synchronization, verified migration, read-only cross-storage verification, a configurable employee repository, SQLite-primary console workflows, and SQLite-only normal saving. SQLite backup and restoration are available through tested commands and interactive console options with confirmation protection, integrity checks, post-restoration session reloading, and activity logging. The authentication foundation now includes a typed user-account model, a tested SQLite `users` table, case-insensitive unique usernames, controlled `admin` and `viewer` roles, active-account defaults, salted PBKDF2-HMAC-SHA256 password hashing, secure password verification, and safe malformed-hash rejection. Twenty-five database tests, one database-backup command test, two database-restoration command tests, three migration tests, ten console-integration tests, six storage-verification tests, nine repository tests, and five authentication tests bring the complete suite to 119 automated tests. SQLite remains the live source of truth, while legacy JSON utilities remain available for migration, verification, and historical compatibility. Console login is not connected yet; the next authentication milestone is tested user-account creation and retrieval.