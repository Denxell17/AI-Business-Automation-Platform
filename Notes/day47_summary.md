# Day 47 Summary — Smallest Department

## Goal

Identify and display the department with the fewest employees.

## Model Update

Added this field to `WorkforceSummary`:

```python
smallest_department: str | None
```

It stores:

- A department name when employees exist
- `None` when there are no employees

## Empty Result

```python
"smallest_department": None,
```

## Calculation

Department counts must be completed before they can be compared:

```python
smallest_department = min(
    department_counts,
    key=department_counts.get,
)
```

`min()` examines the department names stored as dictionary keys.

`key=department_counts.get` tells `min()` to compare each department’s employee count.

## Returned Result

```python
"smallest_department": smallest_department,
```

## Console Report

The workforce summary now displays:

```text
Smallest Department   : Corpus Cristi
Department Employees  : 1
```

## Tied Departments

When multiple departments share the smallest employee count, `min()` returns the first tied department encountered.

With the current data, Corpus Cristi and SSS each contain one employee. Corpus Cristi is selected because it was added to the dictionary first.

## Testing

The existing department-size test was renamed and extended to verify:

- Finance is the largest department with two employees
- Automation is the smallest department with one employee
- `None` is returned for both results when there are no employees

The number of test methods remained unchanged.

All 58 automated tests passed.

## Business Value

This report helps managers identify departments with the smallest workforce and supports staffing and resource-allocation decisions.