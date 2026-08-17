# Day 26 Summary — Automated Test Discovery and Test Runner

## Today’s Goal

Run every automated test in the Employee Management System using one command.

Before Day 26, test files were executed separately:

```text
test_employee_system.py
test_storage.py
test_reports.py
test_exporter.py
```

Test discovery now finds and runs the complete suite automatically.

## Test Discovery Command

```powershell
python -m unittest discover -s Projects/employee_management_system -p "test_*.py" -v
```

## Command Components

### `python -m unittest`

Runs Python’s built-in `unittest` testing framework.

### `discover`

Automatically searches for test files.

### `-s`

```text
-s Projects/employee_management_system
```

Specifies the directory where the search begins.

### `-p`

```text
-p "test_*.py"
```

Specifies the test filename pattern.

The pattern means:

```text
test_    Filename must begin with test_
*        Any characters may appear here
.py      Filename must end with .py
```

Matching examples:

```text
test_employee_system.py
test_storage.py
test_reports.py
test_exporter.py
```

### `-v`

Runs in verbose mode and displays every test method and its result.

## Test Naming Conventions

Test discovery looks for:

```text
test_*.py
```

Inside those files, `unittest` looks for test methods beginning with:

```python
def test_
```

Clear naming allows Python to locate tests automatically.

## Import Side Effects

The old manual boundary script was named:

```text
test_performance.py
```

Test discovery imported it because its filename matched `test_*.py`.

The file contained printing and looping code at the top level. Python executes top-level code whenever a module is imported, so the boundary table appeared before the automated test results.

This unwanted behavior is called an import side effect.

## Main Guard

The manual script was reorganized:

```python
def run_performance_boundary_test():
    # Boundary demonstration code
```

It is called through:

```python
if __name__ == "__main__":
    run_performance_boundary_test()
```

The main guard means:

```text
Run file directly → execute the demonstration
Import the file    → define the function without running it
```

This prevents unwanted output during imports.

## Clearer File Naming

The manual script was renamed:

```text
test_performance.py
```

to:

```text
performance_boundary_demo.py
```

The new name communicates that the file is a manual demonstration rather than an automated `unittest` file.

## Regression Testing

A regression occurs when a newer code change accidentally breaks an existing feature.

Examples:

- Updating reports breaks payroll calculations.
- Adding CSV export breaks employee search.
- Moving a function breaks storage tests.
- Changing configuration breaks allowance calculations.

Running the complete suite checks that existing behavior still works after new changes.

## Reusable Test Runner

New file:

```text
Projects/employee_management_system/run_tests.py
```

Code:

```python
import unittest
from pathlib import Path


TEST_DIRECTORY = Path(__file__).parent


def run_all_tests():
    test_suite = unittest.defaultTestLoader.discover(
        str(TEST_DIRECTORY),
        pattern="test_*.py",
    )

    test_runner = unittest.TextTestRunner(
        verbosity=2
    )
    test_result = test_runner.run(test_suite)

    return test_result.wasSuccessful()


if __name__ == "__main__":
    tests_passed = run_all_tests()

    if tests_passed:
        print()
        print("All automated tests passed.")
    else:
        print()
        print("One or more automated tests failed.")
        raise SystemExit(1)
```

## `TEST_DIRECTORY`

```python
TEST_DIRECTORY = Path(__file__).parent
```

This identifies the directory containing `run_tests.py`.

The test runner searches that directory for matching test files.

## Creating the Test Suite

```python
test_suite = unittest.defaultTestLoader.discover(
    str(TEST_DIRECTORY),
    pattern="test_*.py",
)
```

This discovers the tests and combines them into one suite.

A test suite is a collection of tests that can be executed together.

## Running the Test Suite

```python
test_runner = unittest.TextTestRunner(
    verbosity=2
)
```

Creates a verbose test runner.

```python
test_result = test_runner.run(test_suite)
```

Executes the full suite and stores the result.

## Checking the Result

```python
test_result.wasSuccessful()
```

Returns:

```python
True
```

when every test passes.

It returns:

```python
False
```

when at least one test fails or produces an unexpected error.

## Exit Codes

A successful Python command normally finishes with exit code:

```text
0
```

A failed test suite uses:

```python
raise SystemExit(1)
```

Exit code `1` communicates failure to:

- Windows
- PowerShell
- GitHub Actions
- Deployment systems
- Other automation tools

Printing a failure message alone is not enough for automated tools. The exit code provides a machine-readable result.

## Running the Reusable Test Runner

```powershell
python Projects/employee_management_system/run_tests.py
```

Expected ending:

```text
Ran 22 tests
OK

All automated tests passed.
```

## Expected Invalid-JSON Message

The storage suite intentionally creates invalid JSON.

Therefore, this message can appear:

```text
ERROR: The employee data file contains invalid JSON.
The application will stop to protect your data.
```

The related test still reports:

```text
ok
```

This means error handling behaved correctly. It does not mean the test suite failed.

## Final Test Result

```text
Employee-system tests: 15
Storage tests:          3
Reporting tests:        2
CSV exporter tests:     2
```

Total:

```text
22 tests passed
```

## Key Lesson

As a project grows, developers should not rely on remembering every test command.

Test discovery provides one repeatable command that checks the entire application. A reusable runner makes that command easier to execute and prepares the project for future automated workflows.

## Day 26 Accomplishments

- Learned automatic test discovery.
- Learned the `test_*.py` naming pattern.
- Identified and removed an import side effect.
- Used a main guard correctly.
- Renamed a manual demonstration script.
- Learned the meaning of regression testing.
- Created `run_tests.py`.
- Added machine-readable success and failure behavior.
- Ran all 22 automated tests successfully.