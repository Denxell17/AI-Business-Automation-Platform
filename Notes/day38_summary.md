# Day 38 Summary — Filtering Employees by Salary Range

## Goal

Allow managers to find employees whose salaries fall within a specified compensation range.

## Salary-Range Filter

The following function was added to `employee_service.py`:

```python
def filter_employees_by_salary_range(
    employee_list: list[Employee],
    minimum_salary: int,
    maximum_salary: int,
) -> list[Employee]:
    if minimum_salary > maximum_salary:
        return []

    matching_employees = []

    for employee in employee_list:
        salary = employee["salary"]

        if minimum_salary <= salary <= maximum_salary:
            matching_employees.append(employee)

    return matching_employees
```

## Chained Comparison

This expression:

```python
minimum_salary <= salary <= maximum_salary
```

is equivalent to:

```python
minimum_salary <= salary and salary <= maximum_salary
```

It checks whether one employee’s salary is inside the requested range.

## Inclusive Boundaries

The use of `<=` means both boundaries are included.

For the range `50000–60000`:

- `50000` matches.
- Values between the boundaries match.
- `60000` matches.

## Multiple Results

The function returns:

```python
list[Employee]
```

Several employees may fall within the same salary range. If none match, the function returns an empty list.

## Reversed Ranges

When the minimum is greater than the maximum:

```python
if minimum_salary > maximum_salary:
    return []
```

The service safely returns an empty list.

The menu also checks this condition so it can show a useful message:

```text
Minimum salary cannot be greater than maximum salary.
```

This provides two layers:

- The service protects its own behavior.
- The user interface explains the problem clearly.

## Menu Integration

The menu now includes:

```text
10. Filter Employees by Salary Range
11. Export Employee Report
12. Restore Employee Backup
13. Exit
```

The menu collects validated positive integers, filters the employees, sorts matches from highest to lowest salary, and displays the results.

## Result Sorting

Matching employees are passed to:

```python
sort_employees_by_salary()
```

This makes salary-review results easier to read, with the highest salary displayed first.

## Tests Added

Two tests verify:

- Employees at and between the salary boundaries are returned.
- A reversed salary range safely returns an empty list.

## Final Verification

```text
Ran 56 tests
OK

All automated tests passed.
```

The application can now filter employees using an inclusive salary range without modifying the original employee list.