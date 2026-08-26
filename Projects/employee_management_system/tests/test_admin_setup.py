import unittest
from pathlib import Path
from unittest.mock import patch

from admin_setup import (
    main,
    run_initial_administrator_setup,
)


class TestInitialAdministratorSetupCommand(unittest.TestCase):
    @patch("builtins.print")
    @patch(
        "admin_setup.register_initial_administrator",
        return_value=True,
    )
    def test_successful_initial_administrator_setup(
        self,
        mock_register_initial_administrator,
        mock_print,
    ):
        database_file = Path("temporary.db")

        result = run_initial_administrator_setup(
            "Dennis",
            "SecurePassword123!",
            database_file,
        )

        self.assertTrue(result)
        mock_register_initial_administrator.assert_called_once_with(
            "Dennis",
            "SecurePassword123!",
            database_file,
        )
        mock_print.assert_called_once_with(
            "Initial administrator account created successfully."
        )

    @patch("builtins.print")
    @patch(
        "admin_setup.register_initial_administrator",
        return_value=False,
    )
    def test_failed_initial_administrator_setup(
        self,
        mock_register_initial_administrator,
        mock_print,
    ):
        database_file = Path("temporary.db")

        result = run_initial_administrator_setup(
            "Dennis",
            "SecurePassword123!",
            database_file,
        )

        self.assertFalse(result)
        mock_register_initial_administrator.assert_called_once_with(
            "Dennis",
            "SecurePassword123!",
            database_file,
        )
        mock_print.assert_called_once_with(
            "Initial administrator account was not created."
        )

    @patch(
        "admin_setup.run_initial_administrator_setup",
        return_value=True,
    )
    @patch("admin_setup.getpass")
    @patch(
        "builtins.input",
        return_value="  Dennis  ",
    )
    def test_main_returns_zero_after_successful_setup(
        self,
        mock_input,
        mock_getpass,
        mock_run_setup,
    ):
        mock_getpass.side_effect = [
            "SecurePassword123!",
            "SecurePassword123!",
        ]

        result = main()

        self.assertEqual(result, 0)
        mock_input.assert_called_once_with(
            "Initial administrator username: "
        )
        self.assertEqual(mock_getpass.call_count, 2)
        mock_run_setup.assert_called_once_with(
            "Dennis",
            "SecurePassword123!",
        )

    @patch("builtins.print")
    @patch("admin_setup.run_initial_administrator_setup")
    @patch("admin_setup.getpass")
    @patch(
        "builtins.input",
        return_value="   ",
    )
    def test_main_rejects_missing_username(
        self,
        mock_input,
        mock_getpass,
        mock_run_setup,
        mock_print,
    ):
        mock_getpass.side_effect = [
            "SecurePassword123!",
            "SecurePassword123!",
        ]

        result = main()

        self.assertEqual(result, 1)
        mock_input.assert_called_once_with(
            "Initial administrator username: "
        )
        mock_run_setup.assert_not_called()
        mock_print.assert_called_once_with(
            "Administrator username and password are required."
        )

    @patch("builtins.print")
    @patch("admin_setup.run_initial_administrator_setup")
    @patch("admin_setup.getpass")
    @patch(
        "builtins.input",
        return_value="Dennis",
    )
    def test_main_rejects_mismatched_passwords(
        self,
        mock_input,
        mock_getpass,
        mock_run_setup,
        mock_print,
    ):
        mock_getpass.side_effect = [
            "FirstPassword123!",
            "DifferentPassword123!",
        ]

        result = main()

        self.assertEqual(result, 1)
        mock_input.assert_called_once_with(
            "Initial administrator username: "
        )
        self.assertEqual(mock_getpass.call_count, 2)
        mock_run_setup.assert_not_called()
        mock_print.assert_called_once_with(
            "Administrator passwords do not match."
        )

    @patch(
        "admin_setup.run_initial_administrator_setup",
        return_value=False,
    )
    @patch("admin_setup.getpass")
    @patch(
        "builtins.input",
        return_value="Dennis",
    )
    def test_main_returns_one_when_setup_fails(
        self,
        mock_input,
        mock_getpass,
        mock_run_setup,
    ):
        mock_getpass.side_effect = [
            "SecurePassword123!",
            "SecurePassword123!",
        ]

        result = main()

        self.assertEqual(result, 1)
        mock_input.assert_called_once_with(
            "Initial administrator username: "
        )
        self.assertEqual(mock_getpass.call_count, 2)
        mock_run_setup.assert_called_once_with(
            "Dennis",
            "SecurePassword123!",
        )


if __name__ == "__main__":
    unittest.main()