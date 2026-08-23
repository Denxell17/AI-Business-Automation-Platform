import sqlite3
from pathlib import Path

from config import (
    PRIMARY_STORAGE,
    SUPPORTED_STORAGE_TYPES,
)
from database import (
    DATABASE_FILE,
    load_employees_from_database,
    synchronize_employees_to_database,
)
from models import Employee
from storage import (
    DATA_FILE,
    load_employees,
    save_employees,
)


def load_employee_records(
    storage_type: str = PRIMARY_STORAGE,
    json_file: Path = DATA_FILE,
    database_file: Path = DATABASE_FILE,
) -> list[Employee] | None:
    if storage_type not in SUPPORTED_STORAGE_TYPES:
        print(
            f"Unsupported primary storage type: "
            f"{storage_type}"
        )
        return None

    if storage_type == "json":
        employees = load_employees(json_file)

        if employees is None:
            return None

        database_synchronized = (
            synchronize_employees_to_database(
                employees,
                database_file,
            )
        )

        if not database_synchronized:
            print(
                "WARNING: Employees loaded from JSON, "
                "but SQLite synchronization failed."
            )

        return employees

    if not database_file.exists():
        print("The primary SQLite database was not found.")
        return None

    try:
        return load_employees_from_database(
            database_file
        )
    except sqlite3.Error as error:
        print("The primary SQLite database could not be read.")
        print(f"Details: {error}")
        return None


def save_employee_records(
    employee_list: list[Employee],
    storage_type: str = PRIMARY_STORAGE,
    json_file: Path = DATA_FILE,
    database_file: Path = DATABASE_FILE,
) -> bool:
    if storage_type not in SUPPORTED_STORAGE_TYPES:
        print(
            f"Unsupported primary storage type: "
            f"{storage_type}"
        )
        return False

    if storage_type == "json":
        json_saved = save_employees(
            employee_list,
            json_file,
        )

        if not json_saved:
            return False

        database_synchronized = (
            synchronize_employees_to_database(
                employee_list,
                database_file,
            )
        )

        if not database_synchronized:
            print(
                "WARNING: Employees were saved to JSON, "
                "but SQLite synchronization failed."
            )

        return True

    database_saved = synchronize_employees_to_database(
        employee_list,
        database_file,
    )

    if not database_saved:
        return False

    return True