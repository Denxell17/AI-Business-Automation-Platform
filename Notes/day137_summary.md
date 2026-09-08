# Day 137 Summary — Business Timezone and Recovery Window

## Objective

Define one understandable time policy before schedule occurrences are stored.
ABAP keeps database timestamps in UTC, while administrators enter schedule
times using the business clock.

## Business Timezone Decision

`WORKFLOW_TIME_ZONE` is configured as `Asia/Shanghai`. A schedule such as
`09:30` means 9:30 AM in that business timezone. ABAP converts the occurrence
to UTC before it is saved.

```text
Saved business time:  2026-09-08 09:30 Asia/Shanghai
Stored occurrence:    2026-09-08 01:30:00+00:00
```

This keeps SQLite timestamps consistent while browser JavaScript can display
them in the viewer’s local format. The server’s own timezone cannot silently
move a schedule after Docker or cloud deployment.

Python’s standard `zoneinfo` implementation is used when timezone data is
available. Windows installations without the optional timezone database use a
UTC+08:00 fallback for the configured Shanghai zone. The current business rule
therefore works without another installation dependency.

## Missed-Time Policy

A daily or weekly schedule is due from its configured minute until, but not
including, five minutes later.

```text
Configured time: 09:30
Eligible:         09:30:00 through 09:34:59
Expired:          09:35:00
```

The window tolerates a short restart or a runner that checks once per minute.
ABAP does not perform unlimited catch-up after long downtime. An old occurrence
is skipped instead of unexpectedly starting hours or days later.

The window is defined by `DEFAULT_SCHEDULE_GRACE_MINUTES`, allowing a future
deployment to configure it without rewriting the evaluator.

## Next Eligible Time

- Before today’s daily time, the next occurrence is today.
- During the grace window, the current occurrence remains eligible.
- After the window, a daily rule moves to tomorrow.
- A weekly rule finds the next configured weekday.
- Manual and disabled rules have no automatic next occurrence.

Returned occurrence timestamps are timezone-aware UTC ISO 8601 strings.

## Why This Matters

The administrator’s schedule time, the business timezone used to interpret it,
and the UTC occurrence stored in the database are separate concepts. Making
them explicit prevents time changes during PostgreSQL migration, Dockerization,
or cloud deployment.

## Files and Verification

Changed files include `config.py`, `schedule_service.py`, and the focused
eligibility tests. Tests confirm Shanghai-to-UTC conversion, the exact
five-minute boundary, weekday matching, next-occurrence calculation,
timezone-aware input requirements, and invalid-timezone rejection.

## Result

Day 137 establishes a stable clock contract: schedules use `Asia/Shanghai`,
persisted occurrences use UTC, and only a short five-minute recovery window is
eligible. Day 138 uses that UTC occurrence time to prevent duplicate claims.
