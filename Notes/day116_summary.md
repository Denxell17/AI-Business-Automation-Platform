# Day 116 Summary — Task Maintenance Services

Added administrator-only task-detail editing and list-resequencing services.
Both reload the saved account and require `workflows.manage` before changing
data. The resequencing service accepts one complete, duplicate-free task list.

## Why

Service boundaries prevent browser routes from bypassing authorization,
normalization, or transaction-safe persistence.

## Next Step

Expose task editing through a CSRF-protected form.
