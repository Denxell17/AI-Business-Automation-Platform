# Day 19 Summary — JSON Storage Module

## Goal

Move JSON file reading and writing out of the main application and into a dedicated storage module.

## Business Problem

`main_refactored.py` previously handled menus, employee operations, payroll display, and JSON storage.

A large file with too many responsibilities is difficult to maintain. Storage operations were moved into their own module to improve organization.

## The storage.py Module

The new module is:

```text
storage.py
```

It contains:

```python
load_employees()
save_employees()
```

### load_employees()

This function reads `employees.json` and converts its JSON data into a Python employee list.

```text
employees.json → Python list
```

It returns:

- An employee list when loading succeeds
- `[]` when the file does not exist
- `None` when the JSON is invalid or the file cannot be read safely

### save_employees()

This function converts the Python employee list into JSON and saves it.

```text
Python list → employees.json
```

It returns:

```python
True
```

when saving succeeds and:

```python
False
```

when saving fails.

## pathlib and DATA_FILE

`Path` is used to locate `employees.json` beside `storage.py`.

```python
DATA_FILE = Path(__file__).with_name("employees.json")
```

`__file__` represents the path of the current Python file.

## Importing Storage Functions

The main application imports the storage functions:

```python
from storage import (
    load_employees,
    save_employees,
)
```

The main application can call the functions without directly using `json`, `Path`, or `DATA_FILE`.

## Removing Duplicate Code

After connecting `storage.py`, the following were removed from `main_refactored.py`:

```python
import json
from pathlib import Path
DATA_FILE
load_employees()
save_employees()
```

The calls to `load_employees()` and `save_employees()` remained because they now use the imported functions.

## Important Difference Between [] and None

An empty list means loading was safe but there are no employee records:

```python
[]
```

`None` means a dangerous loading failure occurred:

```python
None
```

The program stops when it receives `None` to prevent accidental data loss.

## Verification

Option `6` displayed two employees loaded from `employees.json`.

The automated test result was:

```text
Ran 9 tests

OK
```

This confirmed that the storage refactoring did not break existing employee-search, performance, or payroll behavior.

## Updated Project Structure

```text
employee_management_system/
├── main_refactored.py
├── validators.py
├── payroll.py
├── storage.py
├── employees.json
└── test_employee_system.py
```

## Business Importance

A dedicated storage module:

- Keeps JSON logic in one location
- Makes the main program easier to understand
- Reduces duplicate code
- Makes future database migration easier
- Improves maintenance and testing
- Protects data through centralized error handling

## Day 19 Accomplishment

I moved JSON loading, saving, path handling, and storage-error handling into `storage.py`. I connected it to the main application and verified the change using saved employee records and nine automated tests.