# Day 70 Summary — SQLite User-Account Registration and Retrieval

## Goal

Build the user-account data layer and service layer needed before connecting authentication to the console application.

The system must:

- Create user accounts in SQLite
- Store protected password hashes instead of plain passwords
- Retrieve accounts using case-insensitive usernames
- Reject duplicate usernames safely
- Keep database responsibilities separate from business logic
- Verify every behavior with temporary test databases

## What Was Added

### SQLite User-Account Insertion

The following function was added to `database.py`:

```python
def insert_user_account(
    username: str,
    password_hash: str,
    role: str,
    database_file: Path = DATABASE_FILE,
) -> bool:
```

This function:

1. Initializes the database and required tables.
2. Opens a SQLite connection.
3. Inserts the username, password hash, and role.
4. Commits the transaction after a successful insertion.
5. Returns `True` when the account is saved.
6. Rolls back and returns `False` when SQLite rejects the record.
7. Always closes the database connection with `finally`.

The function receives a password hash rather than a plain password. This keeps password-security responsibilities outside the database layer.

### Duplicate-Username Protection

The `users.username` column uses:

```sql
COLLATE NOCASE
```

This makes username comparisons case-insensitive.

For example:

- `Dennis`
- `dennis`
- `DENNIS`

are treated as the same username.

The database’s `UNIQUE` constraint rejects duplicate usernames. `insert_user_account()` catches the resulting `sqlite3.IntegrityError`, rolls back the transaction, and returns `False`.

The original account remains unchanged.

### Case-Insensitive User Retrieval

The following function was added to `database.py`:

```python
def load_user_account_by_username(
    username: str,
    database_file: Path = DATABASE_FILE,
) -> UserAccount | None:
```

This function:

1. Initializes the database.
2. Opens a SQLite connection.
3. Configures `sqlite3.Row` so columns can be accessed by name.
4. Searches for the requested username.
5. Returns a complete `UserAccount` dictionary when found.
6. Returns `None` when no matching account exists.
7. Converts SQLite’s integer `is_active` value into a Python Boolean.
8. Always closes the connection.

Because the username column uses `COLLATE NOCASE`, searching for `dennis` can retrieve an account stored as `Dennis`.

### User-Service Layer

A new file was created:

```text
Projects/employee_management_system/user_service.py
```

It contains:

```python
def register_user_account(
    username: str,
    password: str,
    role: str,
    database_file: Path = DATABASE_FILE,
) -> bool:
```

This service function connects password security to database storage.

Its flow is:

```text
Plain password
      ↓
hash_password()
      ↓
Protected password hash
      ↓
insert_user_account()
      ↓
SQLite users table
```

The service receives the plain password from the application but never sends that plain password to the database function.

Instead, it:

1. Calls `hash_password(password)`.
2. Receives the protected storage string.
3. Sends the password hash to `insert_user_account()`.
4. Returns the database operation’s `True` or `False` result.

## Separation of Responsibilities

The new design gives each module one main responsibility.

### `authentication.py`

Responsible for:

- Creating random password salts
- Hashing passwords with PBKDF2-HMAC-SHA256
- Verifying submitted passwords safely

### `database.py`

Responsible for:

- Creating the `users` table
- Inserting user-account records
- Retrieving stored accounts
- Enforcing database constraints
- Managing commits, rollbacks, and connections

### `user_service.py`

Responsible for:

- Coordinating account registration
- Protecting the password before database storage
- Keeping the application away from low-level SQL details

This separation makes the system easier to test, maintain, and extend.

## Tests Added

Six new automated tests were added during Day 70.

### Database Tests

1. `test_insert_user_account_saves_protected_record`

   Confirms that SQLite saves the username, protected hash, role, generated user ID, and default active status.

2. `test_insert_user_account_rejects_duplicate_username`

   Confirms that usernames differing only by letter case are treated as duplicates and that only one account remains stored.

3. `test_load_user_account_by_username_returns_account`

   Confirms that a case-insensitive lookup returns the complete typed user-account dictionary.

4. `test_load_user_account_returns_none_when_missing`

   Confirms that a missing username returns `None` safely.

### User-Service Tests

5. `test_register_user_account_hashes_password_before_storage`

   Confirms that:

   - Registration succeeds
   - The account can be retrieved
   - The plain password is not stored
   - The stored hash still verifies the correct password

6. `test_register_user_account_rejects_duplicate_username`

   Confirms that:

   - The first account is registered successfully
   - A case-insensitive duplicate is rejected
   - The original account is not overwritten
   - The original role remains unchanged
   - The original password still verifies correctly

## Temporary Test Databases

The tests use:

```python
with TemporaryDirectory() as temporary_directory:
```

Each test creates an isolated SQLite database inside a temporary directory.

This protects the real application database because:

- Test accounts are not written to production data
- Duplicate-account tests cannot damage real users
- Each test starts with a clean database
- Temporary files are removed automatically after the test

## Test Results

The complete automated test suite passed:

```text
Ran 125 tests

OK

All automated tests passed.
```

The test count increased from 119 to 125.

The updated breakdown is:

- 58 existing core tests
- 29 database tests
- 1 database-backup command test
- 2 database-restoration command tests
- 3 migration tests
- 10 console-integration tests
- 6 storage-verification tests
- 9 repository tests
- 5 authentication tests
- 2 user-service tests

Total:

```text
125 automated tests
```

## Concepts Practiced

- Service-layer design
- Separation of responsibilities
- SQLite account insertion
- Parameterized SQL statements
- Transactions and commits
- Rollbacks after integrity errors
- `sqlite3.IntegrityError`
- Database uniqueness constraints
- Case-insensitive username handling
- Retrieving rows with `sqlite3.Row`
- Converting SQLite integers to Python Booleans
- Returning `None` for missing records
- Password hashing before storage
- Integration testing across multiple modules
- Temporary database isolation
- Protecting original records from duplicate updates
- Testing successful and failed business workflows

## Business Value

The application can now create and retrieve protected user accounts without storing plain passwords.

This provides the data foundation needed for:

- Secure application login
- Administrator and viewer roles
- Disabled-account enforcement
- Future access-control rules
- Auditable user-account management
- Safer authentication development

## Current Limitation

User accounts can be created and retrieved, but users still cannot log in through the console.

The application does not yet combine:

- Username lookup
- Password verification
- Active-account checking
- Login success or rejection

## Next Step

The next authentication milestone is to create a tested credential-authentication function that:

1. Loads an account by username.
2. Rejects a missing account.
3. Rejects an inactive account.
4. Verifies the submitted password.
5. Returns the authenticated account only when every check succeeds.