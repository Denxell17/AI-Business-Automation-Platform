# Day 52 — Loading Employee Records from SQLite

## Goal

Implement the SQLite read operation by loading employee records from the `employees` table.

## Business Purpose

The Employee Management System must be able to retrieve stored employee information. Reading records is the second SQLite CRUD operation:

- Create — completed on Day 51
- Read — completed on Day 52
- Update — next
- Delete — later

JSON remains the active application storage until the SQLite CRUD operations and migration process are complete.

## Loading Employees

The new function is:

```python
load_employees_from_database()
```

It:

- Opens a connection to the selected database
- Executes a `SELECT` query
- Retrieves all employee rows
- Orders the rows by employee ID
- Closes the database connection
- Converts each row into an `Employee` dictionary
- Returns a list of employees

## SQL SELECT

`SELECT` reads information from a database table.

```sql
SELECT employee_id, name, salary
FROM employees
```

Unlike `INSERT`, `UPDATE`, and `DELETE`, a `SELECT` query does not modify stored records.

## Fetching All Rows

```python
rows = connection.execute(query).fetchall()
```

`fetchall()` returns all rows produced by the query.

If no employees exist, it returns an empty list-like result. The function then returns:

```python
[]
```

## Row Factory

The connection uses:

```python
connection.row_factory = sqlite3.Row
```

Without a row factory, values are normally accessed by position:

```python
row[0]
row[1]
```

With `sqlite3.Row`, values can be accessed by database column name:

```python
row["employee_id"]
row["name"]
row["salary"]
```

Named access is clearer and less dependent on the order of columns in the query.

## Row Conversion

A `sqlite3.Row` belongs to SQLite. The rest of the application expects an `Employee` dictionary.

Each row is therefore converted:

```python
employee: Employee = {
    "employee_id": row["employee_id"],
    "name": row["name"],
    "salary": row["salary"],
}
```

The complete function maps all twelve employee fields.

This is not JSON conversion. It creates normal Python dictionaries that match the `Employee` type.

## Predictable Ordering

The query includes:

```sql
ORDER BY employee_id
```

This returns employees in a predictable order and makes application behavior and automated tests consistent.

## Connection Cleanup

The connection is closed in `finally`:

```python
finally:
    connection.close()
```

The fully fetched rows remain available after the connection closes, allowing the function to convert them safely.

## Automated Tests

Two tests were added:

1. An empty employee table returns `[]`.
2. A saved employee is loaded with all fields unchanged.

The tests use temporary databases, so the real `data/employees.db` file remains unchanged.

## Test Result

```text
Ran 63 tests
OK
All automated tests passed.
```

## Key Concepts Practiced

- SQLite `SELECT`
- Reading database records
- `fetchall()`
- `sqlite3.Row`
- Accessing columns by name
- Converting database rows into typed dictionaries
- Returning an empty list
- Ordering query results
- Temporary database testing

## Next Milestone

Day 53 will implement the SQLite update operation for existing employee records.