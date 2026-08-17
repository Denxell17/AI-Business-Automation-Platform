# Day 35 Summary — Sorting Employees by Name

## Goal

Display employee directories in alphabetical order without changing the original employee list or saved file order.

## Sorting Service

The following function was added to `employee_service.py`:

```python
def sort_employees_by_name(
    employee_list: list[Employee],
) -> list[Employee]:
    return sorted(
        employee_list,
        key=lambda employee: employee["name"].casefold(),
    )
```

## `sorted()` Versus `.sort()`

`sorted()` creates and returns a new list:

```python
sorted_employees = sorted(employee_list)
```

The original list remains in its previous order.

`.sort()` changes the original list directly:

```python
employee_list.sort()
```

It returns `None`.

Using `sorted()` is safer here because displaying employees should not unexpectedly change the application’s main list.

## The `key` Argument

The `key` argument tells `sorted()` which value it should use when comparing items:

```python
key=lambda employee: employee["name"].casefold()
```

For every employee dictionary, the lambda returns the employee’s normalized name.

## Why `.casefold()` Is Used

`.casefold()` prevents capitalization from affecting the alphabetical order.

Without normalization, uppercase and lowercase letters can produce an unexpected order.

The following names are compared consistently:

```text
aki
Dennis
Ruth
```

## Protecting the Original List

The sorted result is assigned to a separate variable:

```python
sorted_employees = sort_employees_by_name(
    employees
)
```

The application then displays that new list:

```python
display_all_employees(sorted_employees)
```

The original `employees` list is not replaced or reordered.

## Sorting Filtered Results

Department results are also sorted before display:

```python
sorted_matching_employees = sort_employees_by_name(
    matching_employees
)

display_all_employees(sorted_matching_employees)
```

The process is:

1. Filter employees by department.
2. Check whether matches exist.
3. Sort the matching employees by name.
4. Display the sorted matches.

## Tests Added

Two tests were added:

- Employees are sorted alphabetically regardless of capitalization.
- Sorting does not change the original list.

The identity assertion:

```python
self.assertIsNot(
    sorted_employees,
    employees,
)
```

verifies that the sorted result and original input are different list objects in memory.

## Final Verification

```text
Ran 50 tests
OK

All automated tests passed.
```

The full employee directory and department-filtered directories are now displayed alphabetically, while the original employee list remains protected.