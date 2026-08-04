# Day 15 Summary — JSON Error Handling and Data Protection

## Day 15 Goal

The goal of Day 15 was to make the Employee Management System safer and more honest when file operations fail.

The application can now:

- Detect invalid JSON
- Handle file-reading errors
- Stop safely when employee data cannot be loaded
- Report whether saving succeeded
- Avoid falsely claiming that changes were saved
- Avoid saving when an update contains no changes

## Why Error Handling Matters

Without error handling:

```text
File problem
→ Python exception
→ application crashes
```

A more professional application follows:

```text
File problem
→ catch exception
→ display understandable message
→ protect existing data
→ stop or continue safely
```

## Valid JSON and Invalid JSON

Valid JSON follows the required structure:

```json
[
    {
        "employee_id": "EMP005",
        "name": "Ruth"
    }
]
```

Invalid JSON might contain ordinary text:

```text
This is not valid JSON
```

It can also be incomplete:

```json
[
    {
        "employee_id": "EMP005"
```

## `json.JSONDecodeError`

This exception occurs when:

- The file exists
- Python can open it
- The contents cannot be interpreted as valid JSON

It does not mean the file is missing.

A missing file is detected separately:

```python
if not DATA_FILE.exists():
    return []
```

## Protected Loading

The loading function now uses `try` and `except`:

```python
def load_employees():
    if not DATA_FILE.exists():
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except json.JSONDecodeError:
        print()
        print("ERROR: The employee data file contains invalid JSON.")
        print("The application will stop to protect your data.")
        return None

    except OSError as error:
        print()
        print("ERROR: The employee data file could not be read.")
        print(f"Details: {error}")
        return None
```

## Understanding `try` and `except`

The `try` block contains an operation that might fail:

```python
try:
    return json.load(file)
```

An `except` block handles a specific failure:

```python
except json.JSONDecodeError:
```

This prevents Python from displaying an uncontrolled traceback and terminating unexpectedly.

## Difference Between `[]` and `None`

The loading function returns:

```python
[]
```

when the file is missing.

This means:

> There is no saved employee file yet, so begin with zero employees.

Starting with an empty list is safe.

The function returns:

```python
None
```

when the file exists but cannot be loaded safely.

This means:

> Something went wrong. Do not treat this as an empty employee database.

If damaged JSON were treated as an empty list, the application might save over the damaged file and destroy recoverable employee information.

## Safe Startup

Inside `run_program()`:

```python
employees = load_employees()

if employees is None:
    print("Employee Management System could not start safely.")
    return
```

If loading fails, `return` stops `run_program()` before the menu appears.

This protects the data file from accidental overwriting.

## Invalid-JSON Test

A separate disposable file was created:

```text
employees_invalid_test.json
```

It contained:

```text
This is not valid JSON
```

The application correctly displayed:

```text
ERROR: The employee data file contains invalid JSON.
The application will stop to protect your data.
Employee Management System could not start safely.
```

The real `employees.json` file was not modified during the test.

## `OSError`

`OSError` represents operating-system and filesystem problems, including:

- Permission denied
- Storage unavailable
- Read failure
- Write failure
- Invalid file location
- Device or disk problem

The exception is stored in:

```python
error
```

Technical details can be displayed with:

```python
print(f"Details: {error}")
```

## Protected Saving

The save function now reports success or failure:

```python
def save_employees(employee_list):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(employee_list, file, indent=4)

        return True

    except OSError as error:
        print()
        print("ERROR: Employee records could not be saved.")
        print(f"Details: {error}")
        return False
```

## Boolean Save Results

The function returns:

```python
True
```

when saving succeeds.

It returns:

```python
False
```

when saving fails.

This is a success flag that allows the calling code to display an accurate message.

## Registration Save Check

After registration:

```python
records_saved = save_employees(employees)

if records_saved:
    print("Employee successfully registered and saved.")
else:
    print(
        "WARNING: Employee was added to the current session "
        "but was not saved to the data file."
    )
```

A failed save means the employee remains in temporary memory during the current run but will disappear after restarting.

## Update Save Check

After a successful update:

```python
records_saved = save_employees(employees)

if records_saved:
    print("Employee changes saved.")
else:
    print(
        "WARNING: Changes exist in the current session "
        "but were not saved to the data file."
    )
```

The application no longer falsely reports that a failed write succeeded.

## Deletion Save Check

After deletion:

```python
records_saved = save_employees(employees)

if records_saved:
    print("Updated employee records saved.")
else:
    print(
        "WARNING: The employee was removed from the "
        "current session, but the deletion was not saved."
    )
```

If saving fails, the record is removed only from the current in-memory list. It can return after restarting because the JSON file was not updated.

## Detecting an Empty Update

The update function asks for a new department and position.

If both are blank:

```python
if not new_department and not new_position:
    print("No changes entered. Employee was not updated.")
    return False
```

The `and` operator requires both conditions to be true:

```text
department is blank
AND
position is blank
```

When both are blank:

- No dictionary value changes
- The function returns `False`
- `save_employees()` is not called
- The application does not falsely claim success

## Day 15 Accomplishments

- Learned why JSON can become invalid
- Handled `json.JSONDecodeError`
- Handled `OSError`
- Distinguished missing data from damaged data
- Stopped startup safely after loading failure
- Added Boolean results to saving
- Checked saving during registration
- Checked saving during updates
- Checked saving during deletions
- Added accurate warning messages
- Prevented unnecessary saves for blank updates
- Tested invalid JSON without risking real employee data

## Important Things to Remember

```text
JSONDecodeError → file exists but JSON is invalid
OSError         → operating-system or file-operation problem
[]              → valid empty employee collection
None            → dangerous loading failure
True            → operation succeeded
False           → operation failed or made no change
try             → operation that might fail
except          → handles a specific failure
```

## Cost and Security Note

All Day 15 protection runs locally and is free. It does not use paid APIs, cloud services, API keys, or credit cards.

## Personal Reflection

Day 15 made the Employee Management System more reliable. The application now protects employee records, handles damaged files safely, and reports file-operation results honestly.