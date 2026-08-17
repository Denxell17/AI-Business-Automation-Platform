# Day 54 — Deleting Employee Records from SQLite

## Goal

Implement the SQLite Delete operation and complete the basic CRUD operations.

## Business Purpose

When an employee leaves the company or a record must be removed, the application needs to delete that specific employee without affecting anyone else.

The employee ID is enough because it uniquely identifies one employee.

## Delete Function

The new function is:

```python
delete_employee_from_database()
```

It:

- Receives an employee ID
- Connects to SQLite
- Deletes the matching employee
- Commits the change
- Returns `True` when an employee was deleted
- Returns `False` when the employee was not found
- Always closes the connection

## SQL DELETE

```sql
DELETE FROM employees
WHERE employee_id = ?
```

Simple meaning:

- `DELETE` means remove data.
- `FROM employees` means use the `employees` table.
- `WHERE` means apply the command only to matching rows.
- `employee_id = ?` means find the employee with the supplied ID.
- `?` is a safe placeholder for the real value.

Without `WHERE`, the command could delete every employee in the table.

## One-Item Tuple

```python
(employee_id,)
```

This supplies one value for the SQL placeholder.

The comma is required because Python uses the comma to recognize a tuple containing one item.

```python
("EMP001")   # A string inside parentheses
("EMP001",)  # A tuple containing one string
```

## Affected Rows

```python
cursor.rowcount
```

`rowcount` reports how many employee rows were affected by the delete command.

```python
return cursor.rowcount > 0
```

Simple meaning:

- One employee deleted: `1 > 0` becomes `True`
- No employee deleted: `0 > 0` becomes `False`

## Saving the Deletion

```python
connection.commit()
```

`commit()` permanently saves the deletion.

Without `commit()`, SQLite may undo the deletion when the connection closes.

## Closing the Connection

```python
finally:
    connection.close()
```

- `finally` is a Python keyword.
- Its block runs whether the earlier work succeeds or fails.
- `close()` is a connection method that releases the database resource.

## Delete Tests

Two tests were added:

1. An existing employee is deleted successfully.
2. A missing employee ID returns `False`.

The successful-delete test loads employees afterward and expects:

```python
[]
```

This proves that the saved employee was removed.

## Test Assertions

```python
self.assertTrue(result)
```

`assertTrue()` is a `unittest.TestCase` assertion method. It passes when the value is `True`.

```python
self.assertFalse(result)
```

`assertFalse()` passes when the value is `False`.

```python
self.assertEqual(saved_employees, [])
```

`assertEqual()` compares the actual value with the expected value. It passes when they are equal.

## Temporary Testing

```python
with TemporaryDirectory() as temporary_directory:
```

- `with` safely manages a temporary resource.
- `TemporaryDirectory()` creates a temporary folder.
- The folder and test database are removed after the block finishes.
- The real `data/employees.db` file remains unchanged.

## Test Result

```text
Ran 67 tests
OK
All automated tests passed.
```

## SQLite CRUD Progress

- Create — complete
- Read — complete
- Update — complete
- Delete — complete

## Key Concepts Practiced

- SQL `DELETE`
- SQL `WHERE`
- Safe SQL placeholders
- One-item tuples
- `cursor.rowcount`
- Boolean results
- Database transactions
- `commit()`
- Connection cleanup
- Temporary database tests

## Next Milestone

Day 55 will begin migrating existing JSON employee records into SQLite.