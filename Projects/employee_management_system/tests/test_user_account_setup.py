import unittest
from pathlib import Path
from unittest.mock import patch

from user_account_setup import (
    run_current_user_password_change,
    run_viewer_account_password_reset,
    run_viewer_account_registration,
    run_viewer_account_status_change,
)


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

    @patch("builtins.print")
    @patch(
        "user_account_setup.set_viewer_account_active_status",
        return_value=True,
    )
    def test_successful_viewer_account_deactivation(
        self,
        mock_set_viewer_account_active_status,
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

        result = run_viewer_account_status_change(
            administrator,
            "ReportViewer",
            False,
            database_file,
        )

        self.assertTrue(result)
        mock_set_viewer_account_active_status.assert_called_once_with(
            administrator,
            "ReportViewer",
            False,
            database_file,
        )
        mock_print.assert_called_once_with(
            "Viewer account deactivated successfully."
        )

    @patch("builtins.print")
    @patch(
        "user_account_setup.set_viewer_account_active_status",
        return_value=True,
    )
    def test_successful_viewer_account_reactivation(
        self,
        mock_set_viewer_account_active_status,
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

        result = run_viewer_account_status_change(
            administrator,
            "ReportViewer",
            True,
            database_file,
        )

        self.assertTrue(result)
        mock_set_viewer_account_active_status.assert_called_once_with(
            administrator,
            "ReportViewer",
            True,
            database_file,
        )
        mock_print.assert_called_once_with(
            "Viewer account activated successfully."
        )

    @patch("builtins.print")
    @patch(
        "user_account_setup.set_viewer_account_active_status",
        return_value=False,
    )
    def test_failed_viewer_account_status_change(
        self,
        mock_set_viewer_account_active_status,
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

        result = run_viewer_account_status_change(
            administrator,
            "ReportViewer",
            False,
            database_file,
        )

        self.assertFalse(result)
        mock_set_viewer_account_active_status.assert_called_once_with(
            administrator,
            "ReportViewer",
            False,
            database_file,
        )
        mock_print.assert_called_once_with(
            "Viewer account status was not changed."
        )

    @patch("builtins.print")
    @patch(
        "user_account_setup.reset_viewer_account_password",
        return_value=True,
    )
    def test_successful_viewer_account_password_reset(
        self,
        mock_reset_viewer_account_password,
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

        result = run_viewer_account_password_reset(
            administrator,
            "ReportViewer",
            "ReplacementPassword123!",
            database_file,
        )

        self.assertTrue(result)
        mock_reset_viewer_account_password.assert_called_once_with(
            administrator,
            "ReportViewer",
            "ReplacementPassword123!",
            database_file,
        )
        mock_print.assert_called_once_with(
            "Viewer account password reset successfully."
        )

    @patch("builtins.print")
    @patch(
        "user_account_setup.reset_viewer_account_password",
        return_value=False,
    )
    def test_failed_viewer_account_password_reset(
        self,
        mock_reset_viewer_account_password,
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

        result = run_viewer_account_password_reset(
            administrator,
            "ReportViewer",
            "ReplacementPassword123!",
            database_file,
        )

        self.assertFalse(result)
        mock_reset_viewer_account_password.assert_called_once_with(
            administrator,
            "ReportViewer",
            "ReplacementPassword123!",
            database_file,
        )
        mock_print.assert_called_once_with(
            "Viewer account password was not reset."
        )

    @patch("builtins.print")
    @patch(
        "user_account_setup.change_current_user_password",
        return_value=True,
    )
    def test_successful_current_user_password_change(
        self,
        mock_change_current_user_password,
        mock_print,
    ):
        current_user = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": True,
        }
        database_file = Path("temporary.db")

        result = run_current_user_password_change(
            current_user,
            "CurrentPassword123!",
            "NewPassword123!",
            database_file,
        )

        self.assertTrue(result)
        mock_change_current_user_password.assert_called_once_with(
            current_user,
            "CurrentPassword123!",
            "NewPassword123!",
            database_file,
        )
        mock_print.assert_called_once_with(
            "Account password changed successfully."
        )

    @patch("builtins.print")
    @patch(
        "user_account_setup.change_current_user_password",
        return_value=False,
    )
    def test_failed_current_user_password_change(
        self,
        mock_change_current_user_password,
        mock_print,
    ):
        current_user = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": True,
        }
        database_file = Path("temporary.db")

        result = run_current_user_password_change(
            current_user,
            "WrongPassword123!",
            "NewPassword123!",
            database_file,
        )

        self.assertFalse(result)
        mock_change_current_user_password.assert_called_once_with(
            current_user,
            "WrongPassword123!",
            "NewPassword123!",
            database_file,
        )
        mock_print.assert_called_once_with(
            "Account password was not changed."
        )


if __name__ == "__main__":
    unittest.main()