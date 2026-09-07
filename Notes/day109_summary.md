# Day 109 Summary — Workflow Status Filtering

## Completed

- Added a workflow-directory status filter for Draft, Active, and Inactive.
- Allowlisted filter values against the server-side workflow status constants.
- Returned a safe `400` response for an unknown filter value.
- Preserved the selected status in the rendered form.
- Kept filtering available to both administrators and viewers.

## Why

The directory remains easy to use as the workflow list grows, without adding
unsafe query construction or granting extra permissions.

## Tests

- Viewer filtering by Draft passed.
- Unknown-status rejection passed.

## Next Step

Run full regression testing, document the completed lifecycle slice, and plan
the next Workflow Automation feature.
