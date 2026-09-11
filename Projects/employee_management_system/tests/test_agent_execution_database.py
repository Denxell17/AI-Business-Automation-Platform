import sqlite3
import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from database import (
    get_database_connection,
    initialize_database,
    insert_agent_template,
    insert_user_account,
    load_user_account_by_username,
)


INSERT_AGENT_EXECUTION_SQL = """
    INSERT INTO agent_executions (
        agent_execution_id,
        agent_template_id,
        agent_template_name,
        model_name,
        status,
        input_text,
        output_text,
        error_message,
        requested_by_user_id,
        started_at,
        finished_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


class TestAgentExecutionDatabase(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.database_file = (
            Path(self.temporary_directory.name)
            / "agent-executions.db"
        )

        initialize_database(self.database_file)

        user_created = insert_user_account(
            "AgentExecutionAdmin",
            "protected_password_hash",
            "admin",
            self.database_file,
        )
        self.assertTrue(user_created)

        self.administrator = load_user_account_by_username(
            "AgentExecutionAdmin",
            self.database_file,
        )
        self.assertIsNotNone(self.administrator)

        if self.administrator is None:
            self.fail(
                "The execution-test administrator was not found."
            )

        self.agent_template_id = "AGENT-EXECUTION-TEST"
        self.started_at = datetime.now(
            timezone.utc
        ).isoformat()

        template_created = insert_agent_template(
            {
                "agent_template_id": self.agent_template_id,
                "name": "Execution Test Agent",
                "description": (
                    "Template used by execution database tests."
                ),
                "system_prompt": (
                    "Return a clear and concise response."
                ),
                "model_name": "test-model",
                "status": "active",
                "created_by_user_id": self.administrator[
                    "user_id"
                ],
                "created_at": self.started_at,
                "updated_at": self.started_at,
            },
            self.database_file,
        )
        self.assertTrue(template_created)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def execution_values(
        self,
        agent_execution_id,
        status,
        output_text=None,
        error_message=None,
        finished_at=None,
    ):
        return (
            agent_execution_id,
            self.agent_template_id,
            "Execution Test Agent",
            "test-model",
            status,
            "Summarize this customer request.",
            output_text,
            error_message,
            self.administrator["user_id"],
            self.started_at,
            finished_at,
        )

    def test_initialization_creates_execution_table_and_indexes(
        self,
    ):
        connection = get_database_connection(
            self.database_file
        )

        try:
            stored_table = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name = 'agent_executions'
                """
            ).fetchone()

            stored_indexes = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'index'
                  AND name LIKE 'idx_agent_executions_%'
                ORDER BY name
                """
            ).fetchall()
        finally:
            connection.close()

        self.assertEqual(
            stored_table,
            ("agent_executions",),
        )
        self.assertEqual(
            stored_indexes,
            [
                (
                    "idx_agent_executions_template_started",
                ),
                (
                    "idx_agent_executions_user_started",
                ),
            ],
        )

    def test_valid_execution_lifecycle_records_can_be_stored(
        self,
    ):
        finished_at = datetime.now(
            timezone.utc
        ).isoformat()

        records = (
            self.execution_values(
                "EXEC-RUNNING",
                "running",
            ),
            self.execution_values(
                "EXEC-COMPLETED",
                "completed",
                output_text="The request was summarized.",
                finished_at=finished_at,
            ),
            self.execution_values(
                "EXEC-FAILED",
                "failed",
                error_message=(
                    "The AI provider was unavailable."
                ),
                finished_at=finished_at,
            ),
        )

        connection = get_database_connection(
            self.database_file
        )

        try:
            for record in records:
                connection.execute(
                    INSERT_AGENT_EXECUTION_SQL,
                    record,
                )

            connection.commit()

            stored_statuses = connection.execute(
                """
                SELECT status
                FROM agent_executions
                ORDER BY agent_execution_id
                """
            ).fetchall()
        finally:
            connection.close()

        self.assertEqual(
            stored_statuses,
            [
                ("completed",),
                ("failed",),
                ("running",),
            ],
        )

    def test_constraints_reject_invalid_execution_states(
        self,
    ):
        finished_at = datetime.now(
            timezone.utc
        ).isoformat()

        invalid_records = (
            self.execution_values(
                "EXEC-UNKNOWN",
                "unknown",
            ),
            self.execution_values(
                "EXEC-RUNNING-FINISHED",
                "running",
                finished_at=finished_at,
            ),
            self.execution_values(
                "EXEC-COMPLETED-NO-OUTPUT",
                "completed",
                finished_at=finished_at,
            ),
            self.execution_values(
                "EXEC-FAILED-NO-ERROR",
                "failed",
                finished_at=finished_at,
            ),
        )

        connection = get_database_connection(
            self.database_file
        )

        try:
            for record in invalid_records:
                with self.subTest(
                    agent_execution_id=record[0]
                ):
                    with self.assertRaises(
                        sqlite3.IntegrityError
                    ):
                        connection.execute(
                            INSERT_AGENT_EXECUTION_SQL,
                            record,
                        )

                    connection.rollback()
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()