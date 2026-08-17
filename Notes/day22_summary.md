# Day 22 Summary — Configuration and Business Rules

## Goal

Move fixed payroll values into a central configuration module and remove unexplained numbers from payroll calculations.

## Business Problem

Payroll rules can change.

Examples include:

- Tax rates
- Allowance amounts
- Overtime amounts
- Number of salary periods per year

When values are written directly throughout calculation code, changes become difficult and risky.

## The config.py Module

A new configuration module was created:

```text
config.py
```

It contains:

```python
MONTHS_PER_YEAR = 12
TAX_RATE = 0.05
DEFAULT_ALLOWANCE = 5000
DEFAULT_OVERTIME = 3000
```

## Configuration Constants

A constant is a configured value that should not change during normal program execution.

Python uses uppercase names as a convention:

```python
TAX_RATE
DEFAULT_ALLOWANCE
```

Uppercase tells developers to treat the value as fixed configuration.

Python does not technically prevent the value from being changed, so developers must follow the convention.

## Meaning of DEFAULT

`DEFAULT` means the value used when another value has not been supplied.

For example:

```python
DEFAULT_ALLOWANCE = 5000
```

means ₱5,000 is the standard allowance currently used by the application.

## Magic Numbers

A magic number is a numeric value written directly into code without explaining its purpose.

Example:

```python
monthly_tax = salary * 0.05
```

The meaning of `0.05` is not immediately clear.

The improved version is:

```python
monthly_tax = salary * TAX_RATE
```

The constant explains that the value represents a tax rate.

## Importing Configuration

`payroll.py` imports the business settings:

```python
from config import (
    DEFAULT_ALLOWANCE,
    DEFAULT_OVERTIME,
    MONTHS_PER_YEAR,
    TAX_RATE,
)
```

## Updated Payroll Calculations

The previous hardcoded calculations:

```python
annual_salary = salary * 12
monthly_tax = salary * 0.05
allowance = 5000
overtime = 3000
```

became:

```python
annual_salary = salary * MONTHS_PER_YEAR
monthly_tax = salary * TAX_RATE
allowance = DEFAULT_ALLOWANCE
overtime = DEFAULT_OVERTIME
```

The calculations now describe their business meaning.

## Centralized Changes

If the business changes the standard allowance, only one value needs to be updated:

```python
DEFAULT_ALLOWANCE = 6000
```

All payroll calculations that use the constant receive the new setting.

## Configuration Tests

Two automated tests were added:

```python
test_default_allowance
test_default_overtime
```

They confirm that payroll uses the values defined in `config.py`.

## Test Result

```text
Ran 11 tests

OK
```

All employee-search, performance, payroll, allowance, and overtime tests passed.

## Updated Project Structure

```text
employee_management_system/
├── activity_logger.py
├── config.py
├── main_refactored.py
├── payroll.py
├── storage.py
├── validators.py
├── test_employee_system.py
└── test_storage.py
```

## Business Importance

Centralized configuration:

- Makes policy changes easier
- Reduces repeated values
- Explains the meaning of business rules
- Prevents inconsistent settings
- Makes code easier to review
- Reduces maintenance risk

## Day 22 Accomplishment

I created a configuration module, replaced payroll magic numbers with named constants, and added automated tests confirming that payroll uses the configured allowance and overtime values.