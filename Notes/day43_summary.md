# Day 43 Summary — Highest-Average-Salary Department

## Goal

Identify and display the department with the highest average employee salary.

## Model Update

Added this field to `WorkforceSummary`:

```python
highest_average_salary_department: str | None
```

It stores:

- A department name when employees exist
- `None` when there are no employees

## Empty Result

```python
"highest_average_salary_department": None,
```

## Calculation

The department averages must be calculated before they can be compared:

```python
highest_average_salary_department = max(
    department_average_salaries,
    key=department_average_salaries.get,
)
```

`max()` examines the department names stored as dictionary keys.

`key=department_average_salaries.get` tells `max()` to compare their average-salary values.

## Returned Result

```python
"highest_average_salary_department": (
    highest_average_salary_department
),
```

Parentheses can split a long expression across lines. A comma after the variable inside those parentheses would accidentally create a tuple.

## Console Report

The workforce summary now displays:

```text
Highest Average Dept. : Corpus Cristi
Department Average    : ₱60,000.00
```

## Important Distinction

The highest-payroll department and highest-average-salary department can be different.

A department with many employees may have the highest combined payroll, while a smaller department may have the highest average salary.

## Testing

Tests verify:

- The correct highest-average-salary department is selected
- `None` is returned when there are no employees
- Existing functionality continues to work

All 57 automated tests passed.

## Business Value

This report helps managers compare department compensation levels and identify where average employee salaries are highest.