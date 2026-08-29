# Day 78 Summary — Administrator-Controlled Viewer Password Reset Console Workflow

## Goal

Complete the end-to-end administrator-controlled viewer password-reset workflow.

Day 77 created the database and service foundations. Day 78 connected those foundations to:

- A command helper
- Hidden console password entry
- Password confirmation
- Required-input validation
- Administrator-only menu authorization
- Success-only activity logging
- Automated command and console tests
- Manual end-to-end verification

## Starting Point

At the beginning of Day 78, the application already had:

- A database function that safely replaces one saved password hash
- A service function containing the password-reset business rules
- Active-administrator authorization
- Viewer-target protection
- Blank-password rejection
- Current-password reuse detection
- Inactive-viewer status preservation
- 189 passing automated tests

However, the feature could not yet be used through the interactive console.

## Command-Layer Password Reset

The following service function was imported into `user_account_setup.py`:

```python
reset_viewer_account_password
```

A new command helper was added:

```python
def run_viewer_account_password_reset(
    current_user: UserAccount,
    target_username: str,
    new_password: str,
    database_file: Path = DATABASE_FILE,
) -> bool:
```

The helper calls the service:

```python
password_reset = reset_viewer_account_password(
    current_user,
    target_username,
    new_password,
    database_file,
)
```

If the service returns `False`, it prints:

```text
Viewer account password was not reset.
```

and returns `False`.

If the service returns `True`, it prints:

```text
Viewer account password reset successfully.
```

and returns `True`.

## Why the Command Message Is Generic

The command helper does not explain whether failure happened because:

- The target username does not exist
- The target is an administrator
- The current user lacks permission
- The current user is inactive
- The new password is blank
- The new password matches the current password
- The database update failed

Instead, every service-level failure receives the same generic message.

This avoids revealing account details to a person who may not be authorized to know them.

## Command-Layer Tests

Two tests were added to `test_user_account_setup.py`.

### Successful Password Reset

The successful test confirms that:

- The helper passes the current user to the service
- The helper passes the target username
- The helper passes the new password
- The helper passes the selected database path
- The helper returns `True`
- The helper prints the success message

### Failed Password Reset

The failure test confirms that:

- The service still receives the exact arguments
- A service result of `False` produces a command result of `False`
- The helper prints only the generic failure message
- The helper does not falsely report success

The viewer-account command test count increased from 5 to 7.

## Console Password-Reset Function

A new console function was added to `main.py`:

```python
def reset_viewer_password(
    current_user: UserAccount,
) -> bool:
```

The function displays:

```text
RESET VIEWER ACCOUNT PASSWORD
```

It collects:

1. The target viewer username
2. The new viewer password
3. Confirmation of the new password

The target username is collected using `input()` and cleaned with `.strip()`.

Both password entries are collected using `getpass()` so the passwords are not displayed in the terminal.

## Required-Input Validation

The console checks:

```python
if (
    not target_username
    or not new_password.strip()
):
```

A blank username is rejected.

A blank or whitespace-only password is also rejected.

The actual password is not changed by `.strip()`. The method is used only to check whether the value contains meaningful characters.

The user receives:

```text
Viewer username and new password are required.
```

The command helper is not called after this validation failure.

## Password Confirmation

The console compares:

```python
new_password != password_confirmation
```

When the entries do not match, it prints:

```text
Viewer passwords do not match.
```

and returns `False`.

This prevents a typing mistake from replacing the saved password with an unintended value.

## Calling the Command Helper

After local input validation succeeds, the console calls:

```python
password_reset = run_viewer_account_password_reset(
    current_user,
    target_username,
    new_password,
)
```

The command helper then calls the previously tested service layer.

The workflow therefore follows this path:

```text
Console input
    ↓
Command helper
    ↓
Business service
    ↓
Database update
```

Each layer has one main responsibility:

- Console layer: collect and validate user input
- Command layer: convert the result into a user-facing message
- Service layer: enforce authorization and business rules
- Database layer: replace the saved password hash

## Success-Only Activity Logging

The console logs the reset only when the command helper returns `True`.

The log message is:

```text
User Dennis reset password for viewer account ReportViewer.
```

The new password and password hash are not included in the activity log.

Failed input validation and rejected reset requests are not recorded as successful password changes.

## Console-Function Tests

Five focused console-function tests were added.

### Valid Input

The valid-input test confirms that:

- Extra spaces around the username are removed
- Both password prompts use `getpass()`
- The command helper receives the cleaned username
- The confirmed password is passed correctly
- A successful reset returns `True`
- A successful reset creates the expected activity-log entry

### Missing Username

This test supplies a whitespace-only target username.

It confirms that:

- The result is `False`
- The command helper is not called
- The activity logger is not called
- The required-input message is printed

### Blank Password

This test supplies a password containing only spaces.

It confirms that:

- `.strip()` detects the password as blank
- The command helper is not called
- The activity logger is not called
- The reset is rejected before reaching the service

### Mismatched Passwords

This test supplies two different passwords.

It confirms that:

- Both hidden prompts are used
- The mismatch message is printed
- The command helper is not called
- No success log is created

### Service-Level Failure

This test supplies valid console input but mocks a command-helper failure.

It confirms that:

- The console returns `False`
- The helper receives the correct arguments
- A failed reset does not create a success log

## Menu Integration

The password-reset workflow was added as option 16:

```text
16. Reset Viewer Account Password
```

Exit moved from option 16 to option 17:

```text
17. Exit
```

The valid-option error message was updated from the range `1 to 16` to `1 to 17`.

## Permission Mapping

Option 16 was mapped to:

```python
MANAGE_USER_ACCOUNTS
```

in `MENU_PERMISSIONS`.

This means authorization is checked before `reset_viewer_password()` is called.

An administrator with `users.manage` permission may proceed.

A viewer is denied before any password-reset prompt appears.

The existing formatting around option 15 in `MENU_PERMISSIONS` was also corrected while updating the same mapping block.

## Exit-Test Renumbering

Before Day 78, the existing console tests used:

```python
"16"
```

to exit.

After option 16 became password reset, Exit moved to option 17.

Exactly 15 existing exit values in `test_main.py` were changed from:

```python
"16"
```

to:

```python
"17"
```

The replacement was limited to `test_main.py`.

The production value `"16"` in `main.py` remained the correct password-reset option.

## Menu-Authorization Tests

Two menu-integration tests were added.

### Administrator Can Open Password Reset

This test enters:

```text
16
17
```

The first choice opens password reset.

The second choice exits.

The test confirms that the administrator account is passed to `reset_viewer_password()`.

### Viewer Cannot Open Password Reset

This test logs in with a viewer account and selects option 16.

It confirms that:

- `reset_viewer_password()` is not called
- The viewer sees the permission-denied message
- The denied `users.manage` permission is recorded in the activity log
- The program continues safely until option 17 is selected

The console test count increased from 28 to 35.

## Focused Test Results

The viewer-account command tests produced:

```text
Ran 7 tests
OK
```

The console tests produced:

```text
Ran 35 tests
OK
```

## Full Regression Test

The complete automated test suite was run:

```powershell
& C:\Users\user\AppData\Local\Python\pythoncore-3.14-64\python.exe -m unittest discover -s Projects\employee_management_system\tests -t Projects\employee_management_system -v
```

Result:

```text
Ran 198 tests in 8.292s

OK
```

Day 78 added 9 tests:

- 2 command-helper tests
- 5 console-input tests
- 2 menu-authorization tests

The previous 189 tests continued to pass.

## Database Backup

A fresh SQLite database backup was created before manual password-reset verification.

The backup command reported:

```text
SQLite database backup completed successfully.
```

This provided a recovery point before changing the real viewer credential.

## Manual Administrator Reset Verification

Administrator Dennis signed in and selected:

```text
16. Reset Viewer Account Password
```

The target was:

```text
ReportViewer
```

The new password and confirmation remained hidden.

The application reported:

```text
Viewer account password reset successfully.
```

Dennis then exited through option 17.

## Old Password Rejection

After the reset, `ReportViewer` attempted to log in with the old password.

The application reported:

```text
Authentication failed.
Employee Management System access denied.
```

This proved that the original password no longer matched the stored hash.

## New Password Acceptance

`ReportViewer` then logged in using the replacement password.

The application reported:

```text
Signed in as ReportViewer (viewer).
```

This proved that:

- The new protected hash was saved correctly
- The new credential was accepted
- The account role remained `viewer`
- The reset did not promote the viewer to administrator

## Manual Viewer Authorization Check

While signed in as `ReportViewer`, option 16 was selected.

The application reported:

```text
You do not have permission to use this option.
```

The password-reset prompts did not appear.

This confirmed that menu authorization stops a viewer before the reset workflow runs.

## Activity-Log Verification

The activity log recorded:

- Application startup
- Dennis signing in
- Dennis resetting `ReportViewer`'s password
- Application closure
- The failed old-password login
- Application access denial
- The successful new-password login
- The viewer's denied `users.manage` permission
- Final application closure

Neither the old password nor the replacement password appeared in the log.

## README Updates

The README now documents:

- The completed password-reset console workflow
- Protected option 16
- Exit option 17
- Hidden password entry
- Password confirmation
- Required-input validation
- Generic failure messages
- Success-only activity logging
- Administrator-only menu authorization
- Role and active-status preservation
- Manual old-password rejection
- Manual new-password acceptance
- Viewer permission denial
- 35 console tests
- 7 viewer-account command tests
- 198 total automated tests

## Files Changed

Day 78 changed:

```text
Projects/employee_management_system/user_account_setup.py
Projects/employee_management_system/tests/test_user_account_setup.py
Projects/employee_management_system/main.py
Projects/employee_management_system/tests/test_main.py
README.md
Notes/day78_summary.md
```

## Important Lessons

### Hidden Input

`getpass()` prevents passwords from being displayed while they are entered.

It protects terminal visibility but does not replace hashing or authorization.

### Input Validation

The console rejects incomplete or mismatched input before calling deeper application layers.

This avoids unnecessary service and database operations.

### Generic Failure Messages

A generic failure message avoids revealing whether an account exists or why a protected operation was rejected.

### Success-Only Logging

A security-sensitive event should be recorded as successful only after the actual operation succeeds.

Logging a failed operation as successful would create an inaccurate audit trail.

### Menu Authorization

The menu permission check runs before the protected workflow.

This prevents unauthorized users from reaching its input prompts.

The service layer still checks authorization again as defense in depth.

### Credential Replacement

A successful password reset means:

- The old credential must fail
- The new credential must succeed
- The account role must remain unchanged
- The account status must remain unchanged

## Day 78 Result

Day 78 completed the administrator-controlled viewer password-reset workflow from the interactive console to the SQLite database.

The feature now includes:

- Administrator-only authorization
- Hidden password entry
- Password confirmation
- Required-input validation
- Generic command failure messages
- Secure service rules
- Protected password hashing
- SQLite hash replacement
- Role and status preservation
- Success-only audit logging
- Automated regression coverage
- Manual end-to-end verification

## Next Milestone

Build a tested self-service password-change workflow that requires the authenticated user's current password.

Unlike administrator-controlled reset, self-service password change will require the user to prove knowledge of the existing password before selecting a replacement.