# Day 129 Summary — Execution Data Safety Review

## Goal

Review the new workflow- and task-execution foundation before adding mutable
task outcomes. The review confirms that the stored history, authorization path,
and browser security rules are suitable for controlled updates.

## Execution-History Protections

The parent-child model uses stable public IDs for both workflow executions
(`WFE-...`) and task executions (`WFTE-...`). These identifiers allow the
application to refer to one specific historical run and one specific historical
task without using database row numbers in browser routes.

Each execution record uses controlled state values and UTC timestamps. Parent
records store the workflow identity, a snapshot of its name, the account that
started it, and an overall status. Child records store the task ID, title,
sequence, status, timestamps, and result summary. Foreign keys preserve the
parent-child relationship and parameterized SQL protects database calls from
submitted text being treated as SQL.

## Security Review

Creating an execution remains layered rather than trusting the browser:

1. The browser loads the authenticated account from the signed session and
   rechecks it against SQLite.
2. The route requires `workflows.manage`; viewers remain read-only.
3. A state-changing browser request needs the session’s CSRF token.
4. The service reloads the account from SQLite and checks the stable user ID,
   active status, and permission again before writing.
5. The repository receives validated records and persists them with database
   constraints.

This is defense in depth. Hiding an action from the viewer interface is useful
for clarity, but the route and service provide the real authorization boundary.

## Verification

Focused workflow-execution tests confirmed that:

- An active workflow creates durable parent execution data.
- Starting a run produces its ordered task snapshots.
- Draft workflows cannot create a run.
- Viewer accounts cannot start a run.
- A user record whose identity does not match the saved account is rejected.
- Execution loading stays scoped to its workflow and returns records in newest
  first order.

The prior full regression suite passed with 428 tests before the Day 130
milestone was documented, showing that the Employee Management and earlier
Workflow Automation features remained intact.

## What the Review Allows Next

The data and security boundaries are ready for a task-outcome feature, but the
feature must still enforce three rules: only an authorized administrator may
write, the update must target the correct parent run and child task, and a
terminal outcome must not be silently replaced later.

## Threat-and-Response Reference

| Risk | Protection in the execution foundation |
| --- | --- |
| A viewer tries to start a workflow by manually sending a POST request. | The route and service both require `workflows.manage`; the UI alone is never trusted. |
| A signed-in administrator is later deactivated. | The live account lookup rejects the saved account before a write. |
| A browser request is forged from another website. | The state-changing route requires a signed-session CSRF token. |
| An attacker changes a route ID to point at another record. | Later repository operations use stable IDs, foreign keys, and scoped conditions. |
| A workflow is edited after a run begins. | The execution stores workflow and task snapshots rather than reusing current display values. |
| A database value contains SQL punctuation. | Parameterized SQL treats it as data, not as executable SQL. |
| A failure occurs during a repository write. | The repository rolls back its transaction rather than leaving a partial write from that operation. |

## How to Explain the Layers

The browser layer is responsible for the web experience: redirecting a missing
session to sign-in, accepting form data, validating CSRF tokens, and returning
safe responses. The service layer is responsible for business rules: which
roles may perform the action, whether the workflow is active, and whether the
live account remains valid. The repository layer is responsible for persistence:
SQL, database constraints, ordering, and transaction handling.

Keeping these responsibilities separate makes the application easier to change
and test. A future command-line worker could reuse the service layer without
copying HTML code, and a future browser page can reuse the repository without
embedding SQL in a route.

## Questions to Ask During Review

**Can the application show a past run after a task definition is deleted?**

Yes. The task-execution snapshot has its own task ID, title, sequence, and
result fields. It does not need the current task definition to explain the old
run.

**Why check authorization in both the route and service?**

The route protects the browser endpoint early. The service protects the
business action when it is called from any entry point, including future routes
or tools.

**Why is a signed session not enough by itself?**

The session proves prior authentication, but the saved account might have been
deactivated, removed, or changed since the session was issued. Live lookup
checks the current account state before sensitive work is saved.

## Next Step

Add protected task completion and failure updates and render each task outcome
under the workflow execution that owns it.
