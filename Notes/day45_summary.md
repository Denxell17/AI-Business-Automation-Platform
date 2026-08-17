# Day 45 Summary — Lowest-Average-Salary Department

## Goal

Identify and display the department with the lowest average employee salary.

## Model Update

Added this field to `WorkforceSummary`:

```python
lowest_average_salary_department: str | None
```

It stores:

- A department name when employees exist
- `None` when there are no employees

## Empty Result

```python
"lowest_average_salary_department": None,
```

## Calculation

Department average salaries must be calculated before they can be compared:

```python
lowest_average_salary_department = min(
    department_average_salaries,
    key=department_average_salaries.get,
)
```

`min()` examines the department names stored as dictionary keys.

`key=department_average_salaries.get` tells `min()` to compare their average-salary values.

## Returned Result

```python
"lowest_average_salary_department": (
    lowest_average_salary_department
),
```

## Console Report

The workforce summary now displays:

```text
Lowest Average Dept.  : SSS
Lowest Dept. Average  : ₱50,000.00
```

## Important Distinction

The lowest-payroll department and lowest-average-salary department can be different.

A department with only a few highly paid employees may have a small total payroll but a high average salary. Another department may have a larger payroll but a lower average salary.

## Testing

Tests verify:

- The correct lowest-average-salary department is selected
- `None` is returned when there are no employees
- Existing functionality continues working

All 57 automated tests passed.

## Business Value

This report helps managers compare compensation levels across departments and identify where average employee salaries are lowest.