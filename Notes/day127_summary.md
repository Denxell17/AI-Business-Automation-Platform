# Day 127 Summary — Task Snapshot Creation

Starting an active workflow creates a running `WFTE-...` snapshot for each ordered task. Later task edits cannot rewrite the earlier execution history. The service uses the existing ordered task list, so the snapshots retain the task sequence that applied to that run.

## How It Works

The workflow execution is saved first. The service then creates a task-execution record for each task in the active workflow using the same UTC start time as the parent. Each task begins as `running` with the safe summary `Task execution started.`

This gives a later task-completion feature a concrete record to update instead of asking it to infer which version of a task should be affected.

## Next Step

Add controlled task-level outcomes and display.
