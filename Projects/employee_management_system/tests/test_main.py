import unittest
from unittest.mock import call, patch

from main import (
    login_user,
    register_viewer_user,
    run_program,
)


class TestMainViewerRegistration(unittest.TestCase):
    @patch("builtins.print")
    @patch("main.log_activity")
    @patch(
        "main.run_viewer_account_registration",
        return_value=True,
    )
    @patch("main.getpass")
    @patch(
        "builtins.input",
        return_value="  Analyst  ",
    )
    def test_register_viewer_user_accepts_valid_input(
        self,
        mock_input,
        mock_getpass,
        mock_run_registration,
        mock_log_activity,
        mock_print,
    ):
        administrator = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": True,
        }
        mock_getpass.side_effect = [
            "ViewerPassword123!",
            "ViewerPassword123!",
        ]

        result = register_viewer_user(administrator)

        self.assertTrue(result)
        mock_input.assert_called_once_with(
            "Viewer username: "
        )
        mock_getpass.assert_has_calls(
            [
                call("Viewer password: "),
                call("Confirm viewer password: "),
            ]
        )
        mock_run_registration.assert_called_once_with(
            administrator,
            "Analyst",
            "ViewerPassword123!",
        )
        mock_log_activity.assert_called_once_with(
            "User Dennis registered viewer account Analyst."
        )

    @patch("builtins.print")
    @patch("main.log_activity")
    @patch("main.run_viewer_account_registration")
    @patch("main.getpass")
    @patch(
        "builtins.input",
        return_value="   ",
    )
    def test_register_viewer_user_rejects_missing_username(
        self,
        mock_input,
        mock_getpass,
        mock_run_registration,
        mock_log_activity,
        mock_print,
    ):
        administrator = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": True,
        }
        mock_getpass.side_effect = [
            "ViewerPassword123!",
            "ViewerPassword123!",
        ]

        result = register_viewer_user(administrator)

        self.assertFalse(result)
        mock_input.assert_called_once_with(
            "Viewer username: "
        )
        mock_run_registration.assert_not_called()
        mock_log_activity.assert_not_called()
        mock_print.assert_any_call(
            "Viewer username and password are required."
        )

    @patch("builtins.print")
    @patch("main.log_activity")
    @patch("main.run_viewer_account_registration")
    @patch("main.getpass")
    @patch(
        "builtins.input",
        return_value="Analyst",
    )
    def test_register_viewer_user_rejects_mismatched_passwords(
        self,
        mock_input,
        mock_getpass,
        mock_run_registration,
        mock_log_activity,
        mock_print,
    ):
        administrator = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": True,
        }
        mock_getpass.side_effect = [
            "FirstPassword123!",
            "DifferentPassword123!",
        ]

        result = register_viewer_user(administrator)

        self.assertFalse(result)
        self.assertEqual(mock_getpass.call_count, 2)
        mock_run_registration.assert_not_called()
        mock_log_activity.assert_not_called()
        mock_print.assert_any_call(
            "Viewer passwords do not match."
        )

    @patch("builtins.print")
    @patch("main.log_activity")
    @patch(
        "main.run_viewer_account_registration",
        return_value=False,
    )
    @patch("main.getpass")
    @patch(
        "builtins.input",
        return_value="Analyst",
    )
    def test_register_viewer_user_does_not_log_failed_registration(
        self,
        mock_input,
        mock_getpass,
        mock_run_registration,
        mock_log_activity,
        mock_print,
    ):
        administrator = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": True,
        }
        mock_getpass.side_effect = [
            "ViewerPassword123!",
            "ViewerPassword123!",
        ]

        result = register_viewer_user(administrator)

        self.assertFalse(result)
        mock_run_registration.assert_called_once_with(
            administrator,
            "Analyst",
            "ViewerPassword123!",
        )
        mock_log_activity.assert_not_called()


class TestMainAuthentication(unittest.TestCase):
    @patch("builtins.print")
    @patch("main.log_activity")
    @patch("main.authenticate_user_account")
    @patch(
        "main.getpass",
        return_value="SecurePassword123!",
    )
    @patch(
        "builtins.input",
        return_value="  dennis  ",
    )
    def test_login_user_returns_authenticated_account(
        self,
        mock_input,
        mock_getpass,
        mock_authenticate_user,
        mock_log_activity,
        mock_print,
    ):
        user_account = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": True,
        }
        mock_authenticate_user.return_value = user_account

        result = login_user()

        self.assertEqual(result, user_account)
        mock_input.assert_called_once_with("Username: ")
        mock_getpass.assert_called_once_with("Password: ")
        mock_authenticate_user.assert_called_once_with(
            "dennis",
            "SecurePassword123!",
        )
        mock_print.assert_has_calls(
            [
                call(),
                call("USER LOGIN"),
                call("Signed in as Dennis (admin)."),
            ]
        )
        mock_log_activity.assert_called_once_with(
            "User Dennis logged in."
        )

    @patch("builtins.print")
    @patch("main.log_activity")
    @patch(
        "main.authenticate_user_account",
        return_value=None,
    )
    @patch(
        "main.getpass",
        return_value="WrongPassword123!",
    )
    @patch(
        "builtins.input",
        return_value="UnknownUser",
    )
    def test_login_user_returns_none_after_failed_authentication(
        self,
        mock_input,
        mock_getpass,
        mock_authenticate_user,
        mock_log_activity,
        mock_print,
    ):
        result = login_user()

        self.assertIsNone(result)
        mock_input.assert_called_once_with("Username: ")
        mock_getpass.assert_called_once_with("Password: ")
        mock_authenticate_user.assert_called_once_with(
            "UnknownUser",
            "WrongPassword123!",
        )
        mock_print.assert_has_calls(
            [
                call(),
                call("USER LOGIN"),
                call("Authentication failed."),
            ]
        )
        mock_log_activity.assert_called_once_with(
            "Failed login attempt."
        )


class TestMainDatabaseSynchronization(unittest.TestCase):
    def setUp(self):
        self.login_patcher = patch("main.login_user")
        self.mock_login_user = self.login_patcher.start()
        self.mock_login_user.return_value = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": True,
        }
        self.addCleanup(self.login_patcher.stop)

    @patch("builtins.print")
    @patch("main.log_activity")
    @patch("main.load_employee_records")
    def test_failed_login_stops_before_employee_records_are_loaded(
        self,
        mock_load_employee_records,
        mock_log_activity,
        mock_print,
    ):
        self.mock_login_user.return_value = None

        run_program()

        self.mock_login_user.assert_called_once_with()
        mock_load_employee_records.assert_not_called()
        mock_print.assert_any_call(
            "Employee Management System access denied."
        )
        mock_log_activity.assert_has_calls(
            [
                call("Application started."),
                call("Application access denied."),
            ]
        )

    @patch("builtins.print")
    @patch("main.log_activity")
    @patch("main.register_employee")
    @patch(
        "main.load_employee_records",
        return_value=[],
    )
    @patch("builtins.input")
    def test_viewer_cannot_register_employee(
        self,
        mock_input,
        mock_load_employee_records,
        mock_register_employee,
        mock_log_activity,
        mock_print,
    ):
        self.mock_login_user.return_value = {
            "user_id": 2,
            "username": "Viewer",
            "password_hash": "protected_hash",
            "role": "viewer",
            "is_active": True,
        }
        mock_input.side_effect = [
            "1",
            "15",
        ]

        run_program()

        mock_load_employee_records.assert_called_once_with()
        mock_register_employee.assert_not_called()
        mock_print.assert_any_call(
            "You do not have permission to use this option."
        )
        mock_log_activity.assert_any_call(
            "User Viewer was denied permission employee.register."
        )

    @patch("builtins.print")
    @patch("main.log_activity")
    @patch("main.display_all_employees")
    @patch(
        "main.sort_employees_by_name",
        return_value=[],
    )
    @patch(
        "main.load_employee_records",
        return_value=[],
    )
    @patch("builtins.input")
    def test_viewer_can_view_all_employees(
        self,
        mock_input,
        mock_load_employee_records,
        mock_sort_employees,
        mock_display_all_employees,
        mock_log_activity,
        mock_print,
    ):
        self.mock_login_user.return_value = {
            "user_id": 2,
            "username": "Viewer",
            "password_hash": "protected_hash",
            "role": "viewer",
            "is_active": True,
        }
        mock_input.side_effect = [
            "6",
            "15",
        ]

        run_program()

        mock_load_employee_records.assert_called_once_with()
        mock_sort_employees.assert_called_once_with([])
        mock_display_all_employees.assert_called_once_with([])
        self.assertNotIn(
            call("You do not have permission to use this option."),
            mock_print.mock_calls,
        )

    @patch("main.log_activity")
    @patch("main.load_employee_records")
    @patch("builtins.input", return_value="15")
    def test_program_startup_loads_employee_records(
        self,
        mock_input,
        mock_load_employee_records,
        mock_log_activity,
    ):
        mock_load_employee_records.return_value = []

        run_program()

        self.mock_login_user.assert_called_once_with()
        mock_load_employee_records.assert_called_once_with()

    @patch("main.log_activity")
    @patch("main.load_employee_records")
    @patch("builtins.input")
    def test_failed_startup_load_stops_program(
        self,
        mock_input,
        mock_load_employee_records,
        mock_log_activity,
    ):
        mock_load_employee_records.return_value = None

        run_program()

        mock_load_employee_records.assert_called_once_with()
        mock_input.assert_not_called()

    @patch("main.log_activity")
    @patch("main.save_employee_records")
    @patch("main.register_employee")
    @patch("main.load_employee_records")
    @patch("builtins.input")
    def test_registration_saves_using_repository(
        self,
        mock_input,
        mock_load_employee_records,
        mock_register_employee,
        mock_save_employee_records,
        mock_log_activity,
    ):
        new_employee = {
            "employee_id": "EMP001",
            "name": "Dennis",
        }

        mock_input.side_effect = [
            "1",
            "15",
        ]
        mock_load_employee_records.return_value = []
        mock_register_employee.return_value = new_employee
        mock_save_employee_records.return_value = True

        run_program()

        mock_register_employee.assert_called_once()
        mock_save_employee_records.assert_called_once_with(
            [new_employee]
        )

    @patch("main.log_activity")
    @patch("main.save_employee_records")
    @patch("main.update_employee")
    @patch("main.load_employee_records")
    @patch("builtins.input")
    def test_update_saves_using_repository(
        self,
        mock_input,
        mock_load_employee_records,
        mock_update_employee,
        mock_save_employee_records,
        mock_log_activity,
    ):
        employee = {
            "employee_id": "EMP001",
            "name": "Dennis",
        }
        employee_list = [employee]

        mock_input.side_effect = [
            "4",
            "15",
        ]
        mock_load_employee_records.return_value = employee_list
        mock_update_employee.return_value = employee
        mock_save_employee_records.return_value = True

        run_program()

        mock_update_employee.assert_called_once_with(
            employee_list
        )
        mock_save_employee_records.assert_called_once_with(
            employee_list
        )

    @patch("main.log_activity")
    @patch("main.save_employee_records")
    @patch("main.delete_employee")
    @patch("main.load_employee_records")
    @patch("builtins.input")
    def test_deletion_saves_using_repository(
        self,
        mock_input,
        mock_load_employee_records,
        mock_delete_employee,
        mock_save_employee_records,
        mock_log_activity,
    ):
        employee = {
            "employee_id": "EMP001",
            "name": "Dennis",
        }
        employee_list = [employee]

        def pretend_delete(employees):
            employees.remove(employee)
            return employee

        mock_input.side_effect = [
            "5",
            "15",
        ]
        mock_load_employee_records.return_value = employee_list
        mock_delete_employee.side_effect = pretend_delete
        mock_save_employee_records.return_value = True

        run_program()

        mock_delete_employee.assert_called_once_with(
            employee_list
        )
        mock_save_employee_records.assert_called_once_with(
            []
        )

    @patch("main.log_activity")
    @patch("main.save_employee_records")
    @patch("main.register_employee")
    @patch("main.load_employee_records")
    @patch("builtins.input")
    def test_cancelled_registration_does_not_save(
        self,
        mock_input,
        mock_load_employee_records,
        mock_register_employee,
        mock_save_employee_records,
        mock_log_activity,
    ):
        mock_input.side_effect = [
            "1",
            "15",
        ]
        mock_load_employee_records.return_value = []
        mock_register_employee.return_value = None

        run_program()

        mock_register_employee.assert_called_once_with([])
        mock_save_employee_records.assert_not_called()

    @patch("main.log_activity")
    @patch("main.run_database_backup")
    @patch("main.load_employee_records")
    @patch("builtins.input")
    def test_sqlite_backup_option_runs_database_backup(
        self,
        mock_input,
        mock_load_employee_records,
        mock_run_database_backup,
        mock_log_activity,
    ):
        mock_input.side_effect = [
            "12",
            "15",
        ]
        mock_load_employee_records.return_value = []
        mock_run_database_backup.return_value = True

        run_program()

        mock_run_database_backup.assert_called_once_with()
        mock_log_activity.assert_any_call(
            "SQLite database backup created."
        )

    @patch("main.log_activity")
    @patch("main.run_database_restoration")
    @patch("main.load_employee_records")
    @patch("builtins.input")
    def test_successful_sqlite_restore_reloads_employees(
        self,
        mock_input,
        mock_load_employee_records,
        mock_run_database_restoration,
        mock_log_activity,
    ):
        restored_employees = [
            {
                "employee_id": "EMP001",
                "name": "Dennis",
            }
        ]

        mock_input.side_effect = [
            "13",
            "RESTORE",
            "15",
        ]
        mock_load_employee_records.side_effect = [
            [],
            restored_employees,
        ]
        mock_run_database_restoration.return_value = True

        run_program()

        mock_run_database_restoration.assert_called_once_with()
        mock_load_employee_records.assert_has_calls(
            [
                call(),
                call("sqlite"),
            ]
        )
        mock_log_activity.assert_any_call(
            "SQLite database restored from backup."
        )

    @patch("main.log_activity")
    @patch("main.run_database_restoration")
    @patch("main.load_employee_records")
    @patch("builtins.input")
    def test_cancelled_sqlite_restore_does_not_restore(
        self,
        mock_input,
        mock_load_employee_records,
        mock_run_database_restoration,
        mock_log_activity,
    ):
        mock_input.side_effect = [
            "13",
            "CANCEL",
            "15",
        ]
        mock_load_employee_records.return_value = []

        run_program()

        mock_run_database_restoration.assert_not_called()
        mock_load_employee_records.assert_called_once_with()

        self.assertNotIn(
            call("SQLite database restored from backup."),
            mock_log_activity.call_args_list,
        )

    @patch("main.log_activity")
    @patch("main.run_database_restoration")
    @patch("main.load_employee_records")
    @patch("builtins.input")
    def test_failed_sqlite_restore_does_not_reload_employees(
        self,
        mock_input,
        mock_load_employee_records,
        mock_run_database_restoration,
        mock_log_activity,
    ):
        mock_input.side_effect = [
            "13",
            "RESTORE",
            "15",
        ]
        mock_load_employee_records.return_value = []
        mock_run_database_restoration.return_value = False

        run_program()

        mock_run_database_restoration.assert_called_once_with()
        mock_load_employee_records.assert_called_once_with()

        self.assertNotIn(
            call("SQLite database restored from backup."),
            mock_log_activity.call_args_list,
        )

    @patch("main.log_activity")
    @patch("main.register_viewer_user")
    @patch(
        "main.load_employee_records",
        return_value=[],
    )
    @patch("builtins.input")
    def test_administrator_can_open_viewer_registration(
        self,
        mock_input,
        mock_load_employee_records,
        mock_register_viewer_user,
        mock_log_activity,
    ):
        administrator = self.mock_login_user.return_value
        mock_input.side_effect = [
            "14",
            "15",
        ]

        run_program()

        mock_load_employee_records.assert_called_once_with()
        mock_register_viewer_user.assert_called_once_with(
            administrator
        )

    @patch("builtins.print")
    @patch("main.log_activity")
    @patch("main.register_viewer_user")
    @patch(
        "main.load_employee_records",
        return_value=[],
    )
    @patch("builtins.input")
    def test_viewer_cannot_open_viewer_registration(
        self,
        mock_input,
        mock_load_employee_records,
        mock_register_viewer_user,
        mock_log_activity,
        mock_print,
    ):
        self.mock_login_user.return_value = {
            "user_id": 2,
            "username": "Viewer",
            "password_hash": "protected_hash",
            "role": "viewer",
            "is_active": True,
        }
        mock_input.side_effect = [
            "14",
            "15",
        ]

        run_program()

        mock_load_employee_records.assert_called_once_with()
        mock_register_viewer_user.assert_not_called()
        mock_print.assert_any_call(
            "You do not have permission to use this option."
        )
        mock_log_activity.assert_any_call(
            "User Viewer was denied permission users.manage."
        )


if __name__ == "__main__":
    unittest.main()