# Day 20 Summary — Safe Automated Storage Testing

## Goal

Test JSON saving and loading without modifying the real employee data file.

## Business Problem

Automated storage tests can be dangerous if they use a business’s real data file.

A careless test could:

- Replace real employee records
- Add fake test records
- Corrupt valid JSON
- Delete important information

Storage tests should therefore use temporary files.

## Configurable File Paths

The storage functions were updated to accept optional file paths.

```python
def load_employees(file_path=DATA_FILE):
```

```python
def save_employees(
    employee_list,
    file_path=DATA_FILE
):
```

`DATA_FILE` remains the default, so the application continues using the real `employees.json`.

Tests can supply a different path:

```python
load_employees(test_file)
save_employees(employees, test_file)
```

## Default Parameters

A default parameter provides a value when the caller does not supply one.

```python
file_path=DATA_FILE
```

Application call:

```python
load_employees()
```

Test call:

```python
load_employees(test_file)
```

This keeps existing application calls working while making storage functions testable.

## TemporaryDirectory

Python’s built-in `TemporaryDirectory` creates a temporary folder for testing.

```python
with TemporaryDirectory() as temporary_directory:
```

When the `with` block ends, Python automatically deletes the temporary folder and its files.

This protects the real employee database.

## pathlib Test Paths

`Path` was used to create temporary JSON file paths:

```python
test_file = (
    Path(temporary_directory)
    / "employee_test.json"
)
```

The `/` operator joins a directory path and filename when using `Path`.

## Storage Tests Created

### Saving and Loading

The first test:

1. Created a test employee list.
2. Saved it to a temporary JSON file.
3. Loaded it back into Python.
4. Confirmed that saving returned `True`.
5. Confirmed that the loaded data matched the original data.

### Missing File

The second test requested a file that did not exist.

Expected result:

```python
[]
```

An empty list means loading was safe, but no employees were stored.

### Invalid JSON

The third test wrote deliberately invalid content:

```text
This is not valid JSON
```

Expected result:

```python
None
```

`None` tells the main application that loading failed and continuing could be unsafe.

## Difference Between [] and None

```text
[]   → valid situation with zero employee records
None → storage failure or corrupted data
```

The application can continue with `[]`, but it should stop when it receives `None`.

## Test Results

```text
Ran 3 tests

OK
```

All storage tests passed.

The existing Employee Management System also loaded the real employee directory correctly.

## Updated Testing Structure

```text
employee_management_system/
├── test_employee_system.py
└── test_storage.py
```

`test_employee_system.py` tests employee search, performance, and payroll.

`test_storage.py` tests JSON saving, loading, missing files, and invalid JSON handling.

## Business Importance

Safe storage tests:

- Protect real business records
- Verify persistent data behavior
- Detect corrupted JSON
- Prevent accidental data replacement
- Automatically clean up test files
- Make future storage changes safer

## Day 20 Accomplishment

I made the storage functions configurable, created temporary JSON files for testing, protected the real employee database, and completed three automated storage tests successfully.