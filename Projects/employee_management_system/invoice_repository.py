"""Persistence operations for immutable invoices and private documents."""

import sqlite3
from pathlib import Path
from uuid import uuid4

from database import DATABASE_FILE, get_database_connection, initialize_database


def _connection(database_file: Path):
    initialize_database(database_file)
    connection = get_database_connection(database_file)
    connection.row_factory = sqlite3.Row
    return connection


def _rows(rows):
    return [dict(row) for row in rows]


def list_invoice_customers(database_file: Path = DATABASE_FILE) -> list[dict]:
    connection = _connection(database_file)
    try:
        return _rows(connection.execute(
            """SELECT customer_id, name, company FROM customers
               WHERE status = 'active' ORDER BY LOWER(name), customer_id LIMIT 200"""
        ).fetchall())
    finally:
        connection.close()


def load_invoice(invoice_id: str, database_file: Path = DATABASE_FILE) -> dict | None:
    connection = _connection(database_file)
    try:
        row = connection.execute(
            """SELECT i.*, c.name AS customer_name, c.company AS customer_company
               FROM invoices i JOIN customers c ON c.customer_id = i.customer_id
               WHERE i.invoice_id = ?""", (invoice_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        connection.close()


def list_invoices(customer_id: str | None = None, database_file: Path = DATABASE_FILE) -> list[dict]:
    connection = _connection(database_file)
    try:
        query = """SELECT i.*, c.name AS customer_name FROM invoices i
                   JOIN customers c ON c.customer_id = i.customer_id"""
        parameters: tuple = ()
        if customer_id:
            query += " WHERE i.customer_id = ?"
            parameters = (customer_id,)
        query += " ORDER BY i.created_at DESC, i.invoice_id DESC LIMIT 100"
        return _rows(connection.execute(query, parameters).fetchall())
    finally:
        connection.close()


def load_invoice_line_items(invoice_id: str, database_file: Path = DATABASE_FILE) -> list[dict]:
    connection = _connection(database_file)
    try:
        return _rows(connection.execute(
            """SELECT * FROM invoice_line_items WHERE invoice_id = ?
               ORDER BY line_number""", (invoice_id,)
        ).fetchall())
    finally:
        connection.close()


def load_invoice_events(invoice_id: str, database_file: Path = DATABASE_FILE) -> list[dict]:
    connection = _connection(database_file)
    try:
        return _rows(connection.execute(
            """SELECT e.status, e.created_at, u.username
               FROM invoice_payment_events e JOIN users u ON u.user_id = e.actor_user_id
               WHERE e.invoice_id = ? ORDER BY e.created_at DESC, e.event_id DESC""",
            (invoice_id,)
        ).fetchall())
    finally:
        connection.close()


def create_invoice_record(invoice: dict, line_items: list[dict], database_file: Path = DATABASE_FILE) -> bool:
    connection = _connection(database_file)
    try:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            """INSERT INTO invoices (invoice_id, customer_id, invoice_number, currency,
               status, due_date, subtotal_cents, tax_cents, total_cents,
               created_by_user_id, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            tuple(invoice[key] for key in (
                "invoice_id", "customer_id", "invoice_number", "currency", "status",
                "due_date", "subtotal_cents", "tax_cents", "total_cents",
                "created_by_user_id", "created_at", "updated_at")),
        )
        connection.executemany(
            """INSERT INTO invoice_line_items (line_item_id, invoice_id, line_number,
               description, quantity, unit_price_cents, tax_rate_basis_points,
               line_subtotal_cents, line_tax_cents, line_total_cents)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [tuple(line[key] for key in (
                "line_item_id", "invoice_id", "line_number", "description", "quantity",
                "unit_price_cents", "tax_rate_basis_points", "line_subtotal_cents",
                "line_tax_cents", "line_total_cents")) for line in line_items],
        )
        connection.execute(
            """INSERT INTO invoice_payment_events (event_id, invoice_id, status,
               actor_user_id, created_at) VALUES (?, ?, ?, ?, ?)""",
            (str(uuid4()), invoice["invoice_id"], "draft", invoice["created_by_user_id"], invoice["created_at"]),
        )
        connection.commit()
        return True
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def transition_invoice_status(invoice_id: str, expected_status: str, new_status: str,
                              actor_user_id: int, now: str,
                              database_file: Path = DATABASE_FILE) -> bool:
    connection = _connection(database_file)
    try:
        connection.execute("BEGIN IMMEDIATE")
        updated = connection.execute(
            """UPDATE invoices SET status = ?, updated_at = ?
               WHERE invoice_id = ? AND status = ?""",
            (new_status, now, invoice_id, expected_status),
        )
        if updated.rowcount != 1:
            connection.rollback()
            return False
        connection.execute(
            """INSERT INTO invoice_payment_events (event_id, invoice_id, status,
               actor_user_id, created_at) VALUES (?, ?, ?, ?, ?)""",
            (str(uuid4()), invoice_id, new_status, actor_user_id, now),
        )
        connection.commit()
        return True
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def load_invoice_document(invoice_id: str, database_file: Path = DATABASE_FILE) -> dict | None:
    connection = _connection(database_file)
    try:
        row = connection.execute(
            "SELECT * FROM protected_documents WHERE invoice_id = ? AND document_type = 'invoice_pdf'",
            (invoice_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        connection.close()


def load_document(document_id: str, database_file: Path = DATABASE_FILE) -> dict | None:
    connection = _connection(database_file)
    try:
        row = connection.execute(
            """SELECT d.*, i.customer_id FROM protected_documents d
               JOIN invoices i ON i.invoice_id = d.invoice_id WHERE d.document_id = ?""",
            (document_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        connection.close()


def create_invoice_document(document: dict, database_file: Path = DATABASE_FILE) -> bool:
    connection = _connection(database_file)
    try:
        connection.execute(
            """INSERT INTO protected_documents (document_id, invoice_id, document_type,
               storage_key, filename, media_type, byte_size, content_sha256,
               created_by_user_id, created_at)
               VALUES (?, ?, 'invoice_pdf', ?, ?, 'application/pdf', ?, ?, ?, ?)""",
            (document["document_id"], document["invoice_id"], document["storage_key"],
             document["filename"], document["byte_size"], document["content_sha256"],
             document["created_by_user_id"], document["created_at"]),
        )
        connection.commit()
        return True
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def list_invoice_workflow_runs(invoice_id: str, database_file: Path = DATABASE_FILE) -> list[dict]:
    connection = _connection(database_file)
    try:
        return _rows(connection.execute(
            """SELECT r.execution_id, r.workflow_id, r.created_at, e.status,
               w.name AS workflow_name FROM invoice_workflow_runs r
               JOIN workflow_executions e ON e.execution_id = r.execution_id
               JOIN workflows w ON w.workflow_id = r.workflow_id
               WHERE r.invoice_id = ? ORDER BY r.created_at DESC""", (invoice_id,)
        ).fetchall())
    finally:
        connection.close()


def link_invoice_workflow_run(invoice_id: str, workflow_id: str, execution_id: str,
                              created_at: str, database_file: Path = DATABASE_FILE) -> bool:
    connection = _connection(database_file)
    try:
        connection.execute(
            """INSERT INTO invoice_workflow_runs (invoice_id, execution_id, workflow_id, created_at)
               VALUES (?, ?, ?, ?)""", (invoice_id, execution_id, workflow_id, created_at)
        )
        connection.commit()
        return True
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
