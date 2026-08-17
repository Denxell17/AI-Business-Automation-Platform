# Day 50 Summary — Begin SQLite Database Integration

## Goal

Begin moving employee storage from JSON toward a structured SQLite database without changing the application’s current JSON behavior.

## Why SQLite?

SQLite is:

- Included with Python
- Free and local
- Stored in a single file
- Suitable for learning database operations
- Useful for small and medium applications

SQLite data is persistent when stored in a normal database file. Temporary databases are used only during automated tests.

## Database Module

Created:

```text
Projects/employee_management_system/database.py
```

## Database Path

```python
DATA_DIRECTORY = Path(__file__).with_name("data")
DATABASE_FILE = DATA_DIRECTORY / "employees.db"
```

The database is stored inside the existing `data` directory.

## Database Connection

Created a reusable connection function:

```python
def get_database_connection(
    database_file: Path = DATABASE_FILE,
) -> sqlite3.Connection:
    return sqlite3.connect(database_file)
```

It returns a `sqlite3.Connection` object that can execute SQL commands.

## Employee Table

Created `initialize_database()` to build the employee table:

```sql
CREATE TABLE IF NOT EXISTS employees (
    employee_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    position TEXT NOT NULL,
    country TEXT NOT NULL,
    salary INTEGER NOT NULL,
    email TEXT NOT NULL,
    phone_number TEXT NOT NULL,
    years_of_experience INTEGER NOT NULL,
    company TEXT NOT NULL,
    employment_status TEXT NOT NULL,
    performance_score INTEGER NOT NULL
)
```

## Important SQL Concepts

### `IF NOT EXISTS`

Creates the table only when it does not already exist.

### `PRIMARY KEY`

```sql
employee_id TEXT PRIMARY KEY
```

The employee ID uniquely identifies one employee record. Duplicate primary-key values are not allowed.

### `NOT NULL`

Requires the column to contain a value.

### `commit()`

```python
connection.commit()
```

Permanently saves the database changes.

### `finally`

```python
finally:
    connection.close()
```

Ensures the connection is closed even when an error occurs.

## Git Protection

Added the generated database to `.gitignore`:

```gitignore
Projects/employee_management_system/data/employees.db
```

Employee database records should not be committed to GitHub.

## Testing

Created:

```text
tests/test_database.py
```

The test initializes a temporary database and checks that the `employees` table exists.

Using a temporary database protects the real employee data and automatically removes test data afterward.

All 59 automated tests passed.

## Current Migration Status

The application still uses JSON for active employee storage. SQLite integration has started safely with:

- A reusable connection function
- A complete employee-table schema
- Temporary database testing

The next step is saving employee records to SQLite.