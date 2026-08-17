REQUIRED_EMPLOYEE_FIELDS = {
    "employee_id": str,
    "name": str,
    "department": str,
    "position": str,
    "country": str,
    "salary": int,
    "email": str,
    "phone_number": str,
    "years_of_experience": int,
    "company": str,
    "employment_status": str,
    "performance_score": int,
}


def get_employee_record_errors(
    employee: object,
) -> list[str]:
    errors = []

    if not isinstance(employee, dict):
        errors.append("Employee record must be a dictionary.")
        return errors

    for field_name, expected_type in REQUIRED_EMPLOYEE_FIELDS.items():
        if field_name not in employee:
            errors.append(
                f"Missing required field: {field_name}"
            )
            continue

        actual_value = employee[field_name]

        if not isinstance(actual_value, expected_type):
            errors.append(
                f"Field '{field_name}' must be "
                f"{expected_type.__name__}, not "
                f"{type(actual_value).__name__}."
            )
            continue

        if expected_type is str and not actual_value.strip():
            errors.append(
                f"Field '{field_name}' cannot be blank."
            )

        if field_name == "salary" and actual_value <= 0:
            errors.append(
                "Field 'salary' must be greater than zero."
            )

        if (
            field_name == "years_of_experience"
            and actual_value < 0
        ):
            errors.append(
                "Field 'years_of_experience' "
                "cannot be negative."
            )

        if (
            field_name == "performance_score"
            and not 0 <= actual_value <= 100
        ):
            errors.append(
                "Field 'performance_score' must be "
                "between 0 and 100."
            )

    return errors


def is_valid_employee_record(employee: object) -> bool:
    errors = get_employee_record_errors(employee)
    return not errors


def get_employee_list_errors(
    employee_data: object,
) -> list[str]:
    errors = []
    seen_employee_ids: set[str] = set()

    if not isinstance(employee_data, list):
        errors.append("Employee data must be a list.")
        return errors

    for employee_number, employee in enumerate(
        employee_data,
        start=1,
    ):
        record_errors = get_employee_record_errors(employee)

        for error in record_errors:
            errors.append(
                f"Employee #{employee_number}: {error}"
            )

        if not isinstance(employee, dict):
            continue

        employee_id = employee.get("employee_id")

        if (
            not isinstance(employee_id, str)
            or not employee_id.strip()
        ):
            continue

        normalized_employee_id = employee_id.strip().upper()

        if normalized_employee_id in seen_employee_ids:
            errors.append(
                f"Employee #{employee_number}: "
                "Duplicate employee ID."
            )
        else:
            seen_employee_ids.add(normalized_employee_id)

    return errors


def is_valid_employee_list(employee_data: object) -> bool:
    errors = get_employee_list_errors(employee_data)
    return not errors