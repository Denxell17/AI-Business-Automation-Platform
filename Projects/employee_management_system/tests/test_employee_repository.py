import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from database import (
    load_employees_from_database,
    synchronize_employees_to_database,
)
from employee_repository import (
    load_employee_records,
    save_employee_records,
)
from storage import (
    load_employees,
    save_employees,
)


class TestEmployeeRepository(unittest.TestCase):
    def test_json_primary_load_synchronizes_sqlite(self):
        employee = {
            "employee_id": "EMP001",
            "name": "Dennis",
            "department": "Automation",
            "position": "Developer",
            "country": "Philippines",
            "salary": 60000,
            "email": "dennis@example.com",
            "phone_number": "09123456789",
            "years_of_experience": 2,
            "company": "ABC Company",
            "employment_status": "Active",
            "performance_score": 90,
        }

        with TemporaryDirectory() as temporary_directory:
            json_file = (
                Path(temporary_directory) / "employees.json"
            )
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            save_result = save_employees(
                [employee],
                json_file,
            )
            loaded_employees = load_employee_records(
                "json",
                json_file,
                database_file,
            )
            database_employees = (
                load_employees_from_database(
                    database_file,
                )
            )

            self.assertTrue(save_result)
            self.assertEqual(
                loaded_employees,
                [employee],
            )
            self.assertEqual(
                database_employees,
                [employee],
            )

    def test_sqlite_primary_load_reads_database(self):
        employee = {
            "employee_id": "EMP001",
            "name": "Dennis",
            "department": "Automation",
            "position": "Developer",
            "country": "Philippines",
            "salary": 60000,
            "email": "dennis@example.com",
            "phone_number": "09123456789",
            "years_of_experience": 2,
            "company": "ABC Company",
            "employment_status": "Active",
            "performance_score": 90,
        }

        with TemporaryDirectory() as temporary_directory:
            json_file = (
                Path(temporary_directory) / "employees.json"
            )
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            setup_result = (
                synchronize_employees_to_database(
                    [employee],
                    database_file,
                )
            )
            loaded_employees = load_employee_records(
                "sqlite",
                json_file,
                database_file,
            )

            self.assertTrue(setup_result)
            self.assertEqual(
                loaded_employees,
                [employee],
            )
            self.assertFalse(json_file.exists())

    def test_configured_primary_load_uses_sqlite(self):
        employee = {
            "employee_id": "EMP001",
            "name": "Dennis",
            "department": "Automation",
            "position": "Developer",
            "country": "Philippines",
            "salary": 60000,
            "email": "dennis@example.com",
            "phone_number": "09123456789",
            "years_of_experience": 2,
            "company": "ABC Company",
            "employment_status": "Active",
            "performance_score": 90,
        }

        with TemporaryDirectory() as temporary_directory:
            json_file = (
                Path(temporary_directory) / "employees.json"
            )
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            setup_result = (
                synchronize_employees_to_database(
                    [employee],
                    database_file,
                )
            )
            loaded_employees = load_employee_records(
                json_file=json_file,
                database_file=database_file,
            )

            self.assertTrue(setup_result)
            self.assertEqual(
                loaded_employees,
                [employee],
            )
            self.assertFalse(json_file.exists())

    def test_unsupported_storage_type_is_rejected(self):
        with TemporaryDirectory() as temporary_directory:
            json_file = (
                Path(temporary_directory) / "employees.json"
            )
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            load_result = load_employee_records(
                "unknown",
                json_file,
                database_file,
            )
            save_result = save_employee_records(
                [],
                "unknown",
                json_file,
                database_file,
            )

            self.assertIsNone(load_result)
            self.assertFalse(save_result)
            self.assertFalse(json_file.exists())
            self.assertFalse(database_file.exists())

    def test_json_primary_save_updates_both_storage_files(self):
        employee = {
            "employee_id": "EMP001",
            "name": "Dennis",
            "department": "Automation",
            "position": "Developer",
            "country": "Philippines",
            "salary": 60000,
            "email": "dennis@example.com",
            "phone_number": "09123456789",
            "years_of_experience": 2,
            "company": "ABC Company",
            "employment_status": "Active",
            "performance_score": 90,
        }

        with TemporaryDirectory() as temporary_directory:
            json_file = (
                Path(temporary_directory) / "employees.json"
            )
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            save_result = save_employee_records(
                [employee],
                "json",
                json_file,
                database_file,
            )
            json_employees = load_employees(json_file)
            database_employees = (
                load_employees_from_database(
                    database_file,
                )
            )

            self.assertTrue(save_result)
            self.assertEqual(
                json_employees,
                [employee],
            )
            self.assertEqual(
                database_employees,
                [employee],
            )

    def test_sqlite_primary_save_updates_only_database(self):
        employee = {
            "employee_id": "EMP001",
            "name": "Dennis",
            "department": "Automation",
            "position": "Developer",
            "country": "Philippines",
            "salary": 60000,
            "email": "dennis@example.com",
            "phone_number": "09123456789",
            "years_of_experience": 2,
            "company": "ABC Company",
            "employment_status": "Active",
            "performance_score": 90,
        }

        with TemporaryDirectory() as temporary_directory:
            json_file = (
                Path(temporary_directory) / "employees.json"
            )
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            save_result = save_employee_records(
                [employee],
                "sqlite",
                json_file,
                database_file,
            )
            database_employees = (
                load_employees_from_database(
                    database_file,
                )
            )

            self.assertTrue(save_result)
            self.assertEqual(
                database_employees,
                [employee],
            )
            self.assertFalse(json_file.exists())

    def test_configured_primary_save_uses_only_sqlite(self):
        employee = {
            "employee_id": "EMP001",
            "name": "Dennis",
            "department": "Automation",
            "position": "Developer",
            "country": "Philippines",
            "salary": 60000,
            "email": "dennis@example.com",
            "phone_number": "09123456789",
            "years_of_experience": 2,
            "company": "ABC Company",
            "employment_status": "Active",
            "performance_score": 90,
        }

        with TemporaryDirectory() as temporary_directory:
            json_file = (
                Path(temporary_directory) / "employees.json"
            )
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            save_result = save_employee_records(
                [employee],
                json_file=json_file,
                database_file=database_file,
            )
            database_employees = (
                load_employees_from_database(database_file)
            )

            self.assertTrue(save_result)
            self.assertEqual(
                database_employees,
                [employee],
            )
            self.assertFalse(json_file.exists())

    def test_missing_sqlite_primary_returns_none(self):
        with TemporaryDirectory() as temporary_directory:
            json_file = (
                Path(temporary_directory) / "employees.json"
            )
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            loaded_employees = load_employee_records(
                "sqlite",
                json_file,
                database_file,
            )

            self.assertIsNone(loaded_employees)
            self.assertFalse(database_file.exists())
            self.assertFalse(json_file.exists())

    def test_invalid_sqlite_primary_returns_none(self):
        with TemporaryDirectory() as temporary_directory:
            json_file = (
                Path(temporary_directory) / "employees.json"
            )
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            database_file.write_text(
                "This is not a SQLite database.",
                encoding="utf-8",
            )

            loaded_employees = load_employee_records(
                "sqlite",
                json_file,
                database_file,
            )

            self.assertIsNone(loaded_employees)
            self.assertEqual(
                database_file.read_text(encoding="utf-8"),
                "This is not a SQLite database.",
            )
            self.assertFalse(json_file.exists())


if __name__ == "__main__":
    unittest.main()