import sqlite3
import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from psycopg.rows import dict_row

from database_connection import (
    open_configured_database_connection,
)


class TestConfiguredDatabaseConnection(unittest.TestCase):
    def test_sqlite_connection_enables_foreign_keys(self):
        with TemporaryDirectory() as directory:
            database_file = Path(directory) / "test.db"

            connection = open_configured_database_connection(
                settings={
                    "backend": "sqlite",
                    "database_url": None,
                },
                sqlite_file=database_file,
            )

            try:
                foreign_keys = connection.execute(
                    "PRAGMA foreign_keys"
                ).fetchone()[0]

                self.assertIsInstance(
                    connection,
                    sqlite3.Connection,
                )
                self.assertEqual(foreign_keys, 1)
            finally:
                connection.close()

    def test_postgresql_uses_psycopg_connection(self):
        database_url = (
            "postgresql://abap_user:password@localhost:5432/abap"
        )
        expected_connection = MagicMock()

        with patch(
            "database_connection.psycopg.connect",
            return_value=expected_connection,
        ) as connect:
            connection = open_configured_database_connection(
                settings={
                    "backend": "postgresql",
                    "database_url": database_url,
                }
            )

        self.assertIs(connection.raw_connection, expected_connection)
        connect.assert_called_once_with(
            database_url,
            row_factory=dict_row,
        )

    def test_postgresql_adapter_translates_queries_and_rows(self):
        raw_connection = MagicMock()
        cursor = MagicMock()
        cursor.fetchone.return_value = {
            "workflow_id": "WF-001",
            "created_at": datetime(
                2026,
                9,
                9,
                tzinfo=timezone.utc,
            ),
        }
        raw_connection.execute.return_value = cursor

        with patch(
            "database_connection.psycopg.connect",
            return_value=raw_connection,
        ):
            connection = open_configured_database_connection(
                settings={
                    "backend": "postgresql",
                    "database_url": "postgresql://user:pass@host/abap",
                }
            )

        row = connection.execute(
            "SELECT workflow_id, created_at FROM workflows "
            "WHERE workflow_id = ?",
            ("WF-001",),
        ).fetchone()

        raw_connection.execute.assert_called_once_with(
            "SELECT workflow_id, created_at FROM workflows "
            "WHERE workflow_id = %s",
            ("WF-001",),
        )
        self.assertEqual(row["workflow_id"], "WF-001")
        self.assertEqual(row[0], "WF-001")
        self.assertEqual(
            row["created_at"],
            "2026-09-09T00:00:00+00:00",
        )

    def test_postgresql_rejects_missing_url(self):
        with self.assertRaises(ValueError):
            open_configured_database_connection(
                settings={
                    "backend": "postgresql",
                    "database_url": None,
                }
            )


if __name__ == "__main__":
    unittest.main()
