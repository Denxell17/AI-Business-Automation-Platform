import unittest
from unittest.mock import patch

from database_restore import run_database_restoration


class TestDatabaseRestoreCommand(unittest.TestCase):
    @patch(
        "database_restore.restore_database_from_backup",
        return_value=True,
    )
    def test_successful_restoration_command_returns_true(
        self,
        mock_restore_database,
    ):
        result = run_database_restoration()

        self.assertTrue(result)
        mock_restore_database.assert_called_once_with()

    @patch(
        "database_restore.restore_database_from_backup",
        return_value=False,
    )
    def test_failed_restoration_command_returns_false(
        self,
        mock_restore_database,
    ):
        result = run_database_restoration()

        self.assertFalse(result)
        mock_restore_database.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()