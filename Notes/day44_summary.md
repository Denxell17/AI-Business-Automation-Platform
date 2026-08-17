# Day 44 Summary — Lowest-Payroll Department

## Goal

Identify and display the department with the smallest combined monthly payroll.

## Model Update

Added this field to `WorkforceSummary`:

```python
lowest_payroll_department: str | None
```

It stores:

- A department name when employees exist
- `None` when there are no employees

## Empty Result

```python
"lowest_payroll_department": None,
```

## Calculation

The department payroll totals must be completed before comparing them:

```python
lowest_payroll_department = min(
    department_payrolls,
    key=department_payrolls.get,
)
```

`min()` examines the department names stored as dictionary keys.

`key=department_payrolls.get` tells `min()` to compare their combined payroll values.

## Returned Result

```python
"lowest_payroll_department": lowest_payroll_department,
```

## Console Report

The workforce summary now displays:

```text
Lowest Payroll Dept.  : SSS
Lowest Dept. Payroll  : ₱50,000.00
```

## Important Distinction

The lowest-paid employee is not necessarily in the lowest-payroll department.

A department can contain the lowest-paid employee but still have a larger combined payroll because it has more employees.

## Testing

Tests verify:

- The department with the smallest payroll is selected
- `None` is returned when there are no employees
- Existing functionality continues working

All 57 automated tests passed.

## Business Value

This report helps managers identify which department has the smallest monthly staffing expense and compare department budgets.