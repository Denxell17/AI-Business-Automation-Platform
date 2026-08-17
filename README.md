# AI Business Automation Platform

A Python learning and portfolio project focused on building practical business automation software. The long-term goal is to develop an AI-powered platform that automates repetitive office processes.

## Current Module

### Employee Management System

The current console application can:

- Register, view, update, and delete employee records
- Store multiple employees in JSON
- Initialize a tested SQLite employee database schema,
  perform complete CRUD operations, and safely migrate
  and verify existing JSON employee records
- Validate loaded employee records and business rules
- Save employee data atomically using temporary files
- Create and restore employee-data backups
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
- Refactoring large functions into focused helper functions
- Type hints and `TypedDict`
- JSON storage and runtime data validation
- SQLite CRUD operations, duplicate-safe migrations,
  JSON-to-SQLite verification, file-existence checks,
  main guards, and process exit codes
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
- Connect the console application to SQLite
  and retire JSON storage after regression testing
- User authentication and access control
- REST APIs
- Web interface
- AI document processing
- AI-generated business reports
- Workflow automation
- Deployment and production configuration

## Project Status

The Employee Management System is an actively developed console application. Core employee management, validated JSON storage, payroll, reporting, backup recovery, logging, filtering, sorting, workforce analytics, and 58 existing automated tests are complete. SQLite integration now includes a tested schema, complete CRUD operations, and a verified JSON-to-SQLite migration process. Twelve database tests and three migration tests bring the complete suite to 73 automated tests. Two existing employee records were successfully migrated and verified in SQLite. The next milestone is connecting the console application to SQLite.