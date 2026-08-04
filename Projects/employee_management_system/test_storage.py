import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from storage import (
    load_employees,
    save_employees,
)



class TestEmployeeStorage(unittest.TestCase):

    def test_save_and_load_employees(self):
        employees = [
            {
                "employee_id": "TEST001",
                "name": "Test Employee",
            }
        ]

        with TemporaryDirectory() as temporary_directory:
            test_file = (
                Path(temporary_directory) / "employee_test.json"
            )

            save_result = save_employees(employees, test_file)

            loaded_employees = load_employees(test_file)

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


if __name__ == "__main__":
    unittest.main()