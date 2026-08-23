import sqlite3
from pathlib import Path

from database import (
    DATABASE_FILE,
    load_employees_from_database,
)
from storage import (
    DATA_FILE,
    load_employees,
)


def verify_json_and_database_match(
    json_file: Path = DATA_FILE,
    database_file: Path = DATABASE_FILE,
) -> bool:
    if not json_file.exists():
        print("The JSON employee file was not found.")
        return False

    if not database_file.exists():
        print("The SQLite employee database was not found.")
        return False

    json_employees = load_employees(json_file)

    if json_employees is None:
        print("Storage verification stopped because JSON is invalid.")
        return False

    try:
        database_employees = load_employees_from_database(
            database_file,
        )
    except sqlite3.Error as error:
        print("The SQLite employee database could not be read.")
        print(f"Details: {error}")
        return False

    sorted_json_employees = sorted(
        json_employees,
        key=lambda employee: employee["employee_id"],
    )
    sorted_database_employees = sorted(
        database_employees,
        key=lambda employee: employee["employee_id"],
    )

    if sorted_json_employees != sorted_database_employees:
        print("JSON and SQLite employee records do not match.")
        print(f"JSON employees: {len(sorted_json_employees)}")
        print(
            "SQLite employees: "
            f"{len(sorted_database_employees)}"
        )
        return False

    print("JSON and SQLite employee records match.")
    print(
        f"Total employees verified: "
        f"{len(sorted_json_employees)}"
    )
    return True


if __name__ == "__main__":
    verification_succeeded = (
        verify_json_and_database_match()
    )

    if not verification_succeeded:
        raise SystemExit(1)