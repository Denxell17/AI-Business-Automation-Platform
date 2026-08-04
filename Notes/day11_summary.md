# Day 11 Summary — Persistent Employee Storage with JSON

## Day 11 Goal

The goal of Day 11 was to make employee information persist after the Python program closes.

Previously, employee records existed only inside a list in temporary memory. Closing the program erased dynamically added employees.

Day 11 introduced JSON file storage so employee records can be saved to the computer and loaded again during a future program run.

## Concepts Practiced

- JSON
- Persistent storage
- `import json`
- `pathlib`
- `Path`
- `__file__`
- `with_name()`
- `open()`
- Read mode (`"r"`)
- Write mode (`"w"`)
- UTF-8 encoding
- `json.dump()`
- `json.load()`
- File-existence checking
- Default data
- Reusable load and save functions
- Preventing duplicate employee records

## Temporary Memory Compared with Persistent Storage

A regular Python list exists only while the program is running:

```text
Start program
→ create list
→ add employee
→ close program
→ list disappears
```

A JSON file remains stored on the computer:

```text
Start program
→ load JSON file
→ modify employee list
→ save JSON file
→ close program
→ file remains
```

When the program starts again, Python can reload the saved employee records.

## What Is JSON?

JSON means JavaScript Object Notation.

It is a text format commonly used for storing and exchanging structured information.

A Python list containing dictionaries:

```python
employees = [
    {
        "employee_id": "EMP001",
        "name": "Dennis",
        "department": "Automation",
    }
]
```

can be represented in JSON:

```json
[
    {
        "employee_id": "EMP001",
        "name": "Dennis",
        "department": "Automation"
    }
]
```

JSON is useful for this project because its arrays and objects closely resemble Python lists and dictionaries.

## Importing the JSON Library

```python
import json
```

The built-in `json` library provides tools for converting between Python data and JSON.

No paid service or external package is required.

## Understanding `pathlib`

`pathlib` is a built-in Python library for working with file and folder locations.

```python
from pathlib import Path
```

`Path` represents a filesystem location in a structured way.

Example:

```python
file_path = Path(__file__).with_name("employees.json")
```

`__file__` represents the location of the Python file currently running.

If the lesson file is:

```text
C:\...\Lessons\lesson11_json_storage.py
```

then:

```python
Path(__file__).with_name("employees.json")
```

produces:

```text
C:\...\Lessons\employees.json
```

`with_name()` changes the filename portion of the path. It does not rename the Python lesson file.

## Opening Files Safely

Python opens a file with:

```python
with open(file_path, "r", encoding="utf-8") as file:
```

The `with` statement safely manages the opened file. Python closes the file automatically when the indented block finishes.

`encoding="utf-8"` allows the file to store standard international text reliably.

## Read Mode

```python
"r"
```

means read mode.

Example:

```python
with open(file_path, "r", encoding="utf-8") as file:
    employees = json.load(file)
```

Read mode allows the program to inspect the file’s contents.

It does not add, remove, or modify data.

## Write Mode

```python
"w"
```

means write mode.

Example:

```python
with open(file_path, "w", encoding="utf-8") as file:
    json.dump(employees, file, indent=4)
```

If the file does not exist, write mode creates it.

If the file already exists, write mode replaces its complete previous contents.

For this reason, the safe workflow is:

```text
Load the complete existing list
→ modify the list in Python
→ save the complete updated list
```

Saving hardcoded default data before loading would overwrite previously saved employee records.

## Understanding `json.dump()`

```python
json.dump(employee_list, file, indent=4)
```

`json.dump()` converts Python data into JSON and writes it into an opened file.

Its parts are:

```text
employee_list → Python data being saved
file          → destination file
indent=4      → readable formatting
```

Memory aid:

```text
json.dump() → Python to JSON file
```

## Understanding `json.load()`

```python
employees = json.load(file)
```

`json.load()` reads a JSON file and converts its contents back into Python data.

A JSON array becomes a Python list, and each JSON object becomes a Python dictionary.

Memory aid:

```text
json.load() → JSON file to Python
```

## The Save Function

```python
def save_employees(file_path, employee_list):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(employee_list, file, indent=4)

    print("Employee records saved successfully.")
    print(f"Saved to: {file_path}")
```

This function receives:

- The destination file path
- The complete employee list

It saves the list as formatted JSON.

## The Load Function

```python
def load_employees(file_path):
    if not file_path.exists():
        print("No employee file found. Starting with an empty list.")
        return []

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)
```

The function first checks:

```python
file_path.exists()
```

This returns:

- `True` when the file exists
- `False` when the file does not exist

The condition:

```python
if not file_path.exists():
```

means:

> If the file does not exist, return an empty employee list.

Returning:

```python
[]
```

allows the application to continue with zero saved employees instead of crashing with `FileNotFoundError`.

## Default Employee Records

The program uses default employees only when nothing was loaded:

```python
loaded_employees = load_employees(file_path)

if not loaded_employees:
    loaded_employees = employees
    save_employees(file_path, loaded_employees)
```

An empty list is treated as false by Python.

Therefore:

```python
if not loaded_employees:
```

means:

> If the loaded list contains no employee records, use and save the default records.

Existing records are not overwritten.

## Saving EMP003 Permanently

The program created a new dictionary:

```python
new_employee = {
    "employee_id": "EMP003",
    "name": "Roxell",
    "department": "Human Resources",
}
```

It searched the loaded list before adding the record:

```python
employee_exists = False

for employee in loaded_employees:
    if employee["employee_id"] == new_employee["employee_id"]:
        employee_exists = True
        break
```

If EMP003 was missing, the program added and saved it:

```python
loaded_employees.append(new_employee)
save_employees(file_path, loaded_employees)
```

During the second program run, EMP003 was loaded from `employees.json`. This proved that the record persisted after the first Python process ended.

## Missing-File Test

A temporary filename was used:

```python
employees_test.json
```

During the first run:

```text
File missing
→ load_employees() returned []
→ default employees were used
→ employees_test.json was created
```

During the second run:

```text
File existed
→ saved employees were loaded
→ no new default file was required
```

This demonstrated how a new installation can start safely without an existing data file.

## Important Distinctions

```text
Python program      → instructions currently executing
Python list         → temporary in-memory collection
JSON file           → persistent data stored on the computer
json.dump()         → saves Python data to JSON
json.load()         → loads JSON into Python
"w"                 → write and replace file contents
"r"                 → read file contents only
[]                  → empty list with zero records
```

## Day 11 Accomplishments

- Created an employee JSON file
- Saved a list of employee dictionaries
- Loaded JSON data into Python
- Displayed loaded employee records
- Created reusable save and load functions
- Used `pathlib` to locate the data file
- Handled a missing data file safely
- Avoided automatically overwriting existing records
- Prevented duplicate EMP003 records
- Confirmed that EMP003 survived a program restart

## Important Security and Cost Note

JSON storage is completely local and free.

It does not require:

- A credit card
- A paid API
- Cloud hosting
- A paid database
- An API key

The employee data is stored in a local file on the computer.

## Personal Reflection

Day 11 changed the Employee Management System from a temporary program into the beginning of a persistent business application.

The system can now retain employee records after it closes. This is an essential step toward databases, APIs, automation workflows, and future local AI features.