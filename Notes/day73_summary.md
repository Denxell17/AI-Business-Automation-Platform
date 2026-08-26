# Day 73 Summary — Interactive Console Login Protection

## Goal

Require users to authenticate before the Employee Management System loads employee records or displays the interactive menu.

The login workflow must:

- Ask for a username
- Hide password entry
- Authenticate against the SQLite user account
- Allow active users with correct credentials
- Reject missing users, incorrect passwords, and inactive accounts
- Prevent employee records from loading after failed authentication
- Prevent the menu from appearing after failed authentication
- Record successful and failed security events
- Preserve all existing console behavior and tests

## What Was Added

### Authentication Imports

The interactive application now imports:

```python
from getpass import getpass
```

`getpass()` collects the password without displaying its characters in the terminal.

The application also imports:

```python
from models import UserAccount, WorkforceSummary
```

`UserAccount` is used as the return type of the login function.

The authentication service is imported with:

```python
from user_service import authenticate_user_account
```

This allows the console layer to use the tested business logic created during Day 71.

## New Login Function

The following function was added near the top of `main.py`:

```python
def login_user() -> UserAccount | None:
    print()
    print("USER LOGIN")

    username = input("Username: ").strip()
    password = getpass("Password: ")

    authenticated_user = authenticate_user_account(
        username,
        password,
    )

    if authenticated_user is None:
        print("Authentication failed.")
        log_activity("Failed login attempt.")
        return None

    print(
        f"Signed in as {authenticated_user['username']} "
        f"({authenticated_user['role']})."
    )
    log_activity(
        f"User {authenticated_user['username']} logged in."
    )
    return authenticated_user
```

This function handles the command-layer login interaction.

It:

1. Displays the login heading.
2. Collects the username.
3. Removes surrounding username spaces with `.strip()`.
4. Collects the password securely with `getpass()`.
5. Sends both credentials to `authenticate_user_account()`.
6. Returns `None` when authentication fails.
7. Displays one uniform failure message.
8. Records the failed login attempt.
9. Displays the authenticated username and role after success.
10. Records the successful login.
11. Returns the complete authenticated user account.

## Login Return Type

The return type is:

```python
UserAccount | None
```

This means the function has two possible results:

```text
UserAccount → authentication succeeded
None        → authentication failed
```

A successful result contains information such as:

```python
{
    "user_id": 1,
    "username": "Dennis",
    "password_hash": "protected_hash",
    "role": "admin",
    "is_active": True,
}
```

The real stored password hash is never displayed by the console.

## Hidden Password Entry

The password is collected with:

```python
password = getpass("Password: ")
```

Unlike ordinary `input()`, `getpass()` does not display:

- Password characters
- Asterisks
- The password hash

The user types the password normally and presses Enter.

Hidden entry protects the password from people who may be watching the terminal.

## Username Cleaning

The username is collected with:

```python
username = input("Username: ").strip()
```

For example:

```python
"  dennis  "
```

becomes:

```python
"dennis"
```

The authentication system also retrieves usernames without treating uppercase and lowercase as different accounts.

Therefore:

```text
Dennis
dennis
DENNIS
```

can identify the same stored user account.

Passwords remain case-sensitive.

## Uniform Authentication Failure

When authentication fails, the function displays:

```python
print("Authentication failed.")
```

It does not reveal whether:

- The username was missing
- The password was incorrect
- The account was inactive
- The stored authentication record was invalid

This reduces the amount of account information exposed to an unauthorized person.

## Successful Login Message

After successful authentication, the application displays:

```python
print(
    f"Signed in as {authenticated_user['username']} "
    f"({authenticated_user['role']})."
)
```

A real administrator login produced:

```text
Signed in as Dennis (admin).
```

This confirms both the account identity and assigned role.

The role is currently displayed and stored, but role-specific menu restrictions have not been added yet.

## Console Startup Integration

The beginning of `run_program()` now contains:

```python
def run_program():
    display_header()
    log_activity("Application started.")

    authenticated_user = login_user()

    if authenticated_user is None:
        print("Employee Management System access denied.")
        log_activity("Application access denied.")
        return

    employees = load_employee_records()
```

The application flow is now:

```text
Start application
        ↓
Display application header
        ↓
Request username and password
        ↓
Authenticate the credentials
        ↓
Authentication successful?
    ├── No → deny access → stop
    └── Yes → load employee records → display menu
```

## Why Login Happens Before Loading Data

The login check is placed before:

```python
employees = load_employee_records()
```

This ordering is important.

If authentication fails:

```python
if authenticated_user is None:
```

the program reaches:

```python
return
```

`return` immediately exits `run_program()`.

Therefore:

- Employee records are not loaded
- The interactive menu is not displayed
- Employee actions cannot be selected
- The application returns to PowerShell

This protects employee information at the application boundary.

## Two Security Log Events

A failed login records:

```python
log_activity("Failed login attempt.")
```

This describes the authentication event.

The application then records:

```python
log_activity("Application access denied.")
```

This describes the application’s response.

They are related but not duplicates:

```text
Authentication failed
        ↓
Application denied access
```

A successful login records:

```python
log_activity(
    f"User {authenticated_user['username']} logged in."
)
```

These messages create a useful security audit trail.

## Login Tests

A new test class was added to `tests/test_main.py`:

```python
class TestMainAuthentication(unittest.TestCase):
```

This separates direct login-function tests from the existing console repository and database synchronization tests.

### Successful Login Test

The test:

```python
test_login_user_returns_authenticated_account
```

confirms that:

- Username input is collected
- Surrounding username spaces are removed
- Password input uses `getpass()`
- The authentication service receives the cleaned username and password
- The authenticated user account is returned
- The signed-in username and role are displayed
- The successful login is recorded

The test uses an example authenticated account:

```python
user_account = {
    "user_id": 1,
    "username": "Dennis",
    "password_hash": "protected_hash",
    "role": "admin",
    "is_active": True,
}
```

The mocked username contains spaces:

```python
return_value="  dennis  "
```

The expected service call uses:

```python
"dennis"
```

This confirms that `.strip()` cleaned the username before authentication.

### Failed Login Test

The test:

```python
test_login_user_returns_none_after_failed_authentication
```

confirms that:

- A failed authentication service result returns `None`
- The username and password are passed correctly
- The console displays `Authentication failed.`
- The failed attempt is recorded
- No authenticated user account is returned

## Duplicate Test Method Correction

During testing, the failed-login method was accidentally defined twice with the same name:

```python
def test_login_user_returns_none_after_failed_authentication(
```

Python classes cannot keep two methods with the same name.

The later definition replaces the earlier definition, meaning `unittest` would only discover the last one.

The duplicate block was removed, leaving one correct failed-login test.

The final file was checked and no duplicate test names remained.

## Shared Successful Login Mock

Existing `run_program()` tests previously started directly with employee loading and menu interaction.

After login protection was added, those tests also needed an authenticated user.

The following setup method was added inside:

```python
class TestMainDatabaseSynchronization(unittest.TestCase):
```

The setup method is:

```python
def setUp(self):
    self.login_patcher = patch("main.login_user")
    self.mock_login_user = self.login_patcher.start()
    self.mock_login_user.return_value = {
        "user_id": 1,
        "username": "Dennis",
        "password_hash": "protected_hash",
        "role": "admin",
        "is_active": True,
    }
    self.addCleanup(self.login_patcher.stop)
```

## How `setUp()` Works

`unittest` automatically runs:

```python
setUp()
```

before every test method in the class.

The capital `U` is required.

This name would not work automatically:

```python
setup()
```

Python is case-sensitive, and `unittest` specifically looks for `setUp()`.

## Shared Login Patch

This line creates the patch:

```python
self.login_patcher = patch("main.login_user")
```

This line activates it:

```python
self.mock_login_user = self.login_patcher.start()
```

This result simulates a successful administrator login:

```python
self.mock_login_user.return_value = {
    "user_id": 1,
    "username": "Dennis",
    "password_hash": "protected_hash",
    "role": "admin",
    "is_active": True,
}
```

The shared patch prevents every older `run_program()` test from waiting for a real username and password.

## Automatic Patch Cleanup

The setup method uses:

```python
self.addCleanup(self.login_patcher.stop)
```

This tells `unittest` to stop the patch after each test.

Cleanup still runs when a test fails.

This prevents one test’s mock from leaking into another test.

## Failed-Login Startup Test

The following integration test was added:

```python
test_failed_login_stops_before_employee_records_are_loaded
```

It overrides the normal successful setup result:

```python
self.mock_login_user.return_value = None
```

It then calls:

```python
run_program()
```

The test confirms:

```python
self.mock_login_user.assert_called_once_with()
```

The login function was called exactly once without arguments.

It also confirms:

```python
mock_load_employee_records.assert_not_called()
```

This is the main data-protection assertion.

It proves that failed authentication prevents employee records from being loaded.

The test also confirms the denied-access message and security activity logs.

## Successful-Startup Assertion

The existing startup test was strengthened with:

```python
self.mock_login_user.assert_called_once_with()
```

Its final assertions confirm:

```python
self.mock_login_user.assert_called_once_with()
mock_load_employee_records.assert_called_once_with()
```

This verifies the normal successful path:

```text
Login succeeds
      ↓
Employee records load
```

The failed-login test verifies the opposite path:

```text
Login fails
      ↓
Employee records do not load
```

Together, these tests protect both branches.

## Tests Added

Three automated tests were added during Day 73.

1. `test_login_user_returns_authenticated_account`

   Confirms successful command-layer authentication, username cleaning, hidden password collection, returned user data, displayed identity and role, and successful-login logging.

2. `test_login_user_returns_none_after_failed_authentication`

   Confirms that failed authentication returns `None`, displays a uniform failure message, and records the failed login attempt.

3. `test_failed_login_stops_before_employee_records_are_loaded`

   Confirms that failed startup authentication prevents employee loading, displays access denied, and records the application denial.

An existing startup test was also strengthened to confirm that `login_user()` is called before normal employee workflows proceed.

## Test Results

The complete automated suite passed:

```text
Ran 141 tests in 2.384s

OK

All automated tests passed.
```

The count increased from 138 to 141.

The updated breakdown is:

- 58 existing core tests
- 30 database tests
- 6 administrator-setup command tests
- 1 database-backup command test
- 2 database-restoration command tests
- 3 migration tests
- 13 console-integration tests
- 6 storage-verification tests
- 9 repository tests
- 5 authentication tests
- 8 user-service tests

Total:

```text
141 automated tests
```

## Real Successful Login Verification

The real interactive application was started with `main.py`.

The administrator entered:

```text
Username: Dennis
```

The password remained hidden.

The application displayed:

```text
Signed in as Dennis (admin).
```

Only after successful authentication did the employee menu appear.

The administrator selected:

```text
14. Exit
```

The program closed safely without changing employee data.

## Real Failed Login Verification

The interactive application was started again.

A valid username and incorrect password were entered.

The application displayed:

```text
Authentication failed.
Employee Management System access denied.
```

The employee menu did not appear.

The program returned directly to PowerShell.

This confirmed that a known username is not sufficient without the correct password.

## Activity-Log Verification

The activity log was inspected with:

```powershell
Get-Content Projects\employee_management_system\logs\activity.log -Tail 10
```

The successful-login sequence included:

```text
Application started.
User Dennis logged in.
Application closed.
```

The failed-login sequence included:

```text
Application started.
Failed login attempt.
Application access denied.
```

This confirms that the application records both authentication outcomes.

## README Updates

The README was updated to state that the interactive console now:

- Requires credential authentication
- Authenticates before loading employee records
- Authenticates before displaying the menu
- Records successful and failed security activity
- Has 13 console-integration tests
- Has 141 total automated tests

The completed authentication milestone was removed from the future roadmap.

## Business Value

The Employee Management System now provides:

- A protected application entry point
- Hidden password entry
- SQLite-backed credential verification
- Rejection of incorrect credentials
- Rejection of inactive accounts
- Uniform authentication failure
- Prevention of unauthorized employee-data loading
- Prevention of unauthorized menu access
- Successful-login audit records
- Failed-login audit records
- Denied-access audit records
- Tested integration with existing console workflows

## Current Limitation

The application authenticates users and stores their roles, but both supported roles can currently reach the same menu after successful login.

The roles are:

```text
admin
viewer
```

The application does not yet restrict individual menu actions according to those roles.

## Next Milestone

The next authentication milestone is role-based authorization.

The application should eventually decide:

```text
admin  → may use management and recovery actions
viewer → may use read-only employee and report actions
```

Authentication answers:

```text
Who is this user?
```

Authorization will answer:

```text
What is this authenticated user allowed to do?
```