# Day 105 Summary — Administrator Workflow Creation Form

## Goal

Add a secure browser form that lets authorized administrators create workflow
definitions through the existing Workflow Automation service layer.

## Completed

- Added the protected `GET /workflows/new` workflow-creation form route.
- Added the protected `POST /workflows/new` workflow-creation submission
  route.
- Required an authenticated session before form access or submission.
- Required the administrator-only `workflows.manage` permission.
- Reused signed-session CSRF protection for workflow submissions.
- Delegated validation and SQLite saving to `create_workflow()`.
- Added Post/Redirect/Get navigation back to `/workflows` after success.
- Logged successful web workflow creation.
- Logged denied workflow-creation access and invalid CSRF attempts.
- Returned a safe `403` response for unauthorized, viewer, and invalid-CSRF
  requests.
- Returned the form with a safe `400` validation message when the service
  rejects input.
- Preserved submitted workflow ID, name, description, and status after a
  validation error.
- Added the administrator-only Create workflow action to the workflow
  directory.
- Kept the action hidden from viewers.
- Created an accessible workflow form with labels, required fields, a status
  selector, description textarea, cancel action, and error alert.
- Extended shared form styling to include textareas.

## Files Changed

- `Projects/employee_management_system/web_app.py`
- `Projects/employee_management_system/templates/workflows.html`
- `Projects/employee_management_system/templates/workflow_form.html`
- `Projects/employee_management_system/static/styles.css`
- `Projects/employee_management_system/tests/test_web_app.py`
- `Notes/day105_summary.md`

## Security Decisions

- The form and POST route both require `workflows.manage`.
- Viewer accounts are denied before CSRF validation or service-layer calls.
- The route reloads the authenticated account through the existing session
  helper before authorization.
- Every successful state-changing request requires a valid signed-session CSRF
  token.
- Invalid CSRF submissions never call `create_workflow()`.
- The browser route delegates validation, account revalidation, status
  allowlisting, timestamp generation, and SQLite insertion to
  `create_workflow()`.
- Validation and storage details are not exposed in browser error messages.
- Denied access, invalid CSRF submissions, and successful workflow creation
  are recorded in the activity log.

## User Experience and Accessibility

- Administrators can open Create workflow from the workflow directory.
- Viewers can browse workflows but cannot see the creation action.
- The form uses semantic labels for Workflow ID, Workflow name, Status, and
  Description.
- Status choices match the server-side `draft`, `active`, and `inactive`
  allowlist.
- The default status is Draft.
- Errors use `role="alert"` so assistive technology announces them.
- The form preserves entered values after a validation error.
- The description textarea uses the same dark-surface, hover, and visible
  keyboard-focus styling as the other form fields.
- Successful submission returns the user to the workflow directory instead of
  re-submitting on browser refresh.

## Tests

New Day 105 coverage verifies:

- Unauthenticated visitors are redirected from the workflow-create form.
- Administrators can view the workflow-create form and its CSRF token.
- Viewers cannot view the workflow-create form.
- Administrators can submit a valid CSRF-protected workflow form.
- Successful submission redirects to the workflow directory.
- Successful creation is recorded in the activity log.
- Invalid CSRF tokens return `403`, are logged, and do not call the service.
- Service-layer validation failures return `400` and preserve entered values.
- Viewers cannot submit the workflow-create POST route.
- The workflow-directory Create workflow action is visible only to
  administrators.
- The stylesheet remains available after textarea styling is added.

Verification completed successfully:

- **146 focused authorization, workflow-service, and web tests passed**
- **374 total automated tests passed**
- No failures or errors remained

## Concepts Practiced

- GET and POST route separation
- Administrator-only form access
- Signed-session CSRF protection
- Default-deny authorization
- Service-layer reuse
- Post/Redirect/Get navigation
- Safe validation-error handling
- Form-value preservation
- Activity logging
- Conditional template actions
- Accessible labels, alerts, and focus states
- Full regression testing

## Current ABAP Status

Day 105 is complete.

Workflow Automation now provides a secure browser path for administrators to
create workflow definitions and a protected directory where administrators and
viewers can read them.

## Next Step

Day 106 should add a protected workflow detail page and administrator-only
workflow lifecycle updates.

The feature should load one workflow safely, return a clear missing-record
page, and allow authorized administrators to update a workflow name,
description, or status through CSRF-protected service-layer logic.

## Quiz — Questions and Answers

1. Why does the browser POST route call `create_workflow()` instead of writing
   directly to SQLite?

   The service centralizes authorization, live account revalidation,
   normalization, status validation, timestamps, and safe repository calls.

2. Why does the create form require `workflows.manage` instead of
   `workflows.view`?

   Viewing data is less powerful than creating it. Separate permissions follow
   least privilege and prevent viewers from changing workflow data.

3. What does CSRF protection prevent in this form?

   It prevents a third-party site from causing a signed-in administrator’s
   browser to submit an unwanted workflow-creation request.

4. Why is a CSRF check performed before `create_workflow()`?

   A forged request should be rejected before validation logic or database work
   is reached.

5. Why does the form return `400` when `create_workflow()` returns `False`?

   The submitted workflow could not pass the server-side creation rules, so the
   user receives a safe form error and can correct the values.

6. Why are submitted values returned after a validation error?

   It avoids forcing the administrator to type valid information again after
   correcting the failed field.

7. Why is the Create workflow action hidden from viewers?

   The interface reflects the viewer’s limited permission, while the POST
   route still independently enforces the same security boundary.

8. Why use a `303` redirect after successful form submission?

   It implements Post/Redirect/Get, so refreshing the directory page does not
   repeat the create request.