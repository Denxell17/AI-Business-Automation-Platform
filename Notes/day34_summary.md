# Day 34 Summary — Filtering Employees by Department

## Goal

Add a feature that allows users to view employees belonging to a specific department.

## New Service Function

The following function was added to `employee_service.py`:

```python
def filter_employees_by_department(
    employee_list: list[Employee],
    department: str,
) -> list[Employee]:
    normalized_department = department.strip().casefold()

    if not normalized_department:
        return []

    matching_employees = []

    for employee in employee_list:
        employee_department = (
            employee["department"].strip().casefold()
        )

        if employee_department == normalized_department:
            matching_employees.append(employee)

    return matching_employees
```

## Text Normalization

`.strip()` removes spaces before and after text.

Example:

```python
"  Finance  ".strip()
```

Result:

```text
Finance
```

`.casefold()` makes text comparison reliably case-insensitive.

Therefore, these inputs can match the same department:

```text
Finance
finance
FINANCE
  finance
```

## Empty Results

The function returns an empty list when:

- The user enters a blank department.
- No employees belong to the requested department.

```python
return []
```

An empty list is falsy, allowing this check:

```python
if not matching_employees:
    print("No employees found in that department.")
```

## Original List Protection

Filtering does not modify the original employee list.

Matching employees are added to a new list:

```python
matching_employees = []
```

The original employee records remain unchanged.

## Menu Integration

The menu now contains:

```text
7. View Employees by Department
8. Export Employee Report
9. Restore Employee Backup
10. Exit
```

Option 7 asks for a department, filters the employees, and displays the matches:

```python
elif choice == "7":
    department = input(
        "Enter department to filter: "
    )

    matching_employees = filter_employees_by_department(
        employees,
        department,
    )

    if not matching_employees:
        print("No employees found in that department.")
    else:
        display_all_employees(matching_employees)
        log_activity(
            "Employee directory filtered by department."
        )
```

## Function Reuse

`display_all_employees()` works with both:

- The complete employee list
- A filtered employee list

Both contain employee dictionaries with the same structure.

## Tests Added

Three department-filter tests verify:

- Matching employees are returned.
- An unknown department returns an empty list.
- Blank department input returns an empty list.

## Final Verification

```text
Ran 48 tests
OK

All automated tests passed.
```

The new department-filtering feature works, and all tested existing features continue to work correctly.