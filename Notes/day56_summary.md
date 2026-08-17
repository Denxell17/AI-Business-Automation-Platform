# Day 56 — Running and Verifying JSON-to-SQLite Migration

## Goal

Create, test, and run a controlled process that copies existing JSON employee records into SQLite and verifies the result.

## Business Purpose

The console application currently uses JSON storage. Before switching it to SQLite, the existing employee records must be copied safely.

The migration process must:

- Reject missing JSON files
- Reject invalid JSON data
- Copy valid employees into SQLite
- Avoid duplicate IDs
- Load SQLite records back
- Compare the copied records with the source records
- Report success or failure

## Migration Module

A new file was created:

```text
migration.py
```

Its main function is:

```python
migrate_json_file_to_database()
```

The function coordinates the complete migration process.

## File-Existence Check

```python
if not json_file.exists():
    print("The JSON employee file was not found.")
    return False
```

`exists()` checks whether the JSON file is present.

If it is missing, the function stops before creating or changing the database.

## Loading and Validation

```python
employees = load_employees(json_file)
```

`load_employees()` reads and validates the JSON data.

Possible results:

```text
Valid employee records → list[Employee]
Valid empty file       → []
Invalid or unreadable  → None
```

`None` does not mean an empty employee list. It means no safe result could be returned.

## Migrating Employees

```python
migrated_count = migrate_employees_to_database(
    employees,
    database_file,
)
```

This copies new employee IDs into SQLite and returns the number of newly inserted records.

The JSON file remains unchanged.

## Loading SQLite Records

```python
database_employees = load_employees_from_database(
    database_file,
)
```

The migrated records are read back from SQLite so they can be verified.

## Consistent Ordering

```python
expected_employees = sorted(
    employees,
    key=lambda employee: employee["employee_id"],
)
```

`sorted()` creates an ordered copy of the JSON list.

`key=lambda` tells `sorted()` to examine each employee’s `employee_id`.

This is necessary because the SQLite loader also returns records ordered by employee ID.

## Verification

```python
if database_employees != expected_employees:
    print("The JSON-to-SQLite migration verification failed.")
    return False
```

`!=` means “not equal.”

If any record is missing, changed, reordered incorrectly, or unexpectedly added, the two lists differ and verification fails.

If the lists match, the function prints the migrated and verified counts and returns `True`.

## Formatted Strings

```python
print(f"New employees migrated: {migrated_count}")
```

The `f` creates a formatted string literal.

The value inside `{}` is evaluated and inserted into the displayed text.

## Main Guard

```python
if __name__ == "__main__":
```

This runs the real migration only when `migration.py` is started directly.

When tests import the migration function, this block does not run. This prevents tests from accidentally modifying the real database.

## Failure Exit Code

```python
raise SystemExit(1)
```

This stops the program with exit code `1` when migration fails.

Common exit-code meaning:

```text
0 → success
1 → failure
```

## Migration Tests

Three tests were added:

1. Missing JSON returns `False`.
2. Valid JSON migrates successfully.
3. Invalid JSON stops before SQLite is created.

All tests use temporary files.

## Automated Test Result

```text
Ran 73 tests
OK
All automated tests passed.
```

## Real Migration Result

```text
JSON-to-SQLite migration completed successfully.
New employees migrated: 2
Total employees verified: 2
```

Two real employee records were copied and verified. The original JSON file remained unchanged.

## Key Concepts Practiced

- Controlled data migration
- Migration orchestration
- File-existence checks
- JSON validation
- SQLite verification
- Sorting with `key=lambda`
- List comparison
- F-strings
- Main guards
- Process exit codes
- Temporary integration testing

## Next Milestone

Day 57 will begin connecting the console application to SQLite while keeping JSON available during regression testing.