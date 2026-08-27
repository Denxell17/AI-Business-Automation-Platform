# Day 74 Summary — Role-Based Authorization and Default-Deny Permissions

## Goal

Add tested role-based authorization to the Employee Management System.

The system already authenticates users by checking who they are. Day 74 adds rules that decide what an authenticated user is allowed to do.

The authorization system must:

- Define clear named permissions
- Assign permissions to supported roles
- Give administrators every current console permission
- Limit viewers to read-only actions
- Deny unknown roles
- Deny unknown permissions
- Map protected menu choices to required permissions
- Prevent unauthorized functions from running
- Allow every authenticated user to exit
- Preserve invalid-choice handling
- Record denied actions in the activity log
- Preserve all existing administrator behavior

## Authentication and Authorization

Authentication answers:

```text
Who is this user?
```

Examples:

- Does the username exist?
- Is the account active?
- Is the password correct?

Authorization answers:

```text
What is this authenticated user allowed to do?
```

Examples:

- May this user register an employee?
- May this user view payroll?
- May this user restore the database?

The complete security flow is now:

```text
User enters credentials
          ↓
Authentication verifies identity
          ↓
Application loads the authenticated role
          ↓
Authorization checks the selected action
          ↓
Action is allowed or denied
```

## New Authorization Module

A new file was created:

```text
Projects/employee_management_system/authorization.py
```

This module contains:

- Named permission constants
- Role-to-permission rules
- The permission-checking function

Keeping authorization in a separate module prevents permission rules from being scattered throughout the console code.

## Named Permission Constants

The following permissions were added:

```python
REGISTER_EMPLOYEE = "employee.register"
VIEW_EMPLOYEE = "employee.view"
VIEW_PAYROLL = "payroll.view"
UPDATE_EMPLOYEE = "employee.update"
DELETE_EMPLOYEE = "employee.delete"
EXPORT_REPORT = "report.export"
BACKUP_DATABASE = "database.backup"
RESTORE_DATABASE = "database.restore"
```

Each constant represents one category of protected business action.

Using named constants is safer than repeatedly typing raw strings.

For example:

```python
REGISTER_EMPLOYEE
```

is easier to recognize and maintain than repeatedly writing:

```python
"employee.register"
```

It also reduces the chance of spelling the same permission differently in separate files.

## Permission Naming Style

The permission strings use a resource-and-action pattern:

```text
resource.action
```

Examples:

```text
employee.register
employee.view
payroll.view
database.backup
database.restore
```

This naming style makes each permission’s purpose clear.

## Role Permission Sets

The role policy is stored in:

```python
ROLE_PERMISSIONS = {
    "admin": {
        REGISTER_EMPLOYEE,
        VIEW_EMPLOYEE,
        VIEW_PAYROLL,
        UPDATE_EMPLOYEE,
        DELETE_EMPLOYEE,
        EXPORT_REPORT,
        BACKUP_DATABASE,
        RESTORE_DATABASE,
    },
    "viewer": {
        VIEW_EMPLOYEE,
        VIEW_PAYROLL,
        EXPORT_REPORT,
    },
}
```

`ROLE_PERMISSIONS` is a dictionary.

Its keys are role names:

```text
admin
viewer
```

Its values are sets containing the permissions assigned to each role.

## Administrator Permissions

The administrator receives:

```text
employee.register
employee.view
payroll.view
employee.update
employee.delete
report.export
database.backup
database.restore
```

This means an administrator can use every currently protected menu action.

The policy is still explicit.

An administrator does not automatically receive arbitrary permission strings. Only permissions placed in the administrator set are allowed.

## Viewer Permissions

The viewer receives:

```text
employee.view
payroll.view
report.export
```

This creates a read-only role.

A viewer may:

- View an employee profile
- View all employees
- Filter employees
- Search employees
- Sort employee information
- View payroll
- Export employee reports

A viewer may not:

- Register employees
- Update employees
- Delete employees
- Create database backups
- Restore database backups

## Why Sets Are Used

Each role’s permissions are stored in a set:

```python
{
    VIEW_EMPLOYEE,
    VIEW_PAYROLL,
    EXPORT_REPORT,
}
```

A set is useful because:

- It stores unique values
- Duplicate permissions are automatically avoided
- Membership checks are direct
- The business rule reads naturally

For example:

```python
permission in allowed_permissions
```

asks:

```text
Is this permission inside the role's allowed set?
```

## Permission-Checking Function

The authorization function is:

```python
def user_has_permission(
    user_account: UserAccount,
    permission: str,
) -> bool:
    allowed_permissions = ROLE_PERMISSIONS.get(
        user_account["role"],
        set(),
    )

    return permission in allowed_permissions
```

This function receives:

1. An authenticated `UserAccount`
2. A permission string

It returns:

```text
True  → permission is allowed
False → permission is denied
```

## Reading the User Role

The function reads:

```python
user_account["role"]
```

For an administrator, this returns:

```python
"admin"
```

For a viewer, it returns:

```python
"viewer"
```

That role is used to retrieve the correct permission set.

## Dictionary `.get()`

The function uses:

```python
ROLE_PERMISSIONS.get(
    user_account["role"],
    set(),
)
```

`.get()` accepts:

1. The key to find
2. A default value to return when the key is missing

For a known administrator role:

```python
ROLE_PERMISSIONS.get("admin", set())
```

returns the administrator permission set.

For an unknown role:

```python
ROLE_PERMISSIONS.get("unknown", set())
```

returns:

```python
set()
```

`set()` creates an empty set.

## Default-Deny Security

The empty-set fallback creates a default-deny rule.

For an unknown role:

```text
Allowed permissions = empty set
```

Every permission check then becomes:

```text
permission in empty set → False
```

This means malformed or unsupported user data receives no access.

The rule is:

```text
Not explicitly allowed → denied
```

This is safer than accidentally granting access when the application encounters an unexpected value.

## Permission Membership Check

The final line is:

```python
return permission in allowed_permissions
```

For example, a viewer checking:

```python
VIEW_EMPLOYEE
```

produces:

```text
"employee.view" in viewer permissions → True
```

A viewer checking:

```python
DELETE_EMPLOYEE
```

produces:

```text
"employee.delete" in viewer permissions → False
```

## Authorization Policy Tests

A new test file was created:

```text
Projects/employee_management_system/tests/test_authorization.py
```

The test class is:

```python
class TestUserAuthorization(unittest.TestCase):
```

Four policy tests were added.

## Administrator Permission Test

The test:

```python
test_administrator_has_all_permissions
```

creates an administrator account and checks all eight permissions.

The permissions are placed in a list:

```python
permissions = [
    REGISTER_EMPLOYEE,
    VIEW_EMPLOYEE,
    VIEW_PAYROLL,
    UPDATE_EMPLOYEE,
    DELETE_EMPLOYEE,
    EXPORT_REPORT,
    BACKUP_DATABASE,
    RESTORE_DATABASE,
]
```

The test loops through the list:

```python
for permission in permissions:
```

During each iteration, the variable `permission` contains one permission from the list.

The test then confirms:

```python
self.assertTrue(
    user_has_permission(
        administrator,
        permission,
    )
)
```

This proves every explicitly assigned administrator permission returns `True`.

## Understanding the Permission Loop

The first iteration checks:

```text
permission = employee.register
```

The second checks:

```text
permission = employee.view
```

The loop continues until every permission has been tested.

The flow is:

```text
Take the next permission
          ↓
Check the user's role
          ↓
Retrieve the role's permission set
          ↓
Check set membership
          ↓
Confirm the expected result
          ↓
Move to the next permission
```

The loop avoids repeating the same assertion eight times.

## `subTest()` Coverage

Each permission check uses:

```python
with self.subTest(permission=permission):
```

`subTest()` gives every loop iteration its own test context.

If one permission fails, the result identifies the specific permission.

For example:

```text
permission='employee.delete'
```

The remaining permission checks can still run.

## Viewer Permission Test

The test:

```python
test_viewer_has_only_read_only_permissions
```

separates permissions into two lists.

Allowed permissions:

```python
allowed_permissions = [
    VIEW_EMPLOYEE,
    VIEW_PAYROLL,
    EXPORT_REPORT,
]
```

Denied permissions:

```python
denied_permissions = [
    REGISTER_EMPLOYEE,
    UPDATE_EMPLOYEE,
    DELETE_EMPLOYEE,
    BACKUP_DATABASE,
    RESTORE_DATABASE,
]
```

The first loop uses:

```python
self.assertTrue(...)
```

The second loop uses:

```python
self.assertFalse(...)
```

This verifies both sides of the viewer policy.

The subtests also include:

```python
expected="allowed"
```

or:

```python
expected="denied"
```

This makes failures easier to understand.

## Unknown-Role Test

The test:

```python
test_unknown_role_has_no_permissions
```

creates a user with:

```python
"role": "unknown"
```

The test loops through every current permission and confirms that each result is `False`.

This verifies the empty-set fallback and default-deny rule.

The SQLite database already rejects unsupported roles, but the authorization function still protects itself from malformed data.

This is defense in depth.

## Unknown-Permission Test

The test:

```python
test_unknown_permission_is_denied
```

checks:

```python
permission_is_allowed = user_has_permission(
    administrator,
    "unknown.permission",
)
```

It confirms:

```python
self.assertFalse(permission_is_allowed)
```

Even an administrator is denied an unknown permission.

This proves:

```text
Administrator → all explicitly assigned permissions
Administrator → not every arbitrary permission string
```

## Console Authorization Imports

`main.py` now imports the permission constants and checking function:

```python
from authorization import (
    BACKUP_DATABASE,
    DELETE_EMPLOYEE,
    EXPORT_REPORT,
    REGISTER_EMPLOYEE,
    RESTORE_DATABASE,
    UPDATE_EMPLOYEE,
    VIEW_EMPLOYEE,
    VIEW_PAYROLL,
    user_has_permission,
)
```

This connects the tested authorization policy to the interactive console.

## Menu-to-Permission Mapping

The console defines:

```python
MENU_PERMISSIONS = {
    "1": REGISTER_EMPLOYEE,
    "2": VIEW_EMPLOYEE,
    "3": VIEW_PAYROLL,
    "4": UPDATE_EMPLOYEE,
    "5": DELETE_EMPLOYEE,
    "6": VIEW_EMPLOYEE,
    "7": VIEW_EMPLOYEE,
    "8": VIEW_EMPLOYEE,
    "9": VIEW_EMPLOYEE,
    "10": VIEW_EMPLOYEE,
    "11": EXPORT_REPORT,
    "12": BACKUP_DATABASE,
    "13": RESTORE_DATABASE,
}
```

This dictionary translates a menu choice into a business permission.

Examples:

```text
"1"  → employee.register
"3"  → payroll.view
"5"  → employee.delete
"12" → database.backup
"13" → database.restore
```

## Shared Employee-View Permission

Six menu choices use:

```python
VIEW_EMPLOYEE
```

They are:

```text
2  → View Employee Profile
6  → View All Employees
7  → View Employees by Department
8  → View Employees by Salary
9  → Search Employees by Name
10 → Filter Employees by Salary Range
```

These choices perform different functions, but all belong to the same permission category:

```text
Read employee information
```

A permission describes a category of access rather than one exact Python function.

## Separate Payroll Permission

Choice `"3"` uses:

```python
VIEW_PAYROLL
```

Payroll is separated from ordinary employee viewing because it contains more sensitive financial information.

This allows the policy to restrict payroll independently in the future without rewriting the menu structure.

## Separate Export Permission

Choice `"11"` uses:

```python
EXPORT_REPORT
```

Exporting is separate from viewing because it creates an external file.

The business may eventually decide that some users can view data but cannot export it.

## Exit Is Not Protected

Choice `"14"` is intentionally absent from `MENU_PERMISSIONS`.

Therefore:

```python
MENU_PERMISSIONS.get("14")
```

returns:

```python
None
```

Every authenticated user must be able to exit the application safely.

## Invalid Choices Remain Separate

Invalid choices are also absent from the permission mapping.

They continue to reach the existing invalid-choice handling.

Authorization does not replace input validation.

The two responsibilities remain separate:

```text
Authorization → Is the user allowed to use this valid action?
Validation    → Is this a recognized menu choice?
```

## Console Authorization Check

Inside the menu loop, the console now reads:

```python
required_permission = MENU_PERMISSIONS.get(choice)
```

It then checks:

```python
if (
    required_permission is not None
    and not user_has_permission(
        authenticated_user,
        required_permission,
    )
):
```

This means denial happens only when:

1. The selected choice has a mapped permission.
2. The authenticated user does not have that permission.

## Short-Circuit `and`

Python evaluates the condition from left to right.

First:

```python
required_permission is not None
```

If this is `False`, Python does not need to evaluate the second part.

This is called short-circuit evaluation.

For choice `"14"`:

```text
required_permission is not None → False
```

The permission function is skipped, and the exit branch remains available.

## Denied-Access Message

When permission is denied, the console prints:

```python
print("You do not have permission to use this option.")
```

This clearly informs the authenticated user that the selected action is restricted.

## Denied-Action Logging

The application records:

```python
log_activity(
    f"User {authenticated_user['username']} was denied "
    f"permission {required_permission}."
)
```

An example log message is:

```text
User Viewer was denied permission employee.register.
```

This creates an audit trail containing:

- The authenticated username
- The denied permission

## `continue` Prevents the Action

After recording the denied attempt, the console uses:

```python
continue
```

`continue` skips the rest of the current loop iteration and begins the next one.

The flow becomes:

```text
Viewer selects restricted option
          ↓
Permission check returns False
          ↓
Display denial message
          ↓
Record denied permission
          ↓
continue
          ↓
Display menu again
```

Because the remaining choice branches are skipped, the protected function never runs.

## Viewer Registration-Denial Test

The console test:

```python
test_viewer_cannot_register_employee
```

simulates a viewer selecting:

```text
1 → Register Employee
```

The mocked inputs are:

```python
mock_input.side_effect = [
    "1",
    "14",
]
```

The first input attempts the protected action.

Authorization denies it and `continue` returns to the menu.

The second input exits safely.

The test confirms:

```python
mock_register_employee.assert_not_called()
```

This is the most important protection assertion.

It proves the registration function never executes.

The test also confirms:

```python
mock_print.assert_any_call(
    "You do not have permission to use this option."
)
```

and:

```python
mock_log_activity.assert_any_call(
    "User Viewer was denied permission employee.register."
)
```

## Viewer Read-Only Access Test

The console test:

```python
test_viewer_can_view_all_employees
```

simulates a viewer selecting:

```text
6 → View All Employees
```

Choice `"6"` requires:

```python
VIEW_EMPLOYEE
```

That permission exists in the viewer set.

The test confirms:

```python
mock_sort_employees.assert_called_once_with([])
```

and:

```python
mock_display_all_employees.assert_called_once_with([])
```

These assertions prove the allowed read-only branch executed.

The test also confirms the denial message was not printed:

```python
self.assertNotIn(
    call("You do not have permission to use this option."),
    mock_print.mock_calls,
)
```

## Existing Administrator Tests

The existing console tests use a shared administrator login mock.

Because administrators receive all mapped permissions, the existing registration, update, deletion, backup, restoration, and viewing tests continued to pass.

This provides regression coverage showing that authorization did not break legitimate administrator workflows.

## Tests Added

Six automated tests were added during Day 74.

### Authorization-Policy Tests

1. `test_administrator_has_all_permissions`

   Confirms that an administrator receives every explicitly assigned permission.

2. `test_viewer_has_only_read_only_permissions`

   Confirms that a viewer receives read-only permissions and is denied management and database permissions.

3. `test_unknown_role_has_no_permissions`

   Confirms that an unsupported role receives an empty permission set.

4. `test_unknown_permission_is_denied`

   Confirms that even an administrator is denied an unknown permission.

### Console-Authorization Tests

5. `test_viewer_cannot_register_employee`

   Confirms that a viewer cannot reach the employee-registration function and that the denial is displayed and logged.

6. `test_viewer_can_view_all_employees`

   Confirms that a viewer can execute an allowed read-only employee-view action without seeing a denial message.

## Test Results

The complete automated suite passed:

```text
Ran 147 tests in 3.491s

OK

All automated tests passed.
```

The count increased from 141 to 147.

The updated breakdown is:

- 58 existing core tests
- 30 database tests
- 6 administrator-setup command tests
- 1 database-backup command test
- 2 database-restoration command tests
- 3 migration tests
- 15 console-integration tests
- 6 storage-verification tests
- 9 repository tests
- 5 authentication tests
- 8 user-service tests
- 4 authorization-policy tests

Total:

```text
147 automated tests
```

## README Updates

The README was updated to document:

- Active role-based authorization
- Named permission constants
- Role-to-permission sets
- Menu-to-permission mapping
- Default-deny behavior
- Administrator permissions
- Viewer read-only permissions
- Denied-action logging
- Four authorization-policy tests
- Fifteen console-integration tests
- 147 total automated tests

## Business Value

The Employee Management System now provides:

- Separation between authentication and authorization
- Explicit permission rules
- Administrator and viewer access levels
- Read-only viewer behavior
- Protection against unauthorized employee changes
- Protection against unauthorized database backup and restoration
- Denial of unknown roles
- Denial of unknown permissions
- Auditing of denied actions
- Tested administrator regression behavior
- Tested viewer denial behavior
- Tested viewer read-only behavior

## Current Limitation

The real SQLite database currently has the initial administrator account, but the console does not yet provide a secure administrator-only workflow for creating viewer accounts.

The viewer policy is implemented and tested, but account management still requires a controlled interface.

The menu also displays every option to every authenticated role. Restricted options are safely denied when selected, but role-specific menu presentation could eventually hide or label unavailable choices.

## Next Milestone

The next account-security milestone is a secure administrator-only user-account management workflow.

The application should eventually allow an administrator to:

- Create viewer accounts
- Validate role selection
- Prevent duplicate usernames
- Protect passwords before storage
- List user accounts without exposing password hashes
- Activate or deactivate accounts
- Record account-management activity

A viewer must never be allowed to create or modify user accounts.