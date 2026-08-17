# Day 31 — Backup Files and Data Recovery

## Learning Objective

Preserve the previous version of employee data before replacing the current JSON file.

## Why Backups Are Needed

Atomic writes protect the current file when writing fails. However, a successful save may still contain an unwanted business change, such as:

- Accidental employee deletion
- Incorrect employee updates
- Unwanted bulk changes
- Valid but incorrect data

A backup preserves the version that existed immediately before the latest successful save.

## File Roles

The storage system now uses three file types:

```text
employees.json      Current employee data
employees.json.tmp  New data being written
employees.json.bak  Previous employee data
```

### Temporary File

`.tmp` means temporary.

It holds the new data while JSON writing is in progress. After writing succeeds, it replaces the current file.

### Backup File

`.bak` means backup.

It holds the previous version of the current file before that file is replaced.

## Backup Path Helper

```python
def get_backup_file_path(
    file_path: Path,
) -> Path:
    return file_path.with_name(
        f"{file_path.name}.bak"
    )
```

Example:

```text
employees.json → employees.json.bak
```

## Copying the Existing File

Python’s `copy2()` function is imported from `shutil`:

```python
from shutil import copy2
```

Before replacing the current file, storage checks whether it exists:

```python
if file_path.exists():
    copy2(file_path, backup_file)
```

`copy2()` copies the existing file contents to the backup path and attempts to preserve filesystem metadata.

## Why File Existence Is Checked

During the first-ever save:

```text
employees.json does not exist
```

There is no previous version to preserve, so no backup is created.

During later saves:

```text
employees.json exists
```

The existing version is copied to `employees.json.bak` before replacement.

## Complete Save Sequence

```text
1. Write new data to employees.json.tmp
2. Confirm temporary writing succeeds
3. Copy current employees.json to employees.json.bak
4. Replace employees.json using employees.json.tmp
5. Remove any leftover temporary file
```

This provides two forms of protection:

- Atomic saving protects against incomplete writes.
- Backups protect against unwanted successful changes.

## Most Recent Backup Only

The current system uses one fixed backup path:

```text
employees.json.bak
```

Each later save replaces that backup with the newest previous version.

Therefore, it keeps:

```text
Current version
Most recent previous version
```

It does not keep every historical version.

## Practical Test

A temporary employee named `DAY31` was registered.

After registration:

```text
employees.json      Contained DAY31
employees.json.bak  Contained the version before DAY31
```

After deleting `DAY31`:

```text
employees.json      Did not contain DAY31
employees.json.bak  Still contained DAY31
```

This confirmed that the backup preserved the version from immediately before deletion.

## Backup Privacy

Backup files contain the same employee information as the main data file, including potentially:

- Names
- Salaries
- Email addresses
- Phone numbers
- Employment information

The following rule was added to `.gitignore`:

```gitignore
# Local backup files
*.bak
```

This prevents backup files from being accidentally committed to Git.

## Testing Completed

Tests confirmed:

- The first save does not create a backup.
- A save over an existing file creates a backup.
- The backup contains the previous file contents.
- The current file contains the new data.
- Atomic-save protection still works.
- Failed saves preserve the existing file.

The complete test suite passed:

```text
Ran 37 tests
OK

All automated tests passed.
```

## Key Lesson

A temporary file protects the writing process, while a backup file protects the previous successful version of business data.