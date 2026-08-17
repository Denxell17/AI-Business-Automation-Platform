# Day 41 Summary — Average Salary by Department

## Goal

Calculate and display the average monthly salary for each department.

## Model Update

Added this field to `WorkforceSummary`:

```python
department_average_salaries: dict[str, float]
```

The dictionary contains:

- Department names as keys
- Average department salaries as values

## Empty Result

When there are no employees:

```python
"department_average_salaries": {}
```

## Calculation

Department averages are calculated after all employees have been counted:

```python
department_average_salaries = {}

for department, department_payroll in department_payrolls.items():
    employee_count = department_counts[department]

    department_average_salaries[department] = (
        department_payroll / employee_count
    )
```

The formula is:

```text
Department average salary =
Department monthly payroll ÷ Department employee count
```

For example:

```text
Finance payroll: ₱90,000
Finance employees: 2
Finance average: ₱90,000 ÷ 2 = ₱45,000
```

## Console Report

The employee directory now displays:

```text
AVERAGE SALARY BY DEPARTMENT
------------------------------------------------------------
Corpus Cristi: ₱60,000.00
SSS: ₱50,000.00
------------------------------------------------------------
```

## Testing

Tests verify:

- Average salaries for different departments
- The correct average when multiple employees share a department
- An empty dictionary when there are no employees

All 57 automated tests passed.

## Business Value

Average salary reporting helps managers compare compensation levels between departments and support budgeting decisions.