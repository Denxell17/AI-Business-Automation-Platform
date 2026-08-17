# Day 27 Summary — Type Hints and Data Models

## Today’s Goal

Document the expected structure and data types used throughout the Employee Management System.

The application passes employee, payroll, and report dictionaries between several modules. Type hints make those expectations clearer and help development tools identify possible mistakes.

## New File

```text
Projects/employee_management_system/models.py
```

## What Is a Type Hint?

A type hint describes the kind of value expected by Python code.

Examples:

```python
name: str
salary: int
bonus_rate: float
```

These hints mean:

```text
name       → text
salary     → whole number
bonus_rate → decimal number
```

Type hints improve:

- Code readability
- VS Code suggestions
- Static error detection
- Module documentation
- Function contracts

They do not automatically enforce or validate values while the application runs.

## Employee Data Model

```python
from typing import TypedDict


class Employee(TypedDict):
    employee_id: str
    name: str
    department: str
    position: str
    country: str
    salary: int
    email: str
    phone_number: str
    years_of_experience: int
    company: str
    employment_status: str
    performance_score: int
```

`Employee` describes an ordinary Python dictionary with required keys and expected value types.

Example:

```python
employee: Employee = {
    "employee_id": "EMP001",
    "name": "Dennis",
    "department": "Automation",
    "position": "Developer",
    "country": "Philippines",
    "salary": 60000,
    "email": "example@example.com",
    "phone_number": "123456789",
    "years_of_experience": 3,
    "company": "Example Company",
    "employment_status": "Active",
    "performance_score": 88,
}
```

Employee records remain normal dictionaries and can still be saved to JSON.

## Payroll Data Model

```python
class PayrollSummary(TypedDict):
    performance_rating: str
    bonus_rate: float
    annual_salary: int
    thirteenth_month_pay: int
    estimated_bonus: float
    monthly_tax: float
    net_monthly_salary: float
    allowance: int
    overtime: int
    monthly_income: int
    net_monthly_income: float
    total_compensation: float
```

This describes the dictionary returned by:

```python
calculate_payroll()
```

The keys must match the real returned dictionary exactly.

## Workforce Report Model

```python
class WorkforceSummary(TypedDict):
    total_employees: int
    total_monthly_payroll: int
    average_salary: float
    highest_paid_employee: Employee | None
    department_counts: dict[str, int]
```

This describes the dictionary returned by:

```python
calculate_workforce_summary()
```

## Exact Dictionary Keys

These are different keys:

```text
total_employee
total_employees
```

A type model must use the same spelling as the actual dictionary.

Exact keys help prevent:

- Inconsistent data structures
- Misspelled dictionary access
- Editor warnings
- Runtime `KeyError` exceptions

## Employee Service Type Hints

```python
def find_employee_by_id(
    employee_list: list[Employee],
    employee_id: str,
) -> Employee | None:
```

Meaning:

```text
employee_list → list containing Employee dictionaries
employee_id   → string
return        → Employee dictionary or None
```

The vertical bar means “or”:

```python
Employee | None
```

### Update Service

```python
def update_employee_details(
    employee: Employee,
    department: str,
    position: str,
) -> bool:
```

Meaning:

- Receives an employee dictionary.
- Receives two strings.
- Returns `True` or `False`.

### Removal Service

```python
def remove_employee(
    employee_list: list[Employee],
    employee: Employee,
) -> bool:
```

Meaning:

- Receives a list of employees.
- Receives one employee.
- Returns a Boolean success result.

## Payroll Type Hints

```python
def determine_performance(
    performance_score: int,
) -> tuple[str, float]:
```

The return type describes a tuple containing two ordered values:

```python
("Outstanding", 0.15)
```

The first value is a string. The second is a float.

```python
def calculate_payroll(
    employee: Employee,
) -> PayrollSummary:
```

This function receives an employee and returns a payroll-summary dictionary.

## Reporting Type Hints

```python
def calculate_workforce_summary(
    employee_list: list[Employee],
) -> WorkforceSummary:
```

This function receives a list of employees and returns a workforce-summary dictionary.

## Exporter Type Hints

```python
def export_employees_to_csv(
    employee_list: list[Employee],
    file_path: Path = EXPORT_FILE,
) -> bool:
```

Meaning:

```text
employee_list → list of Employee dictionaries
file_path     → filesystem Path
return        → True or False
```

## Storage Type Hints

```python
def load_employees(
    file_path: Path = DATA_FILE,
) -> list[Employee] | None:
```

Possible results:

```text
Data loaded       → list of Employee dictionaries
Missing file      → empty list
Unsafe read error → None
```

```python
def save_employees(
    employee_list: list[Employee],
    file_path: Path = DATA_FILE,
) -> bool:
```

Returns `True` after successful saving or `False` after an error.

## Validator Type Hints

```python
def get_positive_integer(
    prompt: str,
    field_name: str,
) -> int:
```

```python
def get_integer_in_range(
    prompt: str,
    field_name: str,
    minimum: int,
    maximum: int,
) -> int:
```

```python
def get_required_text(
    prompt: str,
    field_name: str,
) -> str:
```

These describe the values received and returned by each validator.

## Models Versus Validators

### `models.py`

Describes what application data should look like:

```text
salary should be int
name should be str
employee record should contain specific keys
```

It does not ask for input or reject invalid values at runtime.

### `validators.py`

Checks actual user input while the program is running:

```text
reject blank names
reject nonnumeric salaries
reject performance scores outside 0–100
```

Validators convert and return acceptable values.

## Type Hints Versus Runtime Behavior

Type hints do not normally change how Python executes the program.

This incorrect call may still begin running:

```python
calculate_payroll("incorrect value")
```

A type-aware editor may warn about it, but runtime protection still depends on validation and error handling.

## Test Result

After adding type hints:

```text
Ran 22 tests
OK

All automated tests passed.
```

This confirms the annotations did not change existing application behavior.

## Key Lesson

Type hints describe the application’s data contracts.

Validators enforce input rules while the program runs.

Using both gives the project clearer structure and safer runtime behavior.

## Day 27 Accomplishments

- Learned the purpose of type hints.
- Learned `TypedDict`.
- Created `Employee`.
- Created `PayrollSummary`.
- Created `WorkforceSummary`.
- Documented employee-service function types.
- Documented payroll input and output types.
- Documented reporting types.
- Documented CSV exporter types.
- Documented storage types.
- Documented validator types.
- Preserved all existing behavior.
- Passed all 22 automated tests.