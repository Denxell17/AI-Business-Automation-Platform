"""Validation and lifecycle rules for the CRM domain."""

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from authorization import MANAGE_CRM, user_has_permission
from crm_repository import (
    add_lead_note_record,
    convert_lead_record,
    create_lead_record,
    load_customer,
    load_lead,
    owner_is_active,
    update_customer_record,
    update_lead_record,
)
from database import DATABASE_FILE
from models import CUSTOMER_STATUSES, LEAD_STAGES, UserAccount


ALLOWED_LEAD_STAGE_TRANSITIONS = {
    "new": {"new", "contacted", "unqualified"},
    "contacted": {"contacted", "qualified", "unqualified"},
    "qualified": {"qualified", "contacted", "unqualified"},
    "unqualified": {"unqualified", "contacted"},
    "converted": {"converted"},
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_manager(actor: UserAccount) -> None:
    if not user_has_permission(actor, MANAGE_CRM):
        raise PermissionError("CRM management is not allowed.")


def _text(value: str, label: str, maximum: int, *, required=False) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} is invalid.")
    cleaned = value.strip()
    if len(cleaned) > maximum or (required and not cleaned) or "\x00" in cleaned:
        raise ValueError(f"{label} is invalid.")
    return cleaned


def validate_contact(name: str, email: str, phone_number: str, company: str) -> dict:
    values = {
        "name": _text(name, "Name", 120, required=True),
        "email": _text(email, "Email", 254),
        "phone_number": _text(phone_number, "Phone number", 40),
        "company": _text(company, "Company", 120),
    }
    if values["email"]:
        address = values["email"]
        if (address.count("@") != 1 or " " in address or
                not address.split("@", 1)[0] or "." not in address.split("@", 1)[1]):
            raise ValueError("Email is invalid.")
    return values


def _owner(owner_user_id: int | None, database_file: Path) -> int | None:
    if owner_user_id is not None:
        if isinstance(owner_user_id, bool) or not isinstance(owner_user_id, int):
            raise ValueError("Owner is invalid.")
        if not owner_is_active(owner_user_id, database_file):
            raise ValueError("Owner must be an active user.")
    return owner_user_id


def create_lead(actor: UserAccount, name: str, email: str = "",
                phone_number: str = "", company: str = "",
                owner_user_id: int | None = None,
                database_file: Path = DATABASE_FILE) -> str:
    _require_manager(actor)
    values = validate_contact(name, email, phone_number, company)
    now = _now()
    lead_id = str(uuid4())
    create_lead_record({
        "lead_id": lead_id, **values, "stage": "new",
        "owner_user_id": _owner(owner_user_id, database_file),
        "created_at": now, "updated_at": now,
    }, actor["user_id"], database_file)
    return lead_id


def update_lead(actor: UserAccount, lead_id: str, name: str, email: str,
                phone_number: str, company: str, stage: str,
                owner_user_id: int | None,
                database_file: Path = DATABASE_FILE) -> bool:
    _require_manager(actor)
    existing = load_lead(lead_id, database_file)
    if existing is None or existing["stage"] == "converted":
        return False
    normalized_stage = _text(stage, "Stage", 30)
    if normalized_stage not in LEAD_STAGES or normalized_stage == "converted":
        raise ValueError("Lead stage is invalid.")
    if normalized_stage not in ALLOWED_LEAD_STAGE_TRANSITIONS[existing["stage"]]:
        raise ValueError("Lead stage transition is invalid.")
    values = validate_contact(name, email, phone_number, company)
    values.update(stage=normalized_stage,
                  owner_user_id=_owner(owner_user_id, database_file))
    return update_lead_record(lead_id, existing["stage"], values,
                              actor["user_id"], _now(), database_file)


def add_lead_note(actor: UserAccount, lead_id: str, body: str,
                  database_file: Path = DATABASE_FILE) -> str | None:
    _require_manager(actor)
    normalized_body = _text(body, "Note", 2000, required=True)
    return add_lead_note_record(lead_id, normalized_body, actor["user_id"],
                                _now(), database_file)


def convert_lead(actor: UserAccount, lead_id: str,
                 database_file: Path = DATABASE_FILE) -> str | None:
    _require_manager(actor)
    existing = load_lead(lead_id, database_file)
    if existing is None:
        return None
    if existing["converted_customer_id"]:
        return existing["converted_customer_id"]
    customer_id = convert_lead_record(lead_id, str(uuid4()), actor["user_id"],
                                      _now(), database_file)
    if customer_id is not None:
        return customer_id
    latest = load_lead(lead_id, database_file)
    return latest["converted_customer_id"] if latest else None


def update_customer(actor: UserAccount, customer_id: str, name: str,
                    email: str, phone_number: str, company: str, status: str,
                    database_file: Path = DATABASE_FILE) -> bool:
    _require_manager(actor)
    if load_customer(customer_id, database_file) is None:
        return False
    normalized_status = _text(status, "Status", 20)
    if normalized_status not in CUSTOMER_STATUSES:
        raise ValueError("Customer status is invalid.")
    values = validate_contact(name, email, phone_number, company)
    values["status"] = normalized_status
    return update_customer_record(customer_id, values, actor["user_id"],
                                  _now(), database_file)
