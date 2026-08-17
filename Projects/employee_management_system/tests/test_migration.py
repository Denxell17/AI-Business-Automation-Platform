import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from migration import migrate_json_file_to_database
from storage import save_employees


class TestJsonToSqliteMigration(unittest.TestCase):

    def test_missing_json_file_returns_false(self):
        with TemporaryDirectory() as temporary_directory:
            json_file = (
                Path(temporary_directory) / "employees.json"
            )
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            result = migrate_json_file_to_database(
                json_file,
                database_file,
            )

            self.assertFalse(result)

    def test_valid_json_file_migrates_successfully(self):
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
            migration_result = migrate_json_file_to_database(
                json_file,
                database_file,
            )

            self.assertTrue(save_result)
            self.assertTrue(migration_result)

    def test_invalid_json_file_stops_migration(self):
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

            result = migrate_json_file_to_database(
                json_file,
                database_file,
            )

            self.assertFalse(result)
            self.assertFalse(database_file.exists())


if __name__ == "__main__":
    unittest.main()