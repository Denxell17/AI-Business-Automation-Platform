import unittest

from employee_service import (
    filter_employees_by_department,
    filter_employees_by_salary_range,
    find_employee_by_id,
    remove_employee,
    search_employees_by_name,
    sort_employees_by_name,
    sort_employees_by_salary,
    update_employee_contact_details,
    update_employee_details,
)
from payroll import (
    calculate_payroll,
    determine_performance,
)
from config import (
    DEFAULT_ALLOWANCE,
    DEFAULT_OVERTIME,
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


class TestEmployeeNameSearch(unittest.TestCase):

    def test_partial_name_returns_matching_employees(self):
        employees = [
            {
                "employee_id": "EMP001",
                "name": "Dennis",
            },
            {
                "employee_id": "EMP002",
                "name": "Maria Santos",
            },
            {
                "employee_id": "EMP003",
                "name": "Marian Cruz",
            },
        ]

        matching_employees = search_employees_by_name(
            employees,
            "mari",
        )

        matching_names = [
            employee["name"]
            for employee in matching_employees
        ]

        self.assertEqual(
            matching_names,
            ["Maria Santos", "Marian Cruz"],
        )


    def test_name_search_ignores_spaces_and_capitalization(self):
        employees = [
            {
                "employee_id": "EMP001",
                "name": "Ruth",
            }
        ]

        matching_employees = search_employees_by_name(
            employees,
            "  RU  ",
        )

        self.assertEqual(len(matching_employees), 1)
        self.assertEqual(
            matching_employees[0]["name"],
            "Ruth",
        )


    def test_blank_name_search_returns_empty_list(self):
        employees = [
            {
                "employee_id": "EMP001",
                "name": "Dennis",
            }
        ]

        matching_employees = search_employees_by_name(
            employees,
            "  ",
        )

        self.assertEqual(matching_employees, [])


class TestEmployeeDepartmentFilter(unittest.TestCase):

    def setUp(self):
        self.employees = [
            {
                "employee_id": "EMP001",
                "name": "Dennis",
                "department": "Automation",
            },
            {
                "employee_id": "EMP002",
                "name": "Maria",
                "department": "Finance",
            },
            {
                "employee_id": "EMP003",
                "name": "Ruth",
                "department": "Finance",
            },
        ]


    def test_filter_returns_matching_employees(self):
        matching_employees = filter_employees_by_department(
            self.employees,
            " finance ",
        )

        self.assertEqual(len(matching_employees), 2)
        self.assertEqual(
            matching_employees[0]["name"],
            "Maria",
        )
        self.assertEqual(
            matching_employees[1]["name"],
            "Ruth",
        )


    def test_filter_returns_empty_list_when_no_match(self):
        matching_employees = filter_employees_by_department(
            self.employees,
            "Human Resources",
        )

        self.assertEqual(matching_employees, [])


    def test_filter_returns_empty_list_for_blank_input(self):
        matching_employees = filter_employees_by_department(
            self.employees,
            "  ",
        )

        self.assertEqual(matching_employees, [])


class TestEmployeeSalaryRangeFilter(unittest.TestCase):

    def test_filter_returns_employees_within_salary_range(self):
        employees = [
            {
                "employee_id": "EMP001",
                "name": "Dennis",
                "salary": 40000,
            },
            {
                "employee_id": "EMP002",
                "name": "Maria",
                "salary": 50000,
            },
            {
                "employee_id": "EMP003",
                "name": "Ruth",
                "salary": 70000,
            },
        ]

        matching_employees = filter_employees_by_salary_range(
            employees,
            50000,
            70000,
        )

        matching_names = [
            employee["name"]
            for employee in matching_employees
        ]

        self.assertEqual(
            matching_names,
            ["Maria", "Ruth"],
        )


    def test_reversed_salary_range_returns_empty_list(self):
        employees = [
            {
                "employee_id": "EMP001",
                "name": "Dennis",
                "salary": 60000,
            }
        ]

        matching_employees = filter_employees_by_salary_range(
            employees,
            70000,
            50000,
        )

        self.assertEqual(matching_employees, [])

class TestEmployeeNameSorting(unittest.TestCase):

    def test_employees_are_sorted_by_name(self):
        employees = [
            {
                "employee_id": "EMP001",
                "name": "Ruth",
            },
            {
                "employee_id": "EMP002",
                "name": "aki",
            },
            {
                "employee_id": "EMP003",
                "name": "Dennis",
            },
        ]

        sorted_employees = sort_employees_by_name(employees)

        sorted_names = [
            employee["name"]
            for employee in sorted_employees
        ]

        self.assertEqual(
            sorted_names,
            ["aki", "Dennis", "Ruth"],
        )


    def test_sorting_does_not_change_original_list(self):
        employees = [
            {
                "employee_id": "EMP001",
                "name": "Ruth",
            },
            {
                "employee_id": "EMP002",
                "name": "Aki",
            },
        ]

        sorted_employees = sort_employees_by_name(employees)

        self.assertEqual(
            employees[0]["name"],
            "Ruth",
        )
        self.assertEqual(
            sorted_employees[0]["name"],
            "Aki",
        )
        self.assertIsNot(
            sorted_employees,
            employees,
        )


class TestEmployeeSalarySorting(unittest.TestCase):

    def test_employees_are_sorted_by_highest_salary(self):
        employees = [
            {
                "employee_id": "EMP001",
                "name": "Dennis",
                "salary": 40000,
            },
            {
                "employee_id": "EMP002",
                "name": "Maria",
                "salary": 70000,
            },
            {
                "employee_id": "EMP003",
                "name": "Ruth",
                "salary": 50000,
            },
        ]

        sorted_employees = sort_employees_by_salary(
            employees
        )

        sorted_salaries = [
            employee["salary"]
            for employee in sorted_employees
        ]

        self.assertEqual(
            sorted_salaries,
            [70000, 50000, 40000],
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

    def test_default_allowance(self):
        self.assertEqual(
            self.payroll["allowance"],
            DEFAULT_ALLOWANCE
        )

    def test_default_overtime(self):
        self.assertEqual(
            self.payroll["overtime"],
            DEFAULT_OVERTIME
        )


class TestEmployeeUpdate(unittest.TestCase):

    def test_update_department_and_position(self):
        employee = {
            "employee_id": "EMP001",
            "department": "Finance",
            "position": "Assistant",
        }

        changes_made = update_employee_details(
            employee,
            "Automation",
            "Developer"
        )

        self.assertTrue(changes_made)
        self.assertEqual(
            employee["department"],
            "Automation",
        )
        self.assertEqual(
            employee["position"],
            "Developer",
        )

    def test_blank_values_keep_current_details(self):
        employee = {
            "employee_id": "EMP001",
            "department": "Finance",
            "position": "Assistant",
        }

        changes_made = update_employee_details(
            employee,
            "",
            "   ",
        )

        self.assertFalse(changes_made)
        self.assertEqual(
            employee["department"],
            "Finance",
        )
        self.assertEqual(
            employee["position"],
            "Assistant",
        )

    def test_update_email_and_phone_number(self):
        employee = {
            "employee_id": "EMP001",
            "email": "old@example.com",
            "phone_number": "111111",
        }

        changes_made = update_employee_contact_details(
            employee,
            "new@example.com",
            "222222",
        )

        self.assertTrue(changes_made)
        self.assertEqual(
            employee["email"],
            "new@example.com",
        )
        self.assertEqual(
            employee["phone_number"],
            "222222",
        )

    def test_blank_contact_values_keep_current_details(self):
        employee = {
            "employee_id": "EMP001",
            "email": "old@example.com",
            "phone_number": "111111",
        }

        changes_made = update_employee_contact_details(
            employee,
            "   ",
            "",
        )

        self.assertFalse(changes_made)
        self.assertEqual(
            employee["email"],
            "old@example.com",
        )
        self.assertEqual(
            employee["phone_number"],
            "111111",
        )


class TestEmployeeRemoval(unittest.TestCase):

    def test_remove_existing_employee(self):
        employee = {
            "employee_id": "EMP001",
            "name": "Dennis",
        }
        employees = [employee]

        employee_removed = remove_employee(
            employees,
            employee,
        )

        self.assertTrue(employee_removed)
        self.assertEqual(employees, [])

    def test_remove_missing_employee(self):
        employees = [
            {
                "employee_id": "EMP001",
                "name": "Dennis",
            }
        ]
        missing_employee = {
            "employee_id": "EMP999",
            "name": "Unknown",
        }

        employee_removed = remove_employee(
            employees,
            missing_employee,
        )

        self.assertFalse(employee_removed)
        self.assertEqual(len(employees), 1)

if __name__ == "__main__":
    unittest.main()