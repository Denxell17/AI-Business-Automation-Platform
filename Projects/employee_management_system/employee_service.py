from models import Employee


def find_employee_by_id(
    employee_list: list[Employee],
    employee_id: str,
) -> Employee | None:
    employee_id = employee_id.strip().upper()

    for employee in employee_list:
        if employee["employee_id"].upper() == employee_id:
            return employee

    return None


def filter_employees_by_department(
    employee_list: list[Employee],
    department: str,
) -> list[Employee]:
    normalized_department = department.strip().casefold()

    if not normalized_department:
        return []

    matching_employees = []

    for employee in employee_list:
        employee_department = (
            employee["department"].strip().casefold()
        )

        if employee_department == normalized_department:
            matching_employees.append(employee)

    return matching_employees


def filter_employees_by_salary_range(
    employee_list: list[Employee],
    minimum_salary: int,
    maximum_salary: int,
) -> list[Employee]:
    if minimum_salary > maximum_salary:
        return []

    matching_employees = []

    for employee in employee_list:
        salary = employee["salary"]

        if minimum_salary <= salary <= maximum_salary:
            matching_employees.append(employee)

    return matching_employees


def search_employees_by_name(
    employee_list: list[Employee],
    search_text: str,
) -> list[Employee]:
    normalized_search_text = search_text.strip().casefold()

    if not normalized_search_text:
        return []

    matching_employees = []

    for employee in employee_list:
        normalized_name = employee["name"].casefold()

        if normalized_search_text in normalized_name:
            matching_employees.append(employee)

    return matching_employees


def sort_employees_by_name(
    employee_list: list[Employee],
) -> list[Employee]:
    return sorted(
        employee_list,
        key=lambda employee: employee["name"].casefold(),
    )


def sort_employees_by_salary(
    employee_list: list[Employee],
) -> list[Employee]:
    return sorted(
        employee_list,
        key=lambda employee: employee["salary"],
        reverse=True,
    )


def update_employee_details(
    employee: Employee,
    department: str,
    position: str,
) -> bool:
    changes_made = False

    department = department.strip()
    position = position.strip()

    if department:
        employee["department"] = department
        changes_made = True

    if position:
        employee["position"] = position
        changes_made = True

    return changes_made


def remove_employee(
    employee_list: list[Employee],
    employee: Employee,
) -> bool:
    if employee not in employee_list:
        return False

    employee_list.remove(employee)
    return True