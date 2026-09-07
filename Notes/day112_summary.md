# Day 112 Summary — Workflow Task Display

## Goal

Show each workflow's saved tasks on its protected detail page in the correct
business-process order.

## Completed

- Loaded saved tasks on the protected workflow detail route.
- Displayed tasks in sequence order with titles, instructions, manual type,
  and Required/Optional labels.
- Preserved stored sequence numbers, including gaps, in an ordered list.
- Added empty-task and missing-instructions messages.

## Why and Security Decisions

Administrators and viewers can now inspect the steps belonging to a workflow.
The route uses the existing workflows.view permission before loading tasks.
Jinja autoescaping protects task text, and database failures return the existing
generic safe message. No task-writing route is introduced.

## How It Works

After the detail route authorizes the user and loads the workflow, it calls
`load_workflow_tasks()` with the normalized saved workflow ID. The repository
returns records in sequence order. The template renders an ordered list and
uses each stored sequence number as the list-item value, so intentional gaps
remain visible.

Task type, required status, instructions, and fallback messages are written in
plain text. Jinja's default autoescaping treats saved task text as content
rather than executable HTML.

## Files Changed

- Projects/employee_management_system/web_app.py
- Projects/employee_management_system/templates/workflow_detail.html
- Projects/employee_management_system/tests/test_workflow_web_lifecycle.py
- Notes/day112_summary.md

## Security and User Experience

- Authentication and `workflows.view` are checked before task loading.
- Administrators and viewers receive the same read-only task information.
- Anonymous visitors redirect to login without triggering task queries.
- Database errors return the existing generic workflow-loading response.
- Missing instructions and empty task lists have clear written messages.

## Verification

- All 394 automated tests passed, including Day 111 storage tests and the new
  browser tests. git diff --check passed.
- Added tests for both roles, ordering, sequence gaps, required/optional labels,
  escaped text, empty tasks, anonymous access, and safe database errors.
- Installed declared project dependencies in the ignored local .venv using the
  bundled newer Python runtime, resolving Day 111's missing-FastAPI blocker.

## Concepts Practiced

- Parent-record detail composition
- Ordered Jinja rendering
- Template autoescaping
- Permission reuse for related read-only data
- Accessible empty states
- Dependency-environment troubleshooting

## Current ABAP Status

Workflow tasks support persistence and protected detail-page viewing.
Task creation services/forms and the task-dependent activation rule remain
future work.

Day 112 is complete.

## Next Step

Add an administrator-only task creation service with live account revalidation
and input validation before introducing a browser form.
