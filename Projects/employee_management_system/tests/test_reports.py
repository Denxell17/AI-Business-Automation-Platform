import unittest

from reports import calculate_workforce_summary


class TestWorkforceSummary(unittest.TestCase):

    def test_summary_with_employees(self):
        employees = [
            {
                "employee_id": "EMP001",
                "name": "Dennis",
                "salary": 60000,
                "department": "Automation",
            },
            {
                "employee_id": "EMP002",
                "name": "Maria",
                "salary": 50000,
                "department": "Finance",
            },
        ]

        summary = calculate_workforce_summary(employees)

        self.assertEqual(
            summary["total_employees"], 2,
        )
        self.assertEqual(
            summary["total_departments"], 2,
        )
        self.assertEqual(
            summary["total_monthly_payroll"], 110000,
        )
        self.assertEqual(
            summary["average_salary"], 55000,
        )

        highest_paid_employee = summary[
            "highest_paid_employee"
        ]

        self.assertEqual(
            highest_paid_employee["name"], "Dennis",
        )
        self.assertEqual(
            highest_paid_employee["salary"], 60000,
        )

        lowest_paid_employee = summary[
            "lowest_paid_employee"
        ]

        self.assertEqual(
            lowest_paid_employee["name"], "Maria",
        )
        self.assertEqual(
            lowest_paid_employee["salary"], 50000,
        )
        self.assertEqual(
            summary["salary_range"], 10000,
        )
        self.assertEqual(
            summary["department_counts"],
            {
                "Automation": 1,
                "Finance": 1,
            },
        )
        self.assertEqual(
            summary["department_payrolls"],
            {
                "Automation": 60000,
                "Finance": 50000,
            },
        )
        self.assertEqual(
            summary["department_average_salaries"],
            {
                "Automation": 60000,
                "Finance": 50000,
            },
        )
        self.assertEqual(
            summary["highest_payroll_department"],
            "Automation",
        )
        self.assertEqual(
            summary["highest_average_salary_department"],
            "Automation",
        )
        self.assertEqual(
            summary["lowest_payroll_department"],
            "Finance",
        )
        self.assertEqual(
            summary["lowest_average_salary_department"],
            "Finance",
        )


    def test_largest_and_smallest_departments(self):
        employees = [
            {
                "name": "Dennis",
                "salary": 60000,
                "department": "Automation",
            },
            {
                "name": "Maria",
                "salary": 50000,
                "department": "Finance",
            },
            {
                "name": "Ruth",
                "salary": 40000,
                "department": "Finance",
            },
        ]

        summary = calculate_workforce_summary(employees)

        self.assertEqual(
            summary["largest_department"],
            "Finance",
        )
        self.assertEqual(
            summary["smallest_department"],
            "Automation",
        )


    def test_summary_with_no_employees(self):
        summary = calculate_workforce_summary([])

        self.assertEqual(
            summary["total_employees"], 0,
        )
        self.assertEqual(
            summary["total_departments"], 0,
        )
        self.assertEqual(
            summary["total_monthly_payroll"], 0,
        )
        self.assertEqual(
            summary["average_salary"], 0,
        )
        self.assertIsNone(
            summary["highest_paid_employee"],
        )
        self.assertIsNone(
            summary["lowest_paid_employee"],
        )
        self.assertEqual(
            summary["salary_range"], 0,
        )
        self.assertEqual(
            summary["department_counts"],
            {},
        )
        self.assertEqual(
            summary["department_payrolls"],
            {},
        )
        self.assertEqual(
            summary["department_average_salaries"],
            {},
        )
        self.assertIsNone(
            summary["highest_payroll_department"],
        )
        self.assertIsNone(
            summary["highest_average_salary_department"],
        )
        self.assertIsNone(
            summary["lowest_payroll_department"],
        )
        self.assertIsNone(
            summary["lowest_average_salary_department"],
        )
        self.assertIsNone(
            summary["largest_department"],
        )
        self.assertIsNone(
            summary["smallest_department"],
        )


    def test_department_totals_combine_same_department(self):
        employees = [
            {
                "name": "Maria",
                "salary": 50000,
                "department": "Finance",
            },
            {
                "name": "Ruth",
                "salary": 40000,
                "department": "Finance",
            },
        ]

        summary = calculate_workforce_summary(employees)

        self.assertEqual(
            summary["department_payrolls"],
            {
                "Finance": 90000,
            },
        )
        self.assertEqual(
            summary["department_average_salaries"],
            {
                "Finance": 45000,
            },
        )


if __name__ == "__main__":
    unittest.main()