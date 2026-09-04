# Day 102 Summary — Workflow Automation Foundation

## Goal

Begin the Workflow Automation module by defining its domain model and creating
the first secure SQLite foundation for workflow records.

## Completed

- Created the Workflow Automation domain-design document.
- Defined the relationship among workflows, workflow tasks, schedules,
  workflow executions, and task executions.
- Defined the first Workflow Automation release scope.
- Added the `workflows` SQLite table.
- Added a typed Python `Workflow` record definition.
- Added workflow lifecycle constants:
  - `draft`
  - `active`
  - `inactive`
- Added SQLite constraints for workflow names and statuses.
- Added a foreign-key relationship from each workflow to its creator account.
- Enabled foreign-key enforcement for every SQLite connection.
- Added repository functions to save and load workflow records.
- Added automated tests for workflow schema, constraints, insertion,
  duplicate-ID rejection, loading, and empty states.

## Files Changed

- `Notes/workflow_automation_design.md`
- `Projects/employee_management_system/models.py`
- `Projects/employee_management_system/database.py`
- `Projects/employee_management_system/tests/test_database.py`
- `Notes/day102_summary.md`

## Domain Decisions

A workflow is a reusable business-process definition.

The first release will eventually support workflows, ordered manual tasks,
stored schedules, manual executions, and execution history. It will not yet
perform automatic background execution, AI-agent work, email delivery, or
external API calls.

The initial workflow record contains:

- `workflow_id`
- `name`
- `description`
- `status`
- `created_by_user_id`
- `created_at`
- `updated_at`

A workflow may be `draft`, `active`, or `inactive`.

A draft workflow may have no tasks. A workflow must later have at least one
task before service-layer rules permit activation. Inactive workflows must not
be scheduled or started.

## Database and Security Decisions

The `workflows` table includes these protections:

- A stable public workflow ID as the primary key
- Required, non-blank workflow names
- Allowlisted workflow statuses
- A required creator account ID
- A foreign-key relationship to the existing `users` table
- Required creation and update timestamps

SQLite foreign-key enforcement is now enabled in
`get_database_connection()`.

This is important because SQLite does not enforce declared foreign keys unless
each connection explicitly enables them. ABAP now rejects a workflow that
claims to belong to a nonexistent user account.

The `insert_workflow()` repository function:

- Initializes the schema when needed
- Uses parameterized SQL values
- Commits only a successful insert
- Rolls back and returns `False` for integrity failures
- Always closes its database connection

The `load_workflows_from_database()` repository function:

- Returns an empty list safely when no workflows exist
- Returns complete typed workflow records
- Uses deterministic ordering by creation timestamp and workflow ID
- Always closes its database connection

## Tests

New Workflow Automation foundation coverage verifies:

- The `workflows` table is created with the planned columns
- Invalid workflow statuses are rejected
- Whitespace-only workflow names are rejected
- Missing creator accounts are rejected through foreign-key enforcement
- A valid workflow can be saved
- Duplicate workflow IDs are rejected safely
- Saved workflows can be loaded
- An empty database returns an empty workflow list

Verification completed successfully:

- **45 database tests passed**
- **356 total automated tests passed**
- No test failures or errors remained

## Concepts Practiced

- Domain-driven feature planning
- TypedDict record definitions
- Lifecycle-state constants
- SQLite table constraints
- Primary keys and foreign keys
- Connection-level SQLite foreign-key enforcement
- Repository pattern
- Parameterized SQL inserts
- Transaction rollback after integrity failures
- Test-first database development
- Empty-state handling
- Deterministic record ordering
- Full regression testing after shared database changes

## Current ABAP Status

Day 102 is complete.

Phase 2 now has a documented Workflow Automation design and a tested workflow
persistence foundation. The dashboard continues to list Workflow Automation as
planned because browser routes and user-facing workflow management are not yet
available.

## Next Step

Day 103 should add service-layer workflow validation and safe workflow
creation rules.

The next implementation should validate required names, normalize submitted
values, assign timestamps, restrict statuses to the defined allowlist, and
prevent inactive or invalid workflow records before they reach SQLite.

## Quiz — Questions and Answers

1. What is the difference between a workflow and a workflow execution?

   A workflow is the reusable definition of a business process. A workflow
   execution is one historical attempt to run that definition.

2. Why does ABAP store `created_by_user_id` on a workflow?

   It records who created the workflow and provides audit context for later
   authorization and activity-history features.

3. Why is `workflow_id` a primary key?

   A primary key makes each workflow uniquely identifiable and prevents two
   workflows from using the same public ID.

4. What does the database `CHECK` constraint protect?

   It rejects invalid workflow data, such as blank names or unknown status
   values, even when a request bypasses future browser-form validation.

5. Why is `PRAGMA foreign_keys = ON` necessary in SQLite?

   SQLite disables foreign-key enforcement by default. This setting activates
   the workflow-to-user relationship for every database connection.

6. Why does `insert_workflow()` return `False` for an integrity failure?

   It gives the calling service a safe, predictable result after rolling back,
   rather than leaving a partial database change.

7. Why does `load_workflows_from_database()` return an empty list?

   A new ABAP installation may not have workflows yet. An empty list is a
   normal safe state, not an application error.

8. Why is the Workflow Automation dashboard card still marked Planned?

   The database foundation exists, but protected service and browser workflows
   have not been built yet, so users cannot manage workflows through the
   application interface.