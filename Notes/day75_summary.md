# Day 75 Summary — Administrator-Only Viewer Account Registration

## Goal

Add a secure, tested, administrator-only workflow for creating viewer accounts through the Employee Management System console.

The workflow must:

- Add a dedicated user-account management permission
- Allow only active administrators to create viewer accounts
- Prevent viewers from creating accounts
- Prevent inactive administrators from creating accounts
- Assign the `viewer` role automatically
- Protect passwords before database storage
- Reject duplicate usernames case-insensitively
- Hide password input
- Require password confirmation
- Reject missing usernames and passwords
- Avoid logging unsuccessful registrations as successful
- Connect account creation to the interactive console
- Record successful account creation
- Record denied account-management attempts
- Preserve all existing application behavior

## Starting Point

Before Day 75, the application already supported:

- Secure PBKDF2 password hashing
- Password verification
- SQLite user-account storage
- Case-insensitive username lookup
- Duplicate-username rejection
- Initial administrator creation
- User authentication
- Inactive-account rejection
- Administrator and viewer roles
- Role-based authorization
- Default-deny permission checks
- Interactive console login
- Denied-action activity logging
- 147 automated tests

The application had a viewer authorization policy, but administrators could not yet create viewer accounts through the console.

## New User-Management Permission

The following permission was added to `authorization.py`:

```python
MANAGE_USER_ACCOUNTS = "users.manage"
```

This permission represents user-account management actions.

The naming follows the existing resource-and-action pattern:

```text
users.manage
```

The resource is:

```text
users
```

The action is:

```text
manage
```

## Administrator Permission Update

`MANAGE_USER_ACCOUNTS` was added to the administrator permission set:

```python
"admin": {
    REGISTER_EMPLOYEE,
    VIEW_EMPLOYEE,
    VIEW_PAYROLL,
    UPDATE_EMPLOYEE,
    DELETE_EMPLOYEE,
    EXPORT_REPORT,
    BACKUP_DATABASE,
    RESTORE_DATABASE,
    MANAGE_USER_ACCOUNTS,
},
```

An administrator can therefore perform account-management actions.

## Viewer Permission Policy

`MANAGE_USER_ACCOUNTS` was not added to the viewer permission set.

The viewer continues to receive only:

```python
"viewer": {
    VIEW_EMPLOYEE,
    VIEW_PAYROLL,
    EXPORT_REPORT,
},
```

Therefore:

```text
Administrator + users.manage → allowed
Viewer + users.manage        → denied
```

## Default-Deny Protection

Unknown roles continue to receive:

```python
set()
```

An empty permission set means every permission check returns `False`.

Unknown permissions are also denied, even for administrators.

The security rule remains:

```text
Not explicitly allowed → denied
```

## Authorization Test Updates

The four existing authorization-policy tests were expanded to include:

```python
MANAGE_USER_ACCOUNTS
```

The updated tests confirm:

- Administrators receive `users.manage`
- Viewers are denied `users.manage`
- Unknown roles are denied `users.manage`
- Unknown permissions remain denied

No new authorization-policy test method was necessary because the existing permission loops already test every listed permission.

## Viewer Registration Business Function

A new business function was added to `user_service.py`:

```python
def register_viewer_account(
    current_user: UserAccount,
    username: str,
    password: str,
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

    return register_user_account(
        username,
        password,
        "viewer",
        database_file,
    )
```

This function controls who may create viewer accounts.

## `current_user`

The `current_user` parameter represents the already authenticated account attempting the action.

For example:

```python
{
    "user_id": 1,
    "username": "Dennis",
    "password_hash": "protected_hash",
    "role": "admin",
    "is_active": True,
}
```

The function does not trust only the supplied username.

It checks the authenticated account’s:

- Active status
- Role permissions

## Active-Account Requirement

The first security condition is:

```python
not current_user["is_active"]
```

When:

```python
"is_active": False
```

the expression becomes:

```python
not False → True
```

The function immediately returns:

```python
False
```

An inactive administrator still has the role name `admin`, but is not allowed to manage accounts.

## Permission Requirement

The second security condition is:

```python
not user_has_permission(
    current_user,
    MANAGE_USER_ACCOUNTS,
)
```

For an administrator:

```text
users.manage in administrator permissions → True
not True                                  → False
```

For a viewer:

```text
users.manage in viewer permissions → False
not False                           → True
```

A viewer therefore enters the rejection branch and receives:

```python
return False
```

## Combined Security Condition

The complete condition is:

```python
if (
    not current_user["is_active"]
    or not user_has_permission(
        current_user,
        MANAGE_USER_ACCOUNTS,
    )
):
    return False
```

The function rejects registration when either condition is true:

```text
Account inactive
        OR
Permission missing
```

Both requirements must be satisfied:

```text
Account active
        AND
users.manage permission allowed
```

## Short-Circuit `or`

Python evaluates `or` from left to right.

If the account is inactive:

```python
not current_user["is_active"]
```

is already `True`.

Python does not need the second condition to decide that the complete expression is true.

The function returns `False` immediately.

This prevents an inactive account from continuing through account registration.

## Fixed Viewer Role

The function does not accept a role parameter.

Instead, it calls:

```python
return register_user_account(
    username,
    password,
    "viewer",
    database_file,
)
```

The role is fixed as:

```python
"viewer"
```

This prevents an administrator from accidentally creating another administrator through this workflow.

The business rule is:

```text
Viewer registration workflow → always creates viewer role
```

## Password Protection Reuse

`register_viewer_account()` reuses:

```python
register_user_account()
```

That function hashes the password before calling the database layer.

The complete password flow is:

```text
Plain password entered
        ↓
register_viewer_account()
        ↓
register_user_account()
        ↓
hash_password()
        ↓
Protected password hash
        ↓
SQLite database
```

The plain password is never stored in SQLite.

## Duplicate Username Protection

Viewer registration also reuses the existing SQLite duplicate-username protection.

Usernames are case-insensitively unique.

For example:

```text
Analyst
analyst
```

are treated as the same username.

If `Analyst` already exists, attempting to create `analyst` returns:

```python
False
```

The original account remains unchanged.

## Viewer Registration Service Tests

Four user-service tests were added.

### Administrator Can Register Viewer

```python
test_administrator_can_register_viewer_account
```

This test confirms:

- The current user is an active administrator
- Viewer registration returns `True`
- The viewer exists in SQLite
- The stored role is `viewer`
- The account is active
- The plain password is not stored
- The stored hash verifies the original password

### Viewer Cannot Register Viewer

```python
test_viewer_cannot_register_viewer_account
```

This test creates an active viewer as the current user.

It confirms:

```python
self.assertFalse(registration_result)
self.assertIsNone(stored_user)
```

The viewer has an active account but lacks:

```text
users.manage
```

The new user is not stored.

### Inactive Administrator Cannot Register Viewer

```python
test_inactive_administrator_cannot_register_viewer_account
```

This test uses:

```python
"role": "admin",
"is_active": False,
```

It confirms that the correct role alone is insufficient.

The administrator must also be active.

### Duplicate Viewer Username Is Rejected

```python
test_administrator_cannot_register_duplicate_viewer_username
```

The test first creates:

```text
Analyst
```

It then attempts to create:

```text
analyst
```

The first registration returns `True`.

The duplicate registration returns `False`.

The test also confirms:

- The original username remains `Analyst`
- The original role remains `viewer`
- The original password still verifies
- The second password does not verify
- The failed duplicate attempt does not overwrite the account

## New Command Layer

A new file was created:

```text
Projects/employee_management_system/user_account_setup.py
```

It contains:

```python
def run_viewer_account_registration(
    current_user: UserAccount,
    username: str,
    password: str,
    database_file: Path = DATABASE_FILE,
) -> bool:
    registration_succeeded = register_viewer_account(
        current_user,
        username,
        password,
        database_file,
    )

    if not registration_succeeded:
        print("Viewer account was not created.")
        return False

    print("Viewer account created successfully.")
    return True
```

## Command-Layer Responsibility

The service layer decides:

```text
Is this account registration allowed?
```

The command layer communicates:

```text
What result should the console user see?
```

The command layer does not duplicate:

- Permission rules
- Active-status rules
- Password hashing
- Duplicate checks
- SQLite insertion logic

It delegates those responsibilities to the business and database layers.

## Successful Command Result

When the