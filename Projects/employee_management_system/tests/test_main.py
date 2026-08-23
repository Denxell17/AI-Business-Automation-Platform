import unittest
from unittest.mock import call, patch

from main import run_program


class TestMainDatabaseSynchronization(unittest.TestCase):
    @patch("main.log_activity")
    @patch("main.load_employee_records")
    @patch("builtins.input", return_value="14")
    def test_program_startup_loads_employee_records(
        self,
        mock_input,
        mock_load_employee_records,
        mock_log_activity,
    ):
        mock_load_employee_records.return_value = []

        run_program()

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
            "14",
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
            "14",
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
            "14",
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
            "14",
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
            "14",
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
            "14",
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
            "14",
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
            "14",
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


if __name__ == "__main__":
    unittest.main()