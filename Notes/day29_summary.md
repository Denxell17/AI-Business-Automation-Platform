# Day 29 — Detailed Data Validation Errors

## Learning Objective

Improve runtime validation so the Employee Management System explains why stored employee data is invalid instead of returning only `True` or `False`.

## Why Detailed Errors Matter

Boolean validation can answer:

```text
Valid: True
```

or:

```text
Valid: False
```

However, `False` does not identify the problem.

Detailed validation can report messages such as:

```text
Missing required field: department
Field 'salary' must be int, not str.
```

This makes troubleshooting faster and safer.

## Employee Record Errors

The `get_employee_record_errors()` function validates one employee dictionary and returns a list of error messages.

```python
def get_employee_record_errors(
    employee: object,
) -> list[str]:
    errors = []

    if not isinstance(employee, dict):
        errors.append("Employee record must be a dictionary.")
        return errors

    for field_name, expected_type in REQUIRED_EMPLOYEE_FIELDS.items():
        if field_name not in employee:
            errors.append(
                f"Missing required field: {field_name}"
            )
            continue

        actual_value = employee[field_name]

        if not isinstance(actual_value, expected_type):
            errors.append(
                f"Field '{field_name}' must be "
                f"{expected_type.__name__}, not "
                f"{type(actual_value).__name__}."
            )

    return errors
```

A valid employee returns:

```python
[]
```

An invalid employee returns one or more messages.

## Purpose of continue

When a required field is missing, `continue` skips the rest of the current loop iteration.

Without it, the program would try:

```python
employee[field_name]
```

for a key that does not exist, causing a `KeyError`.

## Reusing Detailed Validation

The Boolean validator now reuses the detailed validator:

```python
def is_valid_employee_record(employee: object) -> bool:
    errors = get_employee_record_errors(employee)
    return not errors
```

An empty list is falsy, so:

```python
not []
```

evaluates to `True`.

A non-empty error list is truthy, so:

```python
not ["Missing required field: salary"]
```

evaluates to `False`.

This creates one source of truth for employee-record validation.

## Employee List Errors

The `get_employee_list_errors()` function validates the entire employee collection:

```python
def get_employee_list_errors(
    employee_data: object,
) -> list[str]:
    errors = []

    if not isinstance(employee_data, list):
        errors.append("Employee data must be a list.")
        return errors

    for employee_number, employee in enumerate(
        employee_data,
        start=1,
    ):
        record_errors = get_employee_record_errors(employee)

        for error in record_errors:
            errors.append(
                f"Employee #{employee_number}: {error}"
            )

    return errors
```

Example output:

```text
Employee #2: Field 'salary' must be int, not str.
```

The employee number identifies the record’s position without exposing the employee’s ID, name, or actual salary.

## Boolean List Validation

The list validator also reuses its detailed validator:

```python
def is_valid_employee_list(employee_data: object) -> bool:
    errors = get_employee_list_errors(employee_data)
    return not errors
```

This prevents duplicated validation rules.

## Storage Integration

`load_employees()` now collects detailed errors after reading JSON:

```python
validation_errors = get_employee_list_errors(
    employee_data
)
```

If errors exist, storage displays them and returns `None`:

```python
if validation_errors:
    print()
    print("ERROR: The employee data has an invalid structure.")

    for validation_error in validation_errors:
        print(f"- {validation_error}")

    print("The application will stop to protect your data.")
    return None
```

## Privacy-Aware Diagnostics

Validation messages may safely report:

- Employee position in the list
- Field name
- Expected type
- Actual type

They should not report:

- Employee names
- Employee IDs
- Email addresses
- Phone numbers
- Actual salary values

This provides useful troubleshooting information while reducing exposure of confidential data.

## Testing Completed

Day 29 added tests confirming:

- Valid records return no errors.
- Missing fields produce specific messages.
- Incorrect types produce specific messages.
- Invalid list records report their list position.
- Non-list data produces a clear diagnostic.

The complete test suite passed:

```text
Ran 34 tests
OK

All automated tests passed.
```

The real application also loaded and displayed its valid employee records without warnings.

## Key Lesson

A robust business application should not only reject unsafe data. It should explain the problem clearly, consistently, and without exposing sensitive information.