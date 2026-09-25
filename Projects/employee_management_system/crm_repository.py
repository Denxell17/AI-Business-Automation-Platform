"""Database operations for leads, customers, notes, and durable CRM history."""

import sqlite3
from pathlib import Path
from uuid import uuid4

from database import DATABASE_FILE, get_database_connection, initialize_database
from database_config import DATABASE_BACKEND_POSTGRESQL, load_database_settings


def _connection(database_file: Path):
    initialize_database(database_file)
    connection = get_database_connection(database_file)
    connection.row_factory = sqlite3.Row
    return connection


def _as_dict(row):
    return dict(row) if row is not None else None


def _audit(connection, entity_type, entity_id, event_type, actor_user_id, now):
    connection.execute(
        """INSERT INTO crm_audit_events
           (event_id, entity_type, entity_id, event_type, actor_user_id, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (str(uuid4()), entity_type, entity_id, event_type, actor_user_id, now),
    )


def list_assignable_owners(database_file: Path = DATABASE_FILE) -> list[dict]:
    connection = _connection(database_file)
    try:
        return [dict(row) for row in connection.execute(
            """SELECT user_id, username FROM users WHERE is_active = ?
               ORDER BY LOWER(username) LIMIT 100""", (True,),
        ).fetchall()]
    finally:
        connection.close()


def owner_is_active(owner_user_id: int | None, database_file: Path = DATABASE_FILE) -> bool:
    if owner_user_id is None:
        return True
    connection = _connection(database_file)
    try:
        return connection.execute(
            "SELECT 1 FROM users WHERE user_id = ? AND is_active = ?",
            (owner_user_id, True),
        ).fetchone() is not None
    finally:
        connection.close()


def create_lead_record(lead: dict, actor_user_id: int, database_file: Path = DATABASE_FILE):
    connection = _connection(database_file)
    try:
        connection.execute(
            """INSERT INTO leads
               (lead_id, name, email, phone_number, company, stage,
                owner_user_id, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (lead["lead_id"], lead["name"], lead["email"],
             lead["phone_number"], lead["company"], lead["stage"],
             lead["owner_user_id"], lead["created_at"], lead["updated_at"]),
        )
        _audit(connection, "lead", lead["lead_id"], "created", actor_user_id, lead["created_at"])
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def list_leads(query: str = "", database_file: Path = DATABASE_FILE) -> list[dict]:
    connection = _connection(database_file)
    try:
        escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        return [dict(row) for row in connection.execute(
            """SELECT l.*, u.username AS owner_username,
                      c.customer_id AS converted_customer_id
               FROM leads l LEFT JOIN users u ON u.user_id = l.owner_user_id
               LEFT JOIN customers c ON c.source_lead_id = l.lead_id
               WHERE LOWER(l.name) LIKE LOWER(?) ESCAPE '\\'
                  OR LOWER(l.email) LIKE LOWER(?) ESCAPE '\\'
                  OR LOWER(l.company) LIKE LOWER(?) ESCAPE '\\'
               ORDER BY l.created_at DESC, l.lead_id DESC LIMIT 100""",
            (pattern, pattern, pattern),
        ).fetchall()]
    finally:
        connection.close()


def load_lead(lead_id: str, database_file: Path = DATABASE_FILE) -> dict | None:
    connection = _connection(database_file)
    try:
        return _as_dict(connection.execute(
            """SELECT l.*, u.username AS owner_username,
                      c.customer_id AS converted_customer_id
               FROM leads l LEFT JOIN users u ON u.user_id = l.owner_user_id
               LEFT JOIN customers c ON c.source_lead_id = l.lead_id
               WHERE l.lead_id = ?""", (lead_id,),
        ).fetchone())
    finally:
        connection.close()


def update_lead_record(lead_id: str, expected_stage: str, values: dict, actor_user_id: int,
                       now: str, database_file: Path = DATABASE_FILE) -> bool:
    connection = _connection(database_file)
    try:
        connection.execute("BEGIN IMMEDIATE")
        cursor = connection.execute(
            """UPDATE leads SET name = ?, email = ?, phone_number = ?,
               company = ?, stage = ?, owner_user_id = ?, updated_at = ?
               WHERE lead_id = ? AND stage = ? AND stage <> 'converted'""",
            (values["name"], values["email"], values["phone_number"],
             values["company"], values["stage"], values["owner_user_id"],
             now, lead_id, expected_stage),
        )
        if cursor.rowcount != 1:
            connection.rollback()
            return False
        _audit(connection, "lead", lead_id, "updated", actor_user_id, now)
        connection.commit()
        return True
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def add_lead_note_record(lead_id: str, body: str, actor_user_id: int,
                         now: str, database_file: Path = DATABASE_FILE) -> str | None:
    note_id = str(uuid4())
    connection = _connection(database_file)
    try:
        connection.execute("BEGIN IMMEDIATE")
        lock = (" FOR UPDATE" if load_database_settings()["backend"] == DATABASE_BACKEND_POSTGRESQL else "")
        lead = connection.execute("SELECT stage FROM leads WHERE lead_id = ?" + lock, (lead_id,)).fetchone()
        if lead is None or lead["stage"] == "converted":
            connection.rollback()
            return None
        connection.execute(
            """INSERT INTO lead_notes
               (note_id, lead_id, body, created_by_user_id, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (note_id, lead_id, body, actor_user_id, now),
        )
        _audit(connection, "lead", lead_id, "note_added", actor_user_id, now)
        connection.commit()
        return note_id
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def list_lead_notes(lead_id: str, database_file: Path = DATABASE_FILE) -> list[dict]:
    connection = _connection(database_file)
    try:
        return [dict(row) for row in connection.execute(
            """SELECT n.note_id, n.body, n.created_at, u.username
               FROM lead_notes n JOIN users u ON u.user_id = n.created_by_user_id
               WHERE n.lead_id = ? ORDER BY n.created_at DESC, n.note_id DESC
               LIMIT 100""", (lead_id,),
        ).fetchall()]
    finally:
        connection.close()


def convert_lead_record(lead_id: str, customer_id: str, actor_user_id: int,
                        now: str, database_file: Path = DATABASE_FILE) -> str | None:
    connection = _connection(database_file)
    try:
        connection.execute("BEGIN IMMEDIATE")
        lock = (" FOR UPDATE" if load_database_settings()["backend"] == DATABASE_BACKEND_POSTGRESQL else "")
        lead = connection.execute(
            "SELECT * FROM leads WHERE lead_id = ?" + lock, (lead_id,),
        ).fetchone()
        if lead is None or lead["stage"] != "qualified":
            connection.rollback()
            return None
        connection.execute(
            """INSERT INTO customers
               (customer_id, source_lead_id, name, email, phone_number,
                company, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)""",
            (customer_id, lead_id, lead["name"], lead["email"],
             lead["phone_number"], lead["company"], now, now),
        )
        connection.execute(
            "UPDATE leads SET stage = 'converted', updated_at = ? WHERE lead_id = ?",
            (now, lead_id),
        )
        _audit(connection, "lead", lead_id, "converted", actor_user_id, now)
        _audit(connection, "customer", customer_id, "created", actor_user_id, now)
        connection.commit()
        return customer_id
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def list_customers(query: str = "", database_file: Path = DATABASE_FILE) -> list[dict]:
    connection = _connection(database_file)
    try:
        escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        return [dict(row) for row in connection.execute(
            """SELECT * FROM customers
               WHERE LOWER(name) LIKE LOWER(?) ESCAPE '\\'
                  OR LOWER(email) LIKE LOWER(?) ESCAPE '\\'
                  OR LOWER(company) LIKE LOWER(?) ESCAPE '\\'
               ORDER BY created_at DESC, customer_id DESC LIMIT 100""",
            (pattern, pattern, pattern),
        ).fetchall()]
    finally:
        connection.close()


def load_customer(customer_id: str, database_file: Path = DATABASE_FILE) -> dict | None:
    connection = _connection(database_file)
    try:
        return _as_dict(connection.execute(
            "SELECT * FROM customers WHERE customer_id = ?", (customer_id,),
        ).fetchone())
    finally:
        connection.close()


def update_customer_record(customer_id: str, values: dict, actor_user_id: int,
                           now: str, database_file: Path = DATABASE_FILE) -> bool:
    connection = _connection(database_file)
    try:
        cursor = connection.execute(
            """UPDATE customers SET name = ?, email = ?, phone_number = ?,
               company = ?, status = ?, updated_at = ? WHERE customer_id = ?""",
            (values["name"], values["email"], values["phone_number"],
             values["company"], values["status"], now, customer_id),
        )
        if cursor.rowcount != 1:
            connection.rollback()
            return False
        _audit(connection, "customer", customer_id, "updated", actor_user_id, now)
        connection.commit()
        return True
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def list_crm_history(entity_type: str, entity_id: str,
                     database_file: Path = DATABASE_FILE) -> list[dict]:
    connection = _connection(database_file)
    try:
        return [dict(row) for row in connection.execute(
            """SELECT e.event_type, e.created_at, u.username
               FROM crm_audit_events e JOIN users u ON u.user_id = e.actor_user_id
               WHERE e.entity_type = ? AND e.entity_id = ?
               ORDER BY e.created_at DESC, e.event_id DESC LIMIT 100""",
            (entity_type, entity_id),
        ).fetchall()]
    finally:
        connection.close()
