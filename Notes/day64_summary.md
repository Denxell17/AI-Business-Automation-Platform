# Day 64 Summary — Making SQLite the Primary Storage

## Goal

Safely change the Employee Management System from JSON-primary storage to SQLite-primary storage without losing employee records or breaking existing features.

## Starting Storage Flow

Before Day 64, the repository used this flow:

```text
JSON = primary storage
SQLite = synchronized secondary copy
```

The application loaded employees from JSON first. Successful saves were written to JSON and then synchronized to SQLite.

## Safety Check Before Switching

Before changing the configuration, the read-only storage verification was run:

```text
JSON and SQLite employee records match.
Total employees verified: 2
```

This proved that both storage locations contained the same employee information.

The console was also manually tested with JSON as primary storage. It successfully displayed:

- EMP004 — Aki
- EMP005 — Ruth

## Configuration Change

In `config.py`, this setting:

```python
PRIMARY_STORAGE = "json"
```

was changed to:

```python
PRIMARY_STORAGE = "sqlite"
```

`SUPPORTED_STORAGE_TYPES` remained unchanged:

```python
SUPPORTED_STORAGE_TYPES = {
    "json",
    "sqlite",
}
```

This means the repository still understands both storage types, but SQLite is now selected when no storage type is explicitly provided.

## New Storage Flow

The application now uses:

```text
SQLite = primary storage
JSON = synchronized secondary copy
```

During startup, `load_employee_records()` reads employee rows from SQLite.

After a successful registration, update, or deletion, `save_employee_records()` saves to SQLite first. It then synchronizes the same employee list to JSON.

JSON has not been deleted because it still provides a temporary secondary copy and is used by the current backup-restoration workflow.

## SQLite-Primary Console Verification

The console application was started after changing the configuration to SQLite.

Menu option 6 successfully displayed the same two employees:

- EMP004 — Aki
- EMP005 — Ruth

The program exited normally without errors.

A second read-only consistency check confirmed that JSON and SQLite still matched after the configuration change.

## New Regression Test

A new repository test was added:

```python
def test_configured_primary_load_uses_sqlite(self):
```

The test calls:

```python
load_employee_records(
    json_file=json_file,
    database_file=database_file,
)
```

It does not provide `"json"` or `"sqlite"` directly. This forces the function to use the configured `PRIMARY_STORAGE` default.

The test proves that:

- SQLite is selected by default
- Employee records are loaded from the temporary database
- A JSON file is not created during SQLite-primary loading

## Keyword Arguments

These are keyword arguments:

```python
json_file=json_file
database_file=database_file
```

The names on the left tell Python which function parameters should receive the values on the right.

They allow the test to provide the file paths while skipping the optional `storage_type` argument.

## Final Test Result

The complete suite passed:

```text
Ran 96 tests
OK
```

The total increased from 95 to 96 because one new configured-primary-storage test was added.

## Current Storage State

SQLite is now the configured primary storage.

JSON remains a synchronized secondary copy while the project still depends on JSON backup restoration. JSON should not be retired until SQLite has its own tested backup and restoration process.

## Next Step

Day 65 will begin implementing a safe SQLite database backup system.