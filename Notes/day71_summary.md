# Day 71 Summary — Credential Authentication and Active-Account Enforcement

## Goal

Build and test the service-layer function that authenticates a user account.

The authentication process must:

- Find the account using a case-insensitive username
- Reject a username that does not exist
- Reject an inactive account
- Verify the submitted password securely
- Reject an incorrect password
- Return the complete user account after successful authentication
- Avoid revealing the specific reason authentication failed

## What Was Added

### Credential-Authentication Service

The following function was added to `user_service.py`:

```python
def authenticate_user_account(
    username: str,
    password: str,
    database_file: Path = DATABASE_FILE,
) -> UserAccount | None:
    user_account = load_user_account_by_username(
        username,
        database_file,
    )

    if user_account is None:
        return None

    if not user_account["is_active"]:
        return None

    password_is_correct = verify_password(
        password,
        user_account["password_hash"],
    )

    if not password_is_correct:
        return None

    return user_account
```

This function connects the account-retrieval and password-verification features created during Days 69 and 70.

## Authentication Flow

The function performs its checks in a controlled order:

```text
Submitted username and password
              ↓
Load account from SQLite
              ↓
Does the account exist?
       No → return None
              ↓ Yes
Is the account active?
       No → return None
              ↓ Yes
Does the password match?
       No → return None
              ↓ Yes
Return the authenticated UserAccount
```

## Step-by-Step Explanation

### Load the Account

```python
user_account = load_user_account_by_username(
    username,
    database_file,
)
```

This searches SQLite using the submitted username.

Because the username column uses `COLLATE NOCASE`, usernames are matched without case sensitivity.

For example, a login using:

```text
dennis
```

can retrieve an account stored as:

```text
Dennis
```

### Reject a Missing Account

```python
if user_account is None:
    return None
```

The database function returns `None` when the username does not exist.

Authentication stops immediately because there is no stored account to verify.

### Reject an Inactive Account

```python
if not user_account["is_active"]:
    return None
```

An account with `is_active` set to `False` cannot authenticate, even when the submitted username and password are correct.

This supports future account suspension and access removal without deleting the account’s historical record.

### Verify the Password

```python
password_is_correct = verify_password(
    password,
    user_account["password_hash"],
)
```

The submitted plain password is processed using the salt and settings stored inside the protected password-hash string.

The plain password is not compared directly and is never stored in SQLite.

### Reject an Incorrect Password

```python
if not password_is_correct:
    return None
```

When password verification fails, authentication stops and returns `None`.

### Return the Authenticated Account

```python
return user_account
```

The complete `UserAccount` dictionary is returned only when:

- The username exists
- The account is active
- The password is correct

The returned account includes:

- `user_id`
- `username`
- `password_hash`
- `role`
- `is_active`

The role can later be used for access-control decisions.

## Uniform Authentication Failure

The function returns the same value for these failures:

- Missing username
- Incorrect password
- Inactive account

Each failure returns:

```python
None
```

This is called uniform authentication failure.

It avoids revealing whether:

- A username is registered
- An account has been disabled
- Only the password was incorrect

The interactive console can later display one general message such as:

```text
Invalid username or password, or the account is inactive.
```

## Tests Added

Four user-service tests were added during Day 71.

### Successful Authentication

```python
test_authenticate_user_account_accepts_valid_credentials
```

This test confirms that:

- Registration succeeds
- Username matching is case-insensitive
- The correct password is accepted
- The complete user account is returned
- The correct role is available
- The account is active

### Incorrect-Password Rejection

```python
test_authenticate_user_account_rejects_wrong_password
```

This test confirms that:

- The account exists
- The correct username is submitted
- An incorrect password is rejected
- Authentication returns `None`
- No account information is returned

### Missing-Username Rejection

```python
test_authenticate_user_account_rejects_missing_username
```

This test confirms that:

- Authentication works safely with an empty users table
- An unknown username returns `None`
- SQLite is initialized safely
- The database file is created without creating a user

### Inactive-Account Rejection

```python
test_authenticate_user_account_rejects_inactive_account
```

This test confirms that:

- A user can be registered normally
- The account can be changed to `is_active = 0`
- The correct username and password are still rejected
- Inactive accounts cannot authenticate

## Inactive Test Setup

New accounts are active by default:

```text
is_active = 1
```

The inactive-account test changes the temporary record using:

```sql
UPDATE users
SET is_active = 0
WHERE username = ?
```

The update uses a parameterized username value:

```python
("Dennis",)
```

The connection is managed with:

```python
try:
    connection.execute(...)
    connection.commit()
finally:
    connection.close()
```

The `finally` block guarantees that the SQLite connection closes whether the test setup succeeds or fails.

This direct SQL update is test setup only. It does not yet provide a normal application feature for disabling accounts.

## Temporary Test Databases

Every authentication test uses:

```python
with TemporaryDirectory() as temporary_directory:
```

This provides an isolated SQLite database for each test.

Benefits include:

- Real user accounts are not modified
- Tests do not depend on previous test data
- Inactive-account changes cannot affect production data
- Temporary databases are removed automatically
- Each authentication scenario begins with a known state

## Important Error Corrected

During the incorrect-password test, two adjacent string literals briefly appeared without a separating comma:

```python
"WrongPassword123!"
"admin",
```

Python automatically combines adjacent string literals into:

```python
"WrongPassword123!admin"
```

This would run without a syntax error but would test a different password than intended.

The call was corrected to use the exact three authentication arguments:

```python
authenticated_user = authenticate_user_account(
    "Dennis",
    "WrongPassword123!",
    database_file,
)
```

This reinforced the importance of checking argument order and commas carefully.

## Test Results

The complete automated test suite passed:

```text
Ran 129 tests

OK

All automated tests passed.
```

The test count increased from 125 to 129.

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
- 6 user-service tests

Total:

```text
129 automated tests
```

## Concepts Practiced

- Service-layer authentication
- Case-insensitive username lookup
- Secure password verification
- Active-account enforcement
- Uniform authentication failure
- Early returns
- Returning `UserAccount | None`
- Preventing unnecessary password checks
- Protecting account information
- SQLite Boolean storage using `0` and `1`
- Parameterized SQL updates
- Transaction commits
- Guaranteed connection cleanup with `finally`
- Temporary database isolation
- Positive and negative authentication testing
- Testing successful and rejected workflows
- Detecting accidental adjacent-string concatenation
- Checking whitespace with `git diff --check`

## Business Value

The application now has tested credential-authentication logic.

It can determine whether a submitted username and password belong to an active user without exposing unnecessary account information.

This foundation supports future features such as:

- Interactive console login
- Administrator-only actions
- Viewer permissions
- Account disabling
- Session-level authenticated users
- Activity logs connected to usernames
- Role-based access control

## Current Limitation

Authentication is implemented and tested in the service layer, but it is not connected to the interactive console.

Users are not yet prompted to log in when the application starts.

The project also does not yet have a normal command for creating the initial administrator account.

## Next Step

The next milestone is to:

1. Create a safe command for registering the initial administrator.
2. Prevent duplicate administrator creation.
3. Connect credential authentication to the console startup.
4. Keep the authenticated user available during the program session.
5. Add role-based access checks in later lessons.