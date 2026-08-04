# Day 21 Summary — Business Activity Logging

## Goal

Add a permanent activity log to the Employee Management System for troubleshooting, auditing, and monitoring.

## What Is Logging?

Logging records important application events in a file.

Unlike console messages, log entries remain available after the program and terminal close.

Example:

```text
2026-08-04 14:54:44,302 | INFO | Application started.
2026-08-04 14:54:51,690 | INFO | Employee EMP005 profile viewed.
```

## The activity_logger.py Module

A new module was created:

```text
activity_logger.py
```

It configures Python’s built-in `logging` module and provides:

```python
log_activity()
```

The main application imports it:

```python
from activity_logger import log_activity
```

## Log File Location

The log file is located beside the application modules:

```python
LOG_FILE = Path(__file__).with_name("activity.log")
```

The generated file is:

```text
activity.log
```

## Log Entry Format

Each entry contains:

```text
Timestamp | Severity | Message
```

The configured format is:

```python
"%(asctime)s | %(levelname)s | %(message)s"
```

### Timestamp

Shows when an event occurred.

### Severity

`INFO` represents a normal application event.

### Message

Describes what happened.

## Activities Recorded

The application now logs:

- Application startup
- Normal application shutdown
- Successful employee registration
- Employee profile viewing
- Payroll viewing
- Successful employee updates
- Successful employee deletion

## Returning Employee Information

The update and delete functions previously returned only:

```python
True
```

They were changed to return the affected employee dictionary after success.

This allows `run_program()` to access:

```python
employee["employee_id"]
```

and create an accurate log entry.

Failure and cancellation still return:

```python
False
```

## Protecting Confidential Information

Logs should not contain sensitive or private information such as:

- Passwords
- API keys
- Salary details
- Email addresses
- Phone numbers
- Confidential documents

The application logs employee IDs and actions because that is usually enough to identify the affected record.

## Append Behavior

New log entries are added to the bottom of `activity.log`.

Existing history is preserved instead of being replaced. This creates a chronological audit trail.

## Git Security

The following rule was added to `.gitignore`:

```gitignore
# Application log files
*.log
```

This keeps `activity.log` on the local computer and prevents it from being included in normal Git commits.

The rule does not delete the log file or stop logging.

## Verification

The activity log successfully recorded registration, profile viewing, payroll viewing, updating, deletion, startup, and shutdown.

Automated test results:

```text
Ran 9 system tests
OK

Ran 3 storage tests
OK
```

All twelve tests passed after logging was added.

## Business Importance

Activity logging helps businesses:

- Investigate problems
- Review important actions
- Maintain an audit history
- Monitor system activity
- Identify when records changed
- Support security investigations

## Day 21 Accomplishment

I created a dedicated logging module, recorded important employee-system activities, protected confidential information, excluded local logs from Git, and confirmed the changes with twelve passing automated tests.