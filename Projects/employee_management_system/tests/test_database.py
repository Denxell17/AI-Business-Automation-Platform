import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from database import (
    backup_database,
    count_user_accounts,
    delete_employee_from_database,
    get_database_connection,
    initialize_database,
    insert_employee,
    insert_workflow,
    insert_user_account,
    load_employees_from_database,
    load_workflows_from_database,
    load_user_account_by_username,
    load_user_account_summaries,
    migrate_employees_to_database,
    restore_database_from_backup,
    synchronize_employees_to_database,
    update_employee_in_database,
    update_user_account_active_status,
    update_user_account_password_hash,
)


class TestEmployeeDatabase(unittest.TestCase):

    def test_backup_returns_false_when_database_missing(self):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )
            backup_file = (
                Path(temporary_directory) / "employees_backup.db"
            )

            result = backup_database(
                database_file,
                backup_file,
            )

            self.assertFalse(result)
            self.assertFalse(backup_file.exists())

    def test_backup_database_copies_employee_records(self):
        employee = {
            "employee_id": "EMP001",
            "name": "Dennis",
            "department": "Automation",
            "position": "Developer",
            "country": "Philippines",
            "salary": 60000,
            "email": "dennis@example.com",
            "phone_number": "09123456789",
            "years_of_experience": 2,
            "company": "ABC Company",
            "employment_status": "Active",
            "performance_score": 90,
        }

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )
            backup_file = (
                Path(temporary_directory)
                / "backups"
                / "employees_backup.db"
            )

            setup_result = synchronize_employees_to_database(
                [employee],
                database_file,
            )
            backup_result = backup_database(
                database_file,
                backup_file,
            )
            backup_employees = load_employees_from_database(
                backup_file,
            )

            self.assertTrue(setup_result)
            self.assertTrue(backup_result)
            self.assertTrue(backup_file.exists())
            self.assertEqual(
                backup_employees,
                [employee],
            )

    def test_backup_database_replaces_existing_backup(self):
        employee = {
            "employee_id": "EMP001",
            "name": "Dennis",
            "department": "Automation",
            "position": "Developer",
            "country": "Philippines",
            "salary": 60000,
            "email": "dennis@example.com",
            "phone_number": "09123456789",
            "years_of_experience": 2,
            "company": "ABC Company",
            "employment_status": "Active",
            "performance_score": 90,
        }
        updated_employee = employee.copy()
        updated_employee["name"] = "Dennis Updated"

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )
            backup_file = (
                Path(temporary_directory) / "employees_backup.db"
            )

            first_setup = synchronize_employees_to_database(
                [employee],
                database_file,
            )
            first_backup = backup_database(
                database_file,
                backup_file,
            )
            second_setup = synchronize_employees_to_database(
                [updated_employee],
                database_file,
            )
            second_backup = backup_database(
                database_file,
                backup_file,
            )
            backup_employees = load_employees_from_database(
                backup_file,
            )

            self.assertTrue(first_setup)
            self.assertTrue(first_backup)
            self.assertTrue(second_setup)
            self.assertTrue(second_backup)
            self.assertEqual(
                backup_employees,
                [updated_employee],
            )

    def test_restore_returns_false_when_backup_missing(self):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )
            backup_file = (
                Path(temporary_directory) / "employees_backup.db"
            )

            result = restore_database_from_backup(
                database_file,
                backup_file,
            )

            self.assertFalse(result)
            self.assertFalse(database_file.exists())

    def test_restore_database_copies_backup_records(self):
        employee = {
            "employee_id": "EMP001",
            "name": "Dennis",
            "department": "Automation",
            "position": "Developer",
            "country": "Philippines",
            "salary": 60000,
            "email": "dennis@example.com",
            "phone_number": "09123456789",
            "years_of_experience": 2,
            "company": "ABC Company",
            "employment_status": "Active",
            "performance_score": 90,
        }

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory)
                / "restored"
                / "employees.db"
            )
            backup_file = (
                Path(temporary_directory) / "employees_backup.db"
            )

            backup_setup = synchronize_employees_to_database(
                [employee],
                backup_file,
            )
            restore_result = restore_database_from_backup(
                database_file,
                backup_file,
            )
            restored_employees = load_employees_from_database(
                database_file,
            )

            self.assertTrue(backup_setup)
            self.assertTrue(restore_result)
            self.assertTrue(database_file.exists())
            self.assertEqual(
                restored_employees,
                [employee],
            )

    def test_restore_database_replaces_changed_records(self):
        backup_employee = {
            "employee_id": "EMP001",
            "name": "Dennis",
            "department": "Automation",
            "position": "Developer",
            "country": "Philippines",
            "salary": 60000,
            "email": "dennis@example.com",
            "phone_number": "09123456789",
            "years_of_experience": 2,
            "company": "ABC Company",
            "employment_status": "Active",
            "performance_score": 90,
        }
        changed_employee = backup_employee.copy()
        changed_employee["name"] = "Wrong Name"

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )
            backup_file = (
                Path(temporary_directory) / "employees_backup.db"
            )

            backup_setup = synchronize_employees_to_database(
                [backup_employee],
                backup_file,
            )
            database_setup = synchronize_employees_to_database(
                [changed_employee],
                database_file,
            )
            restore_result = restore_database_from_backup(
                database_file,
                backup_file,
            )
            restored_employees = load_employees_from_database(
                database_file,
            )

            self.assertTrue(backup_setup)
            self.assertTrue(database_setup)
            self.assertTrue(restore_result)
            self.assertEqual(
                restored_employees,
                [backup_employee],
            )

    def test_invalid_backup_does_not_change_database(self):
        employee = {
            "employee_id": "EMP001",
            "name": "Dennis",
            "department": "Automation",
            "position": "Developer",
            "country": "Philippines",
            "salary": 60000,
            "email": "dennis@example.com",
            "phone_number": "09123456789",
            "years_of_experience": 2,
            "company": "ABC Company",
            "employment_status": "Active",
            "performance_score": 90,
        }

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )
            backup_file = (
                Path(temporary_directory) / "employees_backup.db"
            )

            database_setup = synchronize_employees_to_database(
                [employee],
                database_file,
            )
            backup_file.write_text(
                "This is not a SQLite database.",
                encoding="utf-8",
            )

            restore_result = restore_database_from_backup(
                database_file,
                backup_file,
            )
            database_employees = load_employees_from_database(
                database_file,
            )

            self.assertTrue(database_setup)
            self.assertFalse(restore_result)
            self.assertEqual(
                database_employees,
                [employee],
            )

    def test_initialize_database_creates_employee_table(self):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            initialize_database(database_file)

            connection = get_database_connection(database_file)

            try:
                table = connection.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'table'
                    AND name = 'employees'
                    """
                ).fetchone()
            finally:
                connection.close()

            self.assertIsNotNone(table)

    def test_initialize_database_creates_users_table(self):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            initialize_database(database_file)

            connection = get_database_connection(database_file)

            try:
                table = connection.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'table'
                    AND name = 'users'
                    """
                ).fetchone()
            finally:
                connection.close()

            self.assertIsNotNone(table)

    def test_initialize_database_creates_workflows_table(self):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            initialize_database(database_file)

            connection = get_database_connection(database_file)

            try:
                table = connection.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'table'
                    AND name = 'workflows'
                    """
                ).fetchone()

                columns = connection.execute(
                    "PRAGMA table_info(workflows)"
                ).fetchall()
            finally:
                connection.close()

            column_names = {
                column[1]
                for column in columns
            }

            self.assertIsNotNone(table)
            self.assertEqual(
                column_names,
                {
                    "workflow_id",
                    "name",
                    "description",
                    "status",
                    "created_by_user_id",
                    "created_at",
                    "updated_at",
                },
            )

    def test_workflows_table_rejects_invalid_status(self):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

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
                        "WorkflowAdmin",
                        "temporary_hash",
                        "admin",
                    ),
                )

                creator = connection.execute(
                    """
                    SELECT user_id
                    FROM users
                    WHERE username = ?
                    """,
                    ("WorkflowAdmin",),
                ).fetchone()

                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute(
                        """
                        INSERT INTO workflows (
                            workflow_id,
                            name,
                            description,
                            status,
                            created_by_user_id,
                            created_at,
                            updated_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            "WF-000001",
                            "New employee onboarding",
                            "",
                            "unknown",
                            creator[0],
                            "2026-09-05T00:00:00+00:00",
                            "2026-09-05T00:00:00+00:00",
                        ),
                    )
            finally:
                connection.close()

    def test_workflows_table_rejects_missing_creator(self):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            initialize_database(database_file)

            connection = get_database_connection(database_file)

            try:
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute(
                        """
                        INSERT INTO workflows (
                            workflow_id,
                            name,
                            description,
                            status,
                            created_by_user_id,
                            created_at,
                            updated_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            "WF-000002",
                            "Customer follow-up review",
                            "",
                            "draft",
                            999,
                            "2026-09-05T00:00:00+00:00",
                            "2026-09-05T00:00:00+00:00",
                        ),
                    )
            finally:
                connection.close()

    def test_workflows_table_rejects_blank_name(self):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

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
                        "WorkflowAdmin",
                        "temporary_hash",
                        "admin",
                    ),
                )

                creator = connection.execute(
                    """
                    SELECT user_id
                    FROM users
                    WHERE username = ?
                    """,
                    ("WorkflowAdmin",),
                ).fetchone()

                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute(
                        """
                        INSERT INTO workflows (
                            workflow_id,
                            name,
                            description,
                            status,
                            created_by_user_id,
                            created_at,
                            updated_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            "WF-000003",
                            "   ",
                            "",
                            "draft",
                            creator[0],
                            "2026-09-05T00:00:00+00:00",
                            "2026-09-05T00:00:00+00:00",
                        ),
                    )
            finally:
                connection.close()

    def test_insert_workflow_saves_record(self):
        workflow = {
            "workflow_id": "WF-000001",
            "name": "New employee onboarding",
            "description": "Coordinate onboarding tasks.",
            "status": "draft",
            "created_by_user_id": 0,
            "created_at": "2026-09-05T00:00:00+00:00",
            "updated_at": "2026-09-05T00:00:00+00:00",
        }

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            user_created = insert_user_account(
                "WorkflowAdmin",
                "temporary_hash",
                "admin",
                database_file,
            )
            creator = load_user_account_by_username(
                "WorkflowAdmin",
                database_file,
            )

            self.assertTrue(user_created)
            self.assertIsNotNone(creator)

            if creator is None:
                self.fail(
                    "The workflow creator account was not saved."
                )

            workflow["created_by_user_id"] = creator["user_id"]

            workflow_saved = insert_workflow(
                workflow,
                database_file,
            )

            connection = get_database_connection(database_file)

            try:
                saved_workflow = connection.execute(
                    """
                    SELECT
                        workflow_id,
                        name,
                        description,
                        status,
                        created_by_user_id,
                        created_at,
                        updated_at
                    FROM workflows
                    WHERE workflow_id = ?
                    """,
                    ("WF-000001",),
                ).fetchone()
            finally:
                connection.close()

            self.assertTrue(workflow_saved)
            self.assertEqual(
                saved_workflow,
                (
                    "WF-000001",
                    "New employee onboarding",
                    "Coordinate onboarding tasks.",
                    "draft",
                    creator["user_id"],
                    "2026-09-05T00:00:00+00:00",
                    "2026-09-05T00:00:00+00:00",
                ),
            )

    def test_insert_workflow_rejects_duplicate_id(self):
        workflow = {
            "workflow_id": "WF-000002",
            "name": "Customer follow-up review",
            "description": "",
            "status": "draft",
            "created_by_user_id": 0,
            "created_at": "2026-09-05T00:00:00+00:00",
            "updated_at": "2026-09-05T00:00:00+00:00",
        }

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            user_created = insert_user_account(
                "WorkflowAdmin",
                "temporary_hash",
                "admin",
                database_file,
            )
            creator = load_user_account_by_username(
                "WorkflowAdmin",
                database_file,
            )

            self.assertTrue(user_created)
            self.assertIsNotNone(creator)

            if creator is None:
                self.fail(
                    "The workflow creator account was not saved."
                )

            workflow["created_by_user_id"] = creator["user_id"]

            first_result = insert_workflow(
                workflow,
                database_file,
            )
            second_result = insert_workflow(
                workflow,
                database_file,
            )

            self.assertTrue(first_result)
            self.assertFalse(second_result)

    def test_load_workflows_returns_saved_records(self):
        workflow = {
            "workflow_id": "WF-000003",
            "name": "Invoice approval process",
            "description": "Review and approve invoices.",
            "status": "draft",
            "created_by_user_id": 0,
            "created_at": "2026-09-05T00:00:00+00:00",
            "updated_at": "2026-09-05T00:00:00+00:00",
        }

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            user_created = insert_user_account(
                "WorkflowAdmin",
                "temporary_hash",
                "admin",
                database_file,
            )
            creator = load_user_account_by_username(
                "WorkflowAdmin",
                database_file,
            )

            self.assertTrue(user_created)
            self.assertIsNotNone(creator)

            if creator is None:
                self.fail(
                    "The workflow creator account was not saved."
                )

            workflow["created_by_user_id"] = creator["user_id"]

            workflow_saved = insert_workflow(
                workflow,
                database_file,
            )
            workflows = load_workflows_from_database(
                database_file,
            )

            self.assertTrue(workflow_saved)
            self.assertEqual(workflows, [workflow])

    def test_load_workflows_returns_empty_list(self):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            workflows = load_workflows_from_database(
                database_file,
            )

            self.assertEqual(workflows, [])

    def test_users_table_rejects_duplicate_username_case(self):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

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
                        "Dennis",
                        "temporary_hash",
                        "admin",
                    ),
                )
                connection.commit()

                with self.assertRaises(sqlite3.IntegrityError):
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
                            "dennis",
                            "another_temporary_hash",
                            "viewer",
                        ),
                    )
            finally:
                connection.close()

    def test_users_table_rejects_unsupported_role(self):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            initialize_database(database_file)
            connection = get_database_connection(database_file)

            try:
                with self.assertRaises(sqlite3.IntegrityError):
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
                            "Dennis",
                            "temporary_hash",
                            "manager",
                        ),
                    )
            finally:
                connection.close()

    def test_new_user_is_active_by_default(self):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

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
                        "Dennis",
                        "temporary_hash",
                        "admin",
                    ),
                )
                connection.commit()

                stored_user = connection.execute(
                    """
                    SELECT is_active
                    FROM users
                    WHERE username = ?
                    """,
                    ("Dennis",),
                ).fetchone()
            finally:
                connection.close()

            self.assertIsNotNone(stored_user)
            self.assertEqual(stored_user[0], 1)

    def test_insert_user_account_saves_protected_record(self):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            insert_result = insert_user_account(
                "Dennis",
                "protected_hash",
                "admin",
                database_file,
            )

            connection = get_database_connection(database_file)

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
                    ("Dennis",),
                ).fetchone()
            finally:
                connection.close()

            self.assertTrue(insert_result)
            self.assertEqual(
                stored_user,
                (
                    1,
                    "Dennis",
                    "protected_hash",
                    "admin",
                    1,
                ),
            )

    def test_insert_user_account_rejects_duplicate_username(self):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            first_result = insert_user_account(
                "Dennis",
                "first_protected_hash",
                "admin",
                database_file,
            )
            duplicate_result = insert_user_account(
                "dennis",
                "second_protected_hash",
                "viewer",
                database_file,
            )

            connection = get_database_connection(database_file)

            try:
                user_count = connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM users
                    """
                ).fetchone()[0]
            finally:
                connection.close()

            self.assertTrue(first_result)
            self.assertFalse(duplicate_result)
            self.assertEqual(user_count, 1)

    def test_load_user_account_by_username_returns_account(self):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            insert_result = insert_user_account(
                "Dennis",
                "protected_hash",
                "admin",
                database_file,
            )
            loaded_user = load_user_account_by_username(
                "dennis",
                database_file,
            )

            self.assertTrue(insert_result)
            self.assertEqual(
                loaded_user,
                {
                    "user_id": 1,
                    "username": "Dennis",
                    "password_hash": "protected_hash",
                    "role": "admin",
                    "is_active": True,
                },
            )

    def test_load_user_account_returns_none_when_missing(self):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            loaded_user = load_user_account_by_username(
                "MissingUser",
                database_file,
            )

            self.assertIsNone(loaded_user)
            self.assertTrue(database_file.exists())

    def test_insert_employee_saves_record(self):
        employee = {
            "employee_id": "EMP001",
            "name": "Dennis",
            "department": "Automation",
            "position": "Developer",
            "country": "Philippines",
            "salary": 60000,
            "email": "dennis@example.com",
            "phone_number": "09123456789",
            "years_of_experience": 2,
            "company": "ABC Company",
            "employment_status": "Active",
            "performance_score": 90,
        }

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            initialize_database(database_file)

            result = insert_employee(
                employee,
                database_file,
            )

            connection = get_database_connection(database_file)

            try:
                saved_employee = connection.execute(
                    """
                    SELECT employee_id, name, salary
                    FROM employees
                    WHERE employee_id = ?
                    """,
                    ("EMP001",),
                ).fetchone()
            finally:
                connection.close()

            self.assertTrue(result)
            self.assertEqual(
                saved_employee,
                ("EMP001", "Dennis", 60000),
            )

    def test_insert_employee_rejects_duplicate_id(self):
        employee = {
            "employee_id": "EMP001",
            "name": "Dennis",
            "department": "Automation",
            "position": "Developer",
            "country": "Philippines",
            "salary": 60000,
            "email": "dennis@example.com",
            "phone_number": "09123456789",
            "years_of_experience": 2,
            "company": "ABC Company",
            "employment_status": "Active",
            "performance_score": 90,
        }

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            initialize_database(database_file)

            first_result = insert_employee(
                employee,
                database_file,
            )
            second_result = insert_employee(
                employee,
                database_file,
            )

            self.assertTrue(first_result)
            self.assertFalse(second_result)

    def test_load_employees_returns_empty_list(self):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            initialize_database(database_file)

            employees = load_employees_from_database(
                database_file,
            )

            self.assertEqual(employees, [])

    def test_load_employees_returns_saved_records(self):
        employee = {
            "employee_id": "EMP002",
            "name": "Maria",
            "department": "Finance",
            "position": "Accountant",
            "country": "Philippines",
            "salary": 50000,
            "email": "maria@example.com",
            "phone_number": "09987654321",
            "years_of_experience": 3,
            "company": "ABC Company",
            "employment_status": "Active",
            "performance_score": 85,
        }

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            initialize_database(database_file)
            insert_employee(employee, database_file)

            employees = load_employees_from_database(
                database_file,
            )

            self.assertEqual(employees, [employee])

    def test_update_employee_changes_saved_record(self):
        employee = {
            "employee_id": "EMP001",
            "name": "Dennis",
            "department": "Automation",
            "position": "Developer",
            "country": "Philippines",
            "salary": 60000,
            "email": "dennis@example.com",
            "phone_number": "09123456789",
            "years_of_experience": 2,
            "company": "ABC Company",
            "employment_status": "Active",
            "performance_score": 90,
        }

        updated_employee = employee.copy()
        updated_employee["position"] = "Senior Developer"
        updated_employee["salary"] = 75000

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            initialize_database(database_file)
            insert_employee(employee, database_file)

            result = update_employee_in_database(
                updated_employee,
                database_file,
            )
            saved_employees = load_employees_from_database(
                database_file,
            )

            self.assertTrue(result)
            self.assertEqual(
                saved_employees,
                [updated_employee],
            )

    def test_update_employee_returns_false_when_not_found(self):
        employee = {
            "employee_id": "EMP999",
            "name": "Missing Employee",
            "department": "Unknown",
            "position": "Unknown",
            "country": "Philippines",
            "salary": 30000,
            "email": "missing@example.com",
            "phone_number": "09000000000",
            "years_of_experience": 0,
            "company": "ABC Company",
            "employment_status": "Active",
            "performance_score": 70,
        }

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            initialize_database(database_file)

            result = update_employee_in_database(
                employee,
                database_file,
            )
            saved_employees = load_employees_from_database(
                database_file,
            )

            self.assertFalse(result)
            self.assertEqual(saved_employees, [])

    def test_delete_employee_removes_saved_record(self):
        employee = {
            "employee_id": "EMP001",
            "name": "Dennis",
            "department": "Automation",
            "position": "Developer",
            "country": "Philippines",
            "salary": 60000,
            "email": "dennis@example.com",
            "phone_number": "09123456789",
            "years_of_experience": 2,
            "company": "ABC Company",
            "employment_status": "Active",
            "performance_score": 90,
        }

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            initialize_database(database_file)
            insert_employee(employee, database_file)

            result = delete_employee_from_database(
                "EMP001",
                database_file,
            )
            saved_employees = load_employees_from_database(
                database_file,
            )

            self.assertTrue(result)
            self.assertEqual(saved_employees, [])

    def test_delete_employee_returns_false_when_not_found(self):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            initialize_database(database_file)

            result = delete_employee_from_database(
                "EMP999",
                database_file,
            )
            saved_employees = load_employees_from_database(
                database_file,
            )

            self.assertFalse(result)
            self.assertEqual(saved_employees, [])

    def test_migrate_empty_list_returns_zero(self):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            migrated_count = migrate_employees_to_database(
                [],
                database_file,
            )
            saved_employees = load_employees_from_database(
                database_file,
            )

            self.assertEqual(migrated_count, 0)
            self.assertEqual(saved_employees, [])

    def test_migrate_employees_saves_all_records(self):
        employees = [
            {
                "employee_id": "EMP001",
                "name": "Dennis",
                "department": "Automation",
                "position": "Developer",
                "country": "Philippines",
                "salary": 60000,
                "email": "dennis@example.com",
                "phone_number": "09123456789",
                "years_of_experience": 2,
                "company": "ABC Company",
                "employment_status": "Active",
                "performance_score": 90,
            },
            {
                "employee_id": "EMP002",
                "name": "Maria",
                "department": "Finance",
                "position": "Accountant",
                "country": "Philippines",
                "salary": 50000,
                "email": "maria@example.com",
                "phone_number": "09987654321",
                "years_of_experience": 3,
                "company": "ABC Company",
                "employment_status": "Active",
                "performance_score": 85,
            },
        ]

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            migrated_count = migrate_employees_to_database(
                employees,
                database_file,
            )
            saved_employees = load_employees_from_database(
                database_file,
            )

            self.assertEqual(migrated_count, 2)
            self.assertEqual(saved_employees, employees)

    def test_migrate_employees_skips_existing_ids(self):
        employee = {
            "employee_id": "EMP001",
            "name": "Dennis",
            "department": "Automation",
            "position": "Developer",
            "country": "Philippines",
            "salary": 60000,
            "email": "dennis@example.com",
            "phone_number": "09123456789",
            "years_of_experience": 2,
            "company": "ABC Company",
            "employment_status": "Active",
            "performance_score": 90,
        }

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            first_count = migrate_employees_to_database(
                [employee],
                database_file,
            )
            second_count = migrate_employees_to_database(
                [employee],
                database_file,
            )
            saved_employees = load_employees_from_database(
                database_file,
            )

            self.assertEqual(first_count, 1)
            self.assertEqual(second_count, 0)
            self.assertEqual(saved_employees, [employee])

    def test_synchronize_employees_saves_complete_list(self):
        employee = {
            "employee_id": "EMP001",
            "name": "Dennis",
            "department": "Automation",
            "position": "Developer",
            "country": "Philippines",
            "salary": 60000,
            "email": "dennis@example.com",
            "phone_number": "09123456789",
            "years_of_experience": 2,
            "company": "ABC Company",
            "employment_status": "Active",
            "performance_score": 90,
        }

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            result = synchronize_employees_to_database(
                [employee],
                database_file,
            )
            saved_employees = load_employees_from_database(
                database_file,
            )

            self.assertTrue(result)
            self.assertEqual(
                saved_employees,
                [employee],
            )

    def test_synchronize_empty_list_clears_database(self):
        employee = {
            "employee_id": "EMP001",
            "name": "Dennis",
            "department": "Automation",
            "position": "Developer",
            "country": "Philippines",
            "salary": 60000,
            "email": "dennis@example.com",
            "phone_number": "09123456789",
            "years_of_experience": 2,
            "company": "ABC Company",
            "employment_status": "Active",
            "performance_score": 90,
        }

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            first_result = synchronize_employees_to_database(
                [employee],
                database_file,
            )
            clear_result = synchronize_employees_to_database(
                [],
                database_file,
            )
            saved_employees = load_employees_from_database(
                database_file,
            )

            self.assertTrue(first_result)
            self.assertTrue(clear_result)
            self.assertEqual(saved_employees, [])

    def test_count_user_accounts_returns_current_total(self):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            empty_count = count_user_accounts(
                database_file
            )
            insert_result = insert_user_account(
                "Dennis",
                "protected_hash",
                "admin",
                database_file,
            )
            account_count = count_user_accounts(
                database_file
            )

            self.assertEqual(empty_count, 0)
            self.assertTrue(insert_result)
            self.assertEqual(account_count, 1)

    def test_load_user_account_summaries_returns_safe_sorted_accounts(
        self,
    ):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            first_insert_result = insert_user_account(
                "ZoeAdmin",
                "first_protected_hash",
                "admin",
                database_file,
            )
            second_insert_result = insert_user_account(
                "aliceViewer",
                "second_protected_hash",
                "viewer",
                database_file,
            )

            user_account_summaries = load_user_account_summaries(
                database_file
            )

        self.assertTrue(first_insert_result)
        self.assertTrue(second_insert_result)
        self.assertEqual(
            user_account_summaries,
            [
                {
                    "user_id": 2,
                    "username": "aliceViewer",
                    "role": "viewer",
                    "is_active": True,
                },
                {
                    "user_id": 1,
                    "username": "ZoeAdmin",
                    "role": "admin",
                    "is_active": True,
                },
            ],
        )
        self.assertNotIn(
            "password_hash",
            user_account_summaries[0],
        )

    def test_load_user_account_summaries_returns_none_for_invalid_database(
        self,
    ):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )
            database_file.write_text(
                "This is not a SQLite database.",
                encoding="utf-8",
            )

            user_account_summaries = load_user_account_summaries(
                database_file
            )

        self.assertIsNone(user_account_summaries)

    def test_update_user_account_active_status_deactivates_account(
        self,
    ):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            insert_result = insert_user_account(
                "ReportViewer",
                "protected_hash",
                "viewer",
                database_file,
            )
            update_result = update_user_account_active_status(
                "ReportViewer",
                False,
                database_file,
            )
            stored_user = load_user_account_by_username(
                "ReportViewer",
                database_file,
            )

            self.assertTrue(insert_result)
            self.assertTrue(update_result)
            self.assertIsNotNone(stored_user)

            if stored_user is None:
                self.fail("The updated user account was not found.")

            self.assertFalse(stored_user["is_active"])

    def test_update_user_account_active_status_reactivates_account(
        self,
    ):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            insert_result = insert_user_account(
                "ReportViewer",
                "protected_hash",
                "viewer",
                database_file,
            )
            deactivation_result = (
                update_user_account_active_status(
                    "ReportViewer",
                    False,
                    database_file,
                )
            )
            reactivation_result = (
                update_user_account_active_status(
                    "ReportViewer",
                    True,
                    database_file,
                )
            )
            stored_user = load_user_account_by_username(
                "ReportViewer",
                database_file,
            )

            self.assertTrue(insert_result)
            self.assertTrue(deactivation_result)
            self.assertTrue(reactivation_result)
            self.assertIsNotNone(stored_user)

            if stored_user is None:
                self.fail("The reactivated user account was not found.")

            self.assertTrue(stored_user["is_active"])

    def test_update_user_account_active_status_returns_false_when_missing(
        self,
    ):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            update_result = update_user_account_active_status(
                "MissingUser",
                False,
                database_file,
            )
            stored_user = load_user_account_by_username(
                "MissingUser",
                database_file,
            )

            self.assertFalse(update_result)
            self.assertIsNone(stored_user)

    def test_update_user_account_password_hash_replaces_saved_hash(
        self,
    ):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            insert_result = insert_user_account(
                "ReportViewer",
                "original_protected_hash",
                "viewer",
                database_file,
            )
            update_result = update_user_account_password_hash(
                "ReportViewer",
                "replacement_protected_hash",
                database_file,
            )
            stored_user = load_user_account_by_username(
                "ReportViewer",
                database_file,
            )

            self.assertTrue(insert_result)
            self.assertTrue(update_result)
            self.assertIsNotNone(stored_user)

            if stored_user is None:
                self.fail("The updated user account was not found.")

            self.assertEqual(
                stored_user["password_hash"],
                "replacement_protected_hash",
            )
            self.assertEqual(
                stored_user["role"],
                "viewer",
            )
            self.assertTrue(stored_user["is_active"])

    def test_update_user_account_password_hash_returns_false_when_missing(
        self,
    ):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            update_result = update_user_account_password_hash(
                "MissingViewer",
                "replacement_protected_hash",
                database_file,
            )
            stored_user = load_user_account_by_username(
                "MissingViewer",
                database_file,
            )

            self.assertFalse(update_result)
            self.assertIsNone(stored_user)



if __name__ == "__main__":
    unittest.main()