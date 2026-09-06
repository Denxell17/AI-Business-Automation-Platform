# Day 104 Summary — Protected Workflow Directory

## Goal

Add a secure, read-only Workflow Automation directory that authenticated users
can access from the shared ABAP dashboard.

## Completed

- Added the explicit `workflows.view` permission.
- Granted workflow viewing to administrators and viewers.
- Kept workflow management separate and administrator-only.
- Added the protected `/workflows` browser route.
- Redirected unauthenticated visitors to the login page.
- Returned a safe `403 Access denied.` response when permission is missing.
- Logged denied workflow-directory access attempts.
- Loaded workflow records through the existing SQLite repository function.
- Added a safe database-error page that does not expose raw SQLite details.
- Created an accessible workflow-directory template.
- Added an accessible empty state for databases without workflows.
- Displayed stored workflow ID, name, status, created time, and updated time.
- Added a shared sidebar Workflows link with active-page highlighting.
- Changed the Workflow Automation dashboard card from Planned to Available.
- Kept schedules, tasks, and execution history clearly identified as future work.

## Files Changed

- `Projects/employee_management_system/authorization.py`
- `Projects/employee_management_system/web_app.py`
- `Projects/employee_management_system/templates/application_base.html`
- `Projects/employee_management_system/templates/home.html`
- `Projects/employee_management_system/templates/workflows.html`
- `Projects/employee_management_system/tests/test_authorization.py`
- `Projects/employee_management_system/tests/test_web_app.py`
- `Notes/day104_summary.md`

## Security Decisions

- `workflows.view` is a dedicated permission instead of relying on a broad
  employee or report permission.
- Both administrators and viewers may read workflow records.
- Only administrators retain `workflows.manage`, which protects future
  workflow-creation and workflow-update actions.
- The route checks for a valid authenticated session before loading records.
- The route checks `workflows.view` before calling the repository.
- Denied attempts are recorded in the activity log.
- SQLite exceptions are converted into a safe user-facing message; raw
  database details are not returned in the browser response.

## User Experience and Accessibility

- The Workflows sidebar link uses the shared navigation layout.
- The link has an active-page state and `aria-current="page"` on the workflow
  directory.
- The dashboard card now offers an “Open workflow directory” action.
- The empty state explains why no records are visible.
- The workflow table has a caption, table headers, and a labelled scrollable
  wrapper.
- Workflow status includes text, not color alone.

## Tests

New Day 104 coverage verifies:

- Unauthenticated users are redirected from `/workflows` to `/login`.
- An administrator can view an empty workflow directory.
- A viewer can view stored workflow records.
- The route returns `403` and logs access when a permission check fails.
- A SQLite loading error returns a safe `500` page without raw error details.
- The shared navigation includes the Workflows link.
- The dashboard links to the workflow directory.

Verification completed successfully:

- **139 focused authorization, workflow-service, and web tests passed**
- **367 total automated tests passed**
- No failures or errors remained

## Concepts Practiced

- Read-only route authorization
- Separate view and manage permissions
- Default-deny security
- Shared-template navigation
- Accessible empty states
- Safe database exception handling
- Activity logging for denied access
- Template-driven table rendering
- Dashboard status accuracy
- Focused and full regression testing

## Current ABAP Status

Day 104 is complete.

Workflow Automation now has a documented domain design, tested SQLite
persistence, secure administrator-only creation logic, and a protected
read-only browser directory available to administrators and viewers.

## Next Step

Day 105 should add an administrator-only workflow-creation form.

The form should use CSRF protection, validate submitted values through
`create_workflow()`, preserve safe user input after validation errors, and
redirect successfully created workflows back to the protected directory.

## Quiz — Questions and Answers

1. Why does ABAP use a separate `workflows.view` permission?

   It states exactly who may read workflow information and keeps viewing
   separate from more powerful management actions.

2. Why can viewers open the workflow directory but not create workflows?

   Viewers receive `workflows.view` only. Creating workflows requires the
   separate administrator-only `workflows.manage` permission.

3. What happens when someone visits `/workflows` without a valid session?

   The route returns a `303` redirect to the login page before loading any
   workflow records.

4. Why does the route check permission before calling the repository?

   It avoids loading protected data for an account that is not authorized to
   see it.

5. Why does the route catch `sqlite3.Error`?

   It lets ABAP show a safe, understandable error page instead of exposing
   technical database details to the user.

6. Why is a workflow-directory empty state useful?

   It tells an authorized user that the page works correctly but no workflow
   records have been created yet.

7. Why does the sidebar link use `url_for("workflow_directory")`?

   It connects the template to the named FastAPI route, which is safer than
   duplicating a URL string in multiple places.

8. Why did the dashboard card change from Planned to Available?

   The protected browser directory is now usable. Future scheduling, task,
   and execution features remain planned and are described honestly.