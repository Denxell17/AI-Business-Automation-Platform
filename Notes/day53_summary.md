# Day 53 — Updating Employee Records in SQLite

## Goal

Implement the SQLite Update operation for existing employee records.

## Business Purpose

Employee information changes over time. The application must be able to save changes such as:

- New position
- New department
- Salary adjustment
- Updated contact information
- Employment-status change
- New performance score

The employee ID identifies which existing record should be updated.

## Update Function

The new function is:

```python
update_employee_in_database()
```

It:

- Accepts a complete `Employee` dictionary
- Connects to SQLite
- Updates the matching employee
- Commits the transaction
- Returns `True` when a record was found
- Returns `False` when the employee ID was not found
- Always closes the connection

## SQL UPDATE

The `UPDATE` command changes an existing database record:

```sql
UPDATE employees
SET
    position = ?,
    salary = ?
WHERE employee_id = ?
```

The values following `SET` are changed. The `WHERE` condition identifies the record that receives those changes.

## WHERE Condition

```sql
WHERE employee_id = ?
```

`WHERE` means:

> Only apply the update to records matching this condition.

Without `WHERE`, SQLite would update every employee in the table. This could cause serious data loss.

## Employee ID

The function does not change `employee_id`. It uses the ID to locate the existing employee:

```python
employee["employee_id"]
```

This value appears last in the Python tuple because it matches the final placeholder in:

```sql
WHERE employee_id = ?
```

SQL placeholder values must be in the same order as their corresponding `?` placeholders.

## Affected-Row Count

After executing the update, SQLite provides:

```python
cursor.rowcount
```

This reports how many rows matched the update.

The function returns:

```python
cursor.rowcount > 0
```

Therefore:

- One matching employee → `True`
- No matching employee → `False`

## Transactions

```python
connection.commit()
```

`commit()` permanently saves the updated information. Without it, the database may discard the changes when the connection closes.

## Missing Employees

SQL `UPDATE` does not create a new row when the employee ID is missing.

The function returns:

```python
False
```

The database remains unchanged.

## Automated Tests

Two update tests were added:

1. An existing employee is updated successfully.
2. A missing employee returns `False` and is not created.

The successful-update test loads the record afterward to prove the changes were persisted.

All tests use temporary databases, so the real `data/employees.db` file remains unchanged.

## Test Result

```text
Ran 65 tests
OK
All automated tests passed.
```

## SQLite CRUD Progress

- Create — complete
- Read — complete
- Update — complete
- Delete — next

## Key Concepts Practiced

- SQL `UPDATE`
- SQL `SET`
- SQL `WHERE`
- Parameter order
- `cursor.rowcount`
- Database transactions
- Persisting updates with `commit()`
- Handling missing records
- Testing stored changes

## Next Milestone

Day 54 will implement deletion of employee records from SQLite.