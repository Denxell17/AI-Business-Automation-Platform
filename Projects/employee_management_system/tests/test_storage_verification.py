import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from database import (
    initialize_database,
    synchronize_employees_to_database,
)
from storage import save_employees
from storage_verification import (
    verify_json_and_database_match,
)


class TestStorageVerification(unittest.TestCase):
    def test_matching_json_and_database_returns_true(self):
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
            sync_result = synchronize_employees_to_database(
                [employee],
                database_file,
            )
            verification_result = (
                verify_json_and_database_match(
                    json_file,
                    database_file,
                )
            )

            self.assertTrue(save_result)
            self.assertTrue(sync_result)
            self.assertTrue(verification_result)

    def test_different_json_and_database_returns_false(self):
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
            initialize_database(database_file)

            verification_result = (
                verify_json_and_database_match(
                    json_file,
                    database_file,
                )
            )

            self.assertTrue(save_result)
            self.assertFalse(verification_result)

    def test_missing_json_file_returns_false(self):
        with TemporaryDirectory() as temporary_directory:
            json_file = (
                Path(temporary_directory) / "employees.json"
            )
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            verification_result = (
                verify_json_and_database_match(
                    json_file,
                    database_file,
                )
            )

            self.assertFalse(verification_result)
            self.assertFalse(database_file.exists())

    def test_missing_database_file_returns_false(self):
        with TemporaryDirectory() as temporary_directory:
            json_file = (
                Path(temporary_directory) / "employees.json"
            )
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            save_result = save_employees(
                [],
                json_file,
            )
            verification_result = (
                verify_json_and_database_match(
                    json_file,
                    database_file,
                )
            )

            self.assertTrue(save_result)
            self.assertFalse(verification_result)
            self.assertFalse(database_file.exists())

    def test_invalid_database_file_returns_false(self):
        with TemporaryDirectory() as temporary_directory:
            json_file = (
                Path(temporary_directory) / "employees.json"
            )
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            save_result = save_employees(
                [],
                json_file,
            )
            database_file.write_text(
                "This is not a SQLite database.",
                encoding="utf-8",
            )

            verification_result = (
                verify_json_and_database_match(
                    json_file,
                    database_file,
                )
            )

            self.assertTrue(save_result)
            self.assertFalse(verification_result)
            self.assertEqual(
                database_file.read_text(encoding="utf-8"),
                "This is not a SQLite database.",
            )

    def test_invalid_json_file_returns_false(self):
        with TemporaryDirectory() as temporary_directory:
            json_file = (
                Path(temporary_directory) / "employees.json"
            )
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            json_file.write_text(
                "{invalid json",
                encoding="utf-8",
            )
            initialize_database(database_file)

            verification_result = (
                verify_json_and_database_match(
                    json_file,
                    database_file,
                )
            )

            self.assertFalse(verification_result)
            self.assertTrue(database_file.exists())


if __name__ == "__main__":
    unittest.main()