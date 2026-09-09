import os
import unittest
from unittest.mock import MagicMock, patch

from database import (
    claim_workflow_schedule_occurrence,
    insert_workflow_task_executions,
    load_user_account_by_username,
)


POSTGRESQL_ENVIRONMENT = {
    "DATABASE_BACKEND": "postgresql",
    "DATABASE_URL": "postgresql://user:password@localhost/abap",
}


class TestPostgresqlRepositoryAdapter(unittest.TestCase):
    @patch.dict(os.environ, POSTGRESQL_ENVIRONMENT)
    @patch("database_connection.psycopg.connect")
    def test_authentication_lookup_uses_case_insensitive_postgresql_sql(
        self,
        connect,
    ):
        raw_connection = MagicMock()
        cursor = MagicMock()
        cursor.fetchone.return_value = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": True,
        }
        raw_connection.execute.return_value = cursor
        connect.return_value = raw_connection

        account = load_user_account_by_username("dennis")

        self.assertEqual(account["username"], "Dennis")
        query = raw_connection.execute.call_args.args[0]
        self.assertIn(
            "WHERE LOWER(username) = LOWER(%s)",
            query,
        )

    @patch.dict(os.environ, POSTGRESQL_ENVIRONMENT)
    @patch("database_connection.psycopg.connect")
    def test_task_execution_bulk_insert_uses_postgresql_sql(
        self,
        connect,
    ):
        raw_connection = MagicMock()
        cursor = MagicMock()
        raw_connection.cursor.return_value = cursor
        connect.return_value = raw_connection

        records = [
            {
                "task_execution_id": "TASK-RUN-001",
                "execution_id": "RUN-001",
                "task_id": "TASK-001",
                "sequence_number": 1,
                "task_title": "Review request",
                "status": "running",
                "started_at": "2026-09-09T00:00:00+00:00",
                "finished_at": None,
                "result_summary": "Task execution started.",
            }
        ]

        result = insert_workflow_task_executions(records)

        self.assertTrue(result)

        query = cursor.executemany.call_args.args[0]

        self.assertNotIn("?", query)
        self.assertEqual(query.count("%s"), 9)
        raw_connection.commit.assert_called_once_with()

    @patch.dict(os.environ, POSTGRESQL_ENVIRONMENT)
    @patch("database_connection.psycopg.connect")
    def test_occurrence_claim_uses_postgresql_conflict_handling(
        self,
        connect,
    ):
        raw_connection = MagicMock()
        cursor = MagicMock()
        cursor.rowcount = 1
        raw_connection.execute.return_value = cursor
        connect.return_value = raw_connection
        occurrence = {
            "occurrence_id": "OCC-001",
            "schedule_id": "SCHEDULE-001",
            "workflow_id": "WF-001",
            "scheduled_for_utc": "2026-09-09T00:00:00+00:00",
            "claimed_at": "2026-09-09T00:00:01+00:00",
        }

        result = claim_workflow_schedule_occurrence(occurrence)

        self.assertTrue(result)
        query = raw_connection.execute.call_args.args[0]
        self.assertIn("ON CONFLICT DO NOTHING", query)
        self.assertNotIn("INSERT OR IGNORE", query)
        self.assertIn("schedule.is_enabled = TRUE", query)
        raw_connection.commit.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
