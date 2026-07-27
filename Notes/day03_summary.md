# Day 3 Summary — User Input, Type Conversion, and F-Strings

## Goal

Make the Employee Management System interactive by allowing users to enter employee information.

## Topics Learned

- The `input()` function
- Interactive programs
- Storing user input
- Type conversion with `int()`
- Strings returned by `input()`
- F-strings
- Number and currency formatting
- Empty user input
- Hardcoded versus dynamic values

## Hardcoded Values

Before Day 3, employee information was written directly in the code:

```python
name = "Dennis"
salary = 60000
```

This is called hardcoding.

To change the employee, a developer would need to edit the source code. A real user should not need to modify Python files.

## User Input

The `input()` function asks the user to provide information:

```python
name = input("Enter Employee Name: ")
```

When Python reaches this line, it:

1. Displays the prompt.
2. Waits for the user to type.
3. Waits for Enter to be pressed.
4. Stores the answer in `name`.

Example:

```text
Enter Employee Name: Dennis
```

The variable now contains:

```python
name = "Dennis"
```

## Interactive Applications

A static program displays predetermined information.

An interactive program receives information from a user and responds to it.

The Employee Management System became interactive with inputs such as:

```python
employee_id = input("Enter Employee ID: ")
name = input("Enter Employee Name: ")
department = input("Enter Department: ")
position = input("Enter Position: ")
country = input("Enter Country: ")
email = input("Enter Email: ")
phone_number = input("Enter Phone Number: ")
```

## Important Rule About `input()`

`input()` always returns a string.

If the user enters:

```text
60000
```

Python initially stores:

```python
"60000"
```

This value looks like a number, but quotation marks show that it is text.

The following would not perform the intended arithmetic:

```python
salary = input("Enter Salary: ")
annual_salary = salary * 12
```

Multiplying a string repeats it rather than performing a salary calculation.

## Type Conversion

To use an entered value in arithmetic, convert it to a numeric type:

```python
salary = int(input("Enter Salary: "))
```

The flow is:

```text
User types 60000
→ input() returns "60000"
→ int() converts it
→ salary stores 60000
```

Other numeric inputs included:

```python
years_of_experience = int(
    input("Enter Years of Experience: ")
)

performance_score = int(
    input("Enter Performance Score: ")
)
```

## Why Phone Numbers Remain Strings

A phone number should not be converted with `int()`:

```python
phone_number = input("Enter Phone Number: ")
```

Phone numbers may include:

```text
+
leading zeros
spaces
dashes
country codes
```

They are identifiers rather than values used in calculations.

## Invalid Numeric Input

If Python expects an integer:

```python
salary = int(input("Enter Salary: "))
```

and the user enters:

```text
sixty thousand
```

Python cannot convert it and raises a `ValueError`.

At this stage, the program expected correct numeric input. Input-validation and error-handling lessons will later prevent this crash.

## F-Strings

An f-string inserts variable values into text:

```python
name = "Dennis"

print(f"Welcome, {name}!")
```

Output:

```text
Welcome, Dennis!
```

An f-string begins with:

```python
f
```

Variables or expressions are placed inside braces:

```text
{ }
```

Examples:

```python
print(f"Employee ID: {employee_id}")
print(f"Department: {department}")
print(f"Salary: {salary}")
```

## Correct F-String Style

Correct:

```python
print(f"Employee ID: {employee_id}")
```

The variable appears inside braces, and no comma is necessary.

Older but still valid style:

```python
print("Employee ID:", employee_id)
```

Avoid mixing the two styles unnecessarily:

```python
print(f"Employee ID:", employee_id)
```

Although it may run, it does not use the main benefit of an f-string.

## Formatting Numbers

This f-string displays a thousands separator:

```python
print(f"Salary: {salary:,}")
```

If:

```python
salary = 60000
```

the output is:

```text
Salary: 60,000
```

To display two decimal places:

```python
print(f"Salary: {salary:,.2f}")
```

Output:

```text
Salary: 60,000.00
```

Adding a currency symbol:

```python
print(f"Salary: ₱{salary:,.2f}")
```

Output:

```text
Salary: ₱60,000.00
```

Formatting explanation:

```text
,     → add thousands separators
.2f   → show two decimal places
```

## Empty Input

If the user presses Enter without typing anything:

```python
name = input("Enter Employee Name: ")
```

Python stores:

```python
name = ""
```

This is called an empty string.

The program may then display:

```text
Welcome, !
```

The program did not crash because an empty string is still a valid string. However, the information is not useful.

Later validation will require important fields such as name and employee ID.

## Terminal Interaction

When the application is waiting at:

```text
Enter Employee ID:
```

the user should enter employee data:

```text
EMP001
```

They should not paste the Python command again. Whatever is typed while `input()` is waiting becomes the value stored by the program.

Example:

```text
Enter Employee ID: EMP001
Enter Employee Name: Dennis
Enter Department: AI Automation
```

## Interactive Employee Registration

The Day 3 program collected information:

```python
employee_id = input("Enter Employee ID: ")
name = input("Enter Employee Name: ")
department = input("Enter Department: ")
position = input("Enter Position: ")
country = input("Enter Country: ")
salary = int(input("Enter Salary: "))
email = input("Enter Email: ")
phone_number = input("Enter Phone Number: ")
years_of_experience = int(
    input("Enter Years of Experience: ")
)
company = input("Enter Company: ")
employment_status = input("Enter Employment Status: ")
```

It then displayed the entered profile:

```python
print()
print("EMPLOYEE PROFILE".center(40))
print("-" * 40)

print(f"Employee ID         : {employee_id}")
print(f"Name                : {name}")
print(f"Department          : {department}")
print(f"Position            : {position}")
print(f"Country             : {country}")
print(f"Salary              : ₱{salary:,.2f}")
print(f"Email               : {email}")
print(f"Phone Number        : {phone_number}")
print(f"Years of Experience : {years_of_experience}")
print(f"Company             : {company}")
print(f"Employment Status   : {employment_status}")
```

## Day 3 Accomplishments

- Replaced hardcoded employee data with user input
- Used `input()` to collect text
- Used `int()` to convert numeric input
- Kept identifiers such as phone numbers as strings
- Created an interactive employee-registration process
- Used f-strings consistently
- Formatted salary as currency
- Understood why blank inputs are accepted
- Learned why invalid numeric input can cause an error

## Important Things to Remember

```text
input()             → asks the user and returns a string
int()               → converts suitable text to an integer
f"{variable}"       → inserts a value into text
:,.2f               → formats a number as 1,000.00
""                  → empty string
hardcoded value     → written directly in source code
dynamic value       → provided while the program runs
```

Examples:

```python
name = input("Enter Name: ")
salary = int(input("Enter Salary: "))

print(f"Name: {name}")
print(f"Salary: ₱{salary:,.2f}")
```

## Personal Reflection

Day 3 transformed the Employee Management System from a fixed demonstration into an application that accepts real user information. This interaction pattern will later be used in forms, APIs, databases, and web applications.