# Day 72 Summary — Secure Initial-Administrator Setup Command

## Goal

Create a safe, tested, one-time command for registering the first SQLite administrator account.

The setup process must:

- Check whether user accounts already exist
- Allow setup only when the users table is empty
- Force the first account to use the `admin` role
- Hash the password before storage
- Hide password entry in the terminal
- Require matching password confirmation
- Reject missing required information
- Report success and failure through process exit codes
- Protect the real database with a fresh backup before setup

## What Was Added

### User-Account Counting

The following database function was added to `database.py`:

```python
def count_user_accounts(
    database_file: Path = DATABASE_FILE,
) -> int:
    initialize_database(database_file)
    connection = get_database_connection(database_file)

    try:
        stored_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM users
            """
        ).fetchone()

        return stored_count[0]
    finally:
        connection.close()
```

This function:

1. Initializes the SQLite database and users table.
2. Opens a database connection.
3. Uses `SELECT COUNT(*)` to count every user record.
4. Retrieves the count from the first column of the returned row.
5. Returns `0` when no user accounts exist.
6. Always closes the connection with `finally`.

### Why Account Counting Is Needed

The initial administrator setup must work only once.

The service checks:

```text
Number of existing accounts = 0
              ↓
Initial setup is allowed
```

If the count is greater than zero:

```text
Number of existing accounts != 0
              ↓
Initial setup is rejected
```

This prevents the setup command from becoming an unrestricted method for creating administrator accounts.

## Initial-Administrator Business Logic

The following function was added to `user_service.py`:

```python
def register_initial_administrator(
    username: str,
    password: str,
    database_file: Path = DATABASE_FILE,
) -> bool:
    existing_account_count = count_user_accounts(
        database_file
    )

    if existing_account_count != 0:
        return False

    return register_user_account(
        username,
        password,
        "admin",
        database_file,
    )
```

This function:

1. Counts the existing user accounts.
2. Returns `False` when any account already exists.
3. Uses a fixed role of `"admin"`.
4. Sends the username and password through `register_user_account()`.
5. Relies on the existing service to hash the password.
6. Returns `True` only when the administrator is stored successfully.

The caller cannot choose another role for the initial account because `"admin"` is assigned inside the function.

## New Administrator Setup Command

A new file was created:

```text
Projects/employee_management_system/admin_setup.py
```

This file is the command layer for initial-administrator creation.

### Command Wrapper

The wrapper function is:

```python
def run_initial_administrator_setup(
    username: str,
    password: str,
    database_file: Path = DATABASE_FILE,
) -> bool:
    setup_succeeded = register_initial_administrator(
        username,
        password,
        database_file,
    )

    if not setup_succeeded:
        print("Initial administrator account was not created.")
        return False

    print("Initial administrator account created successfully.")
    return True
```

It:

- Sends the supplied information to the business layer
- Prints a success or failure message
- Returns the service result
- Keeps user-facing messages outside the database and service layers

## Application Layers

The administrator setup now uses three separated layers.

### Database Layer

File:

```text
database.py
```

Responsibilities:

- Count stored user accounts
- Insert user records
- Execute SQL
- Manage database connections and transactions

### Business or Service Layer

File:

```text
user_service.py
```

Responsibilities:

- Decide whether initial setup is allowed
- Force the first account to use the administrator role
- Protect the password before storage
- Reject setup after an account exists

### Command Layer

File:

```text
admin_setup.py
```

Responsibilities:

- Collect terminal input
- Hide password entry
- Confirm the password
- Display success or failure messages
- Return process exit codes

The flow is:

```text
Administrator setup command
             ↓
User-service business rules
             ↓
SQLite database operations
             ↓
Command displays the result
```

## Secure Password Entry

The command imports:

```python
from getpass import getpass
```

`getpass()` works similarly to `input()`, but it does not display password characters in the terminal.

The command collects two password entries:

```python
password = getpass(
    "Initial administrator password: "
)
password_confirmation = getpass(
    "Confirm initial administrator password: "
)
```

The user must enter the same password twice.

The terminal does not display:

- The password characters
- Asterisks
- The stored password hash

## Required-Input Validation

The command checks:

```python
if not username or not password:
    print("Administrator username and password are required.")
    return 1
```

The username is cleaned first:

```python
username = input(
    "Initial administrator username: "
).strip()
```

For example:

```python
"   ".strip()
```

becomes:

```python
""
```

An empty string is falsy, so:

```python
not username
```

becomes:

```python
True
```

The command then stops before calling the setup service.

## Password Confirmation

The command checks:

```python
if password != password_confirmation:
    print("Administrator passwords do not match.")
    return 1
```

If the two hidden entries differ:

- Setup stops immediately
- The service is not called
- The database is not changed
- Exit code `1` is returned

## Process Exit Codes

The interactive function returns an integer:

```python
def main() -> int:
```

It returns:

```text
0 → setup completed successfully
1 → setup was rejected or failed
```

The main guard uses:

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

This calls `main()`, ends the program, and sends its result to the operating system.

Without `SystemExit`, the return value from `main()` would not automatically become the process exit code.

## Mocked Interactive Input

The tests safely replace terminal functions.

### Mocked Username Input

```python
@patch("builtins.input")
```

This prevents the test from waiting for real keyboard input.

### Mocked Password Input

```python
@patch("admin_setup.getpass")
```

This supplies hidden-password values without prompting the person running the tests.

### Mocked Printed Output

```python
@patch("builtins.print")
```

This records success and failure messages without displaying them normally.

### Mocked Setup Service

```python
@patch("admin_setup.run_initial_administrator_setup")
```

This tests the interactive command without creating or changing a real SQLite account.

## Tests Added

Nine tests were added during Day 72.

### Database Test

1. `test_count_user_accounts_returns_current_total`

   Confirms that an empty users table returns `0` and a table with one account returns `1`.

### User-Service Tests

2. `test_register_initial_administrator_creates_first_account`

   Confirms that the first account is created with the `admin` role, active status, and a verifiable password hash.

3. `test_register_initial_administrator_rejects_second_account`

   Confirms that a second setup attempt returns `False` and does not create another administrator.

### Administrator Command Tests

4. `test_successful_initial_administrator_setup`

   Confirms that a successful service result prints the success message and returns `True`.

5. `test_failed_initial_administrator_setup`

   Confirms that a failed service result prints the failure message and returns `False`.

6. `test_main_returns_zero_after_successful_setup`

   Confirms that valid matching input calls setup and returns exit code `0`.

7. `test_main_rejects_missing_username`

   Confirms that a whitespace-only username is rejected before setup is called.

8. `test_main_rejects_mismatched_passwords`

   Confirms that different password entries return exit code `1` without calling setup.

9. `test_main_returns_one_when_setup_fails`

   Confirms that valid input followed by a service-level rejection returns exit code `1`.

## Test Results

The complete automated suite passed:

```text
Ran 138 tests

OK

All automated tests passed.
```

The count increased from 129 to 138.

The updated breakdown is:

- 58 existing core tests
- 30 database tests
- 6 administrator-setup command tests
- 1 database-backup command test
- 2 database-restoration command tests
- 3 migration tests
- 10 console-integration tests
- 6 storage-verification tests
- 9 repository tests
- 5 authentication tests
- 8 user-service tests

Total:

```text
138 automated tests
```

## Real Database Setup

Before changing the real SQLite database, a fresh backup was created:

```text
SQLite database backup completed successfully.
```

The first setup attempt was safely rejected