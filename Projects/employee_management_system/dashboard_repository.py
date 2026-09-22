"""Bounded, permission-scoped data access for the ABAP Dashboard."""

import sqlite3
from pathlib import Path

from database import (
    DATABASE_FILE,
    get_database_connection,
    initialize_database,
)


DASHBOARD_LIST_LIMIT = 5
DEPARTMENT_LIST_LIMIT = 6


def _rows_as_dictionaries(rows) -> list[dict]:
    return [dict(row) for row in rows]


def load_dashboard_snapshot(
    database_file: Path = DATABASE_FILE,
    *,
    include_employees: bool,
    include_workflows: bool,
    include_agents: bool,
    include_crm: bool = False,
) -> dict:
    """Load the authorized Dashboard data with a bounded query set."""
    initialize_database(database_file)
    connection = get_database_connection(database_file)
    connection.row_factory = sqlite3.Row

    snapshot = {
        "employee_total": None,
        "department_total": None,
        "department_counts": None,
        "active_workflow_total": None,
        "failed_workflow_run_total": None,
        "workflow_executions": None,
        "enabled_schedules": None,
        "agent_executions": None,
        "lead_total": None,
        "qualified_lead_total": None,
        "customer_total": None,
    }

    try:
        if include_employees:
            employee_summary = connection.execute(
                """
                SELECT
                    COUNT(*) AS employee_total,
                    COUNT(
                        DISTINCT NULLIF(TRIM(department), '')
                    ) AS department_total
                FROM employees
                """
            ).fetchone()
            snapshot["employee_total"] = employee_summary[
                "employee_total"
            ]
            snapshot["department_total"] = employee_summary[
                "department_total"
            ]
            snapshot["department_counts"] = _rows_as_dictionaries(
                connection.execute(
                    """
                    SELECT department, COUNT(*) AS employee_count
                    FROM employees
                    WHERE TRIM(department) <> ''
                    GROUP BY department
                    ORDER BY employee_count DESC, LOWER(department)
                    LIMIT ?
                    """,
                    (DEPARTMENT_LIST_LIMIT,),
                ).fetchall()
            )

        if include_workflows:
            workflow_summary = connection.execute(
                """
                SELECT COUNT(*) AS active_workflow_total
                FROM workflows
                WHERE status = 'active'
                """
            ).fetchone()
            failed_summary = connection.execute(
                """
                SELECT COUNT(*) AS failed_workflow_run_total
                FROM workflow_executions
                WHERE status = 'failed'
                """
            ).fetchone()
            snapshot["active_workflow_total"] = workflow_summary[
                "active_workflow_total"
            ]
            snapshot["failed_workflow_run_total"] = failed_summary[
                "failed_workflow_run_total"
            ]
            snapshot["workflow_executions"] = _rows_as_dictionaries(
                connection.execute(
                    """
                    SELECT
                        execution_id,
                        workflow_id,
                        workflow_name,
                        status,
                        started_at,
                        finished_at
                    FROM workflow_executions
                    ORDER BY started_at DESC, execution_id DESC
                    LIMIT ?
                    """,
                    (DASHBOARD_LIST_LIMIT,),
                ).fetchall()
            )
            snapshot["enabled_schedules"] = _rows_as_dictionaries(
                connection.execute(
                    """
                    SELECT
                        workflow_schedules.schedule_id,
                        workflow_schedules.workflow_id,
                        workflows.name AS workflow_name,
                        workflow_schedules.schedule_type,
                        workflow_schedules.scheduled_time,
                        workflow_schedules.day_of_week,
                        workflow_schedules.updated_at
                    FROM workflow_schedules
                    INNER JOIN workflows
                        ON workflows.workflow_id =
                           workflow_schedules.workflow_id
                    WHERE
                        workflow_schedules.is_enabled = ?
                        AND workflows.status = 'active'
                    ORDER BY
                        workflow_schedules.updated_at DESC,
                        workflow_schedules.schedule_id DESC
                    LIMIT ?
                    """,
                    (True, DASHBOARD_LIST_LIMIT),
                ).fetchall()
            )

        if include_agents:
            snapshot["agent_executions"] = _rows_as_dictionaries(
                connection.execute(
                    """
                    SELECT
                        agent_execution_id,
                        agent_template_id,
                        agent_template_name,
                        status,
                        started_at,
                        finished_at
                    FROM agent_executions
                    ORDER BY started_at DESC, agent_execution_id DESC
                    LIMIT ?
                    """,
                    (DASHBOARD_LIST_LIMIT,),
                ).fetchall()
            )
        if include_crm:
            crm_summary = connection.execute(
                """SELECT COUNT(*) AS lead_total,
                          SUM(CASE WHEN stage = 'qualified' THEN 1 ELSE 0 END)
                              AS qualified_lead_total FROM leads"""
            ).fetchone()
            snapshot["lead_total"] = crm_summary["lead_total"]
            snapshot["qualified_lead_total"] = crm_summary["qualified_lead_total"] or 0
            snapshot["customer_total"] = connection.execute(
                "SELECT COUNT(*) AS customer_total FROM customers"
            ).fetchone()["customer_total"]
    finally:
        connection.close()

    return snapshot
