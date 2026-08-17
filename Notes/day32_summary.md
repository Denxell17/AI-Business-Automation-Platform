# Day 32 — Restoring Employee Data from Backup

## Learning Objective

Add a safe, validated, and user-confirmed process for restoring employee data from the most recent backup.

## Restoration Function

The storage module now includes:

```python
def restore_employees_from_backup(
    file_path: Path = DATA_FILE,
) -> bool:
    backup_file = get_backup_file_path(file_path)

    if not backup_file.exists():
        print("No employee backup file found.")
        return False

    backup_employees = load_employees(backup_file)

    if backup_employees is None:
        print("The employee backup could not be restored.")
        return False

    return save_employees(
        backup_employees,
        file_path,
    )
```

The function returns:

```python
True
```

when restoration succeeds, and:

```python
False
```

when restoration cannot be completed safely.

## Missing Backup Protection

Before restoration, the function checks:

```python
if not backup_file.exists():
```

If the backup does not exist:

- A clear message is displayed.
- No current file is created or changed.
- The function returns `False`.

## Backup Validation

The backup is loaded using:

```python
backup_employees = load_employees(backup_file)
```

This validates:

- JSON syntax
- Top-level list structure
- Required employee fields
- Employee value types

The backup is not trusted merely because it exists.

## Invalid Backup Protection

If the backup contains invalid JSON or an invalid employee structure:

- Restoration stops.
- An explanation is displayed.
- The function returns `False`.
- The current employee file remains unchanged.

## Reusing Safe Saving

Restoration calls:

```python
save_employees(
    backup_employees,
    file_path,
)
```

This reuses:

- Temporary-file writing
- Atomic replacement
- Current-version backup
- Filesystem error handling
- JSON serialization error handling
- Temporary-file cleanup

The restoration process does not duplicate storage safety logic.

## Version Swapping

Before restoration:

```text
employees.json      Current version
employees.json.bak  Previous version
```

During restoration:

1. Backup data is loaded and validated.
2. The current file is copied into `.bak`.
3. The loaded backup data becomes the current file.

After restoration:

```text
employees.json      Previously backed-up version
employees.json.bak  Version that was current before restoration
```

This creates a safe swap between the current and most recent backup versions.

## Application Menu Integration

The menu now includes:

```text
8. Restore Employee Backup
9. Exit
```

Restoration requires confirmation:

```text
Type RESTORE to continue:
```

The confirmation is normalized with:

```python
.strip().upper()
```

Therefore, inputs such as these are accepted:

```text
RESTORE
restore
 Restore
```

Any other input cancels restoration without changing data.

## Reloading Application Data

After a successful restoration:

```python
restored_employees = load_employees()
employees = restored_employees
```

This ensures the in-memory list matches the restored file immediately. Restarting the application is not required.

## Clearing a Stale Employee Reference

After restoration:

```python
employee = None
```

A previously selected employee may not exist in the restored version. Resetting the reference prevents later features from using outdated employee data.

## Activity Logging

Successful restoration records:

```text
Employee data restored from backup.
```

in `activity.log`.

This provides an audit trail for an important data-recovery action.

## Testing Completed

Storage tests confirmed:

- Missing backup returns `False`.
- Missing backup does not create or modify the current file.
- Valid backup replaces current data.
- Previous current data becomes the new backup.
- Invalid backup JSON is rejected.
- Invalid backup does not modify current data.

The application tests confirmed:

- Restoration cancellation preserves current data.
- A successful restoration recovered `DAY31`.
- The employee list reloaded immediately.
- A second restoration returned to the two-employee version.
- Lowercase confirmation was accepted.

The complete test suite passed:

```text
Ran 40 tests
OK

All automated tests passed.
```

## Key Lesson

Backup recovery must validate the backup, protect the current version, require clear user confirmation, and synchronize the application’s in-memory state with the restored file.