from pathlib import Path

from database import (
    DATABASE_FILE,
    load_employees_from_database,
    migrate_employees_to_database,
)
from storage import (
    DATA_FILE,
    load_employees,
)


def migrate_json_file_to_database(
    json_file: Path = DATA_FILE,
    database_file: Path = DATABASE_FILE,
) -> bool:
    if not json_file.exists():
        print("The JSON employee file was not found.")
        return False

    employees = load_employees(json_file)

    if employees is None:
        print("The JSON-to-SQLite migration was stopped.")
        return False

    migrated_count = migrate_employees_to_database(
        employees,
        database_file,
    )
    database_employees = load_employees_from_database(
        database_file,
    )
    expected_employees = sorted(
        employees,
        key=lambda employee: employee["employee_id"],
    )

    if database_employees != expected_employees:
        print("The JSON-to-SQLite migration verification failed.")
        return False

    print(
        "JSON-to-SQLite migration completed successfully."
    )
    print(f"New employees migrated: {migrated_count}")
    print(f"Total employees verified: {len(database_employees)}")
    return True


if __name__ == "__main__":
    migration_succeeded = migrate_json_file_to_database()

    if not migration_succeeded:
        raise SystemExit(1)