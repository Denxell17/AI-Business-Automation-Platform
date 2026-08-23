import unittest
from unittest.mock import patch

from database_backup import run_database_backup


class TestDatabaseBackupCommand(unittest.TestCase):
    @patch(
        "database_backup.backup_database",
        return_value=True,
    )
    def test_successful_backup_command_returns_true(
        self,
        mock_backup_database,
    ):
        result = run_database_backup()

        self.assertTrue(result)
        mock_backup_database.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()