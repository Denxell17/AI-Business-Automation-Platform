# Day 123 Summary — Workflow Execution Completion and Failure

## Goal

Extend the Day 122 execution-start record into a complete workflow-level
lifecycle. An administrator needs a safe way to say whether a run finished
successfully or failed, while preserving a reliable historical record.

## Completed

- Added a repository update for a running workflow execution.
- Added the administrator-only `finish_workflow_execution_record()` service.
- Allowed only two terminal outcomes: `completed` and `failed`.
- Stored a server-generated UTC `finished_at` timestamp.
- Stored a trimmed, safe result summary that explains the outcome.
- Added protected browser controls on a running execution record.
- Added Post/Redirect/Get navigation after a successful terminal update.
- Logged successful completion or failure and rejected CSRF submissions.

## Lifecycle Rule

An execution begins as `running`. It may transition exactly once to either
`completed` or `failed`.

The SQLite update includes both the execution ID and `status = 'running'` in
its condition. This means the first successful terminal update changes the
status. Any later attempt affects zero records and is rejected. This protects
the historical result from accidental edits or conflicting browser requests.

## Security Decisions

- Only active administrators with `workflows.manage` can finish an execution.
- The service reloads the user account from SQLite rather than trusting session
  role information alone.
- The browser validates its signed-session CSRF token before calling the
  service.
- Only allowlisted terminal statuses reach SQLite.
- Browser errors do not expose database details.
- Viewers can read history but cannot see or use terminal controls.

## Tests

Focused execution tests verify that viewers cannot finish a record, an
administrator can complete a running record, the stored summary and finish time
are retained, and a second terminal update is rejected. The complete regression
suite remains the final protection against unrelated regressions.

## What Dennis Should Be Able to Explain

- Why `running`, `completed`, and `failed` are separate states.
- Why an execution needs a finished timestamp only after it reaches an outcome.
- Why the SQL condition prevents completed records from being changed again.
- Why service-layer account revalidation and browser CSRF checks both matter.

## Next Step

Review the workflow-level lifecycle as a stable boundary before adding a
separate task-execution record for each individual workflow step.
