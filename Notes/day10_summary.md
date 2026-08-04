# Day 10 Summary — Employee Collections

## Day 10 Goal

The goal of Day 10 was to expand the Employee Management System from handling one employee to handling multiple employees.

The program now uses a list containing employee dictionaries. It can add employees, display all employees, search by employee ID, prevent duplicate IDs, and show a repeating menu.

## Concepts Practiced

- Lists
- Dictionaries
- `append()`
- `len()`
- `for` loops
- `enumerate()`
- Functions
- Parameters
- `return`
- `None`
- `while True`
- `break`
- String methods
- Searching collections
- Duplicate-record prevention

## Lists and Dictionaries

A dictionary stores the information for one employee:

```python
employee_one = {
    "employee_id": "EMP001",
    "name": "Dennis",
    "department": "Automation",
}
```

A list stores multiple employee dictionaries:

```python
employees = []

employees.append(employee_one)
employees.append(employee_two)
```

The resulting structure is:

```text
employees
├── Employee 1 dictionary
├── Employee 2 dictionary
└── Employee 3 dictionary
```

## Adding Items with `append()`

This line adds an employee dictionary to the list:

```python
employees.append(new_employee)
```

`append()` places the new item at the end of the existing list.

## Counting Employees with `len()`

This line counts the records currently stored in the list:

```python
len(employees)
```

Example:

```python
print(f"Total Employees: {len(employees)}")
```

If the list contains three employee dictionaries, the result is:

```text
Total Employees: 3
```

## Displaying Multiple Employees

A `for` loop processes every dictionary inside the list:

```python
for employee in employees:
    print(employee["name"])
```

`enumerate()` provides both a number and the current employee:

```python
for employee_number, employee in enumerate(
    employees,
    start=1
):
    print(f"Employee #{employee_number}")
```

`start=1` makes the numbering begin at 1 instead of 0.

## Searching by Employee ID

The search function checks each employee dictionary:

```python
def find_employee_by_id(employee_list, employee_id):
    for employee in employee_list:
        if employee["employee_id"] == employee_id:
            return employee

    return None
```

If a matching ID is found, the function returns the complete employee dictionary.

If the loop ends without finding a match, it returns:

```python
None
```

`None` means that no matching employee exists.

## Normalizing Search Input

The search input uses:

```python
search_id = input(
    "Input Employee ID to search: "
).strip().upper()
```

- `strip()` removes extra spaces from the beginning and end.
- `upper()` converts the value to uppercase.

Because of this, the user can enter:

```text
emp003
```

and the system searches for:

```text
EMP003
```

Both methods require parentheses because they must be executed:

```python
.strip().upper()
```

## Preventing Duplicate IDs

Before adding a new employee, the system searches for the entered ID:

```python
if find_employee_by_id(employee_list, employee_id):
    print("An employee with that ID already exists.")
    return
```

If the ID already exists, `return` immediately stops the function. The duplicate employee is not added.

Employee IDs should be unique because they identify individual employee records.

## Reusable Functions

Day 10 separated features into reusable functions:

```python
display_all_employees(employee_list)
find_employee_by_id(employee_list, employee_id)
add_employee(employee_list)
```

Each function has one main responsibility:

- `display_all_employees()` displays every employee.
- `find_employee_by_id()` searches for one employee.
- `add_employee()` creates and adds a new employee.

This makes the program easier to understand, test, and expand.

## Employee Collection Menu

The application now provides these options:

```text
1. Add Employee
2. View All Employees
3. Search Employee
4. Exit
```

The menu repeats with:

```python
while True:
```

The user’s choice determines which function runs.

Selecting Exit activates:

```python
break
```

This stops the repeating menu loop.

## Temporary Memory

Employees added with `append()` currently exist only while the program is running.

For example, if `EMP003` is added and the program is closed, that employee disappears. When the program starts again, Python recreates the list using only the employee dictionaries written directly in the code.

Current behavior:

```text
Start program
→ Create EMP001 and EMP002
→ Add EMP003 temporarily
→ Close program
→ Temporary list is erased
→ Restart with EMP001 and EMP002
```

A future lesson will introduce file storage or a database so employee records remain available after the program closes.

## Errors Fixed

### Incorrect dictionary key

Incorrect:

```python
"emploee_id"
```

Correct:

```python
"employee_id"
```

Dictionary keys must match exactly. A misspelled key can cause a `KeyError`.

### Missing method parentheses

Incorrect:

```python
.strip.upper()
```

Correct:

```python
.strip().upper()
```

Without `()`, Python refers to the method instead of running it.

### Testing a temporary employee

`EMP003` must be added and searched during the same program run. Restarting the program resets the temporary list.

## Day 10 Accomplishments

- Stored multiple employees in a list
- Represented each employee with a dictionary
- Added employees dynamically
- Displayed all employee records
- Numbered employees using `enumerate()`
- Searched for employees by ID
- Handled missing search results with `None`
- Prevented duplicate employee IDs
- Built a repeating collection-management menu
- Used functions to organize collection operations
- Understood that current data is temporary

## Important Things to Remember

```text
list                 → stores multiple items
dictionary           → stores one structured record
append()             → adds an item to a list
len()                → counts items in a collection
enumerate()          → provides an item and its position
return employee      → sends the matching record back
return None          → reports that no match was found
strip()              → removes surrounding spaces
upper()              → converts text to uppercase
break                → stops a loop
```

## Personal Reflection

Day 10 transformed the project from a single-employee application into a collection-based system. The program can now manage several employee dictionaries during one session.

The next major improvement will be persistent storage so newly registered employees do not disappear after the program closes.