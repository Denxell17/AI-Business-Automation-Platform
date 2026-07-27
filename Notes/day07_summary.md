# Day 7 Summary — Functions and Application Refactoring

## Goal

Learn how functions organize reusable code and refactor the Employee Management System from one long script into smaller, focused parts.

Day 7 was divided into:

```text
Day 7A → Function fundamentals
Day 7B → Employee Management System refactoring
```

## Topics Learned

- Defining functions
- Calling functions
- Parameters
- Arguments
- Return values
- Returning multiple values
- Local variables
- Passing results between functions
- Dictionaries
- `None`
- Separating responsibilities
- Refactoring
- Connecting functions to a menu

# Day 7A — Function Fundamentals

## What Is a Function?

A function is a named, reusable block of code that performs a particular task.

Example:

```python
def display_welcome_message():
    print("=" * 40)
    print("EMPLOYEE MANAGEMENT SYSTEM".center(40))
    print("=" * 40)
```

The function is defined using:

```python
def
```

General structure:

```python
def function_name():
    # Instructions
```

## Defining Versus Calling

Defining a function teaches Python what the function should do:

```python
def display_welcome_message():
    print("Welcome")
```

Defining it does not execute it.

To run the function, call it:

```python
display_welcome_message()
```

The parentheses are required when calling it.

## Function Naming

Function names should explain the action they perform:

```python
display_header()
register_employee()
calculate_payroll()
display_employee_profile()
```

Functions commonly use verbs because they perform actions:

```text
display
register
calculate
determine
run
```

Python function names normally use `snake_case`.

## Parameters

A parameter allows a function to receive information:

```python
def greet_employee(name):
    print(f"Welcome, {name}!")
```

Here:

```text
name → parameter
```

It is a variable available inside the function.

## Arguments

An argument is the actual value passed into a function:

```python
greet_employee("Dennis")
```

Here:

```text
"Dennis" → argument
```

The matching is:

```text
Parameter: name
Argument:  "Dennis"
```

The function can be reused with different arguments:

```python
greet_employee("Dennis")
greet_employee("Maria")
greet_employee("John")
```

## Important Naming Correction

The function was initially named:

```python
great_employee()
```

It was corrected to:

```python
greet_employee()
```

“Greet” means to welcome someone. “Great” means excellent.

Clear spelling helps functions communicate their purpose.

## Functions with Return Values

A function can calculate a result and return it:

```python
def calculate_annual_salary(monthly_salary):
    annual_salary = monthly_salary * 12
    return annual_salary
```

Call:

```python
yearly_salary = calculate_annual_salary(60000)
```

The flow is:

```text
60000 enters the function
→ function multiplies it by 12
→ return sends back 720000
→ yearly_salary stores 720000
```

## `print()` Versus `return`

`print()` displays a value:

```python
print(annual_salary)
```

`return` sends a value back to the caller:

```python
return annual_salary
```

Difference:

```text
print() → show the value to the user
return  → give the value back to the program
```

A returned result can be stored, printed, passed into another function, or used in another calculation.

## Function with Two Parameters

You created:

```python
def calculate_bonus(annual_salary, bonus_rate):
    bonus = annual_salary * bonus_rate
    return bonus
```

Call:

```python
estimated_bonus = calculate_bonus(yearly_salary, 0.10)
```

Argument matching:

```text
yearly_salary → annual_salary
0.10          → bonus_rate
```

The order of arguments matters.

## Important Decimal Correction

The call was initially written:

```python
calculate_bonus(yearly_salary, 0,10)
```

Python interpreted the commas as separating three arguments:

```text
yearly_salary
0
10
```

The function expected only two parameters, producing a `TypeError`.

Correct:

```python
calculate_bonus(yearly_salary, 0.10)
```

Python decimal numbers use a period:

```text
0.10 → one decimal number
0, 10 → two separate values
```

## Returning Multiple Values

A function can return more than one result:

```python
def determine_performance(performance_score):
    if performance_score >= 90:
        return "Outstanding", 0.15
```

Receive both values:

```python
performance_rating, bonus_rate = determine_performance(90)
```

The matching is:

```text
"Outstanding" → performance_rating
0.15          → bonus_rate
```

The returned bonus rate can then be passed to another function:

```python
estimated_bonus = calculate_bonus(
    yearly_salary,
    bonus_rate
)
```

This demonstrates how functions can cooperate.

## Local Variables

Variables created inside a function normally belong to that function:

```python
def calculate_bonus(annual_salary, bonus_rate):
    bonus = annual_salary * bonus_rate
    return bonus
```

The variable:

```python
bonus
```

is local to `calculate_bonus()`.

The rest of the application receives its value through `return`.

## Organizing Definitions and Calls

Functions were organized at the top:

```python
def display_welcome_message():
    ...


def greet_employee(name):
    ...


def calculate_annual_salary(monthly_salary):
    ...
```

Function calls were placed afterward:

```python
display_welcome_message()
greet_employee("Dennis")
```

This separates reusable tools from the instructions that run the program.

# Day 7B — Application Refactoring

## What Is Refactoring?

Refactoring means improving the internal structure of code without changing its intended behavior.

Before refactoring, `main.py` contained one long sequence:

```text
Collect employee information
→ determine performance
→ calculate payroll
→ display profile
→ display payroll
```

After refactoring, each responsibility received its own function.

## Preserving the Working Version

The original application remained in:

```text
main.py
```

The reorganized version was built in:

```text
main_refactored.py
```

This protected the working program while changes were being made.

It is safer to test a new structure before replacing a working version.

## Refactored Functions

The application was divided into:

```python
display_header()
display_menu()
register_employee()
display_employee_profile()
determine_performance()
calculate_payroll()
display_payroll()
run_program()
```

Each function has a focused responsibility.

## Display Functions

These functions display information:

```python
display_header()
display_menu()
display_employee_profile()
display_payroll()
```

Example:

```python
def display_header():
    print("=" * 40)
    print("EMPLOYEE MANAGEMENT SYSTEM".center(40))
    print("=" * 40)
```

## Business-Logic Functions

These functions process data:

```python
determine_performance()
calculate_payroll()
```

Example:

```python
def determine_performance(performance_score):
    if performance_score < 0 or performance_score > 100:
        return "Invalid Score", 0
    elif performance_score >= 90:
        return "Outstanding", 0.15
    elif performance_score >= 80:
        return "Very Good", 0.10
    elif performance_score >= 70:
        return "Good", 0.05
    else:
        return "Needs Improvement", 0
```

Separating calculations from display code makes the business rules easier to test and reuse.

## Dictionaries

A dictionary stores multiple labeled values together:

```python
employee = {
    "employee_id": "0001",
    "name": "Dennis",
    "salary": 60000,
}
```

Each entry has:

```text
key → value
```

Examples:

```text
"name"   → "Dennis"
"salary" → 60000
```

Access a dictionary value using its key:

```python
employee["name"]
employee["salary"]
```

## Employee Registration Dictionary

The registration function collected information into one dictionary:

```python
employee = {
    "employee_id": input("Enter Employee ID: "),
    "name": input("Enter Employee Name: "),
    "department": input("Enter Department: "),
    "position": input("Enter Position: "),
    "country": input("Enter Country: "),
    "salary": int(input("Enter Monthly Salary: ")),
    "email": input("Enter Email: "),
    "phone_number": input("Enter Phone Number: "),
    "years_of_experience": int(
        input("Enter Years of Experience: ")
    ),
    "company": input("Enter Company: "),
    "employment_status": input(
        "Enter Employment Status: "
    ),
    "performance_score": int(
        input("Enter Performance Score (0-100): ")
    ),
}
```

The function returned the completed employee:

```python
return employee
```

The controller stored it:

```python
employee = register_employee()
```

## Why a Dictionary Was Better

Without a dictionary, many separate variables would need to be passed between functions:

```python
display_employee_profile(
    employee_id,
    name,
    department,
    position,
    country,
    salary,
    email,
    phone_number
)
```

With a dictionary:

```python
display_employee_profile(employee)
```

This is shorter and easier to maintain.

## Payroll Dictionary

The payroll function also organized its results:

```python
payroll = {
    "performance_rating": performance_rating,
    "bonus_rate": bonus_rate,
    "annual_salary": annual_salary,
    "thirteenth_month_pay": thirteenth_month_pay,
    "estimated_bonus": estimated_bonus,
    "monthly_tax": monthly_tax,
    "net_monthly_salary": net_monthly_salary,
    "allowance": allowance,
    "overtime": overtime,
    "monthly_income": monthly_income,
    "net_monthly_income": net_monthly_income,
    "total_compensation": total_compensation,
}
```

It returned the dictionary:

```python
return payroll
```

The display function used it:

```python
payroll = calculate_payroll(employee)
```

## Dictionary Commas and Braces

Dictionary entries require commas:

```python
payroll = {
    "monthly_tax": monthly_tax,
    "net_monthly_salary": net_monthly_salary,
}
```

A missing comma caused a red underline:

```python
"monthly_tax": monthly_tax
"net_monthly_salary": net_monthly_salary,
```

The corrected version added:

```python
"monthly_tax": monthly_tax,
```

A dictionary begins and ends with:

```text
{ }
```

## Exact Dictionary Keys

Dictionary keys must match exactly.

Incorrect:

```python
employee["monthly_salary"]
```

The dictionary stored:

```python
employee["salary"]
```

Correct:

```python
employee["salary"]
```

Another incorrect key was:

```python
payroll["net_montly_income"]
```

Correct:

```python
payroll["net_monthly_income"]
```

A missing letter can cause a `KeyError`.

## The Meaning of `None`

At the beginning of the program:

```python
employee = None
```

`None` means:

> No employee value exists yet.

Before showing the profile:

```python
if employee is None:
    print("No employee registered yet.")
else:
    display_employee_profile(employee)
```

This prevented the application from trying to access data before registration.

The same check protected payroll:

```python
if employee is None:
    print("No employee registered yet.")
else:
    display_payroll(employee)
```

## Main Controller Function

`run_program()` controlled the complete application:

```python
def run_program():
    display_header()
    employee = None

    while True:
        display_menu()
        choice = input("Choose an option: ")

        if choice == "1":
            employee = register_employee()
        elif choice == "2":
            if employee is None:
                print("No employee registered yet.")
            else:
                display_employee_profile(employee)
        elif choice == "3":
            if employee is None:
                print("No employee registered yet.")
            else:
                display_payroll(employee)
        elif choice == "4":
            break
        else:
            print("Invalid option.")
```

This function connected:

- Conditions
- Loops
- Functions
- Dictionaries
- User input
- Payroll calculations

## Application Structure

```text
run_program()
├── display_header()
├── display_menu()
├── register_employee()
├── display_employee_profile()
└── display_payroll()
    └── calculate_payroll()
        └── determine_performance()
```

This shows how one function can call another function.

## Separation of Responsibilities

Each function should have a clear responsibility:

```text
register_employee()        → collect employee information
display_employee_profile() → show employee information
determine_performance()    → choose rating and bonus rate
calculate_payroll()        → perform calculations
display_payroll()          → show calculation results
run_program()              → control the application
```

This makes the application:

- Easier to understand
- Easier to test
- Easier to modify
- Easier to debug
- Easier to expand

## Complete Functional Test

The refactored application was tested using this sequence:

```text
2 → no employee registered
3 → no employee registered
1 → register employee
2 → display employee profile
3 → display payroll
4 → exit
```

The test confirmed:

- Safe access before registration
- Registration worked
- Employee data remained available
- Profile display worked
- Payroll calculations worked
- The menu continued running
- Exit worked correctly

## Day 7 Accomplishments

- Defined and called functions
- Used parameters and arguments
- Returned calculated values
- Returned two values
- Passed one function’s result into another
- Preserved the original working application
- Refactored a long script
- Created employee and payroll dictionaries
- Used `None` to represent missing data
- Connected functions to menu options
- Prevented early profile and payroll access
- Corrected dictionary-key errors
- Built a functional, organized console application

## Important Things to Remember

```text
def          → define a function
parameter    → variable accepted by a function
argument     → value passed into a function
return       → send a value back
dictionary   → store labeled values
None         → no value exists yet
refactoring  → improve code structure
```

Function pattern:

```python
def function_name(parameter):
    result = parameter * 2
    return result
```

Dictionary pattern:

```python
record = {
    "key": value,
}
```

Controller pattern:

```python
while True:
    choice = input("Choose: ")

    if choice == "1":
        run_feature()
    elif choice == "4":
        break
```

## Personal Reflection

Day 7 transformed the Employee Management System from one long script into a structured application. Functions separated the program into understandable responsibilities, while dictionaries allowed related employee and payroll values to travel together between functions.