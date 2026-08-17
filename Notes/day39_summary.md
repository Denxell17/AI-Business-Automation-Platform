# Day 39 Summary — Compensation-Range Reporting

## Goal

Show the highest-paid employee, lowest-paid employee, and difference between their salaries.

## Updated Workforce Model

```python
class WorkforceSummary(TypedDict):
    total_employees: int
    total_monthly_payroll: int
    average_salary: float
    highest_paid_employee: Employee | None
    lowest_paid_employee: Employee | None
    salary_range: int
    department_counts: dict[str, int]
```

## Tracking the Lowest Salary

```python
highest_paid_employee = employee_list[0]
lowest_paid_employee = employee_list[0]
```

The first employee provides real starting values.

During the loop:

```python
if employee["salary"] < lowest_paid_employee["salary"]:
    lowest_paid_employee = employee
```

This updates the variable whenever a smaller salary is found.

## Calculating Salary Range

```python
salary_range = (
    highest_paid_employee["salary"]
    - lowest_paid_employee["salary"]
)
```

For salaries of `60000` and `50000`:

```text
60000 - 50000 = 10000
```

## Empty Workforce

When no employees exist:

```python
"highest_paid_employee": None,
"lowest_paid_employee": None,
"salary_range": 0,
```

`None` means no employee can be selected. A range of `0` means no salary difference exists.

## Displayed Report

```text
Highest-Paid Employee : Aki
Highest Salary        : ₱60,000.00
Lowest-Paid Employee  : Ruth
Lowest Salary         : ₱50,000.00
Salary Range          : ₱10,000.00
```

## Testing

Existing workforce-summary tests were extended with additional assertions.

The test count remained 56 because no new test methods were created.

## Final Verification

```text
Ran 56 tests
OK

All automated tests passed.
```