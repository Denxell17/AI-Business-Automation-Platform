import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

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
        expected_connection = object()

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

        self.assertIs(connection, expected_connection)
        connect.assert_called_once_with(database_url)

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