import json
from pathlib import Path
from shutil import copy2

from data_validation import get_employee_list_errors
from models import Employee


DATA_DIRECTORY = Path(__file__).with_name("data")
DATA_FILE = DATA_DIRECTORY / "employees.json"


def get_temporary_file_path(
    file_path: Path,
) -> Path:
    return file_path.with_name(
        f"{file_path.name}.tmp"
    )


def get_backup_file_path(
    file_path: Path,
) -> Path:
    return file_path.with_name(
        f"{file_path.name}.bak"
    )


def load_employees(
    file_path: Path = DATA_FILE,
) -> list[Employee] | None:
    if not file_path.exists():
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            employee_data = json.load(file)

        validation_errors = get_employee_list_errors(
            employee_data
        )

        if validation_errors:
            print()
            print("ERROR: The employee data has an invalid structure.")

            for validation_error in validation_errors:
                print(f"- {validation_error}")

            print("The application will stop to protect your data.")
            return None

        return employee_data

    except json.JSONDecodeError:
        print()
        print("ERROR: The employee data file contains invalid JSON.")
        print("The application will stop to protect your data.")
        return None

    except OSError as error:
        print()
        print("ERROR: The employee data file could not be read.")
        print(f"Details: {error}")
        return None


def save_employees(
    employee_list: list[Employee],
    file_path: Path = DATA_FILE,
) -> bool:
    temporary_file = get_temporary_file_path(file_path)
    backup_file = get_backup_file_path(file_path)

    try:
        with open(
            temporary_file,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(employee_list, file, indent=4)

        if file_path.exists():
            copy2(file_path, backup_file)

        temporary_file.replace(file_path)
        return True

    except (OSError, TypeError) as error:
        print()
        print("ERROR: The employee records could not be saved.")
        print(f"Details: {error}")
        return False

    finally:
        if temporary_file.exists():
            try:
                temporary_file.unlink()
            except OSError:
                pass


def restore_employees_from_backup(
    file_path: Path = DATA_FILE,
) -> bool:
    backup_file = get_backup_file_path(file_path)

    if not backup_file.exists():
        print("No employee backup file found.")
        return False

    backup_employees = load_employees(backup_file)

    if backup_employees is None:
        print("The employee backup could not be restored.")
        return False

    return save_employees(
        backup_employees,
        file_path,
    )