# Day 37 Summary — Searching Employees by Partial Name

## Goal

Allow users to find employees without knowing an exact employee ID or complete name.

## Search Service

The following function was added to `employee_service.py`:

```python
def search_employees_by_name(
    employee_list: list[Employee],
    search_text: str,
) -> list[Employee]:
    normalized_search_text = search_text.strip().casefold()

    if not normalized_search_text:
        return []

    matching_employees = []

    for employee in employee_list:
        normalized_name = employee["name"].casefold()

        if normalized_search_text in normalized_name:
            matching_employees.append(employee)

    return matching_employees
```

## Search Normalization

`.strip()` removes surrounding spaces:

```python
"  RU  ".strip()
```

Result:

```text
RU
```

`.casefold()` provides reliable case-insensitive comparison:

```python
"RU".casefold()
```

Result:

```text
ru
```

## Partial Matching

The `in` operator checks whether one piece of text appears inside another:

```python
"ru" in "ruth"
```

Result:

```python
True
```

Therefore, a user can enter only part of an employee’s name.

## `in` Versus `is`

`in` checks containment:

```python
"ru" in "ruth"
```

`is` checks whether two variables refer to the same object in memory. It should not be used for partial-text matching.

## Multiple Results

The function returns:

```python
list[Employee]
```

A partial search may match more than one employee. For example, `"mari"` can match both:

```text
Maria Santos
Marian Cruz
```

## Blank Input

Blank input returns an empty list:

```python
if not normalized_search_text:
    return []
```

This prevents an empty string from matching every employee name.

## Menu Integration

The menu now includes:

```text
9. Search Employees by Name
10. Export Employee Report
11. Restore Employee Backup
12. Exit
```

Option 9:

1. Requests all or part of a name.
2. Searches the employee list.
3. Handles no matches safely.
4. Sorts matches alphabetically.
5. Displays the matching employees.
6. Records a privacy-conscious activity message.

## Tests Added

Three tests verify:

- Partial text can match multiple employees.
- Spaces and capitalization are ignored.
- Blank input returns an empty list.

## Final Verification

```text
Ran 54 tests
OK

All automated tests passed.
```

The application can now find employees using complete or partial names without modifying the original employee list.