# Day 65 Summary — SQLite Database Backups

## Goal

Create a safe backup of the primary SQLite employee database using SQLite’s native backup operation.

## Backup Files

The primary database is:

```text
data/employees.db
```

The new backup database is:

```text
data/employees_backup.db
```

The standard backup path was added to `database.py`:

```python
DATABASE_BACKUP_FILE = (
    DATA_DIRECTORY / "employees_backup.db"
)
```

## Backup Function

The following function was added to `database.py`:

```python
backup_database()
```

It accepts two paths:

- `database_file` — the original SQLite database
- `backup_file` — the destination backup database

Both parameters have project defaults, while automated tests can provide temporary paths.

## Missing-Database Protection

The function first checks:

```python
if not database_file.exists():
```

This is important because `sqlite3.connect()` normally creates a new empty database when a file does not exist.

Checking first prevents a missing original database from being mistaken for a valid empty database.

## Parent Folder Creation

The backup function uses:

```python
backup_file.parent.mkdir(
    parents=True,
    exist_ok=True,
)
```

`.parent` means the folder containing the backup file.

`mkdir()` creates the folder, `parents=True` allows missing folders above it to be created, and `exist_ok=True` allows the folder to already exist.

## SQLite Backup Operation

Two database connections are opened:

```python
source_connection
backup_connection
```

The source connection reads the original database. The backup connection receives the copied schema and records.

SQLite performs the copy with:

```python
source_connection.backup(backup_connection)
```

Using SQLite’s backup method is safer than treating an active database like an ordinary text file.

## Error Handling and Cleanup

The function catches:

```python
sqlite3.Error
OSError
```

`sqlite3.Error` represents database problems. `OSError` represents file-system problems, such as an inaccessible folder.

A `finally` block closes both connections whether the operation succeeds or fails.

The connections begin as `None`, and `is not None` checks prevent the program from closing a connection that was never opened.

## Backup Replacement

The backup function can use an existing backup path again.

A test first backed up an employee named `"Dennis"`, updated the primary database to contain `"Dennis Updated"`, and ran the backup again.

Reading the backup returned the updated employee, proving that a new backup refreshes the previous backup contents.

## Backup Command

A new command file was created:

```text
database_backup.py
```

Its supervisor function is:

```python
run_database_backup()
```

It calls `backup_database()`, prints a success or failure message, and uses exit code `1` when the command fails.

The real backup was created with:

```powershell
python Projects\employee_management_system\database_backup.py
```

The command completed successfully and created `employees_backup.db`.

## Automated Tests

Three database-backup tests verify:

- A missing source database returns `False`
- A successful backup contains the complete employee records
- A new backup refreshes an existing backup

One command test uses `patch()` to verify that `run_database_backup()` calls `backup_database()` exactly once without touching the real database.

## Final Test Result

The complete suite passed:

```text
Ran 100 tests
OK
```

This is the project’s first 100-test milestone.

## Current Storage State

SQLite is the primary employee storage.

JSON remains a synchronized secondary copy and the current restoration source. SQLite backup creation is complete, but SQLite restoration must be implemented and tested before JSON can be retired.

## Next Step

Day 66 will implement safe restoration of `employees.db` from `employees_backup.db`.