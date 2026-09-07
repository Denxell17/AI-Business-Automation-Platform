# Day 119 Summary — Workflow Activation Readiness Rule

## Goal

Enforce the domain rule that an active workflow must contain at least one task.

## Completed

- Updated `create_workflow()` to reject an initially active workflow.
- Updated `update_workflow()` to check saved tasks before activation.
- Rejected activation when the saved task list is empty.
- Allowed draft and inactive workflows to remain empty.
- Allowed activation after at least one task is saved.
- Preserved normal name, description, draft, and inactive updates.
- Added direct tests for rejected and successful activation.

## How It Works

A newly created workflow has no tasks, so accepting `active` at creation would
produce an unusable process. New workflows must start in a non-active state.

For an existing workflow, the update service checks the requested status. It
loads saved tasks only when the target state is `active` and continues only
when at least one task exists.

## Why ABAP Needs This

Status should represent real operational readiness. An empty active workflow
cannot perform business work. Keeping this rule in the service means browser
forms and future APIs share the same lifecycle behavior.

## Important Files

- `Projects/employee_management_system/workflow_service.py`
- `Projects/employee_management_system/tests/test_workflow_task_maintenance.py`
- `Projects/employee_management_system/tests/test_workflow_lifecycle.py`
- `Projects/employee_management_system/tests/test_workflow_web_lifecycle.py`

## Business and Security Decisions

- Draft workflows may have zero tasks while being designed.
- Inactive workflows may remain stored without being runnable.
- Active workflows require at least one saved task.
- Saved SQLite tasks are authoritative.
- Existing permission and account checks still run before lifecycle changes.

## Tests

Coverage verifies empty activation rejection, successful activation with tasks,
direct active-creation rejection, preserved inactive updates, and browser
editing under the new rule.

## Concepts Practiced

- Domain invariants
- Lifecycle transition validation
- State-dependent repository reads
- Service-layer business rules
- Regression-test maintenance

## Current ABAP Status

Day 119 is complete. Lifecycle status now reflects workflow readiness.

## Next Step

Day 120 verifies and documents the complete maintenance slice.
