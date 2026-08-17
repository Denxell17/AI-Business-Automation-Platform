# Day 33 — Business-Rule Validation

## Learning Objective

Validate the meaning of stored employee values in addition to checking their dictionary structure and Python types.

## Type Validation Versus Business Validation

Type validation asks whether a value has the expected Python type:

```python
"salary": 60000
```

The salary is an integer, so its type is valid.

Business-rule validation asks whether the value makes sense for the application:

```python
"salary": -60000
```

This is still an integer, but a negative salary violates the business rules.

## Blank Text Validation

Required string fields cannot contain only empty text or whitespace:

```python
if expected_type is str and not actual_value.strip():
    errors.append(
        f"Field '{field_name}' cannot be blank."
    )
```

`.strip()` removes surrounding whitespace.

Examples that become empty:

```python
""
" "
"   "
```

## Skipping Rules After Type Errors

After detecting an incorrect type, the validator uses:

```python
continue
```

This moves to the next field.

It prevents unsafe operations such as:

```python
actual_value.strip()
actual_value <= 0
```

when the value has the wrong type.

## Positive Salary Rule

```python
if field_name == "salary" and actual_value <= 0:
    errors.append(
        "Field 'salary' must be greater than zero."
    )
```

This rejects:

```python
0
-1
-50000
```

The rule uses `<= 0` because both zero and negative salaries are invalid.

## Experience Rule

```python
if (
    field_name == "years_of_experience"
    and actual_value < 0
):
    errors.append(
        "Field 'years_of_experience' "
        "cannot be negative."
    )
```

Zero years is valid for a new employee, so the rule rejects only values below zero.

## Performance-Score Rule

```python
if (
    field_name == "performance_score"
    and not 0 <= actual_value <= 100
):
    errors.append(
        "Field 'performance_score' must be "
        "between 0 and 100."
    )
```

The chained comparison means:

```text
Performance score must be at least 0
and
Performance score must be no greater than 100
```

Both boundary values are valid.

## Duplicate Employee IDs

Employee IDs must be unique across the collection.

The validator stores normalized IDs:

```python
seen_employee_ids: set[str] = set()
```

Each ID is normalized using:

```python
normalized_employee_id = employee_id.strip().upper()
```

Therefore, these are treated as the same ID:

```text
EMP001
emp001
 EMP001
```

## Duplicate Detection

```python
if normalized_employee_id in seen_employee_ids:
    errors.append(
        f"Employee #{employee_number}: "
        "Duplicate employee ID."
    )
else:
    seen_employee_ids.add(normalized_employee_id)
```

The set remembers IDs that have already appeared.

The diagnostic identifies the duplicate record’s position without exposing the actual employee ID.

## Why JSON Must Be Validated

Interactive input validation protects newly entered data, but JSON may come from:

- Manual file editing
- Older application versions
- Another program
- Imported data
- File corruption
- Incorrect scripts

Therefore, stored data must be validated again whenever it is loaded.

## Testing Completed

New tests confirmed:

- Whitespace-only text is rejected.
- Zero salary is rejected.
- Negative experience is rejected.
- Performance scores above 100 are rejected.
- Duplicate IDs are detected despite differences in capitalization and spacing.

The complete test suite passed:

```text
Ran 45 tests
OK

All automated tests passed.
```

The real application successfully loaded its two existing employees under the stricter business rules.

## Key Lesson

Correct data types are not enough. Business applications must also validate whether values are meaningful, realistic, and unique.