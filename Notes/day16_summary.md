# Day 16 Summary — Automated Testing with unittest

## Goal

Learn how automated tests verify that important parts of the Employee Management System behave correctly.

## Topics Learned

### 1. The unittest Module

`unittest` is Python’s built-in testing framework. It lets us run checks automatically instead of manually testing every feature.

```python
import unittest
```

### 2. Test Classes

Related tests are organized inside classes that inherit from `unittest.TestCase`.

```python
class TestEmployeeSearch(unittest.TestCase):
```

Our test classes included:

- `TestEmployeeSearch`
- `TestPerformance`
- `TestPayroll`

### 3. Test Methods

A test method must begin with `test_` so `unittest` can discover and run it.

```python
def test_employee_not_found(self):
```

### 4. Meaning of self

`self` represents the current test object created by `unittest`.

It gives the test access to assertion methods such as:

```python
self.assertEqual()
self.assertIsNone()
self.assertIsNotNone()
```

### 5. Assertions

Assertions compare the actual program result with the expected result.

```python
self.assertEqual(actual, expected)
```

Important assertions used:

- `assertEqual()` — values must be equal
- `assertIsNone()` — result must be `None`
- `assertIsNotNone()` — result must not be `None`

### 6. Employee Search Tests

We verified that:

- An existing employee can be found.
- An unknown employee returns `None`.
- Employee ID searches are case-insensitive.

For example, `"emp001"` can find `"EMP001"`.

### 7. Boundary Testing

A boundary is the exact point where program behavior changes.

For performance scores:

- `89` means Very Good.
- `90` means Outstanding.

Testing `90` confirms that the Outstanding category starts at the correct value.

### 8. Invalid Input Testing

We tested a performance score of `101`.

The expected results were:

```text
Rating: Invalid Score
Bonus rate: 0%
```

### 9. Payroll Testing

The payroll test checked that a monthly salary of ₱60,000 and a performance score of 88 produced:

- Annual salary: ₱720,000
- Monthly tax: ₱3,000
- Estimated bonus: ₱72,000
- Total compensation: ₱852,000

### 10. Reading Test Results

```text
......
Ran 6 tests

OK
```

Each `.` represents one successful test.

`OK` means every test ran and all assertions passed.

If an assertion receives an unexpected result, the test reports a failure.

## Business Importance

Automated testing helps a business application by:

- Detecting calculation errors
- Protecting existing features when code changes
- Checking important boundary conditions
- Making future refactoring safer
- Reducing repetitive manual testing

## Day 16 Accomplishment

I created six automated tests covering employee searches, performance ratings, invalid scores, case-insensitive IDs, and payroll calculations. All six tests passed successfully.