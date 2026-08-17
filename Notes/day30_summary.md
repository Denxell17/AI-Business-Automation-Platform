# Day 30 — Atomic JSON Saving

## Learning Objective

Protect existing employee data from incomplete or failed JSON writes by saving through a temporary file.

## Risk of Direct Writing

Opening the real data file with `"w"` immediately clears its existing contents:

```python
with open(file_path, "w", encoding="utf-8") as file:
    json.dump(employee_list, file, indent=4)
```

If writing is interrupted by a shutdown, storage failure, or application error, the real file may be left empty or incomplete.

## Atomic Save Process

The safer process is:

```text
Employee data
      ↓
Write to employees.json.tmp
      ↓
Writing completes successfully
      ↓
Replace employees.json
```

The existing employee file remains untouched until the new JSON has been completely written.

## Temporary-File Path

The helper function creates a temporary filename in the same directory:

```python
def get_temporary_file_path(
    file_path: Path,
) -> Path:
    return file_path.with_name(
        f"{file_path.name}.tmp"
    )
```

Example:

```text
employees.json → employees.json.tmp
```

Keeping both files in the same directory makes replacement safer and more reliable.

## Writing and Replacing

`save_employees()` writes to the temporary path:

```python
with open(
    temporary_file,
    "w",
    encoding="utf-8",
) as file:
    json.dump(employee_list, file, indent=4)
```

Only after writing succeeds does the temporary file replace the real file:

```python
temporary_file.replace(file_path)
```

After replacement:

- The new data is stored as `employees.json`.
- The old file is replaced.
- `employees.json.tmp` no longer exists.

## Handling Save Failures

The save function catches:

```python
except (OSError, TypeError) as error:
```

`OSError` covers filesystem problems, such as:

- Permission errors
- Storage errors
- Invalid file paths
- File replacement failures

`TypeError` covers values that JSON cannot serialize, such as:

```python
{1, 2, 3}
```

A Python set is not supported by JSON.

When saving fails, the function returns:

```python
False
```

## Temporary-File Cleanup

The `finally` block runs after both successful and failed save attempts:

```python
finally:
    if temporary_file.exists():
        try:
            temporary_file.unlink()
        except OSError:
            pass
```

`unlink()` deletes the temporary file.

After a successful replacement, the temporary file already no longer exists. After a failed write, cleanup removes any incomplete temporary file that remains.

## Why Cleanup Errors Are Ignored

Cleanup occurs after the original save attempt.

If deleting the temporary file also fails, that cleanup problem should not hide or replace the original saving error. Therefore, the cleanup `OSError` is safely ignored.

## Testing Completed

The storage tests confirmed:

- Valid employee data saves and loads successfully.
- Successful saves leave no `.tmp` file.
- Invalid JSON is rejected.
- Invalid employee structures are rejected.
- Failed JSON serialization returns `False`.
- Failed saves preserve the existing real file.
- Incomplete temporary files are removed.

The complete automated test suite passed:

```text
Ran 35 tests
OK

All automated tests passed.
```

The real application successfully:

- Registered temporary employee `DAY30`.
- Saved the updated collection atomically.
- Deleted `DAY30`.
- Saved the updated collection again.
- Left no `employees.json.tmp` file behind.

## Key Lesson

Safe storage should never destroy valid existing data before replacement data has been written successfully.