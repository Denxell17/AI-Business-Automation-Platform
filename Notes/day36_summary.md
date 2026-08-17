# Day 36 Summary — Ranking Employees by Salary

## Goal

Display employees from highest to lowest salary for payroll review and business budgeting without changing the original employee list or saved JSON data.

## Salary-Sorting Service

The following function was added to `employee_service.py`:

```python
def sort_employees_by_salary(
    employee_list: list[Employee],
) -> list[Employee]:
    return sorted(
        employee_list,
        key=lambda employee: employee["salary"],
        reverse=True,
    )
```

## Salary Comparison Key

The lambda retrieves the salary from each employee dictionary:

```python
lambda employee: employee["salary"]
```

The returned salary is the value Python uses when comparing employees.

## Ascending and Descending Order

By default, `sorted()` arranges numbers in ascending order:

```text
40000
50000
70000
```

Using:

```python
reverse=True
```

changes the result to descending order:

```text
70000
50000
40000
```

## Lists Versus Files

`sorted()` creates a new list in memory:

```python
salary_ranked_employees = sort_employees_by_salary(
    employees
)
```

It does not create a new file.

It also does not change `employees.json`. A file changes only when the application explicitly saves data to it, such as:

```python
save_employees(employees)
```

The salary-ranked list is displayed but not saved.

## Why `.sort()` Was Not Used

This code would change the existing list directly:

```python
employee_list.sort()
```

This code creates a new sorted list:

```python
sorted(employee_list)
```

Creating a new list is safer for a display-only feature because the main application list remains in its existing order.

## Menu Integration

The menu now includes:

```text
8. View Employees by Salary
9. Export Employee Report
10. Restore Employee Backup
11. Exit
```

Option 8 sorts and displays the employee directory:

```python
elif choice == "8":
    salary_ranked_employees = sort_employees_by_salary(
        employees
    )

    display_all_employees(salary_ranked_employees)
    log_activity(
        "Employee directory sorted by salary."
    )
```

## Tests Added

A salary-sorting test verifies this expected order:

```python
[70000, 50000, 40000]
```

## Final Verification

```text
Ran 51 tests
OK

All automated tests passed.
```

The system can now display employees from highest to lowest salary without modifying the main employee list or saved JSON file.