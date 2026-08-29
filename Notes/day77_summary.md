# Day 77 Summary — Secure Viewer Password-Reset Foundations

## Goal

Build the database and business-service foundations for an administrator-controlled viewer password-reset workflow.

Day 77 was intentionally limited to:

- Replacing a saved password hash in SQLite
- Applying password-reset security rules in the service layer
- Protecting administrator accounts from this viewer-only workflow
- Preserving the viewer's role and active status
- Testing successful and rejected password-reset situations
- Updating the project documentation

The command layer, interactive prompts, menu option, activity logging, and manual console verification were not added today. Those belong to the next milestone.

## Starting Point

At the beginning of Day 77, the application already supported:

- Secure password hashing and verification
- One initial administrator account
- Administrator-created viewer accounts
- Viewer activation and deactivation
- Role-based permissions
- Default-deny authorization
- Login rejection for inactive accounts
- 179 passing automated tests

The missing feature was a safe way for an authorized administrator to replace a viewer account's forgotten or compromised password.

## Database Password-Hash Update

A new database function was added to `database.py`:

```python
def update_user_account_password_hash(
    username: str,
    password_hash: str,
    database_file: Path = DATABASE_FILE,
) -> bool:
```

Its responsibility is limited to replacing the `password_hash` stored for one user account.

The database function does not receive or process a plain-text password. It receives only the protected hash created by the service layer.

The SQL operation uses parameter placeholders:

```sql
UPDATE users
SET password_hash = ?
WHERE username = ?
```

Using placeholders keeps the values separate from the SQL statement and protects the query from unsafe string construction.

The function:

1. Initializes the database when necessary.
2. Opens a database connection.
3. Executes the parameterized `UPDATE`.
4. Commits the transaction when successful.
5. Checks whether exactly one row was affected.
6. Rolls back if SQLite reports an error.
7. Always closes the database connection.

The result is:

```python
return update_result.rowcount == 1
```

This returns `True` only when exactly one matching account was updated.

It returns `False` when:

- The username does not exist
- No row is updated
- SQLite reports an error

## Database Tests

Two database tests were added.

### Replacing a Saved Password Hash

The first test confirms that:

- A viewer account can be inserted
- Its password hash can be replaced
- The database function returns `True`
- The replacement hash is stored
- The original hash is no longer stored
- The viewer role remains unchanged
- The active status remains unchanged

This proves that password reset changes only the intended database field.

### Rejecting a Missing Username

The second test attempts to update a username that does not exist.

It confirms that:

- The function returns `False`
- No unexpected account is created
- The database remains unchanged

The database test count increased from 33 to 35.

## Password-Reset Business Service

A new service function was added to `user_service.py`:

```python
def reset_viewer_account_password(
    current_user: UserAccount,
    target_username: str,
    new_password: str,
    database_file: Path = DATABASE_FILE,
) -> bool:
```

This function contains the business rules for deciding whether a viewer password reset is allowed.

The service layer performs all security checks before changing the database.

## Security Check 1 — Acting User Must Be Active

The service first checks:

```python
not current_user["is_active"]
```

An inactive administrator cannot manage another account.

Even if the user dictionary still contains the `admin` role, an inactive account is not allowed to perform administrative work.

## Security Check 2 — Acting User Must Have Permission

The service calls:

```python
user_has_permission(
    current_user,
    MANAGE_USER_ACCOUNTS,
)
```

The administrator role contains the `users.manage` permission.

The viewer role does not contain this permission.

Therefore:

- An active administrator may continue
- A viewer is rejected
- An unknown role is rejected by default
- An inactive administrator is rejected

## Security Check 3 — New Password Must Not Be Blank

The service checks:

```python
if not new_password.strip():
    return False
```

The `strip()` method removes whitespace from both ends of the string.

Examples that become empty after `strip()` include:

```python
""
"   "
"\t"
```

An empty or whitespace-only password is rejected before hashing or database access continues.

## Security Check 4 — Target Account Must Exist

The target account is loaded with:

```python
target_user = load_user_account_by_username(
    target_username,
    database_file,
)
```

If the result is `None`, the requested account does not exist and the service returns `False`.

This prevents the password-reset workflow from appearing to succeed when no account was updated.

## Security Check 5 — Target Must Be a Viewer

The service checks:

```python
if target_user["role"] != "viewer":
    return False
```

This workflow is specifically for viewer accounts.

It cannot reset an administrator password.

The application currently creates only one administrator through the initial-administrator setup. The service still checks the target role as defense in depth.

Defense in depth means protecting the same important rule at more than one layer so that future code changes or direct function calls cannot easily bypass it.

## Security Check 6 — New Password Must Be Different

The service checks the proposed password against the saved password hash:

```python
if verify_password(
    new_password,
    target_user["password_hash"],
):
    return False
```

If verification returns `True`, the proposed password is already the account's current password.

The reset is rejected because replacing a password with the same password provides no security benefit.

This comparison must happen before hashing the new password.

The password-hashing function uses a new random salt each time. Because of that, hashing the same plain-text password twice normally creates two different hash strings. Comparing two hash strings directly would therefore not reliably detect password reuse.

`verify_password()` correctly determines whether the new plain-text password matches the existing protected hash.

## Delayed Password Hashing

Only after every validation succeeds does the service hash the new password:

```python
new_password_hash = hash_password(new_password)
```

This is delayed intentionally.

The application avoids performing expensive password hashing when the request has already failed because of:

- Missing permission
- Inactive administrator
- Blank password
- Missing target
- Administrator target
- Reused password

The newly created hash is then passed to the database:

```python
return update_user_account_password_hash(
    target_username,
    new_password_hash,
    database_file,
)
```

The plain-text password is never passed to the database layer.

## Inactive Viewer Policy

An active administrator is allowed to reset the password of an inactive viewer account.

Password status and account active status are separate controls:

- The password determines whether the credential is correct
- `is_active` determines whether login is currently allowed

Resetting an inactive viewer's password does not automatically reactivate the account.

The viewer remains inactive until an administrator uses the separate account-status workflow to reactivate it.

This separation avoids accidentally restoring access during a password reset.

## Service Tests

Eight service tests were added.

### Administrator Can Reset Viewer Password

This test confirms that:

- An active administrator can reset a viewer password
- The old password stops working
- The new password works
- The account remains a viewer
- The active status remains unchanged

### Viewer Cannot Reset Viewer Password

This test confirms that a viewer lacks the `users.manage` permission.

The reset returns `False`, the original password continues working, and the proposed replacement password does not work.

### Inactive Administrator Cannot Reset Viewer Password

This test confirms that an administrator marked inactive cannot perform the reset even though the account still has the `admin` role.

### Administrator Cannot Reset Administrator Password

This test targets the existing administrator account.

The reset returns `False` because the target role is not `viewer`.

This protects the single administrator account from being modified through the viewer-only reset workflow.

### Administrator Cannot Reset Missing Viewer Password

This test uses a username that does not exist.

The service returns `False` and does not create a new account.

### Administrator Cannot Reset Viewer to Blank Password

This test supplies a whitespace-only password.

The service returns `False`, and the viewer's original password remains valid.

### Administrator Cannot Reuse Viewer Current Password

This test supplies the viewer's existing password as the proposed new password.

The service returns `False`, and the saved password hash remains unchanged.

### Administrator Can Reset Inactive Viewer Password

This test first deactivates the viewer and then resets the password.

It confirms that:

- The password reset succeeds
- The old password is rejected
- The new password matches the saved hash
- The viewer remains inactive
- The reset does not automatically restore login access

The user-service test count increased from 19 to 27.

## Full Regression Test

The complete automated test suite was run from the main project folder:

```powershell
& C:\Users\user\AppData\Local\Python\pythoncore-3.14-64\python.exe -m unittest discover -s Projects\employee_management_system\tests -t Projects\employee_management_system -v
```

Result:

```text
Ran 189 tests in 5.912s

OK
```

Day 77 added 10 tests:

- 2 database tests
- 8 user-service tests

The previous 179 tests also continued to pass.

This confirms that the new password-reset foundation did not break existing employee management, authentication, authorization, account-status management, backup, restoration, repository, storage, reporting, or console behavior.

## README Updates

The README now documents:

- The tested database and service foundations for viewer password reset
- Active-administrator authorization
- Viewer-only target protection
- Missing-account rejection
- Administrator-target rejection
- Blank-password rejection
- Current-password reuse detection
- Password-hash replacement
- Role and active-status preservation
- The increase from 179 to 189 automated tests
- The command-layer and console workflow as the next milestone

The README carefully avoids claiming that password reset is already available through the interactive menu.

## Files Changed

Day 77 changed:

```text
Projects/employee_management_system/database.py
Projects/employee_management_system/tests/test_database.py
Projects/employee_management_system/user_service.py
Projects/employee_management_system/tests/test_user_service.py
README.md
Notes/day77_summary.md
```

## Important Lessons

### Database Layer

The database layer performs storage operations.

It receives a protected password hash and updates the matching row.

It does not decide who is authorized to request the change.

### Service Layer

The service layer contains the business rules.

It decides:

- Who may request the reset
- Which account roles may be targeted
- Which password values are unacceptable
- When hashing should happen
- When the database update may proceed

### Authentication and Authorization

Authentication answers:

> Is this user really who they claim to be?

Authorization answers:

> Is this authenticated user allowed to perform this action?

Password reset requires authorization because changing another user's credential is an account-management action.

### Returning `False`

The service returns `False` for every rejected or unsuccessful reset.

Possible reasons include:

- Acting account is inactive
- Acting account lacks permission
- New password is blank
- Target account does not exist
- Target account is an administrator
- New password matches the current password
- The database update fails

The command layer added in a future milestone will convert this Boolean result into a user-facing success or failure message.

## Day 77 Result

Day 77 successfully created a secure, tested foundation for administrator-controlled viewer password resets.

The application can now safely replace a viewer's stored password hash while enforcing authorization, target-role protection, password validation, password-reuse protection, and status preservation.

The feature is not yet exposed in the interactive console.

## Next Milestone

Add a tested command-layer and interactive-console workflow for administrator-controlled viewer password resets.

That future work will include:

- Hidden new-password entry
- Password confirmation
- Required-input validation
- Calling the tested service function
- Clear success and failure messages
- Administrator-only menu authorization
- Success-only activity logging
- Console and command-layer tests
- Manual end-to-end verification