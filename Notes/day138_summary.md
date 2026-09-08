# Day 138 Summary — Duplicate Schedule-Occurrence Protection

## Objective

Prevent repeated scheduler checks from preparing the same daily or weekly
occurrence more than once. This protection belongs in SQLite because an
in-memory flag disappears after a restart and cannot coordinate two runners.

## New Occurrence Ledger

The database now creates `workflow_schedule_occurrences`. Each row records one
claimed schedule occurrence:

| Column | Purpose |
|---|---|
| `occurrence_id` | Stable public identifier for one claim. |
| `schedule_id` | Schedule that became due. |
| `workflow_id` | Parent workflow for scoped history loading. |
| `scheduled_for_utc` | Exact UTC occurrence being claimed. |
| `claimed_at` | UTC time when the scheduler reserved it. |

The pair `(schedule_id, scheduled_for_utc)` is unique. Even if the scheduler
checks every minute inside the five-minute window, SQLite stores only one claim
for that occurrence. An index on `(workflow_id, scheduled_for_utc)` supports
future workflow history, and foreign keys reject missing parents.

## Atomic Claim Operation

`claim_workflow_schedule_occurrence()` uses one database statement to insert a
claim only when the schedule still exists, still belongs to the expected
workflow, remains enabled, belongs to an Active workflow, and has not already
been claimed for that UTC time.

This closes the gap between read-only evaluation and the write. If an
administrator disables the schedule after it was read but before it is
claimed, the insert safely does nothing.

`INSERT OR IGNORE` works with the unique occurrence rule to make repetition
safe. The first valid caller receives `True`; later callers receive `False` and
cannot create another row.

## Claim Orchestration

```text
Load active enabled schedules
        ↓
Evaluate each using the explicit current time
        ↓
Build one UTC identity for each due occurrence
        ↓
Atomically claim each occurrence
        ↓
Return only claims created by this caller
```

`claim_due_workflow_schedules()` provides this flow. It still does not start
workflow tasks. The occurrence ledger is the handoff boundary Days 140–142 can
use when creating a scheduled execution.

## Data-Safety Decisions

- Occurrence history is append-only.
- UTC ISO 8601 timestamps provide stable identities.
- Database uniqueness is the final duplicate guard.
- Active and enabled state is checked inside the insert.
- SQLite errors roll back and remain visible to the future runner.
- Read-only evaluation never changes employee or workflow records.

## Files and Verification

The model, database repository, schedule service, and focused test file were
updated. Tests confirm that the first due check creates one claim, repeated
checks create none, the stored record matches the returned claim, and a
disabled schedule cannot be claimed using stale evaluation information.

## Result

Day 138 provides persistent idempotency. ABAP can distinguish “this rule is
due” from “this exact due time has already been reserved.” Day 139 integrates
the evaluator into the protected workflow experience.
