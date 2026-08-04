import unittest

from main_refactored import (
    calculate_payroll,
    determine_performance,
    find_employee_by_id,
)


class TestEmployeeSearch(unittest.TestCase):


    def setUp(self):
        self.employees = [
            {
                "employee_id": "EMP001",
                "name": "Dennis",   
            },
            {
                "employee_id": "EMP002",
                "name": "Maria",
            },
        ]


    def test_find_existing_employee(self):
        employee = find_employee_by_id(
            self.employees,
            "EMP002"
        )

        self.assertIsNotNone(employee)
        self.assertEqual(employee["name"], "Maria")

    def test_employee_not_found(self):
        employee = find_employee_by_id(
            self.employees,
            "EMP999"
        )

        self.assertIsNone(employee)


    def test_search_is_case_insensitive(self):
        employee = find_employee_by_id(
            self.employees,
            "emp001"
        )

        self.assertIsNotNone(employee)
        self.assertEqual(
            employee["employee_id"],
            "EMP001"
        )

class TestPerformance(unittest.TestCase):

    def test_outstanding_boundary(self):
        rating, bonus_rate = determine_performance(90)

        self.assertEqual(
            rating,
            "Outstanding"
        )
        self.assertEqual(
            bonus_rate,
            0.15
        )

    def test_invalid_performance_score(self):
        rating, bonus_rate = determine_performance(101)

        self.assertEqual(rating, "Invalid Score")
        self.assertEqual(bonus_rate, 0)


class TestPayroll(unittest.TestCase):

    def setUp(self):
        employee = {
            "salary": 60000,
            "performance_score": 88,
        }

        self.payroll = calculate_payroll(employee)



    def test_annual_salary_calculation(self):
        self.assertEqual(
            self.payroll["annual_salary"],
            720000
        )

    def test_monthly_tax_calculation(self):
        self.assertEqual(
            self.payroll["monthly_tax"],
            3000
        )

    def test_estimated_bonus_calculation(self):
        self.assertEqual(
            self.payroll["estimated_bonus"],
            72000
        )

    def test_total_compensation_calculation(self):
        self.assertEqual(
            self.payroll["total_compensation"],
            852000
        )


if __name__ == "__main__":
    unittest.main()