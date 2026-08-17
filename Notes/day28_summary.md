# Day 28 — Runtime Employee Data Validation

## Learning Objective

Add runtime validation to protect the Employee Management System from JSON data that has missing fields, incorrect value types, or an invalid overall structure.

## Why Runtime Validation Is Needed

`TypedDict` describes the expected structure of employee dictionaries for developers and type-checking tools. However, it does not automatically validate data loaded from a JSON file while the application is running.

JSON data may have valid syntax but still contain unsafe application data, such as:

- Missing required fields
- Incorrect field names
- Incorrect value types
- A dictionary where a list is expected
- One invalid employee inside an otherwise valid list

Runtime validation checks the actual data before the application uses it.

## Required Employee Fields

`REQUIRED_EMPLOYEE_FIELDS` maps every required employee key to its expected Python type.

```python
REQUIRED_EMPLOYEE_FIELDS = {
    "employee_id": str,
    "name": str,
    "department": str,
    "position": str,
    "country": str,
    "salary": int,
    "email": str,
    "phone_number": str,
    "years_of_experience": int,
    "company": str,
    "employment_status": str,
    "performance_score": int,
}
```

For example, `"salary": int` means the `salary` key must exist and its value must be an integer.

## Validating One Employee

`is_valid_employee_record()` checks:

1. The value is a dictionary.
2. Every required field exists.
3. Every field contains the expected value type.

It returns `True` when the employee record is valid and `False` when any requirement fails.

## Validating an Employee List

`is_valid_employee_list()` first confirms that the loaded data is a list.

It then validates every employee using `is_valid_employee_record()`.

If even one employee is invalid, the entire list is rejected. This prevents partially damaged collections from entering the application.

## JSON Syntax Versus Data Structure

Invalid JSON syntax cannot be decoded:

```text
This is not valid JSON
```

This causes `json.JSONDecodeError`.

Valid JSON can still contain an invalid employee structure:

```json
[
    {
        "employee_id": "EMP001",
        "salary": "60000"
    }
]
```

This is valid JSON syntax, but the record is missing required fields and its salary is text instead of an integer.

## Storage Integration

After `json.load()` reads the file, `load_employees()` now calls:

```python
is_valid_employee_list(employee_data)
```

The data is returned only when validation succeeds.

When the structure is invalid, the function returns `None` to signal that loading failed safely.

## Meaning of Empty List and None

```python
[]
```

Means the employee file does not exist yet and the application can safely start with no employees.

```python
None
```

Means the file could not be loaded safely because of invalid JSON, invalid employee structure, or a file-reading error.

This distinction prevents corrupted data from being mistaken for an empty employee database.

## Testing Completed

Six data-validation tests confirmed:

- A complete employee record is valid.
- A missing required field is rejected.
- An incorrect field type is rejected.
- A valid employee list is accepted.
- Non-list employee data is rejected.
- A list containing an invalid employee is rejected.

Four storage tests confirmed:

- Valid employee data can be saved and loaded.
- A missing file returns an empty list.
- Invalid JSON syntax returns `None`.
- Invalid employee structure returns `None`.

The complete automated test suite passed:

```text
Ran 29 tests
OK

All automated tests passed.
```

The real application also loaded and displayed its existing employee records successfully.

## Key Lesson

Type hints describe what data should look like. Runtime validation checks what the data actually looks like before the application trusts and uses it.