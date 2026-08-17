# Day 51 — Saving Employee Records to SQLite

## Goal

Add the first SQLite create operation to the Employee Management System by saving one employee record to the `employees` table.

## Business Purpose

The application needs to move from JSON storage to a structured database gradually. Saving employee records is the first SQLite CRUD operation:

- Create — insert an employee
- Read — load employees
- Update — modify an employee
- Delete — remove an employee

JSON remains the application’s active storage until the SQLite features are complete and tested.

## Database Function

The `insert_employee()` function:

- Accepts an `Employee` dictionary
- Connects to the selected SQLite database
- Inserts all employee fields
- Commits the transaction
- Returns `True` after a successful insertion
- Returns `False` when the employee ID already exists
- Always closes the database connection

## Parameterized SQL

The SQL statement uses `?` placeholders:

```python
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```

The employee values are passed separately as a tuple. This avoids manually joining data into the SQL string and helps prevent SQL injection, quotation errors, and malformed commands.

## Transactions

```python
connection.commit()
```

A database change begins as part of a transaction. `commit()` permanently saves the successful insertion. Without it, SQLite may discard the change when the connection closes.

## Duplicate-ID Protection

`employee_id` is the table’s primary key, so every employee ID must be unique.

Attempting to insert the same ID twice raises:

```python
sqlite3.IntegrityError
```

The function catches this error and returns `False`, allowing the program to handle the duplicate without crashing.

## Resource Cleanup

The connection is closed inside `finally`:

```python
finally:
    connection.close()
```

This guarantees that the connection closes whether the insertion succeeds or encounters an integrity error.

## Automated Tests

Two database tests were added:

1. Verify that an employee is inserted and can be retrieved.
2. Verify that a duplicate employee ID is rejected.

Each test uses `TemporaryDirectory`, so it creates an isolated temporary database and does not modify the real `data/employees.db` file.

## Test Result

```text
Ran 61 tests
OK
All automated tests passed.
```

## Key Concepts Practiced

- SQLite `INSERT INTO`
- Parameterized SQL statements
- Database transactions
- `commit()`
- Primary-key uniqueness
- `sqlite3.IntegrityError`
- Returning success or failure with `bool`
- Closing connections with `finally`
- Testing with temporary databases

## Next Milestone

Day 52 will implement the SQLite read operation: loading employee records from the database.