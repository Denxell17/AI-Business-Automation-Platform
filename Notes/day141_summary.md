# Day 141 Summary — PostgreSQL Schema and Migration Foundation

## Goal

Day 141 created the first complete PostgreSQL schema for the AI Business Automation Platform and added a safe migration runner. Day 140 prepared the application to select SQLite or PostgreSQL. Day 141 defines the actual PostgreSQL tables needed to store the current application data.

SQLite remains available for local development and automated tests. PostgreSQL is being prepared as the production database.

## PostgreSQL Schema

The initial PostgreSQL migration is stored in:

`Projects/employee_management_system/migrations/postgresql/001_initial_schema.sql`

The `001` prefix identifies this as the first migration. Future database changes can use ordered filenames such as `002_add_feature.sql`. This provides a clear history of schema changes and ensures migrations run in the correct order.

The migration creates eight application tables.

### Users

The `users` table stores application accounts.

It includes:

- An automatically generated numeric user ID.
- A username that cannot be empty.
- A password hash rather than a plain-text password.
- An `admin` or `viewer` role.
- An active-account flag.
- A case-insensitive unique username index.

The unique index prevents usernames such as `Dennis` and `dennis` from being stored as separate accounts.

### Employees

The `employees` table stores employee records.

It includes:

- Employee ID.
- Name.
- Department.
- Position.
- Country.
- Salary.
- Email address.
- Phone number.
- Years of experience.
- Company.
- Employment status.
- Performance score.

Database checks prevent empty employee IDs and names, non-positive salaries, negative experience values, and performance scores outside the accepted range of one through five.

### Workflows

The `workflows` table stores workflow definitions.

It includes:

- Workflow ID.
- Workflow name.
- Description.
- Status.
- The user who created the workflow.
- Creation and update timestamps.

The status must be `draft`, `active`, or `inactive`. The creator field references a valid user account.

### Workflow Tasks

The `workflow_tasks` table stores the ordered steps belonging to a workflow.

It includes:

- Task ID.
- Parent workflow ID.
- Sequence number.
- Task title.
- Instructions.
- Task type.
- Required-task flag.
- Creation and update timestamps.

A workflow cannot contain two tasks with the same sequence number. Each task must also reference an existing workflow.

### Workflow Schedules

The `workflow_schedules` table stores manual, daily, and weekly scheduling rules.

It includes:

- Schedule ID.
- Parent workflow ID.
- Schedule type.
- Scheduled time.
- Optional day of the week.
- Enabled status.
- The user who created the schedule.
- Creation and update timestamps.

Database checks enforce the correct field combination for each schedule type:

- Manual schedules cannot contain a scheduled time or weekday.
- Daily schedules require a valid time and no weekday.
- Weekly schedules require both a valid time and a weekday.

### Workflow Schedule Occurrences

The `workflow_schedule_occurrences` table records scheduled workflow occurrences that have already been claimed.

It includes:

- Occurrence ID.
- Schedule ID.
- Workflow ID.
- Scheduled UTC time.
- Claim timestamp.

The combination of schedule ID and scheduled UTC time is unique. This protects the application from creating the same scheduled occurrence more than once.

### Workflow Executions

The `workflow_executions` table records each workflow run.

It includes:

- Execution ID.
- Workflow ID.
- Manual or scheduled trigger type.
- Optional schedule-occurrence reference.
- Optional user who started the execution.
- Execution status.
- Start and finish timestamps.
- Failure message.

Database checks keep trigger information consistent. A manual execution requires a user and cannot reference a schedule occurrence. A scheduled execution requires a schedule occurrence.

Execution status is limited to `running`, `completed`, or `failed`. A running execution cannot have a finish time, while completed and failed executions require one.

### Workflow Task Executions

The `workflow_task_executions` table records the result of every task within a workflow execution.

It includes:

- Task-execution ID.
- Parent execution ID.
- Task ID.
- Sequence number.
- Task title.
- Task status.
- Start and finish timestamps.
- Result message.

Status and timestamp checks keep running, completed, and failed task records internally consistent. Day 142 added a follow-up migration that ensures each task can appear only once within an execution.

## PostgreSQL Migration Runner

The migration runner is stored in:

`Projects/employee_management_system/postgresql_migrations.py`

Its responsibilities are:

1. Locate the PostgreSQL migration directory.
2. Find SQL migration files.
3. Validate the required `001_description.sql` filename format.
4. Reject missing, empty, or incorrectly named migration files.
5. Sort migrations by filename so they run in order.
6. Connect to PostgreSQL through `psycopg`.
7. Create a `schema_migrations` history table.
8. Read the names of migrations that were already applied.
9. Execute only pending migrations.
10. Record each completed migration in the history table.

Running migrations inside the PostgreSQL connection context gives the operation transaction protection. If a migration fails, PostgreSQL can roll back the transaction instead of leaving a partially applied schema.

The migration runner also makes repeated startup or deployment checks safe because already completed migrations are skipped.

## Migration Tests

The migration tests are stored in:

`Projects/employee_management_system/tests/test_postgresql_migrations.py`

Seven test methods verify that:

- The initial migration file is discovered.
- All eight required application tables are present.
- A missing migrations directory is rejected.
- An empty migrations directory is rejected.
- An invalid migration filename is rejected.
- An empty PostgreSQL database URL is rejected.
- A pending migration is applied and recorded.
- An already applied migration is skipped.

The PostgreSQL connection is mocked in the unit tests. This allows the migration logic to be tested without requiring a running PostgreSQL server during Day 141.

## Verification

The focused PostgreSQL migration tests passed:

- 7 migration tests passed.

The complete application test suite also passed:

- 471 tests passed in 54.241 seconds.
- No existing test failed.

The SQL migration has not yet been executed against a real PostgreSQL server. That integration verification will happen when the PostgreSQL service is available through the planned Docker environment.

The initial employee performance-score constraint used a `1` to `5` range. Day 142 added a follow-up migration that corrects it to the application's established `0` to `100` range.

## Result

Day 141 completed the PostgreSQL schema and migration-management foundation.

The application now has:

- A production-oriented PostgreSQL schema.
- Database constraints that protect important business rules.
- Foreign keys connecting related records.
- Indexes for common workflow queries.
- UTC-aware PostgreSQL timestamp fields.
- Ordered and repeatable SQL migrations.
- A migration-history table.
- Automated migration tests.

## Next Step

Day 142 will connect the existing application repositories and workflow execution services to the configured database backend. It will focus on making the PostgreSQL path usable while preserving SQLite for local development and tests.
