# Day 9 Summary — Input Validation and Error Handling

## Goal

Prevent the Employee Management System from crashing or accepting invalid employee information.

## Topics Learned

- Input validation
- `try`
- `except`
- `ValueError`
- Required text validation
- Positive-integer validation
- Range validation
- `.strip()`
- Repeating prompts
- Reusable validation functions
- Dictionary-key consistency
- Reading Python tracebacks

## Why Validation Is Necessary

User input cannot automatically be trusted.

A user might enter:

```text
hello
```

when the application expects a salary, leave a required field blank, or enter a performance score greater than 100.

Without validation:

```python
salary = int(input("Enter Salary: "))
```

entering text causes the application to crash.

With validation, the program explains the problem and asks again.

## `try` and `except`

Potentially unsafe code is placed inside `try`:

```python
try:
    value = int(input(prompt))
```

If the conversion fails, Python raises a `ValueError`.

The program handles it using:

```python
except ValueError:
    print("Please enter a whole number.")
```

The application remains open instead of crashing.

## `ValueError`

A `ValueError` occurs when a value has the wrong format for an operation.

Example:

```python
int("hello")
```

Python cannot convert `"hello"` into an integer.

Valid:

```python
int("60000")
```

Invalid:

```python
int("sixty thousand")
```

## Positive Integer Validation

The reusable function was:

```python
def get_positive_integer(prompt, field_name):
    while True:
        try:
            value = int(input(prompt))

            if value <= 0:
                print(
                    f"{field_name} must be greater than zero."
                )
                continue

            return value

        except ValueError:
            print(
                f"Invalid {field_name}. "
                "Please enter a whole number."
            )
```

It rejects:

```text
hello
-500
0
```

It accepts:

```text
60000
```

This function is appropriate for salary because salary must be positive.

## Range Validation

Some values must stay between minimum and maximum limits:

```python
def get_integer_in_range(
    prompt,
    field_name,
    minimum,
    maximum
):
    while True:
        try:
            value = int(input(prompt))

            if minimum <= value <= maximum:
                return value

            print(
                f"{field_name} must be between "
                f"{minimum} and {maximum}."
            )

        except ValueError:
            print(
                f"Invalid {field_name}. "
                "Please enter a whole number."
            )
```

Performance score uses:

```python
performance_score = get_integer_in_range(
    "Enter Performance Score (0-100): ",
    "Performance score",
    0,
    100
)
```

Experience uses:

```python
years_of_experience = get_integer_in_range(
    "Enter Years of Experience: ",
    "Years of experience",
    0,
    60
)
```

Zero experience is valid for a new employee, so the positive-integer function was not appropriate for this field.

## Required Text Validation

Required text fields use:

```python
def get_required_text(prompt, field_name):
    while True:
        value = input(prompt).strip()

        if value:
            return value

        print(f"{field_name} cannot be blank.")
```

It rejects:

- Pressing Enter without typing
- Entering only spaces

It accepts actual text.

## `.strip()`

`.strip()` removes spaces from the beginning and end of a string.

```text
"   Dennis   "
```

becomes:

```text
"Dennis"
```

A string containing only spaces becomes empty:

```text
"      " → ""
```

This prevents users from bypassing required-field validation using spaces.

## Repeating Until Valid

Each validation function uses:

```python
while True:
```

Invalid input causes the loop to continue.

Valid input uses:

```python
return value
```

`return` sends the accepted value back and ends the function.

## Function Definitions Before Calls

Python reads a file from top to bottom.

This fails:

```python
value = get_integer_in_range(...)

def get_integer_in_range(...):
    ...
```

The function must be defined first:

```python
def get_integer_in_range(...):
    ...

value = get_integer_in_range(...)
```

## Function Arguments

`get_positive_integer()` accepts two arguments:

```python
prompt
field_name
```

`get_integer_in_range()` accepts four:

```python
prompt
field_name
minimum
maximum
```

Passing four arguments to `get_positive_integer()` caused:

```text
TypeError: get_positive_integer() takes 2 positional arguments but 4 were given
```

The experience field was corrected to call `get_integer_in_range()`.

## Validation in `register_employee()`

Raw input was replaced with reusable functions.

Before:

```python
"salary": int(input("Enter Monthly Salary: "))
```

After:

```python
"salary": get_positive_integer(
    "Enter Monthly Salary: ",
    "Salary"
)
```

Required fields now use:

```python
get_required_text()
```

Limited numeric fields use:

```python
get_integer_in_range()
```

## Dictionary-Key Consistency

The registration dictionary temporarily stored:

```python
"years_of experience"
```

but the profile requested:

```python
employee["years_of_experience"]
```

This caused:

```text
KeyError: 'years_of_experience'
```

The key was corrected:

```python
"years_of_experience"
```

Dictionary keys must match exactly, including underscores, spaces, spelling, and capitalization.

## Reading a Traceback

The traceback showed:

- Which file crashed
- Which line called the failing function
- Which line caused the error
- The error type
- The missing dictionary key

Example:

```text
KeyError: 'years_of_experience'
```

A traceback is a diagnostic report. It should be read from the final line upward to identify the error type and location.

## Terminal Versus Running Program

After an application crashes, the terminal returns to:

```text
PS C:\...>
```

At that point, entering `3` is no longer a menu choice. It is interpreted as a PowerShell command.

The program must be restarted after a crash.

## Current Validation Limits

The email field currently checks only that it is not blank.

It does not yet verify whether the value resembles:

```text
name@example.com
```

The phone field also checks only that it is not blank.

More advanced format validation can be introduced later.

## Day 9 Accomplishments

- Prevented invalid numeric input from crashing the program
- Rejected negative and zero salary
- Allowed zero years of experience
- Limited experience to `0–60`
- Limited performance scores to `0–100`
- Rejected blank required fields
- Removed unnecessary surrounding spaces
- Created three reusable validation functions
- Added validation to the real application
- Read and corrected `TypeError`
- Read and corrected `KeyError`
- Confirmed that payroll and profile features still work

## Important Things to Remember

```text
try               → attempt code that may fail
except ValueError → handle invalid value conversion
.strip()          → remove surrounding spaces
while True        → keep asking
continue          → ask again
return            → accept the value and end the function
```

Validation choices:

```text
Required text       → get_required_text()
Positive number     → get_positive_integer()
Limited whole number → get_integer_in_range()
```

## Personal Reflection

Day 9 made the Employee Management System safer and more user-friendly. Instead of assuming that every user enters perfect information, the application now detects common mistakes, explains the problem, and gives the user another opportunity.