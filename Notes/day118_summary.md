# Day 118 Summary — Task Resequencing

Added a protected task-order form. Administrators choose the task for each
position, and the service requires every saved task exactly once. SQLite uses
one transaction and a temporary positive offset to avoid unique-position
collisions before saving the contiguous final order.

## Next Step

Enforce the rule that only workflows with tasks can become active.
