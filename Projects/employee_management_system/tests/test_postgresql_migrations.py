import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from postgresql_migrations import (
    POSTGRESQL_MIGRATIONS_DIRECTORY,
    apply_postgresql_migrations,
    load_postgresql_migration_files,
)


class TestPostgresqlMigrations(unittest.TestCase):
    def test_initial_migration_contains_expected_tables(self):
        migration_files = load_postgresql_migration_files(
            POSTGRESQL_MIGRATIONS_DIRECTORY
        )

        self.assertEqual(
            [path.name for path in migration_files],
            [
                "001_initial_schema.sql",
                "002_correct_schema_contract.sql",
                "003_create_agent_templates.sql",
            ],
        )

        initial_migration_sql = migration_files[0].read_text(
            encoding="utf-8-sig"
        )

        expected_tables = (
            "users",
            "employees",
            "workflows",
            "workflow_tasks",
            "workflow_schedules",
            "workflow_schedule_occurrences",
            "workflow_executions",
            "workflow_task_executions",
        )

        for table_name in expected_tables:
            self.assertIn(
                f"CREATE TABLE IF NOT EXISTS {table_name}",
                initial_migration_sql,
            )

    def test_schema_correction_matches_application_rules(self):
        migration_files = load_postgresql_migration_files(
            POSTGRESQL_MIGRATIONS_DIRECTORY
        )
        correction_sql = migration_files[1].read_text(
            encoding="utf-8-sig"
        )

        self.assertIn(
            "performance_score BETWEEN 0 AND 100",
            correction_sql,
        )
        self.assertIn(
            "UNIQUE (execution_id, task_id)",
            correction_sql,
        )

    def test_agent_template_migration_contains_expected_contract(
        self,
    ):
        migration_files = load_postgresql_migration_files(
            POSTGRESQL_MIGRATIONS_DIRECTORY
        )
        agent_template_sql = migration_files[2].read_text(
            encoding="utf-8-sig"
        )

        self.assertIn(
            "CREATE TABLE IF NOT EXISTS agent_templates",
            agent_template_sql,
        )
        self.assertIn(
            "status IN ('draft', 'active', 'inactive')",
            agent_template_sql,
        )
        self.assertIn(
            "created_by_user_id BIGINT NOT NULL",
            agent_template_sql,
        )
        self.assertIn(
            "REFERENCES users(user_id)",
            agent_template_sql,
        )
        self.assertIn(
            "created_at TIMESTAMPTZ NOT NULL",
            agent_template_sql,
        )
        self.assertIn(
            "agent_templates_status_name_index",
            agent_template_sql,
        )

    def test_missing_migrations_directory_is_rejected(self):
        with TemporaryDirectory() as temporary_directory:
            missing_directory = (
                Path(temporary_directory) / "missing"
            )

            with self.assertRaises(FileNotFoundError):
                load_postgresql_migration_files(
                    missing_directory
                )

    def test_empty_migrations_directory_is_rejected(self):
        with TemporaryDirectory() as temporary_directory:
            with self.assertRaises(ValueError):
                load_postgresql_migration_files(
                    Path(temporary_directory)
                )

    def test_invalid_migration_filename_is_rejected(self):
        with TemporaryDirectory() as temporary_directory:
            migrations_directory = Path(temporary_directory)
            invalid_file = (
                migrations_directory / "initial_schema.sql"
            )
            invalid_file.write_text(
                "CREATE TABLE example (id BIGINT);",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                load_postgresql_migration_files(
                    migrations_directory
                )

    def test_empty_database_url_is_rejected(self):
        with self.assertRaises(ValueError):
            apply_postgresql_migrations("")

    def test_pending_migration_is_applied_and_recorded(self):
        connection = MagicMock()
        connection_context = MagicMock()
        connection_context.__enter__.return_value = connection

        cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = (
            cursor
        )
        cursor.fetchall.return_value = []

        with TemporaryDirectory() as temporary_directory:
            migrations_directory = Path(temporary_directory)
            migration_file = (
                migrations_directory / "001_test_schema.sql"
            )
            migration_file.write_text(
                "CREATE TABLE sample (id BIGINT);",
                encoding="utf-8",
            )

            with patch(
                "postgresql_migrations.psycopg.connect",
                return_value=connection_context,
            ) as mocked_connect:
                applied_migrations = (
                    apply_postgresql_migrations(
                        "postgresql://user:password@localhost/abap",
                        migrations_directory,
                    )
                )

        self.assertEqual(
            applied_migrations,
            ["001_test_schema.sql"],
        )
        mocked_connect.assert_called_once_with(
            "postgresql://user:password@localhost/abap"
        )

        executed_sql = [
            call.args[0]
            for call in cursor.execute.call_args_list
        ]

        self.assertTrue(
            any(
                "CREATE TABLE sample" in sql
                for sql in executed_sql
            )
        )
        self.assertEqual(
            cursor.execute.call_args_list[-1].args[1],
            ("001_test_schema.sql",),
        )

    def test_applied_migration_is_skipped(self):
        connection = MagicMock()
        connection_context = MagicMock()
        connection_context.__enter__.return_value = connection

        cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = (
            cursor
        )
        cursor.fetchall.return_value = [
            ("001_test_schema.sql",)
        ]

        with TemporaryDirectory() as temporary_directory:
            migrations_directory = Path(temporary_directory)
            migration_file = (
                migrations_directory / "001_test_schema.sql"
            )
            migration_file.write_text(
                "CREATE TABLE sample (id BIGINT);",
                encoding="utf-8",
            )

            with patch(
                "postgresql_migrations.psycopg.connect",
                return_value=connection_context,
            ):
                applied_migrations = (
                    apply_postgresql_migrations(
                        "postgresql://user:password@localhost/abap",
                        migrations_directory,
                    )
                )

        self.assertEqual(applied_migrations, [])

        executed_sql = [
            call.args[0]
            for call in cursor.execute.call_args_list
        ]
        self.assertFalse(
            any(
                "CREATE TABLE sample" in sql
                for sql in executed_sql
            )
        )


if __name__ == "__main__":
    unittest.main()
