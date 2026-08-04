# Day 13 Summary — Complete CRUD Operations

## Day 13 Goal

The goal of Day 13 was to complete the Employee Management System’s CRUD features by adding employee update and deletion operations.

The application can now:

- Create employee records
- Read employee profiles and payroll
- Update existing employees
- Delete employees
- Save every successful change to JSON
- Cancel dangerous deletion operations
- Retain updates and deletions after restarting

## What CRUD Means

CRUD represents the four primary operations performed on business data:

```text
Create → add a new record
Read   → retrieve and display a record
Update → modify an existing record
Delete → remove an existing record
```

In the Employee Management System:

```text
Create → Register Employee
Read   → View Employee Profile and Payroll
Update → Update Employee
Delete → Delete Employee
```

CRUD is used in many business systems, including:

- Employee management
- Customer relationship management
- Inventory management
- Banking
- E-commerce
- Document management

## Expanded Application Menu

The application menu now contains:

```text
1. Register Employee
2. View Employee Profile
3. View Payroll
4. Update Employee
5. Delete Employee
6. Exit
```

Placeholder messages were tested first before implementing update and deletion.

This development process was:

```text
Create menu option
→ test menu routing
→ build function
→ connect function
→ test data persistence
```

## Updating an Employee

The update function receives the complete employee list:

```python
def update_employee(employee_list):
```

It asks for an employee ID and searches for the matching dictionary:

```python
employee = find_employee_by_id(
    employee_list,
    employee_id
)
```

If no matching record exists:

```python
if employee is None:
    print("Employee not found.")
    return False
```

If an employee is found, the program displays the current values and asks for replacements.

## Keeping Existing Values

The update feature accepts blank input:

```python
new_department = input(
    "Enter new department "
    "(press Enter to keep current): "
).strip()
```

The value is updated only when the user enters nonblank text:

```python
if new_department:
    employee["department"] = new_department
```

If the user presses Enter without typing anything:

```python
new_department == ""
```

An empty string is treated as false, so the assignment is skipped. The existing value remains unchanged.

This was tested by:

- Changing Ruth’s department to `SSS`
- Leaving her position blank
- Confirming that the department changed
- Confirming that the old position remained

## Dictionary Mutation

The `employee` returned by the search function refers to the same dictionary stored inside `employees`.

Therefore:

```python
employee["department"] = new_department
```

changes that dictionary inside the list.

The program does not need to append the employee again.

Appending it again would create a duplicate record.

## Returning `True` and `False`

The update function returns:

```python
return True
```

after a successful change.

This tells `run_program()`:

> Employee data was changed and needs to be saved.

The result is stored:

```python
employee_updated = update_employee(employees)
```

Then checked:

```python
if employee_updated:
    save_employees(employees)
```

The complete communication is:

```text
update_employee()
→ employee found and updated
→ return True
→ save employees.json
```

If the employee does not exist:

```text
update_employee()
→ no employee found
→ return False
→ do not save
```

This Boolean return value is a success flag.

## Persistent Updates

Updating the Python list changes temporary memory first.

This line makes the change persistent:

```python
save_employees(employees)
```

The update process is:

```text
Load employees from JSON
→ find the employee
→ change dictionary values
→ save the complete list
→ restart program
→ load the updated values
```

Ruth’s updated department remained `SSS` after restarting, proving the change was stored in `employees.json`.

## Deleting an Employee

The delete function receives the complete list:

```python
def delete_employee(employee_list):
```

It finds the requested employee using the existing search function.

If the employee does not exist:

```python
return False
```

If the employee exists, the program displays identifying information before continuing:

```python
print(f"Employee ID : {employee['employee_id']}")
print(f"Name        : {employee['name']}")
```

## Deletion Confirmation

The application requires explicit confirmation:

```python
confirmation = input(
    "Type YES to confirm deletion: "
).strip().upper()
```

Only this condition permits deletion:

```python
confirmation == "YES"
```

Because `.upper()` is used, all these inputs are accepted:

```text
yes
Yes
YES
```

Any other input cancels deletion:

```python
if confirmation != "YES":
    print("Deletion cancelled.")
    return False
```

This protects employee records from accidental removal.

## Removing an Employee from the List

The deletion operation uses:

```python
employee_list.remove(employee)
```

This removes the matching employee dictionary from the list.

It does not remove every employee. It removes only the dictionary passed to `remove()`.

## Saving a Deletion

Removing an employee from the list changes only temporary memory.

The menu saves after a successful deletion:

```python
employee_deleted = delete_employee(employees)

if employee_deleted:
    save_employees(employees)
```

The full flow is:

```text
Find employee
→ ask for confirmation
→ remove dictionary from list
→ return True
→ save updated list to JSON
```

If deletion is cancelled:

```text
Return False
→ do not save
→ original record remains
```

## Deletion Tests

EMP006 was created as a temporary test employee.

The successful deletion test proved:

```text
Find EMP006
→ type YES
→ remove EMP006
→ save JSON
→ second search returns not found
```

After restarting the application, EMP006 was still missing. This confirmed persistent deletion.

The cancellation test used EMP005:

```text
Find EMP005
→ type no
→ deletion cancelled
→ profile still available
```

This proved that confirmation protects records.

## Case-Insensitive IDs

Employee searches continued to work with different capitalization:

```text
emp005
Emp005
EMP005
```

The search function normalizes IDs using:

```python
.strip().upper()
```

## Day 13 Accomplishments

- Learned the meaning of CRUD
- Expanded the application menu
- Created an employee update function
- Preserved fields when input was blank
- Updated dictionary values inside a list
- Used Boolean success flags
- Saved successful updates to JSON
- Created an employee delete function
- Added explicit deletion confirmation
- Cancelled deletion safely
- Removed employee dictionaries with `remove()`
- Saved successful deletions to JSON
- Verified updates after restarting
- Verified deletion after restarting

## Important Things to Remember

```text
CRUD             → Create, Read, Update, Delete
return True      → operation succeeded
return False     → operation failed or was cancelled
remove()         → removes a matching item from a list
blank input      → keeps the current update value
YES confirmation → permits deletion
save_employees() → persists list changes in JSON
```

## Temporary and Persistent Changes

```text
Change Python list
→ temporary memory only
```

```text
Change Python list
→ call save_employees()
→ change written to employees.json
→ persistent
```

Without saving, an update or deletion would disappear when the program closes.

## Cost and Security Note

The CRUD system uses local JSON storage and remains completely free.

It does not require:

- Paid APIs
- Cloud databases
- Credit cards
- API keys
- Paid hosting

## Personal Reflection

Day 13 completed the Employee Management System’s first full CRUD workflow.

The project now behaves like a real data-management application: it can create, retrieve, modify, and safely remove persistent employee records.