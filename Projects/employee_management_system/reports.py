from models import (
    Employee,
    WorkforceSummary,
)


def calculate_workforce_summary(
    employee_list: list[Employee],
) -> WorkforceSummary:
    if not employee_list:
        return {
            "total_employees": 0,
            "total_departments": 0,
            "total_monthly_payroll": 0,
            "average_salary": 0,
            "highest_paid_employee": None,
            "lowest_paid_employee": None,
            "salary_range": 0,
            "department_counts": {},
            "department_payrolls": {},
            "department_average_salaries": {},
            "highest_payroll_department": None,
            "highest_average_salary_department": None,
            "lowest_payroll_department": None,
            "lowest_average_salary_department": None,
            "largest_department": None,
            "smallest_department": None,
        }

    total_monthly_payroll = 0
    highest_paid_employee = employee_list[0]
    lowest_paid_employee = employee_list[0]
    department_counts = {}
    department_payrolls = {}

    for employee in employee_list:
        total_monthly_payroll += employee["salary"]

        if employee["salary"] > highest_paid_employee["salary"]:
            highest_paid_employee = employee

        if employee["salary"] < lowest_paid_employee["salary"]:
            lowest_paid_employee = employee

        department = employee["department"]

        if department in department_counts:
            department_counts[department] += 1
        else:
            department_counts[department] = 1

        department_payrolls[department] = (
            department_payrolls.get(department, 0)
            + employee["salary"]
        )

    total_departments = len(department_counts)

    department_average_salaries = {}

    for department, department_payroll in department_payrolls.items():
        employee_count = department_counts[department]

        department_average_salaries[department] = (
            department_payroll / employee_count
        )

    highest_payroll_department = max(
        department_payrolls,
        key=department_payrolls.get,
    )

    highest_average_salary_department = max(
        department_average_salaries,
        key=department_average_salaries.get,
    )

    lowest_payroll_department = min(
        department_payrolls,
        key=department_payrolls.get,
    )

    lowest_average_salary_department = min(
        department_average_salaries,
        key=department_average_salaries.get,
    )

    largest_department = max(
        department_counts,
        key=department_counts.get,
    )

    smallest_department = min(
        department_counts,
        key=department_counts.get,
    )

    average_salary = (
        total_monthly_payroll / len(employee_list)
    )
    salary_range = (
        highest_paid_employee["salary"]
        - lowest_paid_employee["salary"]
    )

    return {
        "total_employees": len(employee_list),
        "total_departments": total_departments,
        "total_monthly_payroll": total_monthly_payroll,
        "average_salary": average_salary,
        "highest_paid_employee": highest_paid_employee,
        "lowest_paid_employee": lowest_paid_employee,
        "salary_range": salary_range,
        "department_counts": department_counts,
        "department_payrolls": department_payrolls,
        "department_average_salaries": department_average_salaries,
        "highest_payroll_department": highest_payroll_department,
        "highest_average_salary_department": (
            highest_average_salary_department
        ),
        "lowest_payroll_department": lowest_payroll_department,
        "lowest_average_salary_department": (
            lowest_average_salary_department
        ),
        "largest_department": largest_department,
        "smallest_department": smallest_department,
    }
