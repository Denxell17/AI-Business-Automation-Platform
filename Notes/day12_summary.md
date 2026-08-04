# Day 12 Summary — Integrating JSON Storage into the Employee Management System

## Day 12 Goal

The goal of Day 12 was to connect the JSON knowledge from Day 11 to the real Employee Management System.

The application can now:

- Load saved employees when it starts
- Register new employees
- Save new employee records
- Search saved employees by ID
- Display saved employee profiles
- Generate payroll for saved employees
- Prevent duplicate employee IDs
- Retain employee records after restarting Python

## Project Data File

The real application stores its employee data here:

```text
Projects/
└── employee_management_system/
    ├── main_refactored.py
    └── employees.json
```

The JSON file inside `Lessons` was used for practice.

The JSON file inside `employee_management_system` belongs to the real application.

## Required Imports

The application now imports:

```python
import json
from pathlib import Path
```

- `json` converts between Python data and JSON.
- `Path` helps determine the correct file location.

## Data File Constant

The application uses:

```python
DATA_FILE = Path(__file__).with_name("employees.json")
```

`DATA_FILE` contains the location of the application’s JSON file.

It is uppercase because it is a constant—a value that should not change while the program runs.

Because `__file__` refers to `main_refactored.py`, `employees.json` is placed in the same folder.

## Loading Employees

The loading function is:

```python
def load_employees():
    if not DATA_FILE.exists():
        return []

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)
```

When the application starts:

```python
employees = load_employees()
```

`employees` becomes a list containing every employee dictionary saved in JSON.

If the file does not exist, the function returns an empty list:

```python
[]
```

## Saving Employees

The saving function is:

```python
def save_employees(employee_list):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(employee_list, file, indent=4)
```

This function receives the complete employee list and writes it into `employees.json`.

## Singular and Plural Variables

Inside `run_program()`:

```python
employees = load_employees()
employee = None
```

These variables have different purposes:

```text
employees → list containing all employee dictionaries
employee  → one selected employee dictionary
```

Example:

```python
employees = [
    {"employee_id": "EMP004", "name": "Aki"},
    {"employee_id": "EMP005", "name": "Ruth"},
]
```

If Ruth is selected:

```python
employee = {
    "employee_id": "EMP005",
    "name": "Ruth",
}
```

## Saving a New Registration

Registration now follows this process:

```python
new_employee = register_employee(employees)

if new_employee is not None:
    employees.append(new_employee)
    save_employees(employees)
    employee = new_employee
```

The steps are:

```text
Collect employee information
→ return a new dictionary
→ append it to the employee list
→ save the complete list to JSON
```

Calling `save_employees()` immediately after `append()` ensures the new employee does not remain only in temporary memory.

## Searching by Employee ID

The application uses:

```python
def find_employee_by_id(employee_list, employee_id):
    employee_id = employee_id.strip().upper()

    for employee in employee_list:
        if employee["employee_id"].upper() == employee_id:
            return employee

    return None
```

The function:

1. Cleans and normalizes the requested ID.
2. Loops through all saved employees.
3. Returns the matching employee dictionary.
4. Returns `None` if no match exists.

Because `.upper()` is used, these inputs are treated equally:

```text
emp004
EMP004
Emp004
```

## Viewing a Saved Profile

Option `2` now requests an employee ID:

```python
employee_id = input(
    "Enter Employee ID to view: "
)

employee = find_employee_by_id(
    employees,
    employee_id
)
```

If a match exists:

```python
display_employee_profile(employee)
```

If no match exists:

```text
Employee not found.
```

This works after restarting because the search uses the list loaded from JSON.

## Viewing Saved Payroll

Option `3` independently requests an employee ID:

```python
employee_id = input(
    "Enter Employee ID for payroll: "
)

employee = find_employee_by_id(
    employees,
    employee_id
)
```

If the employee exists:

```python
display_payroll(employee)
```

This allows payroll to be generated without registering the employee again or viewing the profile first.

## Immediate Duplicate Detection

The improved registration function accepts the full employee list:

```python
def register_employee(employee_list):
```

It collects the Employee ID first:

```python
employee_id = get_required_text(
    "Enter Employee ID: ",
    "Employee ID"
).upper()
```

It then searches for that ID:

```python
existing_employee = find_employee_by_id(
    employee_list,
    employee_id
)
```

If the ID already exists:

```python
if existing_employee is not None:
    print("An employee with that ID already exists.")
    return None
```

The function stops immediately. It does not request the remaining fields.

## Why Return `None`?

For a duplicate ID:

```python
return None
```

means:

> No new employee dictionary was created.

The menu checks:

```python
if new_employee is not None:
```

Therefore, a duplicate record is not:

- Appended to the list
- Saved to JSON
- Reported as successfully registered

`None` acts as a signal that registration did not produce a valid new record.

## Persistence Test

EMP005 was registered as Ruth.

During the first run:

```text
Register EMP005
→ append Ruth to employees
→ save employees to employees.json
→ close program
```

During the second run:

```text
Start program
→ load employees.json
→ search EMP005
→ display Ruth’s profile
```

Ruth remained available because her dictionary was stored in `employees.json`.

She was not retained by the previous Python process. That process had already ended.

## Temporary Memory Compared with the JSON File

```text
Python variables and lists
→ exist while the program is running
→ disappear when the process ends
```

```text
employees.json
→ stored on the computer
→ remains after the program ends
→ can be loaded during the next run
```

## Common Input Mistake

When the program displays:

```text
Choose an Option:
```

the user must enter:

```text
1, 2, 3, or 4
```

When it displays:

```text
Enter Employee ID to view:
```

the user can enter:

```text
EMP005
```

Entering an employee ID at the menu prompt causes an invalid-option message.

## Day 12 Accomplishments

- Added JSON imports to the real application
- Created the application data-file path
- Added reusable load and save functions
- Loaded all saved employees during startup
- Saved new registrations immediately
- Searched persistent employee records
- Displayed saved profiles
- Generated payroll for saved employees
- Added case-insensitive employee ID searches
- Prevented duplicate IDs immediately
- Confirmed that EMP005 remained after restarting

## Important Things to Remember

```text
employee             → one employee dictionary
employees            → list of all employee dictionaries
DATA_FILE             → location of employees.json
load_employees()      → JSON file to Python list
save_employees()      → Python list to JSON file
find_employee_by_id() → searches the employee list
append()              → adds a new dictionary to the list
None                  → no employee or no new registration
```

## Cost and Security Note

This persistence system is local and free.

It does not use:

- Paid APIs
- Cloud databases
- Credit cards
- API keys
- Paid hosting

The employee data is stored locally in `employees.json`.

## Personal Reflection

Day 12 transformed the Employee Management System into a persistent multi-session application.

The program now combines input validation, functions, lists, dictionaries, searching, payroll calculations, and JSON storage in one working business application.