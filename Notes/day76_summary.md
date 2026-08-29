# Day 76 Summary — Administrator-Only Viewer Account Status Management

## Goal

Add a secure, tested workflow that allows active administrators to deactivate and reactivate viewer accounts.

The workflow must:

- Store account-status changes in SQLite
- Allow only active administrators to manage viewer status
- Prevent viewers from changing account status
- Prevent inactive administrators from changing account status
- Protect administrator accounts from this viewer-management workflow
- Reject missing target accounts
- Reject requests that do not actually change the status
- Support both activation and deactivation
- Provide clear command-layer messages
- Validate console input
- Protect the console option with authorization
- Record only successful status changes
- Prevent inactive viewers from logging in
- Preserve all existing application behavior

## Starting Point

Before Day 76, the application already supported:

- Protected password storage
- Secure password verification
- SQLite user-account storage
- Case-insensitive username retrieval
- Duplicate-username rejection
- Initial administrator creation
- Credential authentication
- Inactive-account login rejection
- Administrator and viewer roles
- Role-based authorization
- Default-deny permission checks
- Administrator-only viewer registration
- Hidden viewer-password entry
- Password confirmation
- Success-only account-creation logging
- 159 automated tests

The `users` table already contained:

```text
is_active
```

New accounts were active by default, and authentication already rejected inactive accounts.

However, the application did not yet provide a controlled workflow for changing a viewer’s active status.

## Account Status Meaning

A user account contains:

```python
"is_active": True
```

or:

```python
"is_active": False
```

The meanings are:

```text
True  → the account is active and may authenticate
False → the account is inactive and cannot authenticate
```

The account is not deleted when deactivated.

Its username, password hash, role, and other stored information remain in SQLite.

Deactivation temporarily blocks access while preserving the account for possible reactivation.

## Database Status-Update Function

A new function was added to `database.py`:

```python
def update_user_account_active_status(
    username: str,
    is_active: bool,
    database_file: Path = DATABASE_FILE,
) -> bool:
    initialize_database(database_file)
    connection = get_database_connection(database_file)

    try:
        update_result = connection.execute(
            """
            UPDATE users
            SET is_active = ?
            WHERE username = ?
            """,
            (
                int(is_active),
                username,
            ),
        )
        connection.commit()
        return update_result.rowcount == 1
    except sqlite3.Error:
        connection.rollback()
        return False
    finally:
        connection.close()
```

## Database Initialization

The function begins with:

```python
initialize_database(database_file)
```

This ensures that the SQLite database and required tables exist before the update is attempted.

It then opens a connection:

```python
connection = get_database_connection(database_file)
```

The connection is used to execute the SQL update.

## Parameterized SQL Update

The database operation is:

```sql
UPDATE users
SET is_active = ?
WHERE username = ?
```

The values are passed separately:

```python
(
    int(is_active),
    username,
)
```

Parameterized SQL keeps user-provided values separate from the SQL command.

This avoids building SQL by joining raw input into a string.

## Boolean-to-SQLite Conversion

Python uses:

```python
True
False
```

SQLite stores the active status as an integer:

```text
1
0
```

The conversion is:

```python
int(is_active)
```

Therefore:

```text
int(True)  → 1
int(False) → 0
```

The database stores:

```text
1 → active
0 → inactive
```

When the account is loaded, the stored value is converted back to a Python Boolean.

## Affected-Row Verification

After the update, the function returns:

```python
update_result.rowcount == 1
```

This means success is reported only when exactly one user row was updated.

Examples:

```text
One matching account → rowcount is 1 → return True
No matching account  → rowcount is 0 → return False
```

This prevents the application from reporting success when the username does not exist.

## Transaction Safety

When the update succeeds:

```python
connection.commit()
```

permanently saves the status change.

If SQLite raises an error:

```python
connection.rollback()
```

cancels the unfinished transaction.

The function then returns:

```python
False
```

The connection is always closed through:

```python
finally:
    connection.close()
```

## Database Tests

Three database tests were added.

### Deactivation Test

```python
test_update_user_account_active_status_deactivates_account
```

This test confirms that:

- A user account is inserted
- The status update receives `False`
- The update returns `True`
- The account is stored as inactive

### Reactivation Test

```python
test_update_user_account_active_status_reactivates_account
```

This test confirms that:

- An account can first be deactivated
- The status can later be changed to `True`
- The update returns `True`
- The account becomes active again

### Missing-Account Test

```python
test_update_user_account_active_status_returns_false_when_missing
```

This test confirms that attempting to update a username that does not exist returns:

```python
False
```

The database test count increased from:

```text
30
```

to:

```text
33
```

## Viewer Status Business Function

A new service function was added to `user_service.py`:

```python
def set_viewer_account_active_status(
    current_user: UserAccount,
    target_username: str,
    is_active: bool,
    database_file: Path = DATABASE_FILE,
) -> bool:
    if (
        not current_user["is_active"]
        or not user_has_permission(
            current_user,
            MANAGE_USER_ACCOUNTS,
        )
    ):
        return False

    target_user = load_user_account_by_username(
        target_username,
        database_file,
    )

    if target_user is None:
        return False

    if target_user["role"] != "viewer":
        return False

    if target_user["is_active"] == is_active:
        return False

    return update_user_account_active_status(
        target_username,
        is_active,
        database_file,
    )
```

This function contains the business and security rules for account-status management.

## Acting User and Target User

The function works with two different users.

The acting user is:

```python
current_user
```

This is the authenticated user attempting the operation.

The target user is found using:

```python
target_username
```

This is the account whose status may be changed.

Example:

```text
Current user: Dennis
Target user : ReportViewer
```

Dennis performs the action.

`ReportViewer` receives the status change.

## Active Administrator Requirement

The first rule checks:

```python
not current_user["is_active"]
```

If the acting administrator is inactive, the expression becomes:

```text
not False → True
```

The function returns:

```python
False
```

An inactive administrator cannot manage other user accounts.

## Permission Requirement

The function also checks:

```python
user_has_permission(
    current_user,
    MANAGE_USER_ACCOUNTS,
)
```

The required permission is:

```text
users.manage
```

Administrators receive this permission.

Viewers do not.

The complete rule requires the acting user to be:

```text
Active
AND
Allowed users.manage
```

If either requirement fails, the operation is rejected.

## Missing-Target Protection

The target account is loaded using:

```python
target_user = load_user_account_by_username(
    target_username,
    database_file,
)
```

If the account does not exist:

```python
if target_user is None:
    return False
```

No database status update is attempted.

## Administrator-Account Protection

The workflow is specifically for viewer-account management.

The rule is:

```python
if target_user["role"] != "viewer":
    return False
```

This prevents the function from changing an administrator account.

Examples:

```text
Target role viewer → may continue
Target role admin  → rejected
Target role unknown → rejected
```

This reduces the risk of accidentally disabling an administrator through the viewer-management workflow.

## Unchanged-Status Protection

The function rejects a request when the requested status is already stored:

```python
if target_user["is_active"] == is_active:
    return False
```

Examples:

```text
Viewer active + request True   → no change → False
Viewer inactive + request False → no change → False
```

This prevents the application from claiming that a change occurred when nothing was modified.

It also prevents misleading success messages and activity-log entries.

## Final Database Update

Only after all business rules pass does the function call:

```python
return update_user_account_active_status(
    target_username,
    is_active,
    database_file,
)
```

The workflow is:

```text
Check acting account
        ↓
Check permission
        ↓
Load target account
        ↓
Require target to exist
        ↓
Require viewer role
        ↓
Require a real status change
        ↓
Update SQLite
```

## Service-Layer Tests

Seven status-management tests were added to `test_user_service.py`.

### Administrator Can Deactivate Viewer

```python
test_administrator_can_deactivate_viewer_account
```

This confirms:

- The acting user is an active administrator
- The target is a viewer
- `False` requests deactivation
- The operation returns `True`
- The viewer becomes inactive

### Administrator Can Reactivate Viewer

```python
test_administrator_can_reactivate_viewer_account
```

This confirms:

- The viewer can first be deactivated
- `True` requests reactivation
- The operation returns `True`
- The viewer becomes active again

### Viewer Cannot Change Viewer Status

```python
test_viewer_cannot_change_viewer_account_status
```

This confirms that an active viewer cannot manage another viewer because the acting viewer lacks:

```text
users.manage
```

### Inactive Administrator Cannot Change Viewer Status

```python
test_inactive_administrator_cannot_change_viewer_status
```

This confirms that an administrator role is insufficient when:

```python
"is_active": False
```

### Administrator Cannot Change Administrator Status

```python
test_administrator_cannot_change_administrator_status
```

This confirms that the viewer-management workflow protects administrator targets.

### Missing Viewer Is Rejected

```python
test_administrator_cannot_change_missing_viewer_status
```

This confirms that a nonexistent username returns:

```python
False
```

and remains absent from SQLite.

### Unchanged Viewer Status Is Rejected

```python
test_administrator_cannot_apply_unchanged_viewer_status
```

This confirms that requesting `True` for an already-active viewer returns:

```python
False
```

The user-service test count increased from:

```text
12
```

to:

```text
19
```

## Command-Layer Status Function

The existing `user_account_setup.py` command layer was expanded with:

```python
def run_viewer_account_status_change(
    current_user: UserAccount,
    target_username: str,
    is_active: bool,
    database_file: Path = DATABASE_FILE,
) -> bool:
    status_changed = set_viewer_account_active_status(
        current_user,
        target_username,
        is_active,
        database_file,
    )

    if not status_changed:
        print("Viewer account status was not changed.")
        return False

    status_text = (
        "activated"
        if is_active
        else "deactivated"
    )

    print(
        f"Viewer account {status_text} successfully."
    )
    return True
```

## Command-Layer Responsibility

The service layer decides:

```text
Is this operation permitted and valid?
```

The command layer communicates:

```text
What result should the console user see?
```

The command layer does not duplicate:

- Permission checks
- Active-administrator checks
- Missing-account checks
- Target-role checks
- Unchanged-status checks
- SQLite update logic

## Conditional Status Text

The expression:

```python
status_text = (
    "activated"
    if is_active
    else "deactivated"
)
```

means:

```text
is_active is True  → "activated"
is_active is False → "deactivated"
```

The success messages are:

```text
Viewer account activated successfully.
Viewer account deactivated successfully.
```

A rejected operation prints:

```text
Viewer account status was not changed.
```

## Command-Layer Tests

Three status-management command tests were added.

### Successful Deactivation

```python
test_successful_viewer_account_deactivation
```

This confirms that:

- `False` reaches the service
- The command returns `True`
- The deactivation success message is printed

### Successful Reactivation

```python
test_successful_viewer_account_reactivation
```

This confirms that:

- `True` reaches the service
- The command returns `True`
- The activation success message is printed

### Failed Status Change

```python
test_failed_viewer_account_status_change
```

This confirms that:

- A rejected service operation returns `False`
- The command returns `False`
- The safe failure message is printed
- No false success is reported

The viewer-account command test count increased from:

```text
2
```

to:

```text
5
```

## Console Status Helper

A new helper was added to `main.py`:

```python
def change_viewer_account_status(
    current_user: UserAccount,
) -> bool:
    print()
    print("CHANGE VIEWER ACCOUNT STATUS")

    target_username = input(
        "Viewer username: "
    ).strip()

    if not target_username:
        print("Viewer username is required.")
        return False

    status_action = input(
        "Type ACTIVATE or DEACTIVATE: "
    ).strip().upper()

    if status_action == "ACTIVATE":
        is_active = True
    elif status_action == "DEACTIVATE":
        is_active = False
    else:
        print("Invalid viewer account status action.")
        return False

    status_changed = run_viewer_account_status_change(
        current_user,
        target_username,
        is_active,
    )

    if status_changed:
        status_text = (
            "activated"
            if is_active
            else "deactivated"
        )
        log_activity(
            f"User {current_user['username']} {status_text} "
            f"viewer account {target_username}."
        )

    return status_changed
```

## Early Username Validation

The username is normalized with:

```python
.strip()
```

This removes unnecessary spaces from both ends.

The function then checks:

```python
if not target_username:
```

A blank or spaces-only username becomes an empty string.

An empty string is falsy, so:

```python
not target_username
```

becomes:

```python
True
```

The helper prints:

```text
Viewer username is required.
```

and stops before requesting an action or calling the service.

## Action Normalization

The entered action uses:

```python
.strip().upper()
```

Examples:

```text
" activate "   → "ACTIVATE"
"deactivate"   → "DEACTIVATE"
" DEACTIVATE " → "DEACTIVATE"
```

The console therefore accepts different capitalization and surrounding spaces.

## Action-to-Boolean Conversion

The helper converts the action to a Boolean:

```python
if status_action == "ACTIVATE":
    is_active = True
elif status_action == "DEACTIVATE":
    is_active = False
```

Therefore:

```text
ACTIVATE   → True
DEACTIVATE → False
```

Any other action is rejected with:

```text
Invalid viewer account status action.
```

## Success-Only Activity Logging

The activity log is written only when:

```python
if status_changed:
```

is true.

Successful entries use:

```text
User Dennis activated viewer account ReportViewer.
User Dennis deactivated viewer account ReportViewer.
```

Rejected or unchanged operations are not recorded as successful changes.

## Console Helper Tests

Five console-helper tests cover:

```python
test_change_viewer_status_accepts_activation
test_change_viewer_status_accepts_deactivation
test_change_viewer_status_rejects_missing_username
test_change_viewer_status_rejects_invalid_action
test_change_viewer_status_does_not_log_failed_change
```

They confirm:

- Activation becomes `True`
- Deactivation becomes `False`
- Usernames are stripped
- Actions are normalized
- Missing usernames stop early
- Invalid actions do not reach the service
- Failed changes are not logged as successful

## Menu Permission Mapping

The menu-permission mapping was expanded:

```python
"14": MANAGE_USER_ACCOUNTS,
"15": MANAGE_USER_ACCOUNTS,
```

Option 14 creates viewer accounts.

Option 15 changes viewer-account status.

Both actions require:

```text
users.manage
```

## Updated Console Menu

The final menu contains:

```text
14. Register Viewer Account
15. Change Viewer Account Status
16. Exit
```

Exit moved from option 15 to option 16.

All existing tests using the old Exit option were updated.

## Menu Execution Branch

The new menu branch is:

```python
elif choice == "15":
    change_viewer_account_status(
        authenticated_user
    )
```

Exit is now:

```python
elif choice == "16":
    print("Closing the program...")
    log_activity("Application closed.")
    break
```

The invalid-option message was updated to:

```text
Please choose a number from 1 to 16.
```

## Menu Authorization Tests

Two menu-integration tests were added.

### Administrator Can Open Status Management

```python
test_administrator_can_open_viewer_status_management
```

This confirms that option 15 calls:

```python
change_viewer_account_status(administrator)
```

### Viewer Cannot Open Status Management

```python
test_viewer_cannot_open_viewer_status_management
```

This confirms that:

- The viewer is denied before the helper runs
- The helper is not called
- A permission-denied message is shown
- The denied `users.manage` attempt is logged

The console-integration test count increased from:

```text
21
```

to:

```text
28
```

## Automated Test Results

The complete suite produced:

```text
Ran 179 tests in 3.754s

OK
```

The suite increased from:

```text
159 tests
```

to:

```text
179 tests
```

Day 76 added:

```text
20 automated tests
```

The final relevant counts are:

```text
Database tests               : 33
Administrator setup tests    : 6
Database backup tests        : 1
Database restoration tests   : 2
Migration tests              : 3
Console integration tests    : 28
Storage verification tests   : 6
Repository tests             : 9
Authentication tests         : 5
User-service tests           : 19
Authorization tests          : 4
Viewer command-layer tests   : 5
Existing core tests          : 58
Complete suite               : 179
```

## Manual Verification

A fresh SQLite database backup was created before manual testing.

Administrator Dennis then:

1. Logged in successfully
2. Opened option 15
3. Selected `ReportViewer`
4. Entered `DEACTIVATE`
5. Received:

```text
Viewer account deactivated successfully.
```

The application was closed using option 16.

`ReportViewer` then attempted to log in with valid credentials and received:

```text
Authentication failed.
Employee Management System access denied.
```

This proved that the inactive status blocks authentication.

Dennis then:

1. Logged in again
2. Opened option 15
3. Selected `ReportViewer`
4. Entered `ACTIVATE`
5. Received:

```text
Viewer account activated successfully.
```

After reactivation, `ReportViewer` logged in successfully and exited normally.

## Activity-Log Verification

The activity log recorded:

```text
User Dennis deactivated viewer account ReportViewer.
Failed login attempt.
Application access denied.
User Dennis activated viewer account ReportViewer.
User ReportViewer logged in.
```

The log therefore provides evidence of:

- Administrator authentication
- Viewer deactivation
- Rejected inactive-account login
- Viewer reactivation
- Successful viewer login
- Normal application closure

## Files Modified

Day 76 modified:

```text
Projects/employee_management_system/database.py
Projects/employee_management_system/main.py
Projects/employee_management_system/tests/test_database.py
Projects/employee_management_system/tests/test_main.py
Projects/employee_management_system/tests/test_user_account_setup.py
Projects/employee_management_system/tests/test_user_service.py
Projects/employee_management_system/user_account_setup.py
Projects/employee_management_system/user_service.py
README.md
```

Day 76 also created:

```text
Notes/day76_summary.md
```

## Security Rules Completed

The final account-status rules are:

```text
Active administrator + viewer target + real change → allowed
Viewer acting user                               → denied
Inactive administrator                          → denied
Missing target                                  → denied
Administrator target                            → denied
Unchanged status                                → denied
Unknown or invalid console action                → denied
```

The overall rule is:

```text
Not explicitly valid and authorized → no status change
```

## Business Value

The new workflow allows a business to:

- Temporarily suspend viewer access
- Restore access without recreating the account
- Preserve the account’s username and password hash
- Prevent viewers from managing accounts
- Prevent inactive administrators from exercising privileges
- Protect administrator accounts from the viewer workflow
- Avoid misleading unchanged-status success reports
- Maintain an audit trail of successful changes
- Verify behavior through automated and manual testing

## Key Lessons

Day 76 reinforced:

- Python Booleans can be converted to SQLite integers
- `rowcount` can verify whether an update found a target
- Transactions require commits, rollbacks, and cleanup
- Database functions should report storage results
- Service functions should enforce business rules
- Command functions should communicate outcomes
- Console helpers should validate and normalize input
- Authorization should occur before protected actions
- Security workflows require both success and rejection tests
- Inactive accounts can be blocked without deleting them
- Administrator targets require stronger protection
- Activity logs must not report failed actions as successful
- End-to-end manual testing confirms that the layers work together

## Current Limitation

The administrator can activate and deactivate viewer accounts, but cannot yet reset a viewer’s forgotten password through a controlled workflow.

## Next Step

The next account-security milestone is:

```text
Tested administrator-controlled viewer password reset
```

That workflow should:

- Require an active administrator
- Require `users.manage`
- Accept only viewer targets
- Reject missing accounts
- Protect administrator accounts
- Hash the replacement password
- Avoid storing plain passwords
- Require confirmation in the console
- Record only successful resets
- Include database, service, command, console, and manual tests