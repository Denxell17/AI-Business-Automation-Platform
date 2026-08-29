# Day 79 Summary — Self-Service Password-Change Foundation

## Goal

Build the service-layer foundation that allows an authenticated user to change their own password after proving knowledge of the current password.

Day 79 was intentionally limited to:

- Self-service password-change business rules
- Current-password verification
- Live SQLite account reloading
- Session-to-database identity matching
- Active-status protection
- Password-reuse rejection
- Secure hash replacement
- Service-level security tests
- README documentation

The command layer, hidden console prompts, menu option, activity logging, and manual end-to-end verification were not added today. Those belong to the next milestone.

## Starting Point

At the beginning of Day 79, the application already supported:

- Secure password hashing and verification
- Credential authentication
- Administrator-controlled viewer password reset
- SQLite password-hash replacement
- Viewer activation and deactivation
- Role-based permissions
- Default-deny menu authorization
- 198 passing automated tests

The missing feature was a secure way for an authenticated user to change their own password.

## Password Reset Versus Password Change

Administrator-controlled password reset and self-service password change are different workflows.

### Administrator-Controlled Reset

The administrator resets a viewer password.

The viewer does not need to provide the current password.

Authorization depends on:

```text
users.manage
```

The target must be a viewer account.

### Self-Service Password Change

The authenticated user changes their own password.

The user must prove knowledge of the current password.

No `users.manage` permission is required because the user is managing their own credential.

Both administrators and viewers may use self-service password change.

## New Service Function

A new function was added to `user_service.py`:

```python
def change_current_user_password(
    current_user: UserAccount,
    current_password: str,
    new_password: str,
    database_file: Path = DATABASE_FILE,
) -> bool:
```

The function returns `True` only when every security rule passes and the saved password hash is successfully replaced.

It returns `False` when any validation, identity, authentication, or database rule fails.

## Security Check 1 — Session Account Must Be Active

The service first checks:

```python
if not current_user["is_active"]:
    return False
```

An inactive session cannot change a password.

This check stops the request before database loading or password verification.

## Security Check 2 — Password Input Must Not Be Blank

The service checks:

```python
if (
    not current_password.strip()
    or not new_password.strip()
):
    return False
```

This rejects:

- An empty current password
- A whitespace-only current password
- An empty new password
- A whitespace-only new password

The passwords themselves are not modified by `.strip()`.

The method is used only to determine whether each value contains meaningful characters.

## Security Check 3 — Reload the Live Account

The service does not trust only the account dictionary created during login.

It loads the current saved account again:

```python
stored_user = load_user_account_by_username(
    current_user["username"],
    database_file,
)
```

This matters because the database may have changed after the session began.

Examples include:

- The account was deactivated
- The account was removed
- The session dictionary became stale
- The session identity was accidentally modified

## Security Check 4 — Saved Account Must Exist

The service checks:

```python
if stored_user is None:
    return False
```

An old or fabricated session cannot create a missing account through password change.

The workflow only updates an existing saved user.

## Security Check 5 — Saved Account Must Still Be Active

The service checks:

```python
if not stored_user["is_active"]:
    return False
```

This is separate from checking:

```python
current_user["is_active"]
```

The session may still say active even if the live SQLite record was deactivated after login.

Checking both values prevents a stale active session from changing the credential of a newly deactivated account.

## Security Check 6 — Session User ID Must Match

The service checks:

```python
if stored_user["user_id"] != current_user["user_id"]:
    return False
```

The username and user ID must refer to the same saved account.

This protects against:

- A corrupted session dictionary
- A changed username
- A fabricated account dictionary
- Accidental targeting of another saved user

The username may be valid and the supplied password may be correct, but a mismatched session identity is still rejected.

## Security Check 7 — Current Password Must Be Correct

The service verifies:

```python
if not verify_password(
    current_password,
    stored_user["password_hash"],
):
    return False
```

An authenticated session alone is not enough.

The user must prove knowledge of the account's current password.

This is the main security difference between self-service password change and administrator-controlled password reset.

## Security Check 8 — New Password Must Be Different

The service checks:

```python
if verify_password(
    new_password,
    stored_user["password_hash"],
):
    return False
```

If the new password matches the current saved password, the request is rejected.

A password change must actually replace the credential with a different password.

`verify_password()` is used instead of directly comparing hash strings because password hashes use random salts.

The same plain-text password can produce different protected hash strings.

## Delayed Hashing

The new password is hashed only after all security checks pass:

```python
new_password_hash = hash_password(new_password)
```

This avoids expensive hashing for requests that have already failed.

It also prevents invalid requests from reaching the database update step.

## Reusing the Existing Database Function

Day 79 did not require a new database function.

The service reuses:

```python
update_user_account_password_hash()
```

The final call is:

```python
return update_user_account_password_hash(
    stored_user["username"],
    new_password_hash,
    database_file,
)
```

Only the protected replacement hash reaches the database layer.

The plain-text current and new passwords are never stored.

## Role-Independent Self-Service

The service does not check:

```python
MANAGE_USER_ACCOUNTS
```

This is intentional.

Administrators and viewers may both change their own credentials.

The security requirement is ownership plus knowledge of the current password, not account-management permission.

## Successful Administrator Test

A test confirms that an administrator can change their own password.

The test:

- Registers an administrator
- Authenticates with the current password
- Changes to a new password
- Confirms the old password no longer matches
- Confirms the new password matches
- Confirms the role remains `admin`
- Confirms the active status remains `True`

## Successful Viewer Test

A separate test confirms that a viewer can change their own password.

The test proves that a viewer does not need `users.manage` permission for self-service credential ownership.

It confirms:

- Old password rejection
- New password acceptance
- Viewer-role preservation
- Active-status preservation

## Wrong Current Password Test

A test supplies an incorrect current password.

It confirms that:

- The change returns `False`
- The saved current password remains valid
- The proposed new password does not become valid
- The account remains unchanged

## Blank-Input Boundary Test

One test uses two related cases:

- Blank current password
- Blank new password

The cases are executed using:

```python
with self.subTest(case=case_name):
```

`subTest()` labels each loop case separately.

If one case fails, unittest reports which case failed and can continue checking the remaining cases.

The two cases still count as one test method.

## Password-Reuse Test

A test attempts to use the current password as the new password.

It confirms that:

- The service returns `False`
- The saved password hash remains exactly unchanged
- The current password remains valid

The unchanged hash proves that rejection occurred before a replacement hash was generated and saved.

## Inactive-Session Test

A test authenticates a user and then changes the session dictionary to:

```python
"is_active": False
```

The saved database account remains active.

The service still returns `False` because the current session is not allowed to perform the change.

## Deactivated Saved-Account Test

A separate test keeps the session dictionary active but deactivates the live SQLite record.

The test confirms that:

- The session still says active
- The saved account says inactive
- The password change is rejected
- The original password remains valid
- The proposed password remains invalid

This proves that the service reloads and trusts the live database state.

## Missing Saved-Account Test

A fabricated active session refers to a username that is not saved.

The service returns `False`.

It does not create an account or password record.

## Mismatched User-ID Test

A user is registered and authenticated normally.

The session `user_id` is then changed before requesting a password change.

The username and current password remain correct.

The service rejects the request because the session user ID no longer matches the saved account ID.

Without this check, the change would incorrectly succeed.

## Test Results

The user-service test count increased from 27 to 36.

Day 79 added nine tests:

1. Administrator can change own password
2. Viewer can change own password
3. Wrong current password is rejected
4. Blank current and new password inputs are rejected
5. Current-password reuse is rejected
6. Inactive session is rejected
7. Deactivated saved account is rejected
8. Missing saved account is rejected
9. Mismatched session user ID is rejected

## Full Regression Test

The complete automated suite was run:

```powershell
& C:\Users\user\AppData\Local\Python\pythoncore-3.14-64\python.exe -m unittest discover -s Projects\employee_management_system\tests -t Projects\employee_management_system -v
```

Result:

```text
Ran 207 tests in 12.963s

OK
```

All previous 198 tests continued to pass.

No existing authentication, authorization, viewer-account management, employee management, backup, restoration, reporting, repository, or console behavior was broken.

## Why No Manual Console Test Was Performed

Day 79 added only a service-layer foundation.

There is no menu option or command-layer function for self-service password change yet.

Manual console testing would not be meaningful until the feature is connected to the interactive application.

## README Updates

The README now documents:

- The self-service password-change foundation
- Support for active administrators and viewers
- Current-password verification
- Live account reloading
- Session and database active-status checks
- Session-to-record user-ID matching
- Missing-account rejection
- Blank-input rejection
- Password-reuse prevention
- Role and active-status preservation
- `subTest()` boundary coverage
- 36 user-service tests
- 207 total automated tests
- Command and console integration as the next milestone

## Files Changed

Day 79 changed:

```text
Projects/employee_management_system/user_service.py
Projects/employee_management_system/tests/test_user_service.py
README.md
Notes/day79_summary.md
```

## Important Lessons

### Self-Service Requires Proof

A logged-in session is not enough for a sensitive credential change.

The user must also provide the current password.

### Live State Matters

Session data can become stale.

Security-sensitive workflows should reload important account state from the database before making a change.

### Identity Uses More Than Username

Matching the session and stored user IDs adds protection against an altered or corrupted session identity.

### Active Status Is Checked Twice

The session status and the saved database status protect different situations.

Both checks are required for defense in depth.

### Password Change Must Create a Real Change

A new password that matches the current password is rejected.

### Plain-Text Passwords Stay Out of Storage

The database receives only the protected replacement hash.

## Day 79 Result

Day 79 successfully created a secure, tested self-service password-change foundation.

Active administrators and viewers can change their own password when:

- Their session is active
- Their saved account exists
- Their saved account remains active
- Their session user ID matches the saved account
- Their current password is correct
- Their new password is not blank
- Their new password differs from the current password

## Next Milestone

Add the tested command-layer and interactive-console workflow for self-service password changes.

That future workflow will include:

- Hidden current-password entry
- Hidden new-password entry
- New-password confirmation
- Required-input validation
- Generic success and failure messages
- A menu option available to both administrators and viewers
- Success-only activity logging
- Automated command and console tests
- Manual old-password and new-password verification