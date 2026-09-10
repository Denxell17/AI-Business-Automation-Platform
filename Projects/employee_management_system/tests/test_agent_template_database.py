import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from database import (
    get_database_connection,
    initialize_database,
    insert_user_account,
    load_user_account_by_username,
)


class TestAgentTemplateDatabase(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.database_file = (
            Path(self.temporary_directory.name) / "employees.db"
        )

        initialize_database(self.database_file)

        user_created = insert_user_account(
            "AgentTemplateAdmin",
            "protected_password_hash",
            "admin",
            self.database_file,
        )
        self.assertTrue(user_created)

        self.administrator = load_user_account_by_username(
            "AgentTemplateAdmin",
            self.database_file,
        )
        self.assertIsNotNone(self.administrator)

        if self.administrator is None:
            self.fail(
                "The agent-template administrator was not found."
            )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_initialization_creates_agent_templates_table(self):
        connection = get_database_connection(
            self.database_file
        )

        try:
            stored_table = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name = 'agent_templates'
                """
            ).fetchone()
            stored_index = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'index'
                  AND name = 'idx_agent_templates_status_name'
                """
            ).fetchone()
        finally:
            connection.close()

        self.assertEqual(
            stored_table,
            ("agent_templates",),
        )
        self.assertEqual(
            stored_index,
            ("idx_agent_templates_status_name",),
        )

    def test_valid_agent_template_can_be_stored(self):
        connection = get_database_connection(
            self.database_file
        )

        try:
            connection.execute(
                """
                INSERT INTO agent_templates (
                    agent_template_id,
                    name,
                    description,
                    system_prompt,
                    model_name,
                    status,
                    created_by_user_id,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "AGENT-000001",
                    "Customer Support Assistant",
                    "Helps prepare customer-support responses.",
                    "Respond clearly and protect customer data.",
                    "gpt-5.6-terra",
                    "draft",
                    self.administrator["user_id"],
                    "2026-09-10T00:00:00+00:00",
                    "2026-09-10T00:00:00+00:00",
                ),
            )
            connection.commit()

            stored_template = connection.execute(
                """
                SELECT
                    agent_template_id,
                    name,
                    status,
                    created_by_user_id
                FROM agent_templates
                WHERE agent_template_id = ?
                """,
                ("AGENT-000001",),
            ).fetchone()
        finally:
            connection.close()

        self.assertEqual(
            stored_template,
            (
                "AGENT-000001",
                "Customer Support Assistant",
                "draft",
                self.administrator["user_id"],
            ),
        )

    def test_constraints_reject_invalid_templates(self):
        invalid_cases = [
            (
                "blank system prompt",
                "AGENT-000002",
                "Valid template",
                "   ",
                "gpt-5.6-terra",
                "draft",
                self.administrator["user_id"],
            ),
            (
                "unknown status",
                "AGENT-000003",
                "Valid template",
                "Valid system instructions.",
                "gpt-5.6-terra",
                "unknown",
                self.administrator["user_id"],
            ),
            (
                "missing creator",
                "AGENT-000004",
                "Valid template",
                "Valid system instructions.",
                "gpt-5.6-terra",
                "draft",
                999999,
            ),
        ]

        for (
            case_name,
            template_id,
            name,
            system_prompt,
            model_name,
            status,
            creator_id,
        ) in invalid_cases:
            with self.subTest(case=case_name):
                connection = get_database_connection(
                    self.database_file
                )

                try:
                    with self.assertRaises(
                        sqlite3.IntegrityError
                    ):
                        connection.execute(
                            """
                            INSERT INTO agent_templates (
                                agent_template_id,
                                name,
                                description,
                                system_prompt,
                                model_name,
                                status,
                                created_by_user_id,
                                created_at,
                                updated_at
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                template_id,
                                name,
                                "",
                                system_prompt,
                                model_name,
                                status,
                                creator_id,
                                "2026-09-10T00:00:00+00:00",
                                "2026-09-10T00:00:00+00:00",
                            ),
                        )
                finally:
                    connection.close()


if __name__ == "__main__":
    unittest.main()