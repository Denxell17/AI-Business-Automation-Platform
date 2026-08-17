import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from storage import (
    get_backup_file_path,
    get_temporary_file_path,
    load_employees,
    restore_employees_from_backup,
    save_employees,
)



class TestEmployeeStorage(unittest.TestCase):

    def test_save_and_load_employees(self):
        employees = [
            {
                "employee_id": "TEST001",
                "name": "Test Employee",
                "department": "Testing",
                "position": "Tester",
                "country": "Philippines",
                "salary": 50000,
                "email": "test@example.com",
                "phone_number": "123456789",
                "years_of_experience": 2,
                "company": "Test Company",
                "employment_status": "Active",
                "performance_score": 85,
            }
        ]

        with TemporaryDirectory() as temporary_directory:
            test_file = (
                Path(temporary_directory) / "employee_test.json"
            )

            save_result = save_employees(employees, test_file)

            loaded_employees = load_employees(test_file)

            temporary_file = get_temporary_file_path(test_file)

            self.assertFalse(temporary_file.exists())

        self.assertTrue(save_result)
        self.assertEqual(loaded_employees, employees)


    def test_load_missing_file_returns_empty_list(self):
        with TemporaryDirectory() as temporary_directory:
            missing_file = (
                Path(temporary_directory) / "missing_employees.json"
            )

            loaded_employees = load_employees(missing_file)

        self.assertEqual(loaded_employees, [])


    def test_invalid_json_returns_none(self):
        with TemporaryDirectory() as temporary_directory:
            invalid_file = (
                Path(temporary_directory) / "invalid_employees.json"
            )
            invalid_file.write_text("This is not valid JSON", encoding="utf-8")

            loaded_employees = load_employees(invalid_file)

        self.assertIsNone(loaded_employees)


    def test_invalid_employee_structure_returns_none(self):
        invalid_employees = [
            {
                "employee_id": "TEST001",
                "name": "Test Employee",
                "salary": "50000",
            }
        ]

        with TemporaryDirectory() as temporary_directory:
            invalid_file = (
                Path(temporary_directory)
                / "invalid_employee_structure.json"
            )

            invalid_file.write_text(
                json.dumps(invalid_employees),
                encoding="utf-8",
            )

            loaded_employees = load_employees(invalid_file)

        self.assertIsNone(loaded_employees)


    def test_failed_save_preserves_existing_file(self):
        invalid_employees = [
            {
                "unsupported_value": {1, 2, 3},
            }
        ]

        with TemporaryDirectory() as temporary_directory:
            test_file = (
                Path(temporary_directory) / "employees.json"
            )
            test_file.write_text(
                "[]",
                encoding="utf-8",
            )

            save_result = save_employees(
                invalid_employees,
                test_file,
            )

            temporary_file = get_temporary_file_path(
                test_file
            )
            saved_content = test_file.read_text(
                encoding="utf-8"
            )

            self.assertFalse(save_result)
            self.assertEqual(saved_content, "[]")
            self.assertFalse(temporary_file.exists())


    def test_first_save_does_not_create_backup(self):
        with TemporaryDirectory() as temporary_directory:
            test_file = (
                Path(temporary_directory) / "employees.json"
            )
            backup_file = get_backup_file_path(test_file)

            save_result = save_employees(
                [],
                test_file,
            )

            self.assertTrue(save_result)
            self.assertTrue(test_file.exists())
            self.assertFalse(backup_file.exists())


    def test_existing_file_is_backed_up_before_save(self):
        original_content = '[{"version": 1}]'

        with TemporaryDirectory() as temporary_directory:
            test_file = (
                Path(temporary_directory) / "employees.json"
            )
            test_file.write_text(
                original_content,
                encoding="utf-8",
            )

            save_result = save_employees(
                [],
                test_file,
            )

            backup_file = get_backup_file_path(test_file)

            backup_content = backup_file.read_text(
                encoding="utf-8"
            )
            current_data = json.loads(
                test_file.read_text(encoding="utf-8")
            )

            self.assertTrue(save_result)
            self.assertTrue(backup_file.exists())
            self.assertEqual(
                backup_content,
                original_content,
            )
            self.assertEqual(current_data, [])


    def test_restore_returns_false_when_backup_is_missing(self):
        with TemporaryDirectory() as temporary_directory:
            test_file = (
                Path(temporary_directory) / "employees.json"
            )

            restore_result = restore_employees_from_backup(
                test_file
            )

            self.assertFalse(restore_result)
            self.assertFalse(test_file.exists())


    def test_restore_replaces_current_data_with_backup(self):
        backup_employees = [
            {
                "employee_id": "BACKUP001",
                "name": "Backup Employee",
                "department": "Recovery",
                "position": "Tester",
                "country": "Philippines",
                "salary": 40000,
                "email": "backup@example.com",
                "phone_number": "123456789",
                "years_of_experience": 2,
                "company": "Test Company",
                "employment_status": "Active",
                "performance_score": 85,
            }
        ]

        with TemporaryDirectory() as temporary_directory:
            test_file = (
                Path(temporary_directory) / "employees.json"
            )
            backup_file = get_backup_file_path(test_file)

            test_file.write_text(
                "[]",
                encoding="utf-8",
            )
            backup_file.write_text(
                json.dumps(backup_employees),
                encoding="utf-8",
            )

            restore_result = restore_employees_from_backup(
                test_file
            )

            restored_employees = load_employees(test_file)
            previous_current_data = json.loads(
                backup_file.read_text(encoding="utf-8")
            )

            self.assertTrue(restore_result)
            self.assertEqual(
                restored_employees,
                backup_employees,
            )
            self.assertEqual(previous_current_data, [])


    def test_restore_rejects_invalid_backup(self):
        with TemporaryDirectory() as temporary_directory:
            test_file = (
                Path(temporary_directory) / "employees.json"
            )
            backup_file = get_backup_file_path(test_file)

            test_file.write_text(
                "[]",
                encoding="utf-8",
            )
            backup_file.write_text(
                "This is not valid JSON",
                encoding="utf-8",
            )

            restore_result = restore_employees_from_backup(
                test_file
            )

            current_content = test_file.read_text(
                encoding="utf-8"
            )

            self.assertFalse(restore_result)
            self.assertEqual(current_content, "[]")


if __name__ == "__main__":
    unittest.main()