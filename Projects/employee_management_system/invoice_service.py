"""Invoice validation, decimal-safe calculation, document and workflow services."""

import hashlib
import re
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from uuid import uuid4

from authorization import MANAGE_INVOICES, MANAGE_WORKFLOWS, user_has_permission
from crm_repository import load_customer
from database import DATABASE_FILE, load_workflow_by_id, load_workflows_from_database
from document_storage import DocumentStorage
from invoice_pdf import generate_invoice_pdf
from invoice_repository import (
    create_invoice_document, create_invoice_record, link_invoice_workflow_run,
    load_invoice, load_invoice_document, load_invoice_line_items,
    transition_invoice_status,
)
from models import UserAccount
from workflow_service import start_workflow_execution


MAX_DOCUMENT_BYTES = 2 * 1024 * 1024
INVOICE_NUMBER_PATTERN = re.compile(r"[A-Z0-9][A-Z0-9-]{0,39}")
INVOICE_STATUS_TRANSITIONS = {
    "draft": {"sent", "void"},
    "sent": {"paid", "void"},
    "paid": set(),
    "void": set(),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require(actor: UserAccount, permission: str) -> None:
    if not actor["is_active"] or not user_has_permission(actor, permission):
        raise PermissionError("Invoice access is not allowed.")


def _decimal(value: str, label: str, scale: Decimal, maximum: Decimal) -> Decimal:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} is required.")
    try:
        parsed = Decimal(value.strip())
    except InvalidOperation as error:
        raise ValueError(f"{label} is invalid.") from error
    if not parsed.is_finite() or parsed <= 0 or parsed > maximum:
        raise ValueError(f"{label} is invalid.")
    if parsed.quantize(scale, rounding=ROUND_HALF_UP) != parsed:
        raise ValueError(f"{label} has too many decimal places.")
    return parsed


def calculate_invoice_lines(lines: list[dict]) -> tuple[list[dict], int, int, int]:
    """Round each monetary line half up to cents, then sum snapshots."""
    if not isinstance(lines, list) or not 1 <= len(lines) <= 20:
        raise ValueError("An invoice needs between one and twenty line items.")
    snapshots: list[dict] = []
    for position, input_line in enumerate(lines, start=1):
        if not isinstance(input_line, dict):
            raise ValueError("Invoice line item is invalid.")
        description = input_line.get("description", "")
        if not isinstance(description, str) or not 1 <= len(description.strip()) <= 300:
            raise ValueError("Line description is invalid.")
        quantity = _decimal(str(input_line.get("quantity", "")), "Quantity", Decimal("0.001"), Decimal("999999999.999"))
        price = _decimal(str(input_line.get("unit_price", "")), "Unit price", Decimal("0.01"), Decimal("999999999.99"))
        tax_rate = input_line.get("tax_rate_percent", "0")
        if not isinstance(tax_rate, str):
            raise ValueError("Tax rate is invalid.")
        try:
            tax = Decimal(tax_rate.strip() or "0")
        except InvalidOperation as error:
            raise ValueError("Tax rate is invalid.") from error
        if not tax.is_finite() or tax < 0 or tax > 100 or tax.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) != tax:
            raise ValueError("Tax rate is invalid.")
        subtotal_cents = int((quantity * price * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        tax_basis_points = int((tax * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        tax_cents = int((Decimal(subtotal_cents) * tax_basis_points / 10000).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        snapshots.append({
            "line_item_id": str(uuid4()), "line_number": position,
            "description": description.strip(), "quantity": format(quantity, "f"),
            "unit_price_cents": int(price * 100), "tax_rate_basis_points": tax_basis_points,
            "line_subtotal_cents": subtotal_cents, "line_tax_cents": tax_cents,
            "line_total_cents": subtotal_cents + tax_cents,
        })
    subtotal = sum(line["line_subtotal_cents"] for line in snapshots)
    taxes = sum(line["line_tax_cents"] for line in snapshots)
    return snapshots, subtotal, taxes, subtotal + taxes


def create_invoice(actor: UserAccount, customer_id: str, invoice_number: str,
                   due_date: str, lines: list[dict],
                   database_file: Path = DATABASE_FILE) -> str:
    _require(actor, MANAGE_INVOICES)
    if not isinstance(customer_id, str) or not customer_id.strip():
        raise ValueError("Customer is required.")
    customer = load_customer(customer_id.strip(), database_file)
    if customer is None or customer["status"] != "active":
        raise ValueError("Invoice customer must be active.")
    if not isinstance(invoice_number, str):
        raise ValueError("Invoice number is invalid.")
    normalized_number = invoice_number.strip().upper()
    if INVOICE_NUMBER_PATTERN.fullmatch(normalized_number) is None:
        raise ValueError("Invoice number is invalid.")
    normalized_due_date: str | None = None
    if not isinstance(due_date, str):
        raise ValueError("Due date is invalid.")
    if due_date.strip():
        try:
            normalized_due_date = date.fromisoformat(due_date.strip()).isoformat()
        except ValueError as error:
            raise ValueError("Due date is invalid.") from error
    snapshots, subtotal, taxes, total = calculate_invoice_lines(lines)
    now = _now()
    invoice_id = str(uuid4())
    for line in snapshots:
        line["invoice_id"] = invoice_id
    invoice = {
        "invoice_id": invoice_id, "customer_id": customer["customer_id"],
        "invoice_number": normalized_number, "currency": "USD", "status": "draft",
        "due_date": normalized_due_date, "subtotal_cents": subtotal, "tax_cents": taxes,
        "total_cents": total, "created_by_user_id": actor["user_id"],
        "created_at": now, "updated_at": now,
    }
    create_invoice_record(invoice, snapshots, database_file)
    return invoice_id


def change_invoice_status(actor: UserAccount, invoice_id: str, new_status: str,
                          database_file: Path = DATABASE_FILE) -> bool:
    _require(actor, MANAGE_INVOICES)
    invoice = load_invoice(invoice_id, database_file)
    if invoice is None:
        return False
    normalized_status = new_status.strip().casefold() if isinstance(new_status, str) else ""
    if normalized_status not in INVOICE_STATUS_TRANSITIONS[invoice["status"]]:
        raise ValueError("Invoice status transition is invalid.")
    return transition_invoice_status(invoice_id, invoice["status"], normalized_status,
                                     actor["user_id"], _now(), database_file)


def generate_invoice_document(actor: UserAccount, invoice_id: str, storage: DocumentStorage,
                              database_file: Path = DATABASE_FILE) -> dict | None:
    _require(actor, MANAGE_INVOICES)
    existing = load_invoice_document(invoice_id, database_file)
    if existing is not None:
        return existing
    invoice = load_invoice(invoice_id, database_file)
    if invoice is None:
        return None
    customer = load_customer(invoice["customer_id"], database_file)
    if customer is None:
        return None
    content = generate_invoice_pdf(invoice, customer, load_invoice_line_items(invoice_id, database_file))
    if not content.startswith(b"%PDF-") or len(content) > MAX_DOCUMENT_BYTES:
        raise ValueError("Generated document is invalid.")
    document_id = str(uuid4())
    storage_key = uuid4().hex + ".pdf"
    filename = f"invoice-{invoice['invoice_number']}.pdf"
    document = {
        "document_id": document_id, "invoice_id": invoice_id, "storage_key": storage_key,
        "filename": filename, "byte_size": len(content),
        "content_sha256": hashlib.sha256(content).hexdigest(),
        "created_by_user_id": actor["user_id"], "created_at": _now(),
    }
    storage.save(storage_key, content)
    try:
        create_invoice_document(document, database_file)
    except Exception:
        # A concurrent request may have persisted the invoice document first.
        concurrent = load_invoice_document(invoice_id, database_file)
        if concurrent is not None:
            return concurrent
        raise
    return document


def available_invoice_workflows(actor: UserAccount, database_file: Path = DATABASE_FILE) -> list[dict]:
    _require(actor, MANAGE_INVOICES)
    return [workflow for workflow in load_workflows_from_database(database_file)
            if workflow["status"] == "active"]


def trigger_invoice_workflow(actor: UserAccount, invoice_id: str, workflow_id: str,
                             database_file: Path = DATABASE_FILE) -> str | None:
    _require(actor, MANAGE_INVOICES)
    _require(actor, MANAGE_WORKFLOWS)
    if load_invoice(invoice_id, database_file) is None:
        return None
    workflow = load_workflow_by_id(workflow_id.strip().upper(), database_file)
    if workflow is None or workflow["status"] != "active":
        raise ValueError("Workflow must be active.")
    execution = start_workflow_execution(actor, workflow["workflow_id"], database_file)
    if execution is None:
        return None
    link_invoice_workflow_run(invoice_id, workflow["workflow_id"], execution["execution_id"],
                              _now(), database_file)
    return execution["execution_id"]
