# Day 80 Summary — Self-Service Password Change Console Workflow

## Goal

Complete the self-service password-change workflow by connecting the tested Day 79 business service to:

- A command helper
- Hidden console input
- Input validation
- Activity logging
- The interactive menu
- Automated command and console tests
- Manual end-to-end verification

Day 79 established the business-service foundation. Day 80 made that foundation available to authenticated administrators and viewers through the console application.

## What I Built

Day 80 added:

- A self-service password-change command helper
- Generic command success and failure messages
- A console function using three hidden password entries
- Required-input validation
- New-password confirmation
- Success-only activity logging
- Interactive menu option 17
- Exit-option renumbering from 17 to 18
- Administrator menu-routing coverage
- Viewer menu-routing coverage
- Complete automated and manual verification

## Application Layers

The completed workflow follows this path:

```text
Interactive console
    ↓
Command helper
    ↓
Business service
    ↓
Database function
    ↓
SQLite users table
```

Each layer has a focused responsibility.

### Console Layer

The console layer:

- Collects the current password
- Collects the new password
- Collects confirmation
- Rejects missing input
- Rejects mismatched confirmation
- Calls the command helper
- Logs only successful changes

### Command Layer

The command layer:

- Calls the business service
- Receives `True` or `False`
- Prints a generic success or failure message
- Returns the result to the console layer

### Business-Service Layer

The service layer:

- Requires an active authenticated session
- Rejects blank input
- Reloads the live saved account
- Requires the saved account to remain active
- Matches the session user ID to the saved user ID
- Verifies the current password
- Rejects reuse of the current password
- Protects the new password
- Requests the database update

### Database Layer

The database layer:

- Updates the saved password hash
- Commits the transaction
- Verifies that one row was changed
- Preserves the username, role, and active status

## Command Helper

The following import was added to `user_account_setup.py`:

```python
from user_service import (
    change_current_user_password,
    register_viewer_account,
    reset_viewer_account_password,
    set_viewer_account_active_status,
)
```

The new command helper is:

```python
def run_current_user_password_change(
    current_user: UserAccount,
    current_password: str,
    new_password: str,
    database_file: Path = DATABASE_FILE,
) -> bool:
    password_changed = change_current_user_password(
        current_user,
        current_password,
        new_password,
        database_file,
    )

    if not password_changed:
        print("Account password was not changed.")
        return False

    print("Account password changed successfully.")
    return True
```

The command helper does not contain password rules. Those rules belong to the service layer.

Its responsibility is translating a Boolean service result into a user-facing message.

The message uses `Account` instead of `Viewer` because the helper supports both administrators and viewers.

## Generic Failure Reporting

All service-layer rejection reasons produce the same command message:

```text
Account password was not changed.
```

Possible causes include:

- Incorrect current password
- Blank current password
- Blank new password
- Reused password
- Inactive session
- Deactivated saved account
- Missing saved account
- Mismatched session identity
- Failed database update

The generic message avoids revealing internal account-security information.

## Console Function

The following command helper was imported into `main.py`:

```python
from user_account_setup import (
    run_current_user_password_change,
    run_viewer_account_password_reset,
    run_viewer_account_registration,
    run_viewer_account_status_change,
)
```

The new console function is:

```python
def change_own_password(
    current_user: UserAccount,
) -> bool:
    print()
    print("CHANGE YOUR PASSWORD")

    current_password = getpass(
        "Current password: "
    )
    new_password = getpass(
        "New password: "
    )
    password_confirmation = getpass(
        "Confirm new password: "
    )

    if (
        not current_password.strip()
        or not new_password.strip()
    ):
        print("Current and new passwords are required.")
        return False

    if new_password != password_confirmation:
        print("New passwords do not match.")
        return False

    password_changed = run_current_user_password_change(
        current_user,
        current_password,
        new_password,
    )

    if password_changed:
        log_activity(
            f"User {current_user['username']} "
            "changed their password."
        )

    return password_changed
```

## Hidden Password Entry

The workflow calls `getpass()` three times:

```python
current_password = getpass(
    "Current password: "
)
new_password = getpass(
    "New password: "
)
password_confirmation = getpass(
    "Confirm new password: "
)
```

The entered characters do not appear in the terminal.

This protects passwords from:

- Screen observation
- Terminal screenshots
- Accidental copying
- Visible terminal history

## Required-Input Validation

The console rejects blank current or new passwords:

```python
if (
    not current_password.strip()
    or not new_password.strip()
):
    print("Current and new passwords are required.")
    return False
```

Calling `.strip()` removes surrounding whitespace.

Examples treated as blank include:

```python
""
" "
"   "
```

When validation fails, the command helper is not called.

## Password Confirmation

The console compares the new password with its confirmation:

```python
if new_password != password_confirmation:
    print("New passwords do not match.")
    return False
```

Both values must match exactly.

This protects users from saving a password that was mistyped.

## Success-Only Activity Logging

The console records the action only when the command succeeds:

```python
if password_changed:
    log_activity(
        f"User {current_user['username']} "
        "changed their password."
    )
```

A failed password change is not logged as a successful change.

The activity-log message contains:

- The authenticated username
- The completed action

It does not contain:

- The current password
- The new password
- The password confirmation
- A password hash

## Menu Integration

The interactive menu now includes:

```python
print("16. Reset Viewer Account Password")
print("17. Change Your Password")
print("18. Exit")
```

The `run_program()` routing includes:

```python
elif choice == "17":
    change_own_password(
        authenticated_user
    )

elif choice == "18":
    print("Closing the program...")
    log_activity("Application closed.")
    break
```

The invalid-option message now uses:

```python
"Please choose a number from 1 to 18."
```

## Why Option 17 Is Not in `MENU_PERMISSIONS`

Option 17 was deliberately not added to:

```python
MENU_PERMISSIONS
```

The application already requires authentication before displaying the menu.

Both supported roles may change their own credentials:

- `admin`
- `viewer`

The user is not managing another account, so `users.manage` is not required.

This differs from option 16:

```text
Reset Viewer Account Password
```

Option 16 allows an administrator to change another user’s credential and therefore requires account-management permission.

## Administrator-Controlled Reset Versus Self-Service Change

### Administrator-Controlled Reset

The administrator:

- Selects another viewer account
- Provides a replacement password
- Does not need the viewer’s current password
- Must possess `users.manage`
- Cannot target an administrator

### Self-Service Change

The authenticated user:

- Changes only their own password
- Must prove knowledge of the current password
- Does not require `users.manage`
- May be an administrator or viewer
- Cannot target another account

## Command-Layer Tests

Two command tests were added.

### Successful Change

The success test verifies that:

- The command calls the service once
- The correct user and passwords are passed
- The result is `True`
- The success message is printed

### Failed Change

The failure test verifies that:

- The command calls the service once
- A `False` service result is returned
- The generic failure message is printed

The user-account command test file increased from:

```text
7 tests
```

to:

```text
9 tests
```

## Console Tests

Six console and menu-integration tests were added.

### Valid Console Input

The test verifies:

- Three calls to `getpass()`
- Correct prompt text
- Correct command arguments
- A `True` result
- Success-only activity logging
- The console heading

### Blank Password Input

A loop and `subTest()` check:

- Blank current password
- Blank new password

Each case verifies that:

- The result is `False`
- The command helper is not called
- Activity is not logged as successful
- The required-input message is printed

### Mismatched Confirmation

The test verifies that:

- All three passwords are collected
- Different new-password entries are rejected
- The command helper is not called
- Activity is not logged
- The mismatch message is printed

### Command-Layer Failure

The test uses valid console input but makes the mocked command return `False`.

It verifies that:

- The request reaches the command helper
- The console returns `False`
- No successful activity entry is created

### Administrator Menu Routing

The administrator selects:

```text
17
18
```

The test proves option 17 calls:

```python
change_own_password(administrator)
```

### Viewer Menu Routing

The viewer selects:

```text
17
18
```

The test proves option 17 calls:

```python
change_own_password(viewer)
```

This confirms that the viewer is not blocked by `users.manage`.

The console test file increased from:

```text
35 tests
```

to:

```text
41 tests
```

## Exit Renumbering

Before Day 80, Exit used option 17.

Day 80 assigned option 17 to self-service password changes, so Exit moved to option 18.

Seventeen existing test selections were updated from:

```python
"17"
```

to:

```python
"18"
```

The replacements affected existing Exit choices only.

## Complete Automated Test Suite

The full suite passed:

```text
Ran 215 tests in 9.852s

OK
```

The total increased from:

```text
207 tests
```

to:

```text
215 tests
```

The eight new tests consist of:

```text
2 command-layer tests
6 console and menu-integration tests
```

## Manual Verification

A fresh SQLite database backup was created before modifying a real credential:

```text
SQLite database backup completed successfully.
```

`ReportViewer` signed in successfully with the existing password.

The first password-change attempt was safely rejected:

```text
Account password was not changed.
```

A second attempt used the exact authenticated current password and a genuinely different new password.

The application reported:

```text
Account password changed successfully.
```

The application was closed through option 18.

## Old-Password Rejection

A new login was attempted using the old password.

The application reported:

```text
Authentication failed.
Employee Management System access denied.
```

This proved the old password was no longer accepted.

## New-Password Authentication

Another login was attempted using the new password.

The application reported:

```text
Signed in as ReportViewer (viewer).
```

This proved:

- The new password hash was saved
- The new password authenticated successfully
- The account remained a viewer
- The active status was preserved

## Activity-Log Verification

The activity log contained:

```text
User ReportViewer changed their password.
Failed login attempt.
Application access denied.
User ReportViewer logged in.
Application closed.
```

The log did not expose either password.

The rejected password-change attempt did not create a misleading successful-change entry.

## Files Modified

Day 80 modified:

```text
Projects/employee_management_system/main.py
Projects/employee_management_system/user_account_setup.py
Projects/employee_management_system/tests/test_main.py
Projects/employee_management_system/tests/test_user_account_setup.py
README.md
```

Day 80 also created:

```text
Notes/day80_summary.md
```

## Key Lessons

### Command Helpers Connect Layers

A command helper connects user-facing workflows to business services.

It should remain small and should not duplicate service-layer security rules.

### Validation Should Stop Work Early

Invalid console input should return before calling deeper layers.

This reduces unnecessary work and keeps responsibilities clear.

### Authentication Is Different From Authorization

Authentication proves who the user is.

Authorization decides what the user may do.

Both administrators and viewers are already authenticated before using option 17. Because they are changing only their own credentials, no administrator-only permission is required.

### Password Ownership Requires Current-Password Proof

A self-service password change requires knowledge of the existing password.

This protects an unattended authenticated session from silently changing the account credential.

### Passwords Must Never Be Logged

Passwords and password hashes must not appear in:

- Activity logs
- Error messages
- Test output
- Debug output

### Tests Must Cover Both Roles

A feature intended for both administrators and viewers should include routing coverage for both roles.

### Manual Verification Complements Automated Tests

Automated tests verified isolated and integrated behavior.

Manual verification proved that the real SQLite account transitioned from the old password to the new password correctly.

## Day 80 Result

Day 80 completed the self-service password-change workflow.

The Employee Management System now supports:

- Administrator-controlled viewer password resets
- Administrator self-service password changes
- Viewer self-service password changes
- Current-password verification
- New-password confirmation
- Hidden credential entry
- Generic failure messages
- Password-reuse prevention
- Role and active-status preservation
- Success-only activity logging
- Protected SQLite password-hash replacement
- 215 passing automated tests

## Next Step

Day 81 begins the tested web-interface foundation.

The web interface will reuse the existing:

- Business services
- Employee repository
- SQLite database
- Authentication rules
- Authorization policy
- Password protection
- Activity logging

The existing console application will remain available while the new interface is developed.
