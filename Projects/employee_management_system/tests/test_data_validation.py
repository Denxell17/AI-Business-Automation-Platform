import unittest

from data_validation import (
    get_employee_list_errors,
    get_employee_record_errors,
    is_valid_employee_list,
    is_valid_employee_record,
)


class TestEmployeeRecordValidation(unittest.TestCase):

    def setUp(self):
        self.employee = {
            "employee_id": "EMP001",
            "name": "Dennis",
            "department": "Automation",
            "position": "Developer",
            "country": "Philippines",
            "salary": 60000,
            "email": "dennis@example.com",
            "phone_number": "123456789",
            "years_of_experience": 3,
            "company": "Example Company",
            "employment_status": "Active",
            "performance_score": 88,
        }


    def test_valid_employee_record(self):
        self.assertTrue(
            is_valid_employee_record(self.employee)
        )


    def test_valid_employee_record_has_no_errors(self):
        errors = get_employee_record_errors(self.employee)

        self.assertEqual(errors, [])


    def test_missing_required_fields(self):
        employee = self.employee.copy()
        employee.pop("salary")

        self.assertFalse(
            is_valid_employee_record(employee)
        )


    def test_missing_field_reports_error_message(self):
        employee = self.employee.copy()
        employee.pop("salary")

        errors = get_employee_record_errors(employee)

        self.assertIn(
            "Missing required field: salary",
            errors,
        )


    def test_incorrect_field_type(self):
        employee = self.employee.copy()
        employee["salary"] = "60000"

        self.assertFalse(
            is_valid_employee_record(employee)
        )


    def test_incorrect_type_reports_error_message(self):
        employee = self.employee.copy()
        employee["salary"] = "60000"

        errors = get_employee_record_errors(employee)

        self.assertIn(
            "Field 'salary' must be int, not str.",
            errors,
        )


    def test_blank_text_field_reports_error(self):
        employee = self.employee.copy()
        employee["name"] = " "

        errors = get_employee_record_errors(employee)

        self.assertFalse(
            is_valid_employee_record(employee)
        )
        self.assertIn(
            "Field 'name' cannot be blank.",
            errors,
        )


    def test_zero_salary_reports_error(self):
        employee = self.employee.copy()
        employee["salary"] = 0

        errors = get_employee_record_errors(employee)

        self.assertFalse(
            is_valid_employee_record(employee)
        )
        self.assertIn(
            "Field 'salary' must be greater than zero.",
            errors,
        )


    def test_negative_experience_reports_error(self):
        employee = self.employee.copy()
        employee["years_of_experience"] = -1

        errors = get_employee_record_errors(employee)

        self.assertFalse(
            is_valid_employee_record(employee)
        )
        self.assertIn(
            "Field 'years_of_experience' cannot be negative.",
            errors,
        )


    def test_invalid_performance_score_reports_error(self):
        employee = self.employee.copy()
        employee["performance_score"] = 101

        errors = get_employee_record_errors(employee)

        self.assertFalse(
            is_valid_employee_record(employee)
        )
        self.assertIn(
            "Field 'performance_score' must be between 0 and 100.",
            errors,
        )


class TestEmployeeListValidation(unittest.TestCase):

    def setUp(self):
        self.employee = {
            "employee_id": "EMP001",
            "name": "Dennis",
            "department": "Automation",
            "position": "Developer",
            "country": "Philippines",
            "salary": 60000,
            "email": "dennis@example.com",
            "phone_number": "123456789",
            "years_of_experience": 3,
            "company": "Example Company",
            "employment_status": "Active",
            "performance_score": 88,
        }


    def test_valid_employee_list(self):
        employee_list = [self.employee]

        self.assertTrue(
            is_valid_employee_list(employee_list)
        )


    def test_non_list_data_is_invalid(self):
        employee_data = {
            "employee_id": "EMP001",
            "name": "Dennis",
        }

        self.assertFalse(
            is_valid_employee_list(employee_data)
        )


    def test_non_list_data_reports_error_message(self):
        employee_data = {
            "employee_id": "EMP001",
            "name": "Dennis",
        }

        errors = get_employee_list_errors(employee_data)

        self.assertEqual(
            errors,
            ["Employee data must be a list."],
        )


    def test_list_with_invalid_employee_is_invalid(self):
        invalid_employee = self.employee.copy()
        invalid_employee.pop("department")

        employee_list = [
            self.employee,
            invalid_employee,
        ]

        self.assertFalse(
            is_valid_employee_list(employee_list)
        )


    def test_invalid_employee_reports_list_position(self):
        invalid_employee = self.employee.copy()
        invalid_employee["salary"] = "60000"

        employee_list = [
            self.employee,
            invalid_employee,
        ]

        errors = get_employee_list_errors(employee_list)

        self.assertIn(
            "Employee #2: Field 'salary' must be int, not str.",
            errors,
        )


    def test_duplicate_employee_id_reports_error(self):
        duplicate_employee = self.employee.copy()
        duplicate_employee["employee_id"] = " emp001 "

        employee_list = [
            self.employee,
            duplicate_employee,
        ]

        errors = get_employee_list_errors(employee_list)

        self.assertFalse(
            is_valid_employee_list(employee_list)
        )
        self.assertIn(
            "Employee #2: Duplicate employee ID.",
            errors,
        )


if __name__ == "__main__":
    unittest.main()