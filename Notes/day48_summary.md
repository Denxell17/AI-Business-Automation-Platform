# Day 48 Summary — Total Number of Departments

## Goal

Calculate and display the number of unique departments represented in the workforce.

## Model Update

Added this field to `WorkforceSummary`:

```python
total_departments: int
```

It stores a whole-number department count.

## Empty Result

When there are no employees:

```python
"total_departments": 0,
```

The result is `0` because the workforce contains zero departments.

## Calculation

After all employees have been processed:

```python
total_departments = len(department_counts)
```

`department_counts` uses department names as dictionary keys.

Dictionary keys are unique, so a department appears only once even when it contains multiple employees.

For example:

```python
{
    "Automation": 3,
    "Finance": 2,
}
```

The dictionary contains two keys, so:

```python
total_departments = 2
```

## Returned Result

```python
"total_departments": total_departments,
```

## Console Report

The employee directory now displays:

```text
Total Employees: 2
Total Departments: 2
```

## Testing

Existing tests were extended to verify:

- Two unique departments return `2`
- An empty employee list returns `0`

No new test method was added, so the test count remained unchanged.

All 58 automated tests passed.

## Business Value

The total department count gives managers a quick overview of how many organizational areas are represented in the workforce.