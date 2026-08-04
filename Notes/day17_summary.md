# Day 17 Summary — Organizing Automated Tests

## Goal

Improve the organization, readability, and usefulness of the Employee Management System’s automated tests.

## Topics Learned

### 1. The setUp() Method

`setUp()` is a special `unittest` method that runs automatically before each test method.

```python
def setUp(self):
    self.employees = [
        {
            "employee_id": "EMP001",
            "name": "Dennis",
        },
        {
            "employee_id": "EMP002",
            "name": "Maria",
        },
    ]
```

It prepares fresh test data for every test.

### 2. Reusable Test Data

Instead of repeating an employee list inside every test, the tests use:

```python
self.employees
```

This makes the code shorter and easier to maintain.

### 3. Test Isolation

Each test receives fresh data from `setUp()`.

If one test changes its employee list, that change does not affect the other tests. This prevents tests from interfering with each other.

### 4. Using self in Tests

`self` represents the current test object.

Values stored using `self`, such as:

```python
self.employees
self.payroll
```

can be accessed by other methods belonging to that test object.

### 5. Verbose Test Output

The `-v` option means verbose.

It displays the name and result of every test:

```text
test_employee_not_found ... ok
test_annual_salary_calculation ... ok
```

This makes failed tests easier to identify.

### 6. Focused Tests

The original payroll test checked several calculations in one method.

It was divided into separate tests for:

- Annual salary
- Monthly tax
- Estimated bonus
- Total compensation

Each test now checks one specific behavior.

### 7. Test Naming

Test names should clearly describe what they verify.

Examples:

```python
test_search_is_case_insensitive
test_annual_salary_calculation
test_invalid_performance_score
```

Clear names help developers understand failures quickly.

## Final Test Result

```text
Ran 9 tests

OK
```

All nine automated tests passed.

## Business Importance

Well-organized tests:

- Reduce repeated code
- Detect calculation errors
- Prevent old features from breaking
- Make failures easier to locate
- Make future changes safer
- Improve confidence in the application

## Day 17 Accomplishment

I refactored the automated tests using `setUp()`, reusable test data, test isolation, verbose output, descriptive names, and focused payroll tests. The Employee Management System now has nine passing automated tests.