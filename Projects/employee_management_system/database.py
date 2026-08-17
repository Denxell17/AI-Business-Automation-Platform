import sqlite3
from pathlib import Path

from models import Employee

DATA_DIRECTORY = Path(__file__).with_name("data")
DATABASE_FILE = DATA_DIRECTORY / "employees.db" 


def get_database_connection(
    database_file: Path = DATABASE_FILE,
) -> sqlite3.Connection:
    return sqlite3.connect(database_file)


def initialize_database(
    database_file: Path = DATABASE_FILE,
) -> None:
    connection = get_database_connection(database_file)

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS employees (
                employee_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                position TEXT NOT NULL,
                country TEXT NOT NULL,
                salary INTEGER NOT NULL,
                email TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                years_of_experience INTEGER NOT NULL,
                company TEXT NOT NULL,
                employment_status TEXT NOT NULL,
                performance_score INTEGER NOT NULL
            )
            """
        )
        connection.commit()
    finally:
        connection.close()


def insert_employee(
    employee: Employee,
    database_file: Path = DATABASE_FILE,
) -> bool:
    connection = get_database_connection(database_file)

    try:
        connection.execute(
            """
            INSERT INTO employees (
                employee_id,
                name,
                department,
                position,
                country,
                salary,
                email,
                phone_number,
                years_of_experience,
                company,
                employment_status,
                performance_score
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                employee["employee_id"],
                employee["name"],
                employee["department"],
                employee["position"],
                employee["country"],
                employee["salary"],
                employee["email"],
                employee["phone_number"],
                employee["years_of_experience"],
                employee["company"],
                employee["employment_status"],
                employee["performance_score"]
            ),
        )
        connection.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        connection.close()


def load_employees_from_database(
    database_file: Path = DATABASE_FILE,
) -> list[Employee]:
    connection = get_database_connection(database_file)
    connection.row_factory = sqlite3.Row

    try:
        rows = connection.execute(
            """
            SELECT
                employee_id,
                name,
                department,
                position,
                country,
                salary,
                email,
                phone_number,
                years_of_experience,
                company,
                employment_status,
                performance_score
            FROM employees
            ORDER BY employee_id
            """
        ).fetchall()
    finally:
        connection.close()

    employees: list[Employee] = []

    for row in rows:
        employee: Employee = {
            "employee_id": row["employee_id"],
            "name": row["name"],
            "department": row["department"],
            "position": row["position"],
            "country": row["country"],
            "salary": row["salary"],
            "email": row["email"],
            "phone_number": row["phone_number"],
            "years_of_experience": row[
                "years_of_experience"
            ],
            "company": row["company"],
            "employment_status": row[
                "employment_status"
            ],
            "performance_score": row[
                "performance_score"
            ],
        }

        employees.append(employee)

    return employees


def update_employee_in_database(
    employee: Employee,
    database_file: Path = DATABASE_FILE,
) -> bool:
    connection = get_database_connection(database_file)

    try:
        cursor = connection.execute(
            """
            UPDATE employees
            SET
                name = ?,
                department = ?,
                position = ?,
                country = ?,
                salary = ?,
                email = ?,
                phone_number = ?,
                years_of_experience = ?,
                company = ?,
                employment_status = ?,
                performance_score = ?
            WHERE employee_id = ?
            """,
            (
                employee["name"],
                employee["department"],
                employee["position"],
                employee["country"],
                employee["salary"],
                employee["email"],
                employee["phone_number"],
                employee["years_of_experience"],
                employee["company"],
                employee["employment_status"],
                employee["performance_score"],
                employee["employee_id"],
            ),
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def delete_employee_from_database(
    employee_id: str,
    database_file: Path = DATABASE_FILE,
) -> bool:
    connection = get_database_connection(database_file)

    try:
        cursor = connection.execute(
            """
            DELETE FROM employees
            WHERE employee_id = ?
            """,
            (employee_id,),
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def migrate_employees_to_database(
    employee_list: list[Employee],
    database_file: Path = DATABASE_FILE,
) -> int:
    initialize_database(database_file)
    migrated_count = 0

    for employee in employee_list:
        if insert_employee(employee, database_file):
            migrated_count += 1

    return migrated_count