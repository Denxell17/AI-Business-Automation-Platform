ALTER TABLE employees
DROP CONSTRAINT IF EXISTS employees_performance_score_check;

ALTER TABLE employees
ADD CONSTRAINT employees_performance_score_range_check
CHECK (performance_score BETWEEN 0 AND 100);

ALTER TABLE workflow_task_executions
ADD CONSTRAINT workflow_task_executions_task_unique
UNIQUE (execution_id, task_id);
