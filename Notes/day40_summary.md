# Day 40 Summary — Department Payroll Reporting

## Goal

Calculate and display the total monthly salary expense for each department.

## Model Update

Added this field to `WorkforceSummary`:

```python
department_payrolls: dict[str, int]
```

The dictionary uses:

- Department names as keys
- Total monthly payrolls as values

## Payroll Calculation

An empty dictionary is created before processing employees:

```python
department_payrolls = {}
```

Each employee’s salary is added to their department:

```python
department_payrolls[department] = (
    department_payrolls.get(department, 0)
    + employee["salary"]
)
```

`.get(department, 0)` returns the existing department total. If the department is not yet present, it returns `0`.

## Empty Employee List

When there are no employees:

```python
"department_payrolls": {}
```

## Console Report

The employee directory now displays:

```text
MONTHLY PAYROLL BY DEPARTMENT
------------------------------------------------------------
Corpus Cristi: ₱60,000.00
SSS: ₱50,000.00
------------------------------------------------------------
```

## Testing

Tests verify:

- Payroll totals for different departments
- Combined salaries for employees in the same department
- An empty result when there are no employees

All 57 automated tests passed.

## Business Value

Department payroll reporting helps managers understand monthly staffing expenses for each part of the organization.