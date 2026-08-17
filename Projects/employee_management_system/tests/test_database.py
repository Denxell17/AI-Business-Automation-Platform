import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from database import (
    delete_employee_from_database,
    get_database_connection,
    initialize_database,
    insert_employee,
    load_employees_from_database,
    migrate_employees_to_database,
    update_employee_in_database,
)


class TestEmployeeDatabase(unittest.TestCase):

    def test_initialize_database_creates_employee_table(self):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            initialize_database(database_file)

            connection = get_database_connection(database_file)

            try:
                table = connection.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'table'
                    AND name = 'employees'
                    """
                ).fetchone()
            finally:
                connection.close()

            self.assertIsNotNone(table)

    def test_insert_employee_saves_record(self):
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
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            initialize_database(database_file)

            result = insert_employee(
                employee,
                database_file,
            )

            connection = get_database_connection(database_file)

            try:
                saved_employee = connection.execute(
                    """
                    SELECT employee_id, name, salary
                    FROM employees
                    WHERE employee_id = ?
                    """,
                    ("EMP001",),
                ).fetchone()
            finally:
                connection.close()

            self.assertTrue(result)
            self.assertEqual(
                saved_employee,
                ("EMP001", "Dennis", 60000),
            )

    def test_insert_employee_rejects_duplicate_id(self):
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
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            initialize_database(database_file)

            first_result = insert_employee(
                employee,
                database_file,
            )
            second_result = insert_employee(
                employee,
                database_file,
            )

            self.assertTrue(first_result)
            self.assertFalse(second_result)

    def test_load_employees_returns_empty_list(self):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            initialize_database(database_file)

            employees = load_employees_from_database(
                database_file,
            )

            self.assertEqual(employees, [])

    def test_load_employees_returns_saved_records(self):
        employee = {
            "employee_id": "EMP002",
            "name": "Maria",
            "department": "Finance",
            "position": "Accountant",
            "country": "Philippines",
            "salary": 50000,
            "email": "maria@example.com",
            "phone_number": "09987654321",
            "years_of_experience": 3,
            "company": "ABC Company",
            "employment_status": "Active",
            "performance_score": 85,
        }

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            initialize_database(database_file)
            insert_employee(employee, database_file)

            employees = load_employees_from_database(
                database_file,
            )

            self.assertEqual(employees, [employee])

    def test_update_employee_changes_saved_record(self):
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

        updated_employee = employee.copy()
        updated_employee["position"] = "Senior Developer"
        updated_employee["salary"] = 75000

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            initialize_database(database_file)
            insert_employee(employee, database_file)

            result = update_employee_in_database(
                updated_employee,
                database_file,
            )
            saved_employees = load_employees_from_database(
                database_file,
            )

            self.assertTrue(result)
            self.assertEqual(
                saved_employees,
                [updated_employee],
            )

    def test_update_employee_returns_false_when_not_found(self):
        employee = {
            "employee_id": "EMP999",
            "name": "Missing Employee",
            "department": "Unknown",
            "position": "Unknown",
            "country": "Philippines",
            "salary": 30000,
            "email": "missing@example.com",
            "phone_number": "09000000000",
            "years_of_experience": 0,
            "company": "ABC Company",
            "employment_status": "Active",
            "performance_score": 70,
        }

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            initialize_database(database_file)

            result = update_employee_in_database(
                employee,
                database_file,
            )
            saved_employees = load_employees_from_database(
                database_file,
            )

            self.assertFalse(result)
            self.assertEqual(saved_employees, [])

    def test_delete_employee_removes_saved_record(self):
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
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            initialize_database(database_file)
            insert_employee(employee, database_file)

            result = delete_employee_from_database(
                "EMP001",
                database_file,
            )
            saved_employees = load_employees_from_database(
                database_file,
            )

            self.assertTrue(result)
            self.assertEqual(saved_employees, [])

    def test_delete_employee_returns_false_when_not_found(self):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            initialize_database(database_file)

            result = delete_employee_from_database(
                "EMP999",
                database_file,
            )
            saved_employees = load_employees_from_database(
                database_file,
            )

            self.assertFalse(result)
            self.assertEqual(saved_employees, [])

    def test_migrate_empty_list_returns_zero(self):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            migrated_count = migrate_employees_to_database(
                [],
                database_file,
            )
            saved_employees = load_employees_from_database(
                database_file,
            )

            self.assertEqual(migrated_count, 0)
            self.assertEqual(saved_employees, [])

    def test_migrate_employees_saves_all_records(self):
        employees = [
            {
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
            },
            {
                "employee_id": "EMP002",
                "name": "Maria",
                "department": "Finance",
                "position": "Accountant",
                "country": "Philippines",
                "salary": 50000,
                "email": "maria@example.com",
                "phone_number": "09987654321",
                "years_of_experience": 3,
                "company": "ABC Company",
                "employment_status": "Active",
                "performance_score": 85,
            },
        ]

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            migrated_count = migrate_employees_to_database(
                employees,
                database_file,
            )
            saved_employees = load_employees_from_database(
                database_file,
            )

            self.assertEqual(migrated_count, 2)
            self.assertEqual(saved_employees, employees)

    def test_migrate_employees_skips_existing_ids(self):
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
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            first_count = migrate_employees_to_database(
                [employee],
                database_file,
            )
            second_count = migrate_employees_to_database(
                [employee],
                database_file,
            )
            saved_employees = load_employees_from_database(
                database_file,
            )

            self.assertEqual(first_count, 1)
            self.assertEqual(second_count, 0)
            self.assertEqual(saved_employees, [employee])


if __name__ == "__main__":
    unittest.main()