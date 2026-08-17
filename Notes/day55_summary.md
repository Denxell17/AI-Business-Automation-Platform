# Day 55 — Preparing JSON Employee Migration to SQLite

## Goal

Create and test a function that copies a list of employee records into SQLite without creating duplicate employee IDs.

## Business Purpose

The application currently uses JSON as its active storage. Before switching to SQLite, existing employee records must be copied safely.

The migration helper accepts employees already loaded and validated from JSON, then inserts them into SQLite.

Today’s work prepared and tested the migration process. It did not modify the real JSON file or real SQLite database.

## Migration Function

The new function is:

```python
migrate_employees_to_database()
```

It:

- Accepts a list of employee dictionaries
- Ensures the SQLite employee table exists
- Processes employees one at a time
- Inserts employees that do not already exist
- Skips duplicate employee IDs
- Counts newly inserted records
- Returns the final count

## Function Type Hints

```python
employee_list: list[Employee]
```

This means the function expects a list containing employee dictionaries.

```python
-> int
```

This means the function returns a whole number.

The returned integer is not merely any number. It specifically represents how many employees were newly migrated.

## Database Initialization

```python
initialize_database(database_file)
```

This ensures that the `employees` table exists before migration begins.

Because the table uses:

```sql
CREATE TABLE IF NOT EXISTS employees
```

SQLite creates the table only when it is missing. An existing table is left unchanged.

## Migration Counter

```python
migrated_count = 0
```

The counter begins at zero because no employee has been migrated yet.

## Migration Loop

```python
for employee in employee_list:
```

- `for` is a Python keyword that repeats work.
- `employee` represents the current employee.
- `in` takes items from a collection.
- `employee_list` is the collection being processed.

The loop handles one employee at a time.

## Successful-Insertion Condition

```python
if insert_employee(employee, database_file):
```

- `if` is a Python keyword that checks a condition.
- `insert_employee()` returns `True` when a new employee is saved.
- It returns `False` when the employee ID already exists.
- The indented block runs only when the result is `True`.

## Increasing the Count

```python
migrated_count += 1
```

This is short for:

```python
migrated_count = migrated_count + 1
```

The counter increases only after a successful new insertion.

## Returning the Result

```python
return migrated_count
```

`return` sends the final result back to the caller.

Examples:

```text
Empty list → 0
Two new employees → 2
One existing ID and one new ID → 1
All IDs already exist → 0
```

## Duplicate-Safe Migration

Running the migration repeatedly does not create additional records with the same employee IDs.

Example:

```text
First migration of EMP001 → returns 1
Second migration of EMP001 → returns 0
Database still contains one EMP001 record
```

This repeat-safe behavior is called idempotent migration.

`idempotent` is a programming term. It means repeating the same operation does not keep changing the result after the first successful run.

## Automated Tests

Three migration tests were added:

1. An empty list returns zero and creates an empty database.
2. Multiple employee records are migrated correctly.
3. Existing employee IDs are skipped during repeated migration.

The tests use temporary databases, so the real `employees.json` and `employees.db` files remain unchanged.

## Test Result

```text
Ran 70 tests
OK
All automated tests passed.
```

## Key Concepts Practiced

- Data migration
- Migration helper functions
- Lists of typed dictionaries
- `for` loops
- `if` conditions
- Counters
- `+=`
- Integer return values
- Duplicate prevention
- Idempotent operations
- Temporary database testing

## Next Milestone

Day 56 will create a controlled one-time process that loads the real validated JSON employee records, copies them into SQLite, and verifies the result before the console application switches storage systems.