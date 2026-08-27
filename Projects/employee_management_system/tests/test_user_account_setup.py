import unittest
from pathlib import Path
from unittest.mock import patch

from user_account_setup import run_viewer_account_registration


class TestViewerAccountSetupCommand(unittest.TestCase):
    @patch("builtins.print")
    @patch(
        "user_account_setup.register_viewer_account",
        return_value=True,
    )
    def test_successful_viewer_account_registration(
        self,
        mock_register_viewer_account,
        mock_print,
    ):
        administrator = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": True,
        }
        database_file = Path("temporary.db")

        result = run_viewer_account_registration(
            administrator,
            "Analyst",
            "ViewerPassword123!",
            database_file,
        )

        self.assertTrue(result)
        mock_register_viewer_account.assert_called_once_with(
            administrator,
            "Analyst",
            "ViewerPassword123!",
            database_file,
        )
        mock_print.assert_called_once_with(
            "Viewer account created successfully."
        )

    @patch("builtins.print")
    @patch(
        "user_account_setup.register_viewer_account",
        return_value=False,
    )
    def test_failed_viewer_account_registration(
        self,
        mock_register_viewer_account,
        mock_print,
    ):
        administrator = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": True,
        }
        database_file = Path("temporary.db")

        result = run_viewer_account_registration(
            administrator,
            "Analyst",
            "ViewerPassword123!",
            database_file,
        )

        self.assertFalse(result)
        mock_register_viewer_account.assert_called_once_with(
            administrator,
            "Analyst",
            "ViewerPassword123!",
            database_file,
        )
        mock_print.assert_called_once_with(
            "Viewer account was not created."
        )


if __name__ == "__main__":
    unittest.main()