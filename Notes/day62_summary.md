# Day 62 Summary — Configurable Employee Repository

## Goal

Prepare the Employee Management System to switch between JSON-primary and SQLite-primary storage without rewriting the console menu.

## Configuration Added

Two values were added to `config.py`:

```python
PRIMARY_STORAGE = "json"
SUPPORTED_STORAGE_TYPES = {
    "json",
    "sqlite",
}
```

`PRIMARY_STORAGE` selects the current primary storage.

`SUPPORTED_STORAGE_TYPES` lists the storage names the repository accepts.

JSON remains primary, so live console behavior did not change today.

## New Repository Module

A new file was created:

```text
Projects/employee_management_system/employee_repository.py
```

A repository hides storage details from the rest of the application.

Instead of deciding between JSON and SQLite inside menu code, the application will eventually call:

```python
load_employee_records()
save_employee_records()
```

## Repository Loading Rules

### JSON Primary

When `storage_type == "json"`:

1. JSON is loaded and validated.
2. Invalid JSON returns `None`.
3. Valid JSON is synchronized to SQLite.
4. SQLite failure displays a warning.
5. The valid JSON list is returned.

### SQLite Primary

When SQLite is selected:

1. The database file must already exist.
2. SQLite is loaded directly.
3. Missing or invalid SQLite returns `None`.
4. JSON is not required or created during loading.

## Repository Saving Rules

### JSON Primary

1. Save JSON first.
2. Return `False` if JSON fails.
3. Synchronize SQLite after JSON succeeds.
4. Warn if SQLite fails.
5. Return `True` because the selected primary storage succeeded.

### SQLite Primary

1. Save SQLite first.
2. Return `False` if SQLite fails.
3. Synchronize JSON after SQLite succeeds.
4. Warn if JSON fails.
5. Return `True` because the selected primary storage succeeded.

## Primary and Secondary Storage
