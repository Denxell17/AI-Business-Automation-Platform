# Day 60 Summary — SQLite Backup-Restoration Synchronization

## Goal

Synchronize SQLite after employee data is successfully restored from a JSON backup.

## What Changed

Menu option 12 previously reloaded restored data using:

```python
restored_employees = load_employees()
```

It now uses:

```python
restored_employees = load_and_synchronize_employees()
```

The existing helper:

1. Loads the restored JSON file.
2. Validates the restored employee data.
3. Stops if loading returns `None`.
4. Synchronizes valid restored data to SQLite.
5. Returns the employee list to the running application.

## Reusing Existing Code

The startup helper was reused instead of creating another backup-specific synchronization function.

This keeps JSON loading, validation, SQLite synchronization, warning messages, and return rules in one place.

## Restore Flow

The completed restoration flow is:

1. The user selects menu option 12.
2. The user types `RESTORE`.
3. The JSON backup replaces the current JSON file.
4. The restored JSON data is loaded and validated.
5. SQLite is synchronized with the restored employee list.
6. The running application begins using the restored list.

SQLite is not synchronized when the backup restoration itself fails.

## Mocked Menu Test

A new test runs `run_program()` with mocked dependencies.

The test supplies these pretend keyboard answers:

```python
mock_input.side_effect = [
    "12",
    "RESTORE",
    "13",
]
```

`side_effect` returns the next value each time the mocked function is called.

The test:

- Selects backup restoration
- Confirms the operation
- Exits the program
- Prevents real file restoration
- Prevents real activity logging
- Confirms the load-and-synchronize helper runs twice

The two helper calls represent:

1. Normal application startup
2. Loading and synchronizing the restored backup

## Mock Terms Practiced

- `side_effect` supplies different mock results on consecutive calls.
-