# Day 2 Summary — Variables and Data Types

## Goal

Learn how Python stores information and use variables to create an employee profile.

## Topics Learned

- Variables
- Assignment
- Strings
- Integers
- Floats
- Booleans
- Lists
- Descriptive variable names
- Changing stored values
- Displaying variables

## What Is a Variable?

A variable is a named place for storing a value.

Example:

```python
name = "Dennis"
salary = 60000
```

Here:

```text
name       → variable name
"Dennis"   → stored value

salary     → variable name
60000      → stored value
```

The general pattern is:

```python
variable_name = value
```

## Assignment Operator

A single equal sign assigns a value:

```python
salary = 60000
```

This means:

> Store `60000` in the variable named `salary`.

It does not mean the same thing as mathematical equality. Python uses `==` for comparison, which was studied later.

## Data Types

A data type describes what kind of value a variable contains.

### String — `str`

A string stores text. It is surrounded by quotation marks:

```python
employee_name = "Dennis"
department = "AI Automation"
employee_id = "EMP001"
```

Both single and double quotation marks can create strings:

```python
country = 'Philippines'
country = "Philippines"
```

Using double quotation marks consistently can make the code easier to read.

### Integer — `int`

An integer stores a whole number without a decimal point:

```python
salary = 60000
age = 35
years_of_experience = 3
```

Integers can be used in calculations.

### Float — `float`

A float stores a number with a decimal point:

```python
tax_rate = 0.05
bonus_rate = 0.10
hourly_rate = 125.50
```

Floats are useful for:

- Percentages
- Prices
- Measurements
- Calculations involving decimals

### Boolean — `bool`

A Boolean stores one of two values:

```python
True
False
```

Examples:

```python
is_learning_python = True
willing_to_relocate = True
is_employed = False
```

Booleans are useful when programs make decisions.

The first letter must be uppercase:

```python
True
False
```

These are incorrect:

```python
true
false
```

### List — `list`

A list stores multiple values together:

```python
dream_countries = ["Canada", "Australia", "New Zealand"]
```

The square brackets identify the list:

```text
[ ]
```

The individual values are separated by commas.

Lists will later help store:

- Multiple employees
- Departments
- Tasks
- Documents
- Menu options

## Employee Variables

The employee profile used variables such as:

```python
employee_id = "EMP001"
name = "Dennis Bernard Basadre"
department = "AI Automation"
position = "Junior Python Developer"
country = "Philippines"
salary = 60000
email = "example@email.com"
phone_number = "+639123456789"
years_of_experience = 3
company = "Looking for Opportunities"
employment_status = "Open to Work"
```

Each variable name explains what its value represents.

## Phone Numbers Are Strings

A phone number may look numeric, but it should normally be stored as text:

```python
phone_number = "+639123456789"
```

It should not be stored as:

```python
phone_number = +639123456789
```

A phone number is an identifier. It is not used for arithmetic.

Storing it as a string preserves:

- The `+` symbol
- Leading zeros
- Spaces
- Dashes
- Country codes

Other identifiers should also often be strings:

```python
employee_id = "0001"
postal_code = "0900"
passport_number = "AB12345"
```

## Descriptive Variable Names

Good variable names clearly describe their purpose:

```python
employee_id
years_of_experience
employment_status
phone_number
expected_salary
```

Avoid unclear names:

```python
x
a
data1
thing
```

Readable names make code easier to understand and maintain.

## Snake Case

Python variable names commonly use `snake_case`:

```python
employee_name
phone_number
years_of_experience
```

Snake case uses:

- Lowercase letters
- Underscores between words

Avoid spaces:

```python
employee name = "Dennis"  # Invalid
```

Use:

```python
employee_name = "Dennis"
```

## Displaying Variables

A variable can be passed to `print()`:

```python
name = "Dennis"

print(name)
```

Output:

```text
Dennis
```

A label can make the output easier to understand:

```python
print("Name:", name)
print("Salary:", salary)
```

Output:

```text
Name: Dennis
Salary: 60000
```

## Variables Can Change

The value stored in a variable can be replaced:

```python
salary = 50000
print(salary)

salary = 60000
print(salary)
```

Output:

```text
50000
60000
```

This is why it is called a variable: its value can vary while the program runs.

A value can also be updated using its current value:

```python
salary = 50000
salary = salary + 10000
```

The new value becomes:

```text
60000
```

## Employee Profile Project

The Day 2 project displayed employee information:

```python
print("=" * 40)
print("EMPLOYEE MANAGEMENT SYSTEM".center(40))
print("=" * 40)

employee_id = "EMP001"
name = "Dennis Bernard Basadre"
department = "AI Automation"
position = "Junior Python Developer"
country = "Philippines"
salary = 60000

print()
print("Employee Profile")
print("-" * 40)

print("Employee ID :", employee_id)
print("Name        :", name)
print("Department  :", department)
print("Position    :", position)
print("Country     :", country)
print("Salary      :", salary)
```

The information was still hardcoded, meaning it was written directly inside the source code. User input was introduced on Day 3.

## Day 2 Accomplishments

- Created variables
- Stored employee information
- Used several data types
- Practiced `snake_case`
- Used clear variable names
- Displayed labels and values
- Learned that variables can change
- Created the first employee profile
- Stored phone numbers correctly as strings
- Used a list to store multiple countries

## Important Things to Remember

```text
variable = value     → stores a value
str                  → text
int                  → whole number
float                → decimal number
bool                 → True or False
list                 → multiple values
snake_case           → Python naming style
```

Examples:

```python
name = "Dennis"                    # str
salary = 60000                     # int
tax_rate = 0.05                    # float
is_learning = True                 # bool
countries = ["Canada", "Japan"]    # list
```

## Personal Reflection

Day 2 taught Python how to remember business information. Variables became the foundation for employee registration, payroll calculations, performance evaluation, databases, and future automation features.