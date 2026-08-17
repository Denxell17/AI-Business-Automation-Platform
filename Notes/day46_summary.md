# Day 46 Summary — Largest Department

## Goal

Identify and display the department with the most employees.

## Model Update

Added this field to `WorkforceSummary`:

```python
largest_department: str | None
```

It stores:

- A department name when employees exist
- `None` when there are no employees

## Empty Result

```python
"largest_department": None,
```

## Calculation

Department counts must be completed before they can be compared:

```python
largest_department = max(
    department_counts,
    key=department_counts.get,
)
```

`max()` examines the department names stored as dictionary keys.

`key=department_counts.get` tells `max()` to compare each department’s employee count.

## Returned Result

```python
"largest_department": largest_department,
```

## Console Report

The workforce summary now displays:

```text
Largest Department    : Corpus Cristi
Department Employees  : 1
```

## Tied Departments

When multiple departments have the same highest employee count, `max()` returns the first tied department encountered.

For example, if both Corpus Cristi and SSS contain one employee, Corpus Cristi is returned because it was added to the dictionary first.

## Testing

A new test verifies that a department with two employees is selected over a department with one employee.

The test count increased because a new test method was added.

All 58 automated tests passed.

## Business Value

This report helps managers identify the department with the largest workforce and supports staffing and resource-planning decisions.