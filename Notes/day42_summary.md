# Day 42 Summary — Highest-Payroll Department

## Goal

Identify and display the department with the largest combined monthly payroll.

## Model Update

Added this field to `WorkforceSummary`:

```python
highest_payroll_department: str | None
```

It stores:

- A department name when employees exist
- `None` when there are no employees

## Empty Result

```python
"highest_payroll_department": None,
```

## Calculation

After all department payroll totals are calculated:

```python
highest_payroll_department = max(
    department_payrolls,
    key=department_payrolls.get,
)
```

`max()` selects a department key.

`key=department_payrolls.get` tells `max()` to compare each department’s payroll value instead of its name.

## Returned Result

```python
"highest_payroll_department": highest_payroll_department,
```

## Console Report

The workforce summary now displays:

```text
Highest Payroll Dept. : Corpus Cristi
Department Payroll    : ₱60,000.00
```

## Important Distinction

The highest-paid employee and highest-payroll department are not necessarily related.

A department may have no individually highest-paid employee but still have the largest combined payroll because it has more employees.

## Testing

Tests verify:

- The department with the largest payroll is selected
- `None` is returned when no employees exist
- Existing features continue working

All 57 automated tests passed.

## Business Value

This report helps managers identify which department creates the largest monthly staffing expense and supports budgeting decisions.