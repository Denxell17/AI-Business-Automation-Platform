# Day 109 Summary — Workflow Status Filtering

## Goal

Help users find workflows by lifecycle state without creating a new permission
or unsafe database query path.

## Completed

- Added a workflow-directory status filter for Draft, Active, and Inactive.
- Allowlisted filter values against the server-side workflow status constants.
- Returned a safe `400` response for an unknown filter value.
- Preserved the selected status in the rendered form.
- Kept filtering available to both administrators and viewers.

## Why

The directory remains easy to use as the workflow list grows, without adding
unsafe query construction or granting extra permissions.

Filtering is a read-only navigation feature, so both administrators and
viewers with `workflows.view` can use it.

## How It Works

The route reads the optional `status` query parameter, normalizes it, and
checks it against `VALID_WORKFLOW_STATUSES`. It loads workflows through the
existing repository and filters the in-memory typed records. The selected
value is returned to the template so the form reflects the active filter.

## Important Files

- `Projects/employee_management_system/web_app.py`
- `Projects/employee_management_system/templates/workflows.html`
- `Projects/employee_management_system/models.py`
- `Projects/employee_management_system/tests/test_workflow_web_lifecycle.py`

## Security and User Experience

- Only allowlisted Draft, Active, and Inactive values are accepted.
- Unknown values receive a safe `400` response.
- No submitted value is inserted into SQL.
- The selected option remains visible after filtering.
- Empty results use the existing accessible directory state.

## Tests

- Viewer filtering by Draft passed.
- Unknown-status rejection passed.

## Concepts Practiced

- GET query parameters
- Server-side allowlists
- Read-only filtering
- Preserved form state
- Safe client-error responses

## Current ABAP Status

Day 109 is complete. The workflow directory supports controlled status filters.

## Next Step

Run full regression testing, document the completed lifecycle slice, and plan
the next Workflow Automation feature.
