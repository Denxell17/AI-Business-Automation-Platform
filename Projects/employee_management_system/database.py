import sqlite3
from pathlib import Path

from models import (
    Employee,
    UserAccount,
    UserAccountSummary,
)

DATA_DIRECTORY = Path(__file__).with_name("data")
DATABASE_FILE = DATA_DIRECTORY / "employees.db"
DATABASE_BACKUP_FILE = (
    DATA_DIRECTORY / "employees_backup.db"
)


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
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT COLLATE NOCASE NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK (
                    role IN ('admin', 'viewer')
                ),
                is_active INTEGER NOT NULL DEFAULT 1 CHECK (
                    is_active IN (0, 1)
                )
            )
            """
        )
        connection.commit()
    finally:
        connection.close()


def backup_database(
    database_file: Path = DATABASE_FILE,
    backup_file: Path = DATABASE_BACKUP_FILE,
) -> bool:
    if not database_file.exists():
        print("The SQLite employee database was not found.")
        return False

    source_connection: sqlite3.Connection | None = None
    backup_connection: sqlite3.Connection | None = None

    try:
        backup_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        source_connection = get_database_connection(
            database_file
        )
        backup_connection = get_database_connection(
            backup_file
        )

        source_connection.backup(backup_connection)
        return True
    except (sqlite3.Error, OSError) as error:
        print("The SQLite database backup failed.")
        print(f"Details: {error}")
        return False
    finally:
        if backup_connection is not None:
            backup_connection.close()

        if source_connection is not None:
            source_connection.close()


def restore_database_from_backup(
    database_file: Path = DATABASE_FILE,
    backup_file: Path = DATABASE_BACKUP_FILE,
) -> bool:
    if not backup_file.exists():
        print("The SQLite database backup was not found.")
        return False

    backup_connection: sqlite3.Connection | None = None
    database_connection: sqlite3.Connection | None = None

    try:
        database_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        backup_connection = get_database_connection(
            backup_file,
        )

        integrity_result = backup_connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()

        if (
            integrity_result is None
            or integrity_result[0] != "ok"
        ):
            print(
                "The SQLite database backup failed "
                "its integrity check."
            )
            return False

        database_connection = get_database_connection(
            database_file,
        )
        backup_connection.backup(database_connection)
        return True
    except (sqlite3.Error, OSError) as error:
        print("The SQLite database restoration failed.")
        print(f"Details: {error}")
        return False
    finally:
        if database_connection is not None:
            database_connection.close()

        if backup_connection is not None:
            backup_connection.close()


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


def synchronize_employees_to_database(
    employee_list: list[Employee],
    database_file: Path = DATABASE_FILE,
) -> bool:
    initialize_database(database_file)

    employee_values = []

    for employee in employee_list:
        employee_values.append(
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
                employee["performance_score"],
            )
        )

    connection = get_database_connection(database_file)

    try:
        connection.execute("DELETE FROM employees")

        connection.executemany(
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
            employee_values,
        )

        connection.commit()
        return True
    except sqlite3.Error:
        connection.rollback()
        return False
    finally:
        connection.close()


def insert_user_account(
    username: str,
    password_hash: str,
    role: str,
    database_file: Path = DATABASE_FILE,
) -> bool:
    initialize_database(database_file)
    connection = get_database_connection(database_file)

    try:
        connection.execute(
            """
            INSERT INTO users (
                username,
                password_hash,
                role
            )
            VALUES (?, ?, ?)
            """,
            (
                username,
                password_hash,
                role,
            ),
        )
        connection.commit()
        return True
    except sqlite3.IntegrityError:
        connection.rollback()
        return False
    finally:
        connection.close()


def load_user_account_by_username(
    username: str,
    database_file: Path = DATABASE_FILE,
) -> UserAccount | None:
    initialize_database(database_file)
    connection = get_database_connection(database_file)
    connection.row_factory = sqlite3.Row

    try:
        stored_user = connection.execute(
            """
            SELECT
                user_id,
                username,
                password_hash,
                role,
                is_active
            FROM users
            WHERE username = ?
            """,
            (username,),
        ).fetchone()

        if stored_user is None:
            return None

        return {
            "user_id": stored_user["user_id"],
            "username": stored_user["username"],
            "password_hash": stored_user["password_hash"],
            "role": stored_user["role"],
            "is_active": bool(stored_user["is_active"]),
        }
    finally:
        connection.close()


def load_user_account_summaries(
    database_file: Path = DATABASE_FILE,
) -> list[UserAccountSummary] | None:
    connection: sqlite3.Connection | None = None

    try:
        initialize_database(database_file)
        connection = get_database_connection(database_file)
        connection.row_factory = sqlite3.Row

        stored_users = connection.execute(
            """
            SELECT
                user_id,
                username,
                role,
                is_active
            FROM users
            ORDER BY username COLLATE NOCASE
            """
        ).fetchall()

        return [
            {
                "user_id": stored_user["user_id"],
                "username": stored_user["username"],
                "role": stored_user["role"],
                "is_active": bool(stored_user["is_active"]),
            }
            for stored_user in stored_users
        ]
    except sqlite3.Error:
        return None
    finally:
        if connection is not None:
            connection.close()


def update_user_account_active_status(
    username: str,
    is_active: bool,
    database_file: Path = DATABASE_FILE,
) -> bool:
    initialize_database(database_file)
    connection = get_database_connection(database_file)

    try:
        update_result = connection.execute(
            """
            UPDATE users
            SET is_active = ?
            WHERE username = ?
            """,
            (
                int(is_active),
                username,
            ),
        )
        connection.commit()
        return update_result.rowcount == 1
    except sqlite3.Error:
        connection.rollback()
        return False
    finally:
        connection.close()


def update_user_account_password_hash(
    username: str,
    password_hash: str,
    database_file: Path = DATABASE_FILE,
) -> bool:
    initialize_database(database_file)
    connection = get_database_connection(database_file)

    try:
        update_result = connection.execute(
            """
            UPDATE users
            SET password_hash = ?
            WHERE username = ?
            """,
            (
                password_hash,
                username,
            ),
        )
        connection.commit()
        return update_result.rowcount == 1
    except sqlite3.Error:
        connection.rollback()
        return False
    finally:
        connection.close()


def count_user_accounts(
    database_file: Path = DATABASE_FILE,
) -> int:
    initialize_database(database_file)
    connection = get_database_connection(database_file)

    try:
        stored_count = connection.execute(
            """
            SELECT count(*)
            FROM users
            """
        ).fetchone()

        return stored_count[0]
    finally:
        connection.close()
