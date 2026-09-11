import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from system_status_service import database_is_ready


class TestSystemStatusService(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_file = (
            Path(self.temporary_directory.name)
            / "system-status-test.db"
        )
        self.environment = patch.dict(
            os.environ,
            {
                "DATABASE_BACKEND": "sqlite",
            },
        )
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temporary_directory.cleanup()

    def test_database_with_core_schema_is_ready(self):
        connection = sqlite3.connect(self.database_file)
        connection.execute(
            """
            CREATE TABLE employees (
                employee_id TEXT PRIMARY KEY
            )
            """
        )
        connection.commit()
        connection.close()

        self.assertTrue(
            database_is_ready(self.database_file)
        )

    def test_database_without_core_schema_is_unavailable(self):
        connection = sqlite3.connect(self.database_file)
        connection.close()

        self.assertFalse(
            database_is_ready(self.database_file)
        )

    @patch(
        "system_status_service.get_database_connection",
        side_effect=ValueError("private configuration detail"),
    )
    def test_configuration_failure_is_unavailable(
        self,
        mock_get_database_connection,
    ):
        self.assertFalse(
            database_is_ready(self.database_file)
        )
        mock_get_database_connection.assert_called_once_with(
            self.database_file
        )

    @patch(
        "system_status_service.get_database_connection"
    )
    def test_database_failure_is_unavailable_and_closes_connection(
        self,
        mock_get_database_connection,
    ):
        connection = MagicMock()
        connection.execute.side_effect = sqlite3.OperationalError(
            "private database detail"
        )
        mock_get_database_connection.return_value = connection

        self.assertFalse(
            database_is_ready(self.database_file)
        )
        connection.execute.assert_called_once_with(
            "SELECT 1 FROM employees LIMIT 1"
        )
        connection.close.assert_called_once_with()