# Day 69 Summary — Authentication and Password-Security Foundation

## Goal

Begin user authentication by creating a tested user-account model, SQLite users table, and secure password-hashing and verification functions.

Console login is not connected yet. Day 69 focused on building and testing the security foundation first.

## What Was Added

### User-Account Model

Added `UserAccount` to `models.py`:

```python
class UserAccount(TypedDict):
    user_id: int
    username: str
    password_hash: str
    role: str
    is_active: bool
```

The fields represent:

- `user_id`: unique account number
- `username`: name used during login
- `password_hash`: protected password result
- `role`: account permission level
- `is_active`: whether the account is allowed to log in

### SQLite Users Table

Updated `initialize_database()` to create a `users` table with:

- Automatically generated user IDs
- Case-insensitive unique usernames
- Required password hashes
- Controlled `admin` and `viewer` roles
- Active accounts by default
- Checks that allow only `0` or `1` for active status

Important SQLite rules:

```text
COLLATE NOCASE → Dennis and dennis are treated as equal
UNIQUE         → duplicate usernames are rejected
CHECK          → only approved role and status values are accepted
DEFAULT 1      → new accounts begin active
```

### Password Hashing

Created `authentication.py` using:

```text
PBKDF2-HMAC-SHA256
600,000 iterations
16 random salt bytes
```

Passwords are stored in this structure:

```text
algorithm$iterations$salt$password_hash
```

Example:

```text
sha256$600000$32-character-salt$64-character-hash
```

The original password is never stored.

### Random Password Salts

Every password receives a unique random salt.

This means identical passwords produce different stored hashes:

```text
Same password + Salt A → Hash A
Same password + Salt B → Hash B
```

This prevents someone who obtains the database from easily identifying accounts that use the same password.

### Password Verification

Added `verify_password()` to:

1. Separate the stored password hash into four parts.
2. Convert the iteration count back into an integer.
3. Convert the salt and expected hash from hexadecimal text into bytes.
4. Recalculate a hash from the entered password.
5. Securely compare the calculated hash with the stored hash.
6. Return `True` for a correct password.
7. Return `False` for an incorrect password or malformed data.

The function uses `hmac.compare_digest()` for secure comparison.

## Tests Added

Four database tests verify that:

- The `users` table is created.
- Usernames are unique regardless of capitalization.
- Unsupported account roles are rejected.
- New accounts are active by default.

Five authentication tests verify that:

- Password hashes use the expected storage format.
- The original password is not stored.
- Identical passwords create different hashes.
- Correct passwords are accepted.
- Incorrect passwords are rejected.
- Malformed stored password hashes are rejected safely.

Some related behaviors are checked together, producing five authentication tests in total.

## Test Results

The complete suite now contains:

```text
58 existing core tests
25 database tests
1 database-backup command test
2 database-restoration command tests
3 migration tests
10 console-integration tests
6 storage-verification tests
9 repository tests
5 authentication tests
```

Total:

```text
Ran 119 tests
OK
All automated tests passed.
```

## Concepts Practiced

- User-account data modeling
- Python `TypedDict`
- SQLite table creation
- Automatically generated primary keys
- Case-insensitive username comparison
- Unique database constraints
- Role and active-status checks
- Boolean values in SQLite
- Default database values
- Password hashing
- PBKDF2-HMAC-SHA256
- Random password salts
- Password-hashing work factors
- Byte and hexadecimal conversion
- Structured password-hash storage
- Secure hash comparison
- Exception handling for malformed hashes
- Authentication regression testing

## Business Value

The authentication foundation protects employee information by:

- Never storing plain-text passwords
- Making automated password guessing more expensive
- Giving every password unique protection
- Rejecting duplicate usernames
- Controlling account roles
- Supporting account disabling
- Rejecting damaged authentication data safely

## Current Limitation

Users cannot log in through the console yet.

The next authentication milestone is to add tested user-account creation and retrieval before connecting login prompts and role-based permissions to the console application.

## References

- Python `hashlib` documentation:
  https://docs.python.org/3/library/hashlib.html
- Python `hmac.compare_digest` documentation:
  https://docs.python.org/3/library/hmac.html#hmac.compare_digest
- OWASP Password Storage Cheat Sheet:
  https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html