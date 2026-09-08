# Manual Website Smoke Test — Days 106–131

## Purpose

Use this checklist to confirm that the main Workflow Automation website changes
from Day 106 through Day 131 work together in a real browser. This is a focused
smoke test: it checks the main user journeys, permissions, visible results, and
important lifecycle rules without repeating the complete automated suite.

The current project also contains Days 132–135 schedule controls. Those may be
visible on an Active workflow, but they are outside this checklist.

## What This Covers

| Days | Website capability |
| --- | --- |
| 106–110 | Workflow detail, editing, lifecycle states, and directory filtering |
| 111–114 | Ordered task storage, display, and administrator task creation |
| 115–120 | Task editing, resequencing, and activation readiness |
| 121 | Confirmed task deletion with automatic resequencing |
| 122–125 | Workflow execution start, history, completion, and failure |
| 126–130 | Historical task snapshots created with each workflow run |
| 131 | Administrator task-level completion and failure outcomes |

## Estimated Time

Allow approximately 20–30 minutes. Keep this file open beside the browser and
mark each checkbox as you complete it.

## Prerequisites

- The VS Code project folder is:
  `C:\Users\user\OneDrive\Documents\Projects\AI-Business-Automation-Platform`
- The current code is commit `40f28b5` or later.
- Python dependencies are installed in `.venv`.
- You have one active administrator account.
- You have one active viewer account for the permission checks.
- Use a development database because this test creates permanent workflow and
  execution-history records.

If the test workflow ID below already exists, replace `01` in every sample ID
with another unique number, such as `02`.

## Start the Website

From the main project folder in the VS Code terminal, run:

```powershell
.\.venv\Scripts\python.exe -m fastapi dev Projects\employee_management_system\web_app.py
```

Open `http://127.0.0.1:8000/`.

### Basic startup checks

- [ ] Open `http://127.0.0.1:8000/health`.
  - Expected: HTTP `200` and a healthy JSON response.
- [ ] Open `http://127.0.0.1:8000/workflows` while signed out.
  - Expected: the browser redirects to the login page.
- [ ] Sign in with the administrator account.
  - Expected: the shared ABAP dashboard displays the signed-in username.
- [ ] Open **Workflow Automation** from the dashboard.
  - Expected: the workflow directory loads without a server error.

## Test Data Used in This Checklist

Create the following workflow and tasks when instructed:

| Record | ID | Name or title |
| --- | --- | --- |
| Workflow | `WF-SMOKE-131-01` | Days 106–131 smoke workflow |
| Task 1 | `TASK-SMOKE-01-A` | Receive request |
| Task 2 | `TASK-SMOKE-01-B` | Review request |
| Task 3 | `TASK-SMOKE-01-C` | Notify requester |

## Part 1 — Workflow Detail and Lifecycle, Days 106–110

### Create the Draft workflow

- [ ] From `/workflows`, select **Create workflow**.
- [ ] Enter:
  - Workflow ID: `WF-SMOKE-131-01`
  - Workflow name: `Days 106–131 smoke workflow`
  - Status: `Draft`
  - Description: `Manual browser verification for workflow updates.`
- [ ] Submit the form.
  - Expected: the browser returns to the workflow directory.
- [ ] Open the new workflow.
  - Expected: the detail page shows the exact ID, Draft status, description,
    created time, and last-updated time.
- [ ] Confirm the page says no tasks have been added and no executions exist.

### Verify workflow editing

- [ ] Select **Edit workflow**.
- [ ] Confirm the workflow ID is visible and read-only.
- [ ] Change the name to `Days 106–131 verified workflow`.
- [ ] Change the description to `Updated during the manual smoke test.`
- [ ] Keep the status as Draft and save.
  - Expected: the detail page shows the new name and description.
  - Expected: the stable workflow ID has not changed.
  - Expected: the created timestamp is unchanged and the updated timestamp is
    current.

### Verify activation readiness

- [ ] Open **Edit workflow**, choose Active, and save before adding a task.
  - Expected: the page returns a safe validation error.
  - Expected: the workflow remains Draft because an empty workflow cannot be
    activated.
  - Expected: no raw SQLite error, traceback, or file path appears.

### Verify directory filtering

- [ ] Return to the workflow directory.
- [ ] Filter by Draft.
  - Expected: `Days 106–131 verified workflow` appears.
- [ ] Filter by Active.
  - Expected: the smoke workflow does not appear yet.
- [ ] Clear the filter.
  - Expected: all permitted workflows return.

## Part 2 — Ordered Tasks and Task Creation, Days 111–114

Return to the smoke workflow detail page.

### Add Task 1

- [ ] Select **Add task** and enter:
  - Task ID: `TASK-SMOKE-01-A`
  - Sequence number: `1`
  - Task title: `Receive request`
  - Instructions: `Confirm the request was received.`
  - Required: checked
- [ ] Submit.
  - Expected: the detail page shows Task 1 as Manual and Required.

### Add Task 2

- [ ] Add another task:
  - Task ID: `TASK-SMOKE-01-B`
  - Sequence number: `2`
  - Task title: `Review request`
  - Instructions: `Review the submitted business information.`
  - Required: unchecked
- [ ] Submit.
  - Expected: Task 2 appears after Task 1 and is labelled Optional.

### Add Task 3

- [ ] Add another task:
  - Task ID: `TASK-SMOKE-01-C`
  - Sequence number: `3`
  - Task title: `Notify requester`
  - Instructions: leave blank
  - Required: checked
- [ ] Submit.
  - Expected: Task 3 appears last and is labelled Required.
  - Expected: its instructions display `No instructions provided.`

### Check basic validation

- [ ] Try to add another task using the existing ID `TASK-SMOKE-01-A`.
  - Expected: the form returns a safe validation error and does not create a
    duplicate.
- [ ] Try to add a new task using sequence number `2`.
  - Expected: the form rejects the duplicate position and preserves the three
    original tasks.

## Part 3 — Task Maintenance, Days 115–120

### Edit task details

- [ ] Select **Edit task** beside `Review request`.
- [ ] Change the title to `Review and approve request`.
- [ ] Change the instructions to `Check the request and record a decision.`
- [ ] Change Required from unchecked to checked and save.
  - Expected: the detail page shows the changed title and instructions.
  - Expected: the task is now labelled Required.
  - Expected: its ID and sequence number remain unchanged.

### Resequence all tasks

- [ ] Select **Set task order**.
- [ ] Choose this complete order:
  1. `TASK-SMOKE-01-C` — Notify requester
  2. `TASK-SMOKE-01-A` — Receive request
  3. `TASK-SMOKE-01-B` — Review and approve request
- [ ] Save the order.
  - Expected: the workflow detail page displays exactly that order.
  - Expected: positions are contiguous: 1, 2, and 3.
  - Expected: task IDs, titles, instructions, and required states remain intact.

### Activate the workflow

- [ ] Select **Edit workflow**, change the status to Active, and save.
  - Expected: activation succeeds because at least one task exists.
  - Expected: the detail page shows Active.
  - Expected: the **Start execution** action appears.
- [ ] Return to `/workflows` and filter by Active.
  - Expected: the smoke workflow now appears in the Active results.

## Part 4 — Workflow and Task Execution History, Days 122–131

### Start a workflow execution

- [ ] Open the smoke workflow and select **Start execution** once.
  - Expected: the browser returns to the workflow detail page.
  - Expected: Execution history contains a new Running record with a stable
    `WFE-...` execution ID and start timestamp.
  - Expected: its summary says `Execution started.`
- [ ] Under that execution, find **Task outcomes**.
  - Expected: exactly three task snapshots appear in the order captured above.
  - Expected: each has a stable `WFTE-...` ID, Running status, start timestamp,
    `Not finished`, and `Task execution started.`

Write down the displayed `WFE-...` and three `WFTE-...` IDs if you want to
compare the records later.

### Record task-level outcomes

- [ ] For `Notify requester`, enter `Notification prepared.` and select
  **Mark task completed**.
  - Expected: its status becomes Completed.
  - Expected: it shows a finish timestamp and the saved result summary.
  - Expected: its task outcome form disappears.
- [ ] For `Receive request`, enter `Request could not be confirmed.` and select
  **Mark task failed**.
  - Expected: its status becomes Failed with a finish timestamp and summary.
  - Expected: its outcome form disappears.
- [ ] For `Review and approve request`, enter `Request approved.` and select
  **Mark task completed**.
  - Expected: its status becomes Completed with the saved summary.
- [ ] Refresh the page.
  - Expected: all three task outcomes remain unchanged and no completed or
    failed task shows another update form.

### Finish the parent workflow execution

- [ ] In the parent execution form, enter
  `Smoke run finished with one recorded task failure.`
- [ ] Select **Mark failed**.
  - Expected: the parent execution status becomes Failed.
  - Expected: the parent finish form disappears.
  - Expected: the three child outcomes remain displayed beneath that parent.
- [ ] Refresh the page again.
  - Expected: the parent and task results remain terminal and unchanged.

### Verify historical snapshots survive definition changes

- [ ] Edit the current task `Review and approve request` and rename it to
  `Review archived request`.
  - Expected: the current Workflow tasks section shows the new name.
  - Expected: the completed execution still shows the historical snapshot name
    `Review and approve request`.

This confirms that execution history does not silently rewrite itself when the
reusable workflow definition changes.

## Part 5 — Task Deletion and Resequencing, Day 121

The execution above already captured three tasks, so deletion can now verify
that current definition maintenance does not damage history.

- [ ] Select **Delete task** beside the current `Receive request` task.
  - Expected: a confirmation page names the exact task and explains that the
    action cannot be undone.
- [ ] Select Cancel once.
  - Expected: no task is deleted.
- [ ] Open the confirmation again and confirm deletion.
  - Expected: the current workflow now has two tasks.
  - Expected: the remaining tasks keep their relative order and are numbered
    contiguously as 1 and 2.
  - Expected: the historical execution still shows all three original task
    snapshots, including `Receive request`.
- [ ] Try to delete current tasks until only one remains, then attempt to delete
  the final task while the workflow is Active.
  - Expected: the last deletion is rejected with a safe message.
  - Expected: an Active workflow always retains at least one task.

## Part 6 — Viewer Permission Smoke Test

Sign out, then sign in as the viewer account.

- [ ] Open `/workflows`.
  - Expected: the viewer can read the workflow directory and use status filters.
- [ ] Open `WF-SMOKE-131-01`.
  - Expected: the viewer can read workflow details, current tasks, execution
    history, and all saved task outcomes.
- [ ] Confirm these controls are absent:
  - Edit workflow
  - Add task
  - Edit task
  - Delete task
  - Set task order
  - Start execution
  - Mark task completed or failed
  - Mark workflow execution completed or failed
- [ ] Manually open
  `/workflows/WF-SMOKE-131-01/edit` in the address bar.
  - Expected: `403 Access denied.`
- [ ] Manually open
  `/workflows/WF-SMOKE-131-01/tasks/new`.
  - Expected: `403 Access denied.`
- [ ] Manually open
  `/workflows/WF-SMOKE-131-01/tasks/resequence`.
  - Expected: `403 Access denied.`

## Part 7 — Accessibility and Responsive Check

These are short visual checks rather than a full accessibility audit.

- [ ] Navigate through the workflow directory and detail actions using Tab and
  Shift+Tab.
  - Expected: links, inputs, selects, and buttons receive visible keyboard focus.
- [ ] Confirm every tested input has a visible label.
- [ ] Confirm validation errors are written in text and do not rely only on
  color.
- [ ] Resize the browser to a narrow phone-like width.
  - Expected: workflow details, task lists, execution history, and forms remain
    readable without controls overlapping.
- [ ] Confirm statuses are written as Draft, Active, Inactive, Running,
  Completed, or Failed rather than communicated only by color.

## Pass Criteria

The Days 106–131 website smoke test passes when:

- [ ] The administrator can create, view, edit, filter, and activate a workflow.
- [ ] Empty workflow activation is rejected.
- [ ] The administrator can create, edit, resequence, and safely delete tasks.
- [ ] Task ordering remains contiguous after resequencing and deletion.
- [ ] An Active workflow cannot lose its final task.
- [ ] Starting an execution creates one parent record and an ordered snapshot of
  every task present at start time.
- [ ] Running task snapshots can each transition once to Completed or Failed.
- [ ] The parent execution can separately transition once to Completed or Failed.
- [ ] Historical task snapshots survive later task edits and deletion.
- [ ] The viewer can read workflows and history but cannot see or open management
  controls.
- [ ] No tested failure displays internal database paths, SQL, or traceback text.
- [ ] Keyboard focus, labels, written statuses, and narrow-screen layout remain
  usable.

## If a Step Fails

Record these details before restarting the server:

- The checklist step and URL.
- The signed-in role: administrator or viewer.
- The workflow, task, execution, or task-execution ID involved.
- The expected result and actual result.
- Any safe message displayed in the page.
- Relevant application terminal output, excluding passwords or session cookies.

Then run the automated regression suite from the main project folder:

```powershell
.\.venv\Scripts\python.exe Projects\employee_management_system\run_tests.py
```

The verified Day 135 baseline is **448 passing tests**. A lower discovered test
count or any failure means the local checkout or environment needs review.
